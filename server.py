"""Flask HTTP server that proxies requests to an OpenAI-compatible API.

Runs inside a QThread for integration with the PyQt6 GUI.
"""

import json
import time
from typing import Any

from flask import Flask, Response, jsonify, request, stream_with_context
from PyQt6.QtCore import QThread, pyqtSignal
from waitress import serve


def _estimate_tokens(text: str) -> int:
    """Rough token count: ~4 characters per token for mixed Chinese/English."""
    return max(1, len(text) // 4)


def create_app(chat_url: str, api_key: str, model: str) -> Flask:
    """Factory: create a Flask app configured for a specific provider."""

    app = Flask(__name__)

    @app.route("/v1/chat/completions", methods=["POST"])

    @app.route("/chat/completions", methods=["POST"])
    def chat_completions():
        """Proxy chat completion requests to the upstream API."""
        import requests as req

        try:
            data: dict[str, Any] = request.get_json(force=True, silent=True)
        except Exception:
            return jsonify({"error": "Invalid JSON body"}), 400

        if data is None:
            return jsonify({"error": "Missing request body"}), 400

        # Override model with the configured one
        data["model"] = model

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        is_stream = data.get("stream", False)

        try:
            upstream = req.post(
                chat_url,
                json=data,
                headers=headers,
                stream=is_stream,
                timeout=120,
            )
        except req.ConnectionError:
            return jsonify({"error": "Cannot connect to API. Check your network and API address."}), 502
        except req.Timeout:
            return jsonify({"error": "API request timed out."}), 504
        except req.RequestException as e:
            return jsonify({"error": f"API request failed: {e}"}), 502

        if not upstream.ok and not is_stream:
            # Forward the upstream error as-is when possible
            try:
                err_body = upstream.json()
            except Exception:
                err_body = upstream.text
            return jsonify({"error": "Upstream API error", "upstream": err_body}), upstream.status_code

        if is_stream:

            def generate():
                try:
                    for line in upstream.iter_lines(decode_unicode=True):
                        if line:
                            # Pass through SSE lines as-is
                            yield f"{line}\n"
                except Exception:
                    yield 'data: {"error": "Stream interrupted"}\n\n'

            return Response(
                stream_with_context(generate()),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )

        # Non-streaming response
        try:
            result = upstream.json()
        except Exception:
            return jsonify({"error": "Failed to parse upstream response"}), 502

        choice_content = ""
        try:
            choice_content = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            pass

        return jsonify({
            "id": f"chatcmpl-verity-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": choice_content,
                },
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": _estimate_tokens(json.dumps(data.get("messages", []))),
                "completion_tokens": _estimate_tokens(choice_content),
                "total_tokens": _estimate_tokens(
                    json.dumps(data.get("messages", [])) + choice_content
                ),
            },
        })

    return app


class ServerThread(QThread):
    """Run the Flask server in a background thread via Waitress."""

    status_changed = pyqtSignal(str)

    def __init__(
        self,
        chat_url: str,
        api_key: str,
        model: str,
        host: str = "127.0.0.1",
        port: int = 5000,
    ):
        super().__init__()
        self._chat_url = chat_url
        self._api_key = api_key
        self._model = model
        self._host = host
        self._port = port

    def run(self):
        try:
            self.status_changed.emit(f"服务启动中 http://{self._host}:{self._port}/v1/chat/completions")
            app = create_app(self._chat_url, self._api_key, self._model)
            serve(app, host=self._host, port=self._port, threads=4)
        except Exception as e:
            self.status_changed.emit(f"服务器错误: {e}")

    def stop(self):
        """Request graceful shutdown. Waitress exits after current requests finish."""
        self.terminate()
        self.wait(3000)
        self.status_changed.emit("已停止")

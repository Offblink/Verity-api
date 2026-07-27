# Implementation Plan: Verity-api 全面重写

## Design Reference
- `DESIGN.md` — Option B: PyQt6 + Flask in QThread

## Component Map

**NEW FILES:**
- `verity-api/providers.py` — Provider definitions + presets
- `verity-api/server.py` — Flask server + QThread wrapper
- `verity-api/app.py` — PyQt6 main window, settings, system tray
- `verity-api/main.py` — Entry point with dependency check
- `verity-api/requirements.txt` — Dependencies
- `verity-api/README.md` — Documentation

**MODIFIED FILES:**
- `verity-api/verity` — Delete, replaced by above

**ASSETS:**
- Copy `C:\Users\37549\Desktop\icon.ico` → `verity-api/resources/icon.ico`

## Interface Contracts

### `providers.py` exports

```python
@dataclass
class Provider:
    name: str           # Display name
    base_url: str       # API base URL (no trailing /)
    default_model: str  # Default model for this provider
    description: str    # Brief description

PRESET_PROVIDERS: list[Provider]
# OpenAI, DeepSeek, Zhipu (glm-4-flash), Tongyi (qwen-turbo), Moonshot, 自定义
```

### `server.py` exports

```python
class ServerThread(QThread):
    status_changed = pyqtSignal(str)   # "running" / "stopped" / error msg
    request_log = pyqtSignal(str)      # Log each request

    def __init__(self, provider: Provider, api_key: str, model: str, port: int = 5000)
    def run(self)                      # Start Flask
    def stop(self)                     # Graceful shutdown
```

### `app.py` exports

```python
class VerityApp(QMainWindow):
    # PyQt6 main window with provider selector, API key, model, log viewer
    # System tray: minimize on close, double-click restore
    # Help dialog
```

## Tasks

### Task 1: Scaffold project + requirements.txt

**What:** Delete old `verity` file, create directory structure, write `requirements.txt`, copy icon.

**Files:**
- `verity-api/verity` — DELETE
- `verity-api/requirements.txt` — CREATE
- `verity-api/resources/icon.ico` — COPY from desktop

**Acceptance:**
- [ ] `verity-api/verity` no longer exists
- [ ] `requirements.txt` lists: `flask>=3.0`, `requests>=2.31`, `PyQt6>=6.5`, `waitress>=3.0` (production WSGI)
- [ ] `resources/icon.ico` exists (16.6KB)

**Depends on:** none

---

### Task 2: Provider system

**What:** Define `Provider` dataclass and preset providers.

**Files:**
- `verity-api/providers.py` — CREATE

**Acceptance:**
- [ ] `Provider` dataclass with 4 fields
- [ ] At least 5 presets: OpenAI, DeepSeek, 智谱, 通义千问, Moonshot
- [ ] `CUSTOM` sentinel provider
- [ ] `from provider import PRESET_PROVIDERS` works

**Depends on:** none (can run parallel with Task 1)

---

### Task 3: Flask server with all fixes

**What:** Rewrite the HTTP server with proper error handling, streaming support, correct routing, and a QThread wrapper.

**Files:**
- `verity-api/server.py` — CREATE

**Acceptance:**
- [ ] Route: `/v1/chat/completions` (correct LiteLLM path)
- [ ] Proper `try/except` with specific exception types
- [ ] JSON error responses (never `return 0`)
- [ ] `created` field = `int(time.time())` (10-digit Unix timestamp)
- [ ] Model field from config, not hardcoded
- [ ] usage tokens estimated from actual response length (char/4 heuristic)
- [ ] Streaming support (`"stream": true` → SSE)
- [ ] `ServerThread(QThread)` with `status_changed` signal
- [ ] Uses `waitress` for production-grade serving (no Flask dev server warnings)

**Depends on:** Task 2

---

### Task 4: PyQt6 GUI + system tray

**What:** Build the settings window and system tray. Complete UI for provider selection, API key, model, start/stop, and status log.

**Files:**
- `verity-api/app.py` — CREATE

**Acceptance:**
- [ ] Provider dropdown (combo box) with all presets
- [ ] API key field (password mask)
- [ ] Model field (pre-filled from selected provider, editable)
- [ ] Custom base URL (editable, disabled for presets)
- [ ] Start/Stop button
- [ ] Status display showing server state
- [ ] Request log viewer (scrollable)
- [ ] Help button → dialog with usage instructions
- [ ] System tray: `_create_tray_icon()` with context menu (打开主界面 / 退出)
- [ ] `closeEvent` → minimize to tray (not quit)
- [ ] Double-click tray icon → restore window
- [ ] `_quit_application()` properly stops server thread
- [ ] 完全参照 Get It 的托盘模式

**Depends on:** Task 3

---

### Task 5: Entry point

**What:** `main.py` with dependency check (参照 Get It `main.py` 模式).

**Files:**
- `verity-api/main.py` — CREATE

**Acceptance:**
- [ ] `_check_dependencies()` auto-installs missing packages
- [ ] `--minimized` flag support
- [ ] Icon set on QApplication
- [ ] `python main.py` launches the app

**Depends on:** Task 4

---

### Task 6: README

**What:** Write comprehensive README in Chinese.

**Files:**
- `verity-api/README.md` — CREATE

**Acceptance:**
- [ ] Project description (what Verity is, what this proxy does)
- [ ] Installation steps
- [ ] Usage guide
- [ ] Supported providers table
- [ ] Screenshot placeholder

**Depends on:** Task 5

---

## Execution Strategy

- **Sequential:** Tasks 1-2 parallel, then 3, then 4, then 5, then 6
- **Checkpoints:** After Task 3 (verify Flask server works standalone), after Task 5 (full smoke test)

## Global Constraints

### Style
- Python 3.10+ type hints on all function signatures
- Chinese comments OK for user-facing strings, English for code logic
- Follow existing Get It project conventions (naming, structure)
- No bare `except:` anywhere
- `f-string` over `.format()` or `%`

### Testing
- No unit test framework required (small project, smoke test sufficient)
- Smoke test: launch app, start server, `curl` a request, verify response

### Boundaries
- NEVER: introduce new dependencies without updating `requirements.txt`
- NEVER: delete `resources/icon.ico`
- ASK FIRST: change the API response format (must stay OpenAI-compatible)

"""Verity API Proxy — PyQt6 main window with system tray.

Provides a settings UI for configuring the LLM provider and a system-tray icon
that keeps the proxy running in the background.
"""

import os
import sys
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStyle,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from providers import PRESET_PROVIDERS, Provider, find_provider
from server import ServerThread


# --- Help Dialog ---

class HelpDialog(QDialog):
    """Show usage instructions."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("帮助")
        self.setMinimumWidth(480)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setMarkdown("""\
### Verity API Proxy

Verity 是一个 Minecraft 恐怖模组，内置 AI 助手实体。
本程序作为桥梁，将模组的 LiteLLM 请求转发到您配置的大模型 API。

#### 使用方法

1. 选择一个 **Provider**（或选择「自定义」手动输入 API 地址）
2. 填入您的 **API Key**
3. 确认 **模型名称** 正确（会自动填入 Provider 默认值）
4. 点击 **启动服务**
5. 在 Verity 模组的 LiteLLM URL 配置中填入 `http://127.0.0.1:5000/v1/chat/completions`
6. 关闭窗口会最小化到**系统托盘**，服务继续运行

#### 支持的 Provider

| Provider | 默认模型 |
|---|---|
| OpenAI | gpt-4o-mini |
| DeepSeek | deepseek-chat |
| 智谱 (Zhipu) | glm-4-flash |
| 通义千问 (Tongyi) | qwen-turbo |
| Moonshot (Kimi) | moonshot-v1-8k |
| SiliconFlow | Qwen/Qwen2.5-7B-Instruct |

#### 注意事项

- 请确保 API Key 有效且有足够余额
- 关闭窗口不会停止服务，右键托盘图标选择「退出」可彻底关闭
- 本程序仅在本地运行，不会上传您的 API Key
""")
        text.setStyleSheet("QTextEdit { background: transparent; border: none; }")

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(text)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)


# --- About Dialog ---

class AboutDialog(QDialog):
    """Show version and project info."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setFixedSize(360, 200)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Verity API Proxy")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version = QLabel("v1.0.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc = QLabel("为 Minecraft Verity 模组提供 LLM API 代理")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)

        repo = QLabel(
            '<a href="https://github.com/wszzxzzxnb/Verity-api" style="color: #4a9eff;">GitHub</a>'
        )
        repo.setOpenExternalLinks(True)
        repo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(version)
        layout.addWidget(desc)
        layout.addWidget(repo)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)


# --- Main Window ---

class VerityApp(QMainWindow):
    """Main settings window for the Verity API proxy."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Verity API Proxy")
        self.setMinimumSize(520, 580)
        self.resize(520, 620)

        # Icon
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # State
        self._server: Optional[ServerThread] = None

        # UI
        self._create_ui()
        self._create_tray_icon()

    # ========================
    # UI Construction
    # ========================

    def _create_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        # --- Provider group ---
        provider_group = QGroupBox("Provider 配置")
        form = QFormLayout(provider_group)
        form.setSpacing(8)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems([p.name for p in PRESET_PROVIDERS])
        self.provider_combo.addItem("自定义 (Custom)")
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        form.addRow("Provider:", self.provider_combo)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://api.example.com")
        form.addRow("API 地址:", self.url_edit)

        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setPlaceholderText("sk-...")
        form.addRow("API Key:", self.key_edit)

        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("gpt-4o-mini")
        form.addRow("模型:", self.model_edit)

        self.host_edit = QLineEdit("127.0.0.1")
        form.addRow("监听地址:", self.host_edit)

        self.port_edit = QLineEdit("5000")
        form.addRow("端口:", self.port_edit)

        root.addWidget(provider_group)

        # --- Server control ---
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(8)

        self.start_btn = QPushButton("启动服务")
        self.start_btn.setMinimumHeight(36)
        self.start_btn.clicked.connect(self._toggle_server)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 6px 20px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #94a3b8;
            }
        """)
        ctrl_layout.addWidget(self.start_btn)

        self.status_label = QLabel("未启动")
        self.status_label.setStyleSheet("color: #64748b;")
        ctrl_layout.addWidget(self.status_label, stretch=1)

        root.addLayout(ctrl_layout)

        # --- Help row ---
        help_layout = QHBoxLayout()
        help_btn = QPushButton("使用帮助")
        help_btn.clicked.connect(self._show_help)
        about_btn = QPushButton("关于")
        about_btn.clicked.connect(self._show_about)
        help_layout.addWidget(help_btn)
        help_layout.addWidget(about_btn)
        help_layout.addStretch()
        root.addLayout(help_layout)

        # --- Log viewer ---
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(200)
        self.log_view.setStyleSheet("""
            QTextEdit {
                background-color: #1e293b;
                color: #e2e8f0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #334155;
                border-radius: 4px;
            }
        """)
        log_layout.addWidget(self.log_view)
        root.addWidget(log_group)

        # Initialize UI state
        self._on_provider_changed(0)

    # ========================
    # System Tray
    # ========================

    def _create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icon.ico")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            )

        menu = QMenu()
        show_action = QAction("打开主界面", self)
        show_action.triggered.connect(self._restore_from_tray)
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit_application)
        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.setToolTip("Verity API Proxy")
        self.tray_icon.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._restore_from_tray()

    def _minimize_to_tray(self):
        self.hide()
        self.tray_icon.showMessage(
            "Verity API Proxy",
            "已最小化到系统托盘，服务继续运行",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    def _restore_from_tray(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _quit_application(self):
        self._stop_server()
        if self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        """Override: always minimize to tray. Quit only via tray menu."""
        event.ignore()
        self._minimize_to_tray()

    # ========================
    # Server Control
    # ========================

    def _toggle_server(self):
        if self._server and self._server.isRunning():
            self._stop_server()
        else:
            self._start_server()

    def _start_server(self):
        key = self.key_edit.text().strip()
        model = self.model_edit.text().strip()
        url = self.url_edit.text().strip()

        if not key:
            self._log("错误: 请填写 API Key")
            return
        if not model:
            self._log("错误: 请填写模型名称")
            return
        if not url:
            self._log("错误: 请填写 API 地址")
            return

        # Build the full chat URL
        url = url.rstrip("/")
        if not url.endswith("/v1/chat/completions"):
            if "/v1" not in url:
                url += "/v1/chat/completions"
            elif not url.endswith("/chat/completions"):
                url += "/chat/completions"

        host = self.host_edit.text().strip() or "127.0.0.1"
        try:
            port = int(self.port_edit.text().strip())
        except ValueError:
            port = 5000

        self._server = ServerThread(url, key, model, host, port)
        self._server.status_changed.connect(self._on_status)
        self._server.finished.connect(self._on_server_stopped)
        self._server.start()

        self.start_btn.setText("停止服务")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 6px 20px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
        """)
        self._set_inputs_enabled(False)
        self._log(f"服务启动: http://{host}:{port}/v1/chat/completions")

    def _stop_server(self):
        if self._server and self._server.isRunning():
            self._server.stop()
            self._log("服务已停止")

    def _on_status(self, msg: str):
        self.status_label.setText(msg)
        self._log(msg)

    def _on_server_stopped(self):
        self.start_btn.setText("启动服务")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 6px 20px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self._set_inputs_enabled(True)
        self.status_label.setText("未启动")
        self.status_label.setStyleSheet("color: #64748b;")

    # ========================
    # Helpers
    # ========================

    def _on_provider_changed(self, index: int):
        if index < 0:
            return
        name = self.provider_combo.currentText()
        provider = find_provider(name)
        if provider:
            self.url_edit.setText(provider.base_url)
            self.model_edit.setText(provider.default_model)
            self.url_edit.setReadOnly(True)
            self.url_edit.setStyleSheet("QLineEdit { color: #64748b; background: #f1f5f9; }")
        else:
            # Custom
            self.url_edit.clear()
            self.url_edit.setPlaceholderText("https://your-api.example.com")
            self.url_edit.setReadOnly(False)
            self.url_edit.setStyleSheet("")
            self.model_edit.clear()
            self.model_edit.setPlaceholderText("your-model-name")

    def _set_inputs_enabled(self, enabled: bool):
        self.provider_combo.setEnabled(enabled)
        self.url_edit.setEnabled(enabled)
        self.key_edit.setEnabled(enabled)
        self.model_edit.setEnabled(enabled)
        self.host_edit.setEnabled(enabled)
        self.port_edit.setEnabled(enabled)

    def _log(self, msg: str):
        self.log_view.append(msg)

    def _show_help(self):
        dlg = HelpDialog(self)
        dlg.exec()

    def _show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()


# ========================
# Entry point for main.py
# ========================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Verity API Proxy")
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray

    window = VerityApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

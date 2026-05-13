"""
settings_dialog.py
User-editable settings saved to config.json.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QSpinBox, QDoubleSpinBox, QCheckBox,
    QPushButton, QGroupBox, QComboBox,
)
from PyQt6.QtCore import Qt

from core.config_manager import save_config
from core.logger_setup import logger

_STYLE = """
QDialog, QWidget { background:#0a0a0a; color:#e0e0e0; font-family:'Segoe UI'; font-size:13px; }
QGroupBox { border:1px solid #1e1e1e; border-radius:6px; margin-top:10px; padding:10px; color:#888; }
QGroupBox::title { subcontrol-origin:margin; left:10px; color:#00f5ff; }
QSpinBox, QDoubleSpinBox, QComboBox {
    background:#111; color:#e0e0e0; border:1px solid #2a2a2a;
    border-radius:4px; padding:4px 8px; }
QCheckBox { color:#e0e0e0; }
QCheckBox::indicator { width:16px; height:16px; border:1px solid #2a2a2a; border-radius:3px; background:#111; }
QCheckBox::indicator:checked { background:#00f5ff; }
QPushButton#save { background:#00f5ff; color:#000; border:none; border-radius:6px;
                   padding:10px 24px; font-weight:700; }
QPushButton#save:hover { background:#33f7ff; }
QPushButton#cancel { background:#1a1a1a; color:#888; border:1px solid #2a2a2a;
                     border-radius:6px; padding:10px 24px; }
QPushButton#cancel:hover { color:#e0e0e0; }
"""


class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Blink — Settings")
        self.setMinimumWidth(420)
        self.setStyleSheet(_STYLE)
        self._cfg = config.copy()
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Settings")
        title.setStyleSheet("color:#00f5ff; font-size:18px; font-weight:700;")
        lay.addWidget(title)

        # --- Camera ---
        cam_group = QGroupBox("Camera")
        cam_form  = QFormLayout(cam_group)
        self._cam_idx = QSpinBox()
        self._cam_idx.setRange(0, 9)
        self._cam_idx.setValue(self._cfg.get("camera_index", 0))
        self._cam_idx.setToolTip("0 = built-in webcam, 1 = first external camera, etc.")
        cam_form.addRow("Camera index:", self._cam_idx)
        lay.addWidget(cam_group)

        # --- Blink Detection ---
        blink_group = QGroupBox("Blink Detection")
        blink_form  = QFormLayout(blink_group)

        self._rate_thr = QDoubleSpinBox()
        self._rate_thr.setRange(1.0, 30.0)
        self._rate_thr.setSingleStep(1.0)
        self._rate_thr.setDecimals(1)
        self._rate_thr.setSuffix(" blinks/min")
        self._rate_thr.setValue(self._cfg.get("blink_rate_threshold", 12.0))
        blink_form.addRow("Alert below:", self._rate_thr)

        self._cooldown = QSpinBox()
        self._cooldown.setRange(30, 600)
        self._cooldown.setSuffix(" sec")
        self._cooldown.setValue(self._cfg.get("notification_cooldown", 90))
        blink_form.addRow("Notification cooldown:", self._cooldown)

        lay.addWidget(blink_group)

        # --- 20-20-20 ---
        rule_group = QGroupBox("20-20-20 Break Reminder")
        rule_form  = QFormLayout(rule_group)

        self._rule_enabled = QCheckBox("Enable")
        self._rule_enabled.setChecked(self._cfg.get("twenty_twenty_twenty_enabled", True))
        rule_form.addRow(self._rule_enabled)

        self._rule_interval = QSpinBox()
        self._rule_interval.setRange(1, 60)
        self._rule_interval.setSuffix(" min")
        self._rule_interval.setValue(
            self._cfg.get("twenty_twenty_twenty_interval_sec", 1200) // 60
        )
        rule_form.addRow("Remind every:", self._rule_interval)

        lay.addWidget(rule_group)

        # --- Buttons ---
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancel")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("save")
        save_btn.clicked.connect(self._save)

        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        lay.addLayout(btn_row)

    # ------------------------------------------------------------------
    def _save(self) -> None:
        self._cfg["camera_index"]                      = self._cam_idx.value()
        self._cfg["blink_rate_threshold"]              = self._rate_thr.value()
        self._cfg["notification_cooldown"]             = self._cooldown.value()
        self._cfg["twenty_twenty_twenty_enabled"]      = self._rule_enabled.isChecked()
        self._cfg["twenty_twenty_twenty_interval_sec"] = self._rule_interval.value() * 60
        save_config(self._cfg)
        logger.info("Settings saved")
        self.accept()

    def get_config(self) -> dict:
        return self._cfg

"""Custom dialogs: CompSettingsDialog, ProjectSettingsDialog, KeyframeEaseDialog."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)


# ---------------------------------------------------------------------------
# TimeSpinBox — frame/second switchable time input
# ---------------------------------------------------------------------------

class TimeSpinBox(QWidget):
    """Composite widget: QDoubleSpinBox + unit selector (Frames / Seconds)."""

    def __init__(self, framerate: float = 30.0, parent=None):
        super().__init__(parent)
        self._framerate = framerate if framerate > 0 else 30.0
        self._seconds = 0.0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.spin = QDoubleSpinBox()
        self.spin.setDecimals(3)
        self.spin.setRange(-999999, 999999)
        self.spin.setSingleStep(0.001)
        layout.addWidget(self.spin, stretch=1)

        self.unit = QComboBox()
        self.unit.addItems(["Seconds", "Frames"])
        self.unit.setFixedWidth(80)
        self.unit.currentIndexChanged.connect(self._on_unit_changed)
        layout.addWidget(self.unit)

        self.spin.valueChanged.connect(self._on_value_changed)

    def set_value_seconds(self, seconds: float):
        self._seconds = seconds
        self._sync_display()

    def value_seconds(self) -> float:
        return self._seconds

    def _sync_display(self):
        self.spin.blockSignals(True)
        if self.unit.currentIndex() == 1:  # Frames
            self.spin.setDecimals(0)
            self.spin.setSingleStep(1)
            self.spin.setValue(round(self._seconds * self._framerate))
        else:  # Seconds
            self.spin.setDecimals(3)
            self.spin.setSingleStep(0.001)
            self.spin.setValue(self._seconds)
        self.spin.blockSignals(False)

    def _on_unit_changed(self, _index: int):
        self._sync_display()

    def _on_value_changed(self, val: float):
        if self.unit.currentIndex() == 1:  # Frames
            self._seconds = val / self._framerate
        else:
            self._seconds = val


# ---------------------------------------------------------------------------
# CompSettingsDialog — replaces 9 separate QInputDialogs
# ---------------------------------------------------------------------------

class CompSettingsDialog(QDialog):
    """Composition Settings dialog (Basic + Advanced tabs)."""

    def __init__(self, comp_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Composition Settings")
        self.setMinimumWidth(480)
        self._comp_data = comp_data
        self._original: dict = {}
        self._color: list[int] = [0, 0, 0]

        main_layout = QVBoxLayout(self)
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # --- Basic tab ---
        basic = QWidget()
        bf = QFormLayout(basic)

        # Composition Name
        self.name_edit = QLineEdit()
        self.name_edit.setText(comp_data.get("name", ""))
        bf.addRow("Composition Name:", self.name_edit)

        # Width / Height
        dim_layout = QHBoxLayout()
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 30000)
        self.width_spin.setValue(comp_data.get("width", 1920))
        dim_layout.addWidget(self.width_spin)
        dim_layout.addWidget(QLabel("\u00d7"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 30000)
        self.height_spin.setValue(comp_data.get("height", 1080))
        dim_layout.addWidget(self.height_spin)
        bf.addRow("Width / Height:", dim_layout)

        # Pixel Aspect
        self.pixel_aspect_spin = QDoubleSpinBox()
        self.pixel_aspect_spin.setRange(0.01, 10.0)
        self.pixel_aspect_spin.setDecimals(4)
        self.pixel_aspect_spin.setValue(comp_data.get("pixelAspect", 1.0))
        bf.addRow("Pixel Aspect Ratio:", self.pixel_aspect_spin)

        # Frame Rate
        self.framerate_spin = QDoubleSpinBox()
        self.framerate_spin.setRange(0.01, 999.0)
        self.framerate_spin.setDecimals(3)
        self.framerate_spin.setValue(comp_data.get("framerate", 30.0))
        bf.addRow("Frame Rate:", self.framerate_spin)

        framerate = comp_data.get("framerate", 30.0)

        # Duration
        self.duration_time = TimeSpinBox(framerate)
        self.duration_time.set_value_seconds(comp_data.get("duration", 10.0))
        bf.addRow("Duration:", self.duration_time)

        # Display Start Time
        self.display_start_time = TimeSpinBox(framerate)
        self.display_start_time.set_value_seconds(
            comp_data.get("displayStartTime", 0.0))
        bf.addRow("Display Start Time:", self.display_start_time)

        # Background Color
        bg = comp_data.get("backgroundColor", {})
        self._color = [int(bg.get("r", 0)), int(bg.get("g", 0)),
                       int(bg.get("b", 0))]
        self.color_btn = QPushButton()
        self._update_color_button()
        self.color_btn.clicked.connect(self._pick_color)
        bf.addRow("Background Color:", self.color_btn)

        # Drop Frame
        flags = comp_data.get("flags", {})
        self.drop_frame_cb = QCheckBox()
        self.drop_frame_cb.setChecked(bool(flags.get("dropFrame", False)))
        bf.addRow("Drop Frame:", self.drop_frame_cb)

        tabs.addTab(basic, "Basic")

        # --- Advanced tab ---
        adv = QWidget()
        af = QFormLayout(adv)

        # Shutter
        self.shutter_angle_spin = QSpinBox()
        self.shutter_angle_spin.setRange(0, 720)
        self.shutter_angle_spin.setSuffix("\u00b0")
        self.shutter_angle_spin.setValue(comp_data.get("shutterAngle", 0))
        af.addRow("Shutter Angle:", self.shutter_angle_spin)

        self.shutter_phase_spin = QSpinBox()
        self.shutter_phase_spin.setRange(-360, 360)
        self.shutter_phase_spin.setSuffix("\u00b0")
        self.shutter_phase_spin.setValue(comp_data.get("shutterPhase", 0))
        af.addRow("Shutter Phase:", self.shutter_phase_spin)

        # MB Samples
        self.samples_spin = QSpinBox()
        self.samples_spin.setRange(1, 64)
        self.samples_spin.setValue(
            comp_data.get("motionBlurSamplesPerFrame", 16))
        af.addRow("Samples Per Frame:", self.samples_spin)

        self.adaptive_spin = QSpinBox()
        self.adaptive_spin.setRange(1, 256)
        self.adaptive_spin.setValue(
            comp_data.get("motionBlurAdaptiveSampleLimit", 128))
        af.addRow("Adaptive Sample Limit:", self.adaptive_spin)

        # Work Area
        self.work_start_time = TimeSpinBox(framerate)
        self.work_start_time.set_value_seconds(comp_data.get("inTime", 0.0))
        af.addRow("Work Area Start:", self.work_start_time)

        self.work_end_time = TimeSpinBox(framerate)
        self.work_end_time.set_value_seconds(comp_data.get("outTime", 0.0))
        af.addRow("Work Area End:", self.work_end_time)

        # Comp Flags checkboxes
        self.flag_cbs: dict[str, QCheckBox] = {}
        for label, key in [
            ("Draft 3D", "draft3d"),
            ("Motion Blur", "motionBlur"),
            ("Frame Blending", "frameBlending"),
            ("Hide Shy Layers", "hideShyLayers"),
            ("Preserve Nested Resolution", "preserveNestedResolution"),
            ("Preserve Nested Frame Rate", "preserveNestedFrameRate"),
        ]:
            cb = QCheckBox(label)
            cb.setChecked(bool(flags.get(key, False)))
            self.flag_cbs[key] = cb
            af.addRow("", cb)

        tabs.addTab(adv, "Advanced")

        # --- Buttons ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        # Store originals for diff
        self._original = {
            "name": self.name_edit.text(),
            "width": self.width_spin.value(),
            "height": self.height_spin.value(),
            "pixelAspect": self.pixel_aspect_spin.value(),
            "framerate": self.framerate_spin.value(),
            "duration": self.duration_time.value_seconds(),
            "displayStartTime": self.display_start_time.value_seconds(),
            "bgColor": list(self._color),
            "dropFrame": self.drop_frame_cb.isChecked(),
            "shutterAngle": self.shutter_angle_spin.value(),
            "shutterPhase": self.shutter_phase_spin.value(),
            "samplesPerFrame": self.samples_spin.value(),
            "adaptiveSampleLimit": self.adaptive_spin.value(),
            "workAreaStart": self.work_start_time.value_seconds(),
            "workAreaEnd": self.work_end_time.value_seconds(),
        }
        for key, cb in self.flag_cbs.items():
            self._original[f"flag_{key}"] = cb.isChecked()

    def _update_color_button(self):
        r, g, b = self._color
        self.color_btn.setStyleSheet(
            f"background-color: rgb({r},{g},{b}); min-width: 60px; "
            f"min-height: 20px; border: 1px solid #555;")
        self.color_btn.setText(f"({r}, {g}, {b})")

    def _pick_color(self):
        r, g, b = self._color
        color = QColorDialog.getColor(QColor(r, g, b), self,
                                      "Background Color")
        if color.isValid():
            self._color = [color.red(), color.green(), color.blue()]
            self._update_color_button()

    def get_changes(self) -> dict:
        """Return only changed fields as a dict."""
        changes: dict = {}
        name = self.name_edit.text().strip()
        if name and name != self._original["name"]:
            changes["name"] = name
        w = self.width_spin.value()
        h = self.height_spin.value()
        if w != self._original["width"] or h != self._original["height"]:
            changes["dimensions"] = (w, h)

        pa = self.pixel_aspect_spin.value()
        if pa != self._original["pixelAspect"]:
            changes["pixelAspect"] = pa

        fps = self.framerate_spin.value()
        if fps != self._original["framerate"]:
            changes["framerate"] = fps

        dur = self.duration_time.value_seconds()
        if dur != self._original["duration"]:
            changes["duration"] = dur

        dst = self.display_start_time.value_seconds()
        if dst != self._original["displayStartTime"]:
            changes["displayStartTime"] = dst

        if self._color != self._original["bgColor"]:
            changes["bgColor"] = tuple(self._color)

        df = self.drop_frame_cb.isChecked()
        if df != self._original["dropFrame"]:
            changes["dropFrame"] = df

        sa = self.shutter_angle_spin.value()
        if sa != self._original["shutterAngle"]:
            changes["shutterAngle"] = sa

        sp = self.shutter_phase_spin.value()
        if sp != self._original["shutterPhase"]:
            changes["shutterPhase"] = sp

        spf = self.samples_spin.value()
        asl = self.adaptive_spin.value()
        if (spf != self._original["samplesPerFrame"]
                or asl != self._original["adaptiveSampleLimit"]):
            changes["mbSamples"] = (spf, asl)

        ws = self.work_start_time.value_seconds()
        if ws != self._original["workAreaStart"]:
            changes["workAreaStart"] = ws

        we = self.work_end_time.value_seconds()
        if we != self._original["workAreaEnd"]:
            changes["workAreaEnd"] = we

        # Comp flags — use snake_case keys matching the tools_project API
        _camel_to_snake = {
            "draft3d": "draft3d",
            "motionBlur": "motion_blur",
            "frameBlending": "frame_blending",
            "hideShyLayers": "hide_shy_layers",
            "preserveNestedResolution": "preserve_nested_resolution",
            "preserveNestedFrameRate": "preserve_nested_frame_rate",
        }
        for camel_key, cb in self.flag_cbs.items():
            if cb.isChecked() != self._original[f"flag_{camel_key}"]:
                snake = _camel_to_snake[camel_key]
                changes[f"flag_{snake}"] = cb.isChecked()

        return changes


# ---------------------------------------------------------------------------
# ProjectSettingsDialog
# ---------------------------------------------------------------------------

class ProjectSettingsDialog(QDialog):
    """Project Settings dialog."""

    def __init__(self, tools_project, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Project Settings")
        self.setMinimumWidth(360)
        self._tp = tools_project

        layout = QFormLayout(self)

        # Bits Per Channel
        bpc_layout = QHBoxLayout()
        self.bpc_radios: dict[int, QRadioButton] = {}
        cur_bpc = getattr(tools_project, "bits_per_channel", 8)
        for bits in [8, 16, 32]:
            rb = QRadioButton(f"{bits} bpc")
            rb.setChecked(bits == cur_bpc)
            self.bpc_radios[bits] = rb
            bpc_layout.addWidget(rb)
        layout.addRow("Bits Per Channel:", bpc_layout)

        # Working Gamma
        gamma_layout = QHBoxLayout()
        self.gamma_radios: dict[float, QRadioButton] = {}
        cur_gamma = getattr(tools_project, "working_gamma", 2.2)
        for gamma in [2.2, 2.4]:
            rb = QRadioButton(str(gamma))
            rb.setChecked(abs(gamma - cur_gamma) < 0.01)
            self.gamma_radios[gamma] = rb
            gamma_layout.addWidget(rb)
        layout.addRow("Working Gamma:", gamma_layout)

        # Linearize Working Space
        self.linearize_cb = QCheckBox()
        self.linearize_cb.setChecked(
            getattr(tools_project, "linearize_working_space", False))
        layout.addRow("Linearize Working Space:", self.linearize_cb)

        # Compensate Scene Referred
        self.compensate_cb = QCheckBox()
        self.compensate_cb.setChecked(
            getattr(tools_project, "compensate_scene_referred", False))
        layout.addRow("Compensate Scene Referred:", self.compensate_cb)

        # Audio Sample Rate
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.setEditable(True)
        rates = ["22050", "32000", "44100", "48000", "96000"]
        self.sample_rate_combo.addItems(rates)
        cur_rate = getattr(tools_project, "audio_sample_rate", 48000.0)
        self.sample_rate_combo.setCurrentText(str(int(cur_rate)))
        layout.addRow("Audio Sample Rate (Hz):", self.sample_rate_combo)

        # Store originals
        self._orig_bpc = cur_bpc
        self._orig_gamma = cur_gamma
        self._orig_linear = self.linearize_cb.isChecked()
        self._orig_compensate = self.compensate_cb.isChecked()
        self._orig_rate = cur_rate

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def apply_changes(self):
        """Apply changed settings directly to the tools_project."""
        # BPC
        for bits, rb in self.bpc_radios.items():
            if rb.isChecked() and bits != self._orig_bpc:
                self._tp.bits_per_channel = bits
                break

        # Gamma
        for gamma, rb in self.gamma_radios.items():
            if rb.isChecked() and abs(gamma - self._orig_gamma) > 0.01:
                self._tp.working_gamma = gamma
                break

        # Booleans
        if self.linearize_cb.isChecked() != self._orig_linear:
            self._tp.linearize_working_space = self.linearize_cb.isChecked()
        if self.compensate_cb.isChecked() != self._orig_compensate:
            self._tp.compensate_scene_referred = self.compensate_cb.isChecked()

        # Audio sample rate
        try:
            rate = float(self.sample_rate_combo.currentText())
            if rate != self._orig_rate:
                self._tp.audio_sample_rate = rate
        except ValueError:
            pass

    def has_changes(self) -> bool:
        for bits, rb in self.bpc_radios.items():
            if rb.isChecked() and bits != self._orig_bpc:
                return True
        for gamma, rb in self.gamma_radios.items():
            if rb.isChecked() and abs(gamma - self._orig_gamma) > 0.01:
                return True
        if self.linearize_cb.isChecked() != self._orig_linear:
            return True
        if self.compensate_cb.isChecked() != self._orig_compensate:
            return True
        try:
            rate = float(self.sample_rate_combo.currentText())
            if rate != self._orig_rate:
                return True
        except ValueError:
            pass
        return False


# ---------------------------------------------------------------------------
# KeyframeEaseDialog
# ---------------------------------------------------------------------------

class KeyframeEaseDialog(QDialog):
    """Per-dimension keyframe temporal ease editor."""

    def __init__(self, kf_data: dict, dimensions: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyframe Temporal Ease")
        self.setMinimumWidth(400)
        self._dimensions = max(dimensions, 1)

        layout = QFormLayout(self)

        in_spd = kf_data.get("inSpeed", [])
        in_inf = kf_data.get("inInfluence", [])
        out_spd = kf_data.get("outSpeed", [])
        out_inf = kf_data.get("outInfluence", [])

        self.in_speed_spins: list[QDoubleSpinBox] = []
        self.in_influence_spins: list[QDoubleSpinBox] = []
        self.out_speed_spins: list[QDoubleSpinBox] = []
        self.out_influence_spins: list[QDoubleSpinBox] = []

        def _make_row(label: str, values: list, spins_list: list,
                      suffix: str = "", min_val: float = -999999,
                      max_val: float = 999999):
            row = QHBoxLayout()
            for i in range(self._dimensions):
                sb = QDoubleSpinBox()
                sb.setRange(min_val, max_val)
                sb.setDecimals(3)
                if suffix:
                    sb.setSuffix(suffix)
                val = values[i] if i < len(values) else 0.0
                sb.setValue(val)
                row.addWidget(sb)
                spins_list.append(sb)
            layout.addRow(label, row)

        _make_row("In Speed:", in_spd, self.in_speed_spins)
        _make_row("In Influence:", in_inf, self.in_influence_spins,
                  suffix="%", min_val=0, max_val=100)
        _make_row("Out Speed:", out_spd, self.out_speed_spins)
        _make_row("Out Influence:", out_inf, self.out_influence_spins,
                  suffix="%", min_val=0, max_val=100)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_ease(self) -> dict:
        return {
            "inSpeed": [s.value() for s in self.in_speed_spins],
            "inInfluence": [s.value() for s in self.in_influence_spins],
            "outSpeed": [s.value() for s in self.out_speed_spins],
            "outInfluence": [s.value() for s in self.out_influence_spins],
        }

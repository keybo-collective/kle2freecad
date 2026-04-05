# -*- coding: utf-8 -*-

import json
import os
import traceback
import FreeCAD
import FreeCADGui
import Sketcher
from PySide6 import QtWidgets, QtGui, QtCore
from kle_json_cleaner import sanitizeAsJson, normalizeKLEData, countCols, countRows, countKeys
from KSutils import iconPath
from KSprefs import get_saved_layout, set_saved_layout
from KSdraw import drawFrame, findKeyCenters, drawCenter, drawCherryKey, drawCherryStab

Qt = QtCore.Qt
_ICON_PATH = os.path.join(iconPath, "kle2sketch.svg")

class _TabFriendlyTextEdit(QtWidgets.QTextEdit):
    """Ignore tabs so that you can tab out of the textedit"""
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            event.ignore()
            self.focusNextChild()
        elif event.key() == Qt.Key_Backtab:
            event.ignore()
            self.focusPreviousChild()
        else:
            super().keyPressEvent(event)

class KLEPromptDialog(QtWidgets.QDialog):
    """Dialog to collect KLE data and parameters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KLE Sketch Generator")
        self.setWindowIcon(QtGui.QIcon(_ICON_PATH))
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(self._build_kle_block())

        row = QtWidgets.QHBoxLayout()
        row.addWidget(self._build_cutouts_group())
        row.addWidget(self._build_fillet_group())
        row.addWidget(self._build_advanced_group())
        layout.addLayout(row)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._handle_ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_kle_block(self):
        box = QtWidgets.QGroupBox()
        box.setTitle("KLE DATA")
        v = QtWidgets.QVBoxLayout(box)

        hint = QtWidgets.QLabel("Paste KLE raw data or JSON here")
        # hint.setStyleSheet("color: #666;")

        self.kle_text = _TabFriendlyTextEdit()
        self.kle_text.setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont))
        self.kle_text.setPlaceholderText("Paste KLE JSON...")
        default_layout = get_saved_layout()
        if default_layout:
            self.kle_text.setPlainText(default_layout)
        self.kle_text.setMinimumHeight(140)

        v.addWidget(hint)
        v.addWidget(self.kle_text)
        return box

    def _build_cutouts_group(self):
        box = QtWidgets.QGroupBox("CUTOUTS")
        v = QtWidgets.QVBoxLayout(box)
        v.addWidget(self._make_hint_label("Default values are recommended."))

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignLeft)

        self.cutout_type = QtWidgets.QComboBox()
        ## TODO : Add support for other cutout types
        self.cutout_type.addItem("Cherry MX Basic")
        self.cutout_type.setEnabled(False)
        form.addRow("Switch Cutout Type", self.cutout_type)

        self.cutout_stab = QtWidgets.QComboBox()
        ## TODO: Add support for other cutout types, depending on selection above
        self.cutout_stab.addItem("Cherry MX Basic")
        self.cutout_stab.setEnabled(False)
        form.addRow("Stabilizer Cutout Type", self.cutout_stab)

        self.cutout_acst = QtWidgets.QComboBox()
        ## TODO: Add support for other Acoustic Cutout types
        self.cutout_acst.addItem("None")
        self.cutout_acst.setEnabled(False)
        form.addRow("Acoustic Cutout Type", self.cutout_acst)

        v.addLayout(form)
        return box

    def _build_fillet_group(self):
        box = QtWidgets.QGroupBox("FILLETING")
        v = QtWidgets.QVBoxLayout(box)
        v.addWidget(self._make_hint_label("Recommended 0.5mm; larger radii can cause fit issues."))

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignLeft)

        self.fillet_rad = self._make_spin(0.5)
        form.addRow("Switch Cutout Fillet Radius", self.fillet_rad)

        self.fillet_cut = self._make_spin(0.5)
        form.addRow("Stabilizer Cutout Fillet Radius", self.fillet_cut)

        self.fillet_acst = self._make_spin(0.5, enabled=False)
        form.addRow("Acoustic Cutout Fillet Radius", self.fillet_acst)

        v.addLayout(form)
        return box

    def _build_advanced_group(self):
        box = QtWidgets.QGroupBox("ADVANCED")
        v = QtWidgets.QVBoxLayout(box)
        v.addWidget(self._make_hint_label("Best leave these alone unless you know what you are doing."))

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignLeft)

        self.adv_w = self._make_spin(19.05)
        form.addRow("Unit Width", self.adv_w)

        self.adv_h = self._make_spin(19.05)
        form.addRow("Unit Height", self.adv_h)

        self.adv_k = self._make_spin(0, enabled=False)
        form.addRow("Kerf", self.adv_k)

        v.addLayout(form)
        return box

    @staticmethod
    def _make_hint_label(text):
        lbl = QtWidgets.QLabel(text)
        lbl.setStyleSheet("color: #666;")
        return lbl

    @staticmethod
    def _make_spin(default, enabled=True):
        spin = QtWidgets.QDoubleSpinBox()
        spin.setDecimals(3)
        spin.setSingleStep(0.05)
        spin.setValue(default)
        spin.setEnabled(enabled)
        spin.setMinimum(0.0)
        spin.setMaximum(9999.0)
        spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        return spin

    def _handle_ok(self):
        for widget in self.findChildren(QtWidgets.QWidget):
            widget.setVisible(False)
        layout = self.layout()
        if layout is not None:
            wait_label = self._make_hint_label("Generating ... please wait.")
            wait_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(wait_label, alignment=Qt.AlignHCenter)
        QtWidgets.QApplication.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)

        adv_w = self.adv_w.value()
        adv_h = self.adv_h.value()
        adv_k = self.adv_k.value() # Kerf
        flt_r = self.fillet_rad.value() # Switch fillet radius
        flt_c = self.fillet_cut.value() # Stab fillet radius

        kle_text = self.kle_text.toPlainText()

        try:
            kle_payload = sanitizeAsJson(kle_text)
            kle_json = json.loads(kle_payload)
            kle_parsed = normalizeKLEData(kle_json)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Invalid KLE data", str(exc) or "Failed to parse KLE input.")
            return

        # All good, lets carry on
        set_saved_layout(kle_text)
        row_count = countRows(kle_parsed)
        col_count = countCols(kle_parsed)

        doc = FreeCAD.ActiveDocument
        if doc is None:
            doc = FreeCAD.newDocument("KLE_Plate")

        full_w = col_count * adv_w
        full_h = row_count * adv_h

        doc = FreeCAD.ActiveDocument
        if doc is None:
            doc = FreeCAD.newDocument("KLE_Plate")

        sketch = doc.addObject("Sketcher::SketchObject", "Sketch.")
        xy_plane = doc.getObject("XY_Plane")
        if xy_plane is not None:
            sketch.AttachmentSupport = [(xy_plane, "")]
        sketch.MapMode = 'FlatFace'

        home_pnt_idx = drawFrame(sketch, full_w, full_h)
        doc.recompute()

        kle_parsed = findKeyCenters(kle_parsed, adv_w, adv_h)

        progress = QtWidgets.QProgressDialog("Drawing key cutouts...", None, 0, countKeys(kle_parsed), self)
        progress.setWindowTitle("KLE Sketch Generator")
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.setWindowModality(Qt.WindowModal)
        progress.forceShow()

        try:
            step = 0
            for row in kle_parsed:
                if not isinstance(row, list):
                    continue
                for item in row:
                    if isinstance(item, dict):
                        cx = item.get("cx",0)
                        cy = item.get("cy",0)
                        # drawCenter(sketch, cx, cy)
                        drawCherryKey(sketch, cx, cy, flt_r, adv_k)
                        w = item.get("w",1)
                        h = item.get("h",1)
                        if w >= 2 or h >= 2:
                            drawCherryStab(sketch, cx, cy, w, h, item.get("r",0), flt_c, adv_k)
                        step += 1
                    progress.setValue(step)
                    QtWidgets.QApplication.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)
        except Exception as e:
            print(str(e))
            traceback.print_exc()

        progress.close()
        doc.recompute()

        try:
            FreeCADGui.ActiveDocument.setEdit(sketch.Name)
        except Exception:
            pass

        self.accept()


class KLESketchGeneratorCommand:
    """FreeCAD command for generating a sketch from KLE data."""

    def GetResources(self):
        return {
            "Pixmap": _ICON_PATH,
            "MenuText": "KLE Sketch Generator",
            "ToolTip": "Generate a sketch from KLE data",
        }

    def Activated(self):
        dlg = KLEPromptDialog()
        dlg.exec_()

    def IsActive(self):
        return True


# Register command with FreeCAD
FreeCADGui.addCommand("KLESketchGenerator", KLESketchGeneratorCommand())

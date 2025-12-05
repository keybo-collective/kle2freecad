# -*- coding: utf-8 -*-

import json
import os

import FreeCAD
import FreeCADGui
import Part
import Sketcher
from PySide2 import QtWidgets, QtGui, QtCore
from KSutils import debug_print_tree, iconPath
from kle_json_cleaner import postParse, preParse, countCols, countRows

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
        self.kle_text.setPlaceholderText("Paste KLE JSON...")
        self.kle_text.setPlainText('["A","B","C"],\n["D","E","F"]')
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

        self.adv_k = self._make_spin(0)
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
        adv_w = self.adv_w.value()
        adv_h = self.adv_h.value()

        kle_text = self.kle_text.toPlainText()
        kle_payload = preParse(kle_text)
        kle_json = json.loads(kle_payload)
        kle_parsed = postParse(kle_json)
        row_count = countRows(kle_parsed)
        col_count = countCols(kle_parsed)

        # FIXME : remove debug info
        debug_print_tree(kle_parsed)
        print(f"rows = {row_count}, cols = {col_count}")

        doc = FreeCAD.ActiveDocument
        if doc is None:
            doc = FreeCAD.newDocument("KLE_Plate")

        sketch = doc.addObject("Sketcher::SketchObject", "Sketch.")
        xy_plane = doc.getObject("XY_Plane")
        if xy_plane is not None:
            sketch.AttachmentSupport = [(xy_plane, "")]
        sketch.MapMode = 'FlatFace'

        full_w = col_count * adv_w
        full_h = row_count * adv_h

        p_vec = FreeCAD.Vector(full_w/-2, full_h/2, 0)

        pnt_1 = Part.Point(p_vec)
        sketch.addGeometry(pnt_1, False)
        dx_idx = sketch.addConstraint(Sketcher.Constraint('DistanceX', -1, 1, 0, 1, full_w))
        dy_idx = sketch.addConstraint(Sketcher.Constraint('DistanceY', -1, 1, 0, 1, full_h))
        sketch.setDatum(dx_idx, FreeCAD.Units.Quantity(f"{(full_w/-2):.6f} mm"))
        sketch.setDatum(dy_idx, FreeCAD.Units.Quantity(f"{(full_h/2):.6f} mm"))

        ln1 = Part.LineSegment(p_vec, FreeCAD.Vector(p_vec.x + full_w, p_vec.y, 0))
        ln1_idx = sketch.addGeometry(ln1, False)
        sketch.addConstraint(Sketcher.Constraint('Coincident', ln1_idx, 1, 0, 1))
        sketch.addConstraint(Sketcher.Constraint('Horizontal', ln1_idx))
        len1_idx = sketch.addConstraint(Sketcher.Constraint('DistanceX', ln1_idx, 1, ln1_idx, 2, full_w))
        sketch.setDatum(len1_idx, FreeCAD.Units.Quantity(f"{full_w:.6f} mm"))

        ln2 = Part.LineSegment(FreeCAD.Vector(full_w/2, full_h/2, 0), FreeCAD.Vector(full_w/2, full_h/-2, 0))
        ln2_idx = sketch.addGeometry(ln2, False)
        len2_idx = sketch.addConstraint(Sketcher.Constraint('DistanceY', ln2_idx, 2, ln2_idx, 1, full_h))
        sketch.setDatum(len2_idx, FreeCAD.Units.Quantity(f"{full_h:.6f} mm"))
        sketch.addConstraint(Sketcher.Constraint('Coincident', ln2_idx, 1, ln1_idx, 2))
        sketch.addConstraint(Sketcher.Constraint('Perpendicular', ln1_idx, ln2_idx))

        ln3 = Part.LineSegment(FreeCAD.Vector(full_w/2, full_h/-2, 0), FreeCAD.Vector(full_w/-2, full_h/-2, 0))
        ln3_idx = sketch.addGeometry(ln3, False)
        sketch.addConstraint(Sketcher.Constraint('Coincident', ln3_idx, 1, ln2_idx, 2))
        sketch.addConstraint(Sketcher.Constraint('Parallel', ln3_idx, ln1_idx))

        ln4 = Part.LineSegment(FreeCAD.Vector(full_w/-2, full_h/-2, 0), FreeCAD.Vector(full_w/-2, full_h/2, 0))
        ln4_idx = sketch.addGeometry(ln4, False)
        sketch.addConstraint(Sketcher.Constraint('Coincident', ln4_idx, 1, ln3_idx, 2))
        sketch.addConstraint(Sketcher.Constraint('Coincident', ln4_idx, 2, ln1_idx, 1))
        sketch.addConstraint(Sketcher.Constraint('Parallel', ln4_idx, ln2_idx))

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
            "MenuText": "KLESketchGenerator",
            "ToolTip": "Generate a sketch from KLE data",
        }

    def Activated(self):
        dlg = KLEPromptDialog()
        dlg.exec_()

    def IsActive(self):
        return True


# Register command with FreeCAD
FreeCADGui.addCommand("KLESketchGenerator", KLESketchGeneratorCommand())

import os
import json
from krita import Extension, Krita, Selection
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QComboBox,
    QCheckBox, QInputDialog
)
from PyQt5.QtCore import QSettings, Qt, QByteArray
from PyQt5.QtGui import QTransform

def set_node_and_parents_visible(node, visible):
    current = node
    while current is not None:
        current.setVisible(visible)
        current = current.parentNode()

class ExportRectangleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Region")
        self.setMinimumWidth(480)

        # Persistent settings
        self.settings = QSettings("MyCompany", "KritaExportRectangle")

        # Load saved regions
        self.regions = self.loadRegions()

        layout = QVBoxLayout()

        # --- Region selector ---
        rs_layout = QHBoxLayout()
        rs_layout.addWidget(QLabel("Region:"))
        self.regionCombo = QComboBox()
        self.regionCombo.addItem("Custom")
        for r in self.regions:
            self.regionCombo.addItem(r["name"])
        rs_layout.addWidget(self.regionCombo)
        layout.addLayout(rs_layout)

        # Restore last-selected region
        last_idx = int(self.settings.value("lastRegionIndex", 0))

        # --- Buttons: Grab, Save, Delete, Select ---
        btn_layout = QHBoxLayout()
        btnGrab   = QPushButton("Grab Selection")
        btnSave   = QPushButton("Save Region")
        btnDelete = QPushButton("Delete Region")
        btnSelect = QPushButton("Select Region")
        btnGrab.clicked.connect(self.grabSelection)
        btnSave.clicked.connect(self.saveRegion)
        btnDelete.clicked.connect(self.deleteRegion)
        btnSelect.clicked.connect(self.selectRegion)
        for btn in (btnGrab, btnSave, btnDelete, btnSelect):
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

        # --- Region fields: X, Y, Width, Height ---
        x_def = self.settings.value("x", "0")
        y_def = self.settings.value("y", "0")
        w_def = self.settings.value("width", "100")
        h_def = self.settings.value("height", "100")
        self.xEdit      = QLineEdit(x_def)
        self.yEdit      = QLineEdit(y_def)
        self.widthEdit  = QLineEdit(w_def)
        self.heightEdit = QLineEdit(h_def)
        region_layout = QHBoxLayout()
        region_layout.addWidget(QLabel("X:"));      region_layout.addWidget(self.xEdit)
        region_layout.addWidget(QLabel("Y:"));      region_layout.addWidget(self.yEdit)
        region_layout.addWidget(QLabel("Width:"));  region_layout.addWidget(self.widthEdit)
        region_layout.addWidget(QLabel("Height:")); region_layout.addWidget(self.heightEdit)
        layout.addLayout(region_layout)

        # --- Resize fields: New Width, New Height ---
        nw_def = self.settings.value("newWidth", w_def)
        nh_def = self.settings.value("newHeight", h_def)
        self.newWidthEdit  = QLineEdit(nw_def)
        self.newHeightEdit = QLineEdit(nh_def)
        resize_layout = QHBoxLayout()
        resize_layout.addWidget(QLabel("New Width:"));  resize_layout.addWidget(self.newWidthEdit)
        resize_layout.addWidget(QLabel("New Height:")); resize_layout.addWidget(self.newHeightEdit)
        layout.addLayout(resize_layout)

        # --- Rotation option ---
        rot_def = self.settings.value("rotation", "None")
        self.rotationCombo = QComboBox()
        self.rotationCombo.addItems(["None", "Rotate Clockwise", "Rotate Counterclockwise"])
        idx = self.rotationCombo.findText(rot_def)
        self.rotationCombo.setCurrentIndex(idx if idx != -1 else 0)
        rot_layout = QHBoxLayout()
        rot_layout.addWidget(QLabel("Rotation:")); rot_layout.addWidget(self.rotationCombo)
        layout.addLayout(rot_layout)

        # --- Export selected layers only ---
        export_sel = self.settings.value("exportSelected", "false") == "true"
        self.exportSelectedCheckbox = QCheckBox("Export Selected Layers Only")
        self.exportSelectedCheckbox.setChecked(export_sel)
        layout.addWidget(self.exportSelectedCheckbox)

        # --- Output file picker ---
        last_dir = self.settings.value("lastOutputDir", "")
        default_out = last_dir
        if last_dir:
            app = Krita.instance()
            doc = app.activeDocument()
            name = doc.activeNode().name() if doc and doc.activeNode() else "export"
            default_out = os.path.join(last_dir, f"{name}.png")
        file_layout = QHBoxLayout()
        self.outputPathEdit = QLineEdit(default_out)
        btnBrowse = QPushButton("Browse")
        btnBrowse.clicked.connect(self.browseFile)
        file_layout.addWidget(QLabel("Output File:"))
        file_layout.addWidget(self.outputPathEdit)
        file_layout.addWidget(btnBrowse)
        layout.addLayout(file_layout)

        # --- Export button ---
        btnExport = QPushButton("Export")
        btnExport.clicked.connect(self.export)
        layout.addWidget(btnExport)

        self.setLayout(layout)

        # Now connect and restore combo
        self.regionCombo.currentIndexChanged.connect(self.onRegionSelected)
        if 0 <= last_idx < self.regionCombo.count():
            self.regionCombo.setCurrentIndex(last_idx)

    # ---- Annotation-based Region Storage ----

    def loadRegions(self):
        app = Krita.instance()
        doc = app.activeDocument()
        if not doc:
            return []
        raw = doc.annotation("exportRegions")
        try:
            data = bytes(raw).decode("utf-8") or "[]"
            return json.loads(data)
        except Exception:
            return []

    def saveRegions(self, regions):
        app = Krita.instance()
        doc = app.activeDocument()
        if not doc:
            return
        payload = QByteArray(json.dumps(regions).encode("utf-8"))
        doc.setAnnotation("exportRegions", "Export Regions", payload)

    # ---- UI Callbacks ----

    def onRegionSelected(self, idx):
        self.settings.setValue("lastRegionIndex", idx)
        if not hasattr(self, 'xEdit'):
            return
        if idx == 0:
            return
        r = self.regions[idx - 1]
        self.xEdit.setText(str(r["x"]))
        self.yEdit.setText(str(r["y"]))
        self.widthEdit.setText(str(r["width"]))
        self.heightEdit.setText(str(r["height"]))
        self.newWidthEdit.setText(str(r.get("newWidth", r["width"])))
        self.newHeightEdit.setText(str(r.get("newHeight", r["height"])))

    def grabSelection(self):
        app = Krita.instance()
        doc = app.activeDocument()
        if not doc:
            QMessageBox.warning(self, "No Document", "No active document found.")
            return
        sel = doc.selection()
        if sel is None or sel.width() == 0 or sel.height() == 0:
            QMessageBox.warning(self, "No Selection", "There is no active selection to grab.")
            return
        x, y, w, h = sel.x(), sel.y(), sel.width(), sel.height()
        self.xEdit.setText(str(x))
        self.yEdit.setText(str(y))
        self.widthEdit.setText(str(w))
        self.heightEdit.setText(str(h))
        self.newWidthEdit.setText(str(w))
        self.newHeightEdit.setText(str(h))

    def selectRegion(self):
        """
        If a saved region is selected, use it; otherwise use the
        X/Y/Width/Height fields to create the selection.
        """
        idx = self.regionCombo.currentIndex()
        if idx > 0:
            r = self.regions[idx - 1]
            x, y, w, h = r["x"], r["y"], r["width"], r["height"]
        else:
            try:
                x = int(self.xEdit.text())
                y = int(self.yEdit.text())
                w = int(self.widthEdit.text())
                h = int(self.heightEdit.text())
            except ValueError:
                QMessageBox.warning(self, "Invalid", "Enter valid integers for X, Y, Width, Height.")
                return

        app = Krita.instance()
        doc = app.activeDocument()
        if not doc:
            QMessageBox.warning(self, "No Document", "No active document found.")
            return

        sel = Selection()
        sel.select(x, y, w, h, 255)
        doc.setSelection(sel)

    def saveRegion(self):
        name, ok = QInputDialog.getText(self, "Save Region", "Name this region:")
        if not ok or not name.strip():
            return
        try:
            x  = int(self.xEdit.text());    y  = int(self.yEdit.text())
            w  = int(self.widthEdit.text()); h  = int(self.heightEdit.text())
            nw = int(self.newWidthEdit.text()); nh = int(self.newHeightEdit.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid", "All values must be integers.")
            return
        new = {
            "name": name.strip(),
            "x": x, "y": y,
            "width": w, "height": h,
            "newWidth": nw, "newHeight": nh
        }
        for r in self.regions:
            if r["name"] == new["name"]:
                r.update(new)
                break
        else:
            self.regions.append(new)
            self.regionCombo.addItem(new["name"])
        self.saveRegions(self.regions)
        QMessageBox.information(self, "Saved", f"Region '{new['name']}' saved.")

    def deleteRegion(self):
        idx = self.regionCombo.currentIndex()
        if idx == 0:
            QMessageBox.warning(self, "Delete Region", "No region selected to delete.")
            return
        name = self.regionCombo.currentText()
        resp = QMessageBox.question(
            self, "Delete Region",
            f"Delete region '{name}'?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp != QMessageBox.Yes:
            return
        self.regions.pop(idx - 1)
        self.saveRegions(self.regions)
        self.regionCombo.removeItem(idx)
        self.regionCombo.setCurrentIndex(0)
        for fld in (
            self.xEdit, self.yEdit, self.widthEdit,
            self.heightEdit, self.newWidthEdit, self.newHeightEdit
        ):
            fld.setText("0")

    # ---- Helpers & Export Logic ----

    def browseFile(self):
        d = self.settings.value("lastOutputDir", "")
        fn, _ = QFileDialog.getSaveFileName(
            self, "Select output file", d,
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*)"
        )
        if fn:
            self.outputPathEdit.setText(fn)

    def get_all_nodes(self, doc):
        nodes = []
        def traverse(n):
            nodes.append(n)
            for c in n.childNodes():
                traverse(c)
        for top in doc.topLevelNodes():
            traverse(top)
        return nodes

    def export(self):
        try:
            x  = int(self.xEdit.text());    y  = int(self.yEdit.text())
            w  = int(self.widthEdit.text()); h  = int(self.heightEdit.text())
            nw = int(self.newWidthEdit.text()); nh = int(self.newHeightEdit.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Enter valid integers for all size fields.")
            return
        out = self.outputPathEdit.text().strip()
        if not out or os.path.isdir(out):
            QMessageBox.warning(self, "Error", "Select a valid output file.")
            return

        app = Krita.instance()
        doc = app.activeDocument()
        view = app.activeWindow().activeView()
        if not doc:
            QMessageBox.warning(self, "Error", "No active document found.")
            return

        layers_exported = 0
        if self.exportSelectedCheckbox.isChecked():
            sel_nodes = view.selectedNodes()
            if not sel_nodes:
                QMessageBox.warning(self, "Error", "No layers selected.")
                return
            all_nodes = self.get_all_nodes(doc)
            old_vis = {n.uniqueId().toString(): n.visible() for n in all_nodes}
            for n in all_nodes: n.setVisible(False)
            for n in sel_nodes:
                set_node_and_parents_visible(n, True)
                layers_exported += 1
            doc.refreshProjection()
            cropped = doc.projection(x, y, w, h)
            for n in all_nodes:
                n.setVisible(old_vis[n.uniqueId().toString()])
            doc.refreshProjection()
        else:
            cropped = doc.projection(x, y, w, h)

        if (nw, nh) != (w, h):
            cropped = cropped.scaled(nw, nh, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        rot = self.rotationCombo.currentText()
        if rot == "Rotate Clockwise":
            cropped = cropped.transformed(QTransform().rotate(90), Qt.SmoothTransformation)
        elif rot == "Rotate Counterclockwise":
            cropped = cropped.transformed(QTransform().rotate(-90), Qt.SmoothTransformation)

        if cropped.save(out):
            self.settings.setValue(
                "exportSelected",
                "true" if self.exportSelectedCheckbox.isChecked() else "false"
            )
            for key, ed in (
                ("x", self.xEdit), ("y", self.yEdit),
                ("width", self.widthEdit), ("height", self.heightEdit),
                ("newWidth", self.newWidthEdit), ("newHeight", self.newHeightEdit)
            ):
                self.settings.setValue(key, ed.text())
            self.settings.setValue("rotation", rot)
            self.settings.setValue("lastOutputDir", os.path.dirname(out))
            QMessageBox.information(
                self, "Success",
                f"Export successful!{f' Layers exported: {layers_exported}' if layers_exported else ''}"
            )
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to save the cropped image.")

class ExportRectangleExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction("export_rectangle", "Export Region", "tools/scripts")
        action.triggered.connect(self.exportRectangle)

    def exportRectangle(self):
        dialog = ExportRectangleDialog()
        dialog.exec_()

Krita.instance().addExtension(ExportRectangleExtension(Krita.instance()))

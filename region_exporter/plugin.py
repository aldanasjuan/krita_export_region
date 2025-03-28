import os
from krita import Extension, Krita
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFileDialog, QMessageBox, QComboBox, QCheckBox)
from PyQt5.QtCore import QRect, QSettings, Qt
from PyQt5.QtGui import QImage, QTransform

def set_node_and_parents_visible(node, visible):
    """
    Sets the visibility of the given node and all of its parent nodes.
    
    Parameters:
        node: The Krita node (layer or group) to update.
        visible: A boolean value indicating whether the node and its parents should be visible.
    """
    current_node = node
    while current_node is not None:
        current_node.setVisible(visible)
        current_node = current_node.parentNode()

class ExportRectangleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Rectangle")
        self.setMinimumWidth(400)
        layout = QVBoxLayout()

        # Create QSettings to persist values.
        self.settings = QSettings("MyCompany", "KritaExportRectangle")

        # Retrieve persisted region values or use defaults.
        x_default = self.settings.value("x", "0")
        y_default = self.settings.value("y", "0")
        width_default = self.settings.value("width", "100")
        height_default = self.settings.value("height", "100")

        # Create input fields for region: X, Y, Width, Height.
        self.xEdit = QLineEdit(x_default)
        self.yEdit = QLineEdit(y_default)
        self.widthEdit = QLineEdit(width_default)
        self.heightEdit = QLineEdit(height_default)

        regionLayout = QHBoxLayout()
        regionLayout.addWidget(QLabel("X:"))
        regionLayout.addWidget(self.xEdit)
        regionLayout.addWidget(QLabel("Y:"))
        regionLayout.addWidget(self.yEdit)
        regionLayout.addWidget(QLabel("Width:"))
        regionLayout.addWidget(self.widthEdit)
        regionLayout.addWidget(QLabel("Height:"))
        regionLayout.addWidget(self.heightEdit)
        layout.addLayout(regionLayout)

        # --- New Button: Fill with Canvas Size ---
        fillLayout = QHBoxLayout()
        btnFillCanvas = QPushButton("Fill with Canvas Size")
        btnFillCanvas.clicked.connect(self.fillCanvasSize)
        fillLayout.addWidget(btnFillCanvas)
        layout.addLayout(fillLayout)
        # --- End New Button ---

        # --- Resize Inputs with Persistence ---
        newWidth_default = self.settings.value("newWidth", width_default)
        newHeight_default = self.settings.value("newHeight", height_default)
        self.newWidthEdit = QLineEdit(newWidth_default)
        self.newHeightEdit = QLineEdit(newHeight_default)
        resizeLayout = QHBoxLayout()
        resizeLayout.addWidget(QLabel("New Width:"))
        resizeLayout.addWidget(self.newWidthEdit)
        resizeLayout.addWidget(QLabel("New Height:"))
        resizeLayout.addWidget(self.newHeightEdit)
        layout.addLayout(resizeLayout)
        # --- End Resize Inputs ---

        # --- Rotation Option ---
        rotation_default = self.settings.value("rotation", "None")
        self.rotationCombo = QComboBox()
        self.rotationCombo.addItems(["None", "Rotate Clockwise", "Rotate Counterclockwise"])
        index = self.rotationCombo.findText(rotation_default)
        if index != -1:
            self.rotationCombo.setCurrentIndex(index)
        else:
            self.rotationCombo.setCurrentIndex(0)
        rotateLayout = QHBoxLayout()
        rotateLayout.addWidget(QLabel("Rotation:"))
        rotateLayout.addWidget(self.rotationCombo)
        layout.addLayout(rotateLayout)
        # --- End Rotation Option ---

        # --- Checkbox for Export Option ---
        self.exportSelectedCheckbox = QCheckBox("Export Selected Layers Only")
        export_selected_default = self.settings.value("exportSelected", "false")
        self.exportSelectedCheckbox.setChecked(export_selected_default == "true")
        layout.addWidget(self.exportSelectedCheckbox)
        # --- End Checkbox Option ---

        # --- Modified Code: Prefill Output File with Layer Name ---
        last_output_dir = self.settings.value("lastOutputDir", "")
        default_output = last_output_dir
        if last_output_dir:
            app = Krita.instance()
            doc = app.activeDocument()
            if doc:
                active_node = doc.activeNode()
                layer_name = active_node.name() if active_node else "export"
            else:
                layer_name = "export"
            default_output = os.path.join(last_output_dir, f"{layer_name}.png")
        fileLayout = QHBoxLayout()
        self.outputPathEdit = QLineEdit(default_output)
        btnBrowse = QPushButton("Browse")
        btnBrowse.clicked.connect(self.browseFile)
        fileLayout.addWidget(QLabel("Output File:"))
        fileLayout.addWidget(self.outputPathEdit)
        fileLayout.addWidget(btnBrowse)
        layout.addLayout(fileLayout)
        # --- End Modified Code ---

        # Export button.
        btnExport = QPushButton("Export")
        btnExport.clicked.connect(self.export)
        layout.addWidget(btnExport)

        self.setLayout(layout)

    def fillCanvasSize(self):
        """
        Sets the region fields to the current canvas size (X=0, Y=0, Width/Height from document).
        """
        app = Krita.instance()
        doc = app.activeDocument()
        if doc is None:
            QMessageBox.warning(self, "Error", "No active document found.")
            return
        self.xEdit.setText("0")
        self.yEdit.setText("0")
        self.widthEdit.setText(str(doc.width()))
        self.heightEdit.setText(str(doc.height()))

    def browseFile(self):
        default_dir = self.settings.value("lastOutputDir", "")
        fileName, _ = QFileDialog.getSaveFileName(
            self,
            "Select output file",
            default_dir,
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*)"
        )
        if fileName:
            self.outputPathEdit.setText(fileName)

    def get_all_nodes(self, doc):
        """Recursively get all nodes from the document."""
        nodes = []
        def traverse(node):
            nodes.append(node)
            for child in node.childNodes():
                traverse(child)
        for node in doc.topLevelNodes():
            traverse(node)
        return nodes
    
    def export(self):
        # Get integer values from region inputs.
        try:
            x = int(self.xEdit.text())
            y = int(self.yEdit.text())
            w = int(self.widthEdit.text())
            h = int(self.heightEdit.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter valid integer values for X, Y, Width and Height.")
            return

        # Get integer values from resize inputs.
        try:
            newW = int(self.newWidthEdit.text())
            newH = int(self.newHeightEdit.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter valid integer values for New Width and New Height.")
            return

        outputFile = self.outputPathEdit.text().strip()
        if not outputFile or os.path.isdir(outputFile):
            QMessageBox.warning(self, "Error", "Please select a valid output file (not a directory).")
            return

        app = Krita.instance()
        doc = app.activeDocument()
        view = app.activeWindow().activeView()
        if doc is None:
            QMessageBox.warning(self, "Error", "No active document found.")
            return

        layers = 0
        # If exporting selected layers only, hide all other layers temporarily.
        if self.exportSelectedCheckbox.isChecked():
            selected_nodes = view.selectedNodes()
            if not selected_nodes:
                QMessageBox.warning(self, "Error", "No layers selected.")
                return
            # Get all nodes to adjust their visibility.
            all_nodes = self.get_all_nodes(doc)
            old_visibility = {}
            for node in all_nodes:
                id = node.uniqueId().toString()
                old_visibility[id] = node.visible()
                node.setVisible(False)
            for node in selected_nodes:
                set_node_and_parents_visible(node, True)
                layers = layers + 1
            doc.refreshProjection()
            # Perform the projection on the selected layers.
            cropped = doc.projection(x, y, w, h)
            # Restore original visibility.
            for node in all_nodes:
                id = node.uniqueId().toString()
                node.setVisible(old_visibility[id])
            doc.refreshProjection()
        else:
            # Use the projection method on the whole document.
            cropped = doc.projection(x, y, w, h)

        # Resize if necessary.
        if newW != w or newH != h:
            cropped = cropped.scaled(newW, newH, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        # --- Rotation Logic ---
        rotation = self.rotationCombo.currentText()
        if rotation == "Rotate Clockwise":
            transform = QTransform().rotate(90)
            cropped = cropped.transformed(transform, Qt.SmoothTransformation)
        elif rotation == "Rotate Counterclockwise":
            transform = QTransform().rotate(-90)
            cropped = cropped.transformed(transform, Qt.SmoothTransformation)
        # --- End Rotation Logic ---

        # Save the cropped image.
        if cropped.save(outputFile):
            # Save the exportSelected choice.
            self.settings.setValue("exportSelected", "true" if self.exportSelectedCheckbox.isChecked() else "false")
            # Persist current region values.
            self.settings.setValue("x", self.xEdit.text())
            self.settings.setValue("y", self.yEdit.text())
            self.settings.setValue("width", self.widthEdit.text())
            self.settings.setValue("height", self.heightEdit.text())
            # Persist new resize values.
            self.settings.setValue("newWidth", self.newWidthEdit.text())
            self.settings.setValue("newHeight", self.newHeightEdit.text())
            # Persist rotation option.
            self.settings.setValue("rotation", self.rotationCombo.currentText())
            # Persist the output directory.
            self.settings.setValue("lastOutputDir", os.path.dirname(outputFile))
            QMessageBox.information(self, "Success", "Export successful!{0}".format(" Layers exported: {0}".format(layers) if self.exportSelectedCheckbox.isChecked() else ""))
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

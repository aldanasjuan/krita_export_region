import os
from krita import Extension, Krita
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import QRect, QSettings, Qt
from PyQt5.QtGui import QImage

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

        # --- New Code: Resize Inputs with Persistence ---
        # Retrieve persisted new width/height values, defaulting to region values.
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
        # --- End New Code ---

        # Create file output selector.
        last_output_dir = self.settings.value("lastOutputDir", "")
        fileLayout = QHBoxLayout()
        self.outputPathEdit = QLineEdit(last_output_dir)
        btnBrowse = QPushButton("Browse")
        btnBrowse.clicked.connect(self.browseFile)
        fileLayout.addWidget(QLabel("Output File:"))
        fileLayout.addWidget(self.outputPathEdit)
        fileLayout.addWidget(btnBrowse)
        layout.addLayout(fileLayout)

        # Export button.
        btnExport = QPushButton("Export")
        btnExport.clicked.connect(self.export)
        layout.addWidget(btnExport)

        self.setLayout(layout)

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
        if not outputFile:
            QMessageBox.warning(self, "Error", "Please select an output file.")
            return

        # Get the active document from Krita.
        app = Krita.instance()
        doc = app.activeDocument()
        if doc is None:
            QMessageBox.warning(self, "Error", "No active document found.")
            return

        # Use the projection method to get the cropped image.
        cropped = doc.projection(x, y, w, h)

        # --- New Code: Resize if necessary ---
        # If the new dimensions differ from the region's, scale the cropped image.
        if newW != w or newH != h:
            cropped = cropped.scaled(newW, newH, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        # --- End New Code ---

        # Save the cropped (and possibly resized) image.
        if cropped.save(outputFile):
            # Persist current region values.
            self.settings.setValue("x", self.xEdit.text())
            self.settings.setValue("y", self.yEdit.text())
            self.settings.setValue("width", self.widthEdit.text())
            self.settings.setValue("height", self.heightEdit.text())
            # Persist new resize values.
            self.settings.setValue("newWidth", self.newWidthEdit.text())
            self.settings.setValue("newHeight", self.newHeightEdit.text())
            # Persist the output directory.
            self.settings.setValue("lastOutputDir", os.path.dirname(outputFile))
            QMessageBox.information(self, "Success", "Export successful!")
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

import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, 
                           QFileDialog, QMessageBox, QFrame, QProgressBar, QHBoxLayout, 
                           QSizePolicy, QGridLayout, QTabWidget, QCheckBox, QGroupBox,
                           QRadioButton, QComboBox, QSpinBox)
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QObject, pyqtSlot
from PIL import Image, ImageFile
import os
import concurrent.futures
import time

# Enable loading of truncated images to prevent the "image file is truncated" error
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Check if AVIF is supported
AVIF_SUPPORT = False
try:
    from pillow_avif import AvifImagePlugin  # This is an optional dependency
    AVIF_SUPPORT = True
except ImportError:
    # pillow_avif is not installed - AVIF format will not be available
    pass

class DropArea(QLabel):
    dropped = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #BBBBBB;
                border-radius: 10px;
                background-color: #F0F0F0;
                padding: 25px;
            }
        """)
        self.setText("Drop Image Here or Click 'Select Input Image'")
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QLabel {
                    border: 2px dashed #2196F3;
                    border-radius: 10px;
                    background-color: #E3F2FD;
                    padding: 25px;
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #BBBBBB;
                border-radius: 10px;
                background-color: #F0F0F0;
                padding: 25px;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                self.dropped.emit(file_path)
            else:
                QMessageBox.warning(self, "Invalid File", "Please drop an image file.")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #BBBBBB;
                border-radius: 10px;
                background-color: #F0F0F0;
                padding: 25px;
            }
        """)

class MultiDropArea(QLabel):
    dropped = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #BBBBBB;
                border-radius: 10px;
                background-color: #F0F0F0;
                padding: 25px;
            }
        """)
        self.setText("Drop Image(s) Here or Click 'Select Input'")
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QLabel {
                    border: 2px dashed #2196F3;
                    border-radius: 10px;
                    background-color: #E3F2FD;
                    padding: 25px;
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #BBBBBB;
                border-radius: 10px;
                background-color: #F0F0F0;
                padding: 25px;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                    file_paths.append(file_path)
            
            if file_paths:
                self.dropped.emit(file_paths)
            else:
                QMessageBox.warning(self, "Invalid Files", "Please drop valid image files.")
        
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #BBBBBB;
                border-radius: 10px;
                background-color: #F0F0F0;
                padding: 25px;
            }
        """)
        
    def update_preview(self, file_paths):
        if not file_paths:
            self.setText("Drop Image(s) Here or Click 'Select Input'")
            return
            
        # If there's just one image, show a preview
        if len(file_paths) == 1:
            try:
                pixmap = QPixmap(file_paths[0])
                if not pixmap.isNull():
                    preview = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.setPixmap(preview)
                    self.setAlignment(Qt.AlignCenter)
                    return
            except:
                pass
        
        # If multiple images or preview failed, just show text
        if len(file_paths) == 1:
            self.setText(f"1 image selected")
        else:
            self.setText(f"{len(file_paths)} images selected")

class ImageResizerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                color: #333333;
                font-family: 'Roboto', sans-serif;
            }
            QLabel {
                font-size: 12px;
            }
            QProgressBar {
                border: 1px solid #BBBBBB;
                border-radius: 5px;
                text-align: center;
                height: 20px;
                background-color: #F0F0F0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
            QTabWidget::pane {
                border: 1px solid #BBBBBB;
                border-radius: 5px;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #F0F0F0;
                border: 1px solid #BBBBBB;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 10px 15px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                border-bottom: 1px solid #FFFFFF;
            }
            QGroupBox {
                border: 1px solid #BBBBBB;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QCheckBox, QRadioButton {
                spacing: 8px;
            }
            QComboBox, QSpinBox {
                border: 1px solid #BBBBBB;
                border-radius: 3px;
                padding: 3px;
            }
        """)

    def create_button(self, text, callback, extra_styles=""):
        btn = QPushButton(text, self)
        btn.setFont(QFont('Roboto', 12, QFont.Bold))
        base_style = """
            QPushButton {
                background-color: #2196F3; 
                color: white; 
                border-radius: 10px; 
                padding: 12px;
                width: 200px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #BBBBBB;
                color: #F5F5F5;
            }
        """
        btn.setStyleSheet(base_style + extra_styles)
        btn.clicked.connect(callback)
        return btn

    def create_label(self, text):
        label = QLabel(text, self)
        label.setFont(QFont('Roboto', 12))
        label.setWordWrap(True)
        return label

    def initUI(self):
        self.setWindowTitle('PWA Asset Generator')
        self.setGeometry(100, 100, 800, 600)

        self.input_image_path = ""
        self.output_directory = ""
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.pwa_tab = QWidget()
        self.converter_tab = QWidget()
        
        # Add tabs to widget
        self.tab_widget.addTab(self.pwa_tab, "PWA Icon Generator")
        self.tab_widget.addTab(self.converter_tab, "Image Format Converter")
        
        # Set up PWA Icon Generator tab
        self.setup_pwa_tab()
        
        # Set up Image Format Converter tab
        self.setup_converter_tab()
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

    def setup_pwa_tab(self):
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("PWA Asset Generator", self)
        title_label.setFont(QFont('Roboto', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #1976D2; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Generate all the icon sizes you need for your Progressive Web App", self)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #666666; margin-bottom: 20px;")
        layout.addWidget(desc_label)

        # Drag and drop area
        self.drop_area = DropArea(self)
        self.drop_area.dropped.connect(self.set_input_image)
        layout.addWidget(self.drop_area)

        # Input section
        input_layout = QHBoxLayout()
        self.input_label = self.create_label("Input Image: Not selected")
        self.input_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        input_layout.addWidget(self.input_label)
        self.input_button = self.create_button('Select Input Image', self.select_input_image)
        input_layout.addWidget(self.input_button)
        layout.addLayout(input_layout)

        self.add_separator(layout)

        # Output section
        output_layout = QHBoxLayout()
        self.output_label = self.create_label("Output Directory: Not selected")
        self.output_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        output_layout.addWidget(self.output_label)
        self.output_button = self.create_button('Select Output Directory', self.select_output_directory)
        output_layout.addWidget(self.output_button)
        layout.addLayout(output_layout)

        self.add_separator(layout)

        # Progress bar
        self.progress_label = QLabel("Ready to generate icons", self)
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Resize button
        self.resize_button = self.create_button('Generate Icons', self.start_resizing, 
                                               "\nmargin-top: 30px;\nmargin-bottom: 30px;")
        layout.addWidget(self.resize_button, alignment=Qt.AlignCenter)
        
        # Status
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #666666;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.pwa_tab.setLayout(layout)

    def setup_converter_tab(self):
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Image Format Converter", self)
        title_label.setFont(QFont('Roboto', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #1976D2; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Convert your images to different formats with optimal compression", self)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #666666; margin-bottom: 20px;")
        layout.addWidget(desc_label)

        # Drag and drop area
        self.converter_drop_area = MultiDropArea(self)
        self.converter_drop_area.dropped.connect(self.set_converter_input_files)
        layout.addWidget(self.converter_drop_area)

        # Input section
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout()
        
        # Single file or multiple files
        self.single_file_radio = QRadioButton("Single File")
        self.single_file_radio.setChecked(True)
        self.single_file_radio.toggled.connect(self.toggle_input_mode)
        self.multiple_files_radio = QRadioButton("Multiple Files")
        
        file_select_layout = QHBoxLayout()
        file_select_layout.addWidget(self.single_file_radio)
        file_select_layout.addWidget(self.multiple_files_radio)
        file_select_layout.addStretch()
        input_layout.addLayout(file_select_layout)
        
        # Input file selection
        input_file_layout = QHBoxLayout()
        self.converter_input_label = self.create_label("Input File(s): Not selected")
        self.converter_input_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        input_file_layout.addWidget(self.converter_input_label)
        self.converter_input_button = self.create_button('Select Input', self.select_converter_input)
        input_file_layout.addWidget(self.converter_input_button)
        input_layout.addLayout(input_file_layout)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Output section
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        
        # Output format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItem("WebP (best quality/size balance)")
        self.format_combo.addItem("JPEG (smaller files)")
        self.format_combo.addItem("PNG (lossless quality)")
        
        if AVIF_SUPPORT:
            self.format_combo.addItem("AVIF (best compression)")
        else:
            # Add an option to show users how to enable AVIF support
            self.format_combo.addItem("AVIF (not available - click for info)")
            
        self.format_combo.currentIndexChanged.connect(self.update_quality_options)
        format_layout.addWidget(self.format_combo)
        output_layout.addLayout(format_layout)
        
        # Quality settings
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_slider = QSpinBox()
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(80)
        quality_layout.addWidget(self.quality_slider)
        output_layout.addLayout(quality_layout)
        
        # Resize option
        resize_layout = QHBoxLayout()
        self.resize_checkbox = QCheckBox("Resize images")
        self.resize_checkbox.toggled.connect(self.toggle_resize_options)
        resize_layout.addWidget(self.resize_checkbox)
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(1, 10000)
        self.width_spinbox.setValue(800)
        self.width_spinbox.setEnabled(False)
        resize_layout.addWidget(QLabel("Width:"))
        resize_layout.addWidget(self.width_spinbox)
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(1, 10000)
        self.height_spinbox.setValue(600)
        self.height_spinbox.setEnabled(False)
        resize_layout.addWidget(QLabel("Height:"))
        resize_layout.addWidget(self.height_spinbox)
        self.keep_aspect_ratio = QCheckBox("Keep aspect ratio")
        self.keep_aspect_ratio.setChecked(True)
        self.keep_aspect_ratio.setEnabled(False)
        resize_layout.addWidget(self.keep_aspect_ratio)
        output_layout.addLayout(resize_layout)
        
        # Output directory selection
        output_dir_layout = QHBoxLayout()
        self.converter_output_label = self.create_label("Output Directory: Not selected")
        self.converter_output_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        output_dir_layout.addWidget(self.converter_output_label)
        self.converter_output_button = self.create_button('Select Output Directory', self.select_converter_output)
        output_dir_layout.addWidget(self.converter_output_button)
        output_layout.addLayout(output_dir_layout)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Progress section
        self.converter_progress_label = QLabel("Ready to convert", self)
        layout.addWidget(self.converter_progress_label)
        
        self.converter_progress_bar = QProgressBar(self)
        self.converter_progress_bar.setMaximum(100)
        self.converter_progress_bar.setValue(0)
        layout.addWidget(self.converter_progress_bar)
        
        # Convert button
        self.convert_button = self.create_button('Convert Images', self.start_conversion, 
                                                "\nmargin-top: 30px;\nmargin-bottom: 30px;")
        layout.addWidget(self.convert_button, alignment=Qt.AlignCenter)
        
        # Status
        self.converter_status_label = QLabel("", self)
        self.converter_status_label.setAlignment(Qt.AlignCenter)
        self.converter_status_label.setStyleSheet("color: #666666;")
        layout.addWidget(self.converter_status_label)
        
        layout.addStretch()
        self.converter_tab.setLayout(layout)
        
        # Initialize variables
        self.converter_input_files = []
        self.converter_output_dir = ""

    def add_separator(self, layout):
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("margin-top: 10px; margin-bottom: 10px;")
        layout.addWidget(separator)

    def select_input_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Input Image", "", 
            "Image files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.set_input_image(file_path)
    
    def set_input_image(self, file_path):
        self.input_image_path = file_path
        file_name = os.path.basename(file_path)
        self.input_label.setText(f"Input Image: {file_name}")
        self.status_label.setText(f"Image '{file_name}' selected")
        
        # Show preview if possible
        try:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                preview = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.drop_area.setPixmap(preview)
                self.drop_area.setAlignment(Qt.AlignCenter)
            else:
                self.drop_area.setText("Drop Image Here or Click 'Select Input Image'")
        except:
            self.drop_area.setText("Drop Image Here or Click 'Select Input Image'")

    def select_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_directory = directory
            self.output_label.setText(f"Output Directory: {os.path.basename(directory)}")
            self.status_label.setText(f"Output folder set to '{os.path.basename(directory)}'")

    def start_resizing(self):
        if not self.input_image_path or not self.output_directory:
            QMessageBox.warning(self, "Warning", "Please select both input image and output directory.")
            return
        
        # Disable UI elements during processing
        self.resize_button.setEnabled(False)
        self.input_button.setEnabled(False)
        self.output_button.setEnabled(False)
        
        sizes = [16, 72, 96, 128, 144, 152, 192, 384, 512]
        self.thread = QThread()
        self.worker = ImageResizerWorker(self.input_image_path, self.output_directory, sizes)
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.update_progress)
        self.worker.status_update.connect(self.update_status)
        self.worker.finished.connect(self.on_resize_finished)
        self.worker.error.connect(self.on_resize_error)
        
        # Start the thread
        self.progress_bar.setValue(0)
        self.progress_label.setText("Generating icons...")
        self.thread.start()

    @pyqtSlot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    @pyqtSlot(str)
    def update_status(self, message):
        self.status_label.setText(message)

    def on_resize_finished(self):
        QMessageBox.information(self, "Success", "Icons generated successfully!")
        self.reset_input()
        self.thread.quit()
        self.thread.wait()

    def on_resize_error(self, error_message):
        QMessageBox.critical(self, "Error", error_message)
        self.thread.quit()
        self.thread.wait()
        self.reset_ui()

    def reset_input(self):
        self.input_image_path = ""
        self.output_directory = ""
        self.input_label.setText("Input Image: Not selected")
        self.output_label.setText("Output Directory: Not selected")
        self.progress_bar.setValue(0)
        self.progress_label.setText("Ready to generate icons")
        self.status_label.setText("")
        self.drop_area.setText("Drop Image Here or Click 'Select Input Image'")
        self.drop_area.setPixmap(QPixmap())
        self.reset_ui()
    
    def reset_ui(self):
        self.resize_button.setEnabled(True)
        self.input_button.setEnabled(True)
        self.output_button.setEnabled(True)

    def toggle_input_mode(self):
        if self.single_file_radio.isChecked():
            self.converter_input_button.setText('Select Input File')
        else:
            self.converter_input_button.setText('Select Input Files')

        # Clear current selection only if switching modes
        if self.single_file_radio.isChecked() and len(self.converter_input_files) > 1:
            self.converter_input_files = []
            self.converter_input_label.setText("Input File(s): Not selected")
        elif self.multiple_files_radio.isChecked() and len(self.converter_input_files) == 1:
            self.converter_input_files = []
            self.converter_input_label.setText("Input File(s): Not selected")

    def toggle_resize_options(self, checked):
        self.width_spinbox.setEnabled(checked)
        self.height_spinbox.setEnabled(checked)
        self.keep_aspect_ratio.setEnabled(checked)

    def update_quality_options(self, index):
        # Adjust quality defaults based on format
        if index == 0:  # WebP
            self.quality_slider.setValue(80)
        elif index == 1:  # JPEG
            self.quality_slider.setValue(85)
        elif index == 2:  # PNG
            self.quality_slider.setValue(100)
        elif index == 3:  # AVIF or AVIF info
            if AVIF_SUPPORT:
                self.quality_slider.setValue(60)
            else:
                # Show info about installing AVIF support
                QMessageBox.information(
                    self, 
                    "AVIF Support Not Available", 
                    "To enable AVIF format support, please install the required package:\n\n"
                    "pip install pillow-avif\n\n"
                    "After installation, restart the application to use AVIF format."
                )
                # Reset to WebP format
                self.format_combo.setCurrentIndex(0)

    def select_converter_input(self):
        if self.single_file_radio.isChecked():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Input Image", "", 
                "Image files (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
            )
            if file_path:
                self.converter_input_files = [file_path]
                file_name = os.path.basename(file_path)
                self.converter_input_label.setText(f"Input File: {file_name}")
                self.converter_status_label.setText(f"Selected file: {file_name}")
                # Update the drop area with preview
                self.converter_drop_area.update_preview(self.converter_input_files)
        else:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "Select Input Images", "", 
                "Image files (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
            )
            if file_paths:
                self.converter_input_files = file_paths
                self.converter_input_label.setText(f"Input Files: {len(file_paths)} files selected")
                self.converter_status_label.setText(f"Selected {len(file_paths)} files")
                # Update the drop area with preview
                self.converter_drop_area.update_preview(self.converter_input_files)

    def select_converter_output(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.converter_output_dir = directory
            self.converter_output_label.setText(f"Output Directory: {os.path.basename(directory)}")
            self.converter_status_label.setText(f"Output folder set to '{os.path.basename(directory)}'")

    def start_conversion(self):
        if not self.converter_input_files or not self.converter_output_dir:
            QMessageBox.warning(self, "Warning", "Please select both input file(s) and output directory.")
            return
        
        # Get conversion settings
        format_index = self.format_combo.currentIndex()
        
        # Check if AVIF is selected but not supported
        if format_index == 3 and not AVIF_SUPPORT:
            QMessageBox.warning(
                self, 
                "Format Not Available", 
                "AVIF format is not available. Please install pillow-avif package or select a different format."
            )
            return
            
        if format_index == 0:
            output_format = 'WebP'
        elif format_index == 1:
            output_format = 'JPEG'
        elif format_index == 2:
            output_format = 'PNG'
        elif AVIF_SUPPORT and format_index == 3:
            output_format = 'AVIF'
        
        quality = self.quality_slider.value()
        
        resize_enabled = self.resize_checkbox.isChecked()
        resize_settings = None
        if resize_enabled:
            resize_settings = {
                'width': self.width_spinbox.value(),
                'height': self.height_spinbox.value(),
                'keep_aspect_ratio': self.keep_aspect_ratio.isChecked()
            }
        
        # Disable UI elements during processing
        self.convert_button.setEnabled(False)
        self.converter_input_button.setEnabled(False)
        self.converter_output_button.setEnabled(False)
        
        # Start conversion in a separate thread
        self.convert_thread = QThread()
        self.convert_worker = ImageConverterWorker(
            self.converter_input_files,
            self.converter_output_dir,
            output_format,
            quality,
            resize_settings
        )
        self.convert_worker.moveToThread(self.convert_thread)
        
        # Connect signals
        self.convert_thread.started.connect(self.convert_worker.run)
        self.convert_worker.progress.connect(self.update_converter_progress)
        self.convert_worker.status_update.connect(self.update_converter_status)
        self.convert_worker.finished.connect(self.on_conversion_finished)
        self.convert_worker.error.connect(self.on_conversion_error)
        
        # Start the thread
        self.converter_progress_bar.setValue(0)
        self.converter_progress_label.setText("Converting images...")
        self.convert_thread.start()
    
    @pyqtSlot(int)
    def update_converter_progress(self, value):
        self.converter_progress_bar.setValue(value)
    
    @pyqtSlot(str)
    def update_converter_status(self, message):
        self.converter_status_label.setText(message)

    def on_conversion_finished(self):
        QMessageBox.information(self, "Success", "Images converted successfully!")
        self.reset_converter()
        self.convert_thread.quit()
        self.convert_thread.wait()

    def on_conversion_error(self, error_message):
        QMessageBox.critical(self, "Error", error_message)
        self.convert_thread.quit()
        self.convert_thread.wait()
        self.reset_converter_ui()
    
    def reset_converter(self):
        # Reset all converter-related inputs
        self.converter_input_files = []
        self.converter_output_dir = ""
        self.converter_input_label.setText("Input File(s): Not selected")
        self.converter_output_label.setText("Output Directory: Not selected")
        self.converter_progress_bar.setValue(0)
        self.converter_progress_label.setText("Ready to convert")
        self.converter_status_label.setText("")
        self.converter_drop_area.setText("Drop Image(s) Here or Click 'Select Input'")
        self.converter_drop_area.setPixmap(QPixmap())  # Clear any preview image
        self.reset_converter_ui()
    
    def reset_converter_ui(self):
        self.convert_button.setEnabled(True)
        self.converter_input_button.setEnabled(True)
        self.converter_output_button.setEnabled(True)

    def set_converter_input_files(self, file_paths):
        self.converter_input_files = file_paths
        
        if len(file_paths) == 1:
            # If single file is dropped, set the radio button to "Single File"
            self.single_file_radio.setChecked(True)
            file_name = os.path.basename(file_paths[0])
            self.converter_input_label.setText(f"Input File: {file_name}")
            self.converter_status_label.setText(f"Selected file: {file_name}")
        else:
            # If multiple files are dropped, set the radio button to "Multiple Files"
            self.multiple_files_radio.setChecked(True)
            self.converter_input_label.setText(f"Input Files: {len(file_paths)} files selected")
            self.converter_status_label.setText(f"Selected {len(file_paths)} files")
        
        # Update the drop area with preview or count information
        self.converter_drop_area.update_preview(file_paths)

class ImageResizerWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    status_update = pyqtSignal(str)

    def __init__(self, input_path, output_dir, sizes):
        super().__init__()
        self.input_path = input_path
        self.output_dir = output_dir
        self.sizes = sizes

    def run(self):
        try:
            # First verify the image can be opened
            try:
                img = Image.open(self.input_path)
                # Verify image is valid by accessing a property
                img.size
            except Exception as e:
                self.error.emit(f"Failed to open image: {str(e)}")
                return
                
            # Now process with the valid image
            with Image.open(self.input_path) as img:
                # Use parallel processing for faster resizing
                total_tasks = len(self.sizes)
                completed_tasks = 0
                self.status_update.emit("Loading image...")
                
                # Use a thread pool to resize images in parallel
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = []
                    
                    # Function to resize a single image
                    def resize_image(size):
                        try:
                            resized_img = img.copy()
                            if resized_img is None:
                                return "Failed to copy image - received None object"
                                
                            resized_img = resized_img.resize((size, size), Image.LANCZOS)
                            
                            # Save the resized image
                            if size == 16:
                                # Fix for ICO format saving
                                output_path = os.path.join(self.output_dir, 'favicon.ico')
                                # For ICO files, we need to convert to RGBA mode
                                if resized_img.mode != 'RGBA':
                                    resized_img = resized_img.convert('RGBA')
                                try:
                                    # Save the image using PIL's ico format directly
                                    resized_img.save(output_path, format='ICO', sizes=[(16, 16)])
                                except Exception as save_error:
                                    return f"Failed to save favicon.ico: {str(save_error)}"
                            else:
                                output_path = os.path.join(self.output_dir, f'icon-{size}x{size}.png')
                                try:
                                    resized_img.save(output_path, format='PNG')
                                except Exception as save_error:
                                    return f"Failed to save icon-{size}x{size}.png: {str(save_error)}"
                                
                            return True
                        except Exception as e:
                            return f"Failed to resize image to {size}x{size}: {str(e)}"
                    
                    # Submit all resizing tasks to the executor
                    for size in self.sizes:
                        futures.append(executor.submit(resize_image, size))
                    
                    # Process the results as they complete
                    for i, future in enumerate(concurrent.futures.as_completed(futures)):
                        result = future.result()
                        if result is not True:
                            self.error.emit(f"Failed to resize image: {result}")
                            return
                        
                        completed_tasks += 1
                        progress_value = int((completed_tasks / total_tasks) * 100)
                        self.progress.emit(progress_value)
                        self.status_update.emit(f"Generating icons: {completed_tasks}/{total_tasks}")
                
                # Also create a manifest.json file with all the icons
                manifest_icons = []
                for size in self.sizes:
                    if size != 16:  # Skip favicon
                        manifest_icons.append({
                            "src": f"icon-{size}x{size}.png",
                            "sizes": f"{size}x{size}",
                            "type": "image/png"
                        })
                
                manifest_content = {
                    "name": "PWA App",
                    "short_name": "PWA",
                    "icons": manifest_icons,
                    "start_url": ".",
                    "display": "standalone",
                    "theme_color": "#ffffff",
                    "background_color": "#ffffff"
                }
                
                import json
                try:
                    with open(os.path.join(self.output_dir, 'manifest.json'), 'w') as f:
                        json.dump(manifest_content, f, indent=2)
                except Exception as e:
                    self.error.emit(f"Failed to create manifest.json: {str(e)}")
                    return
                
            self.status_update.emit("All icons generated successfully!")
            self.progress.emit(100)
            self.finished.emit()
            
        except FileNotFoundError:
            self.error.emit("File not found.")
        except PermissionError:
            self.error.emit("Permission denied.")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")

class ImageConverterWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    status_update = pyqtSignal(str)

    def __init__(self, input_files, output_dir, output_format, quality, resize_settings=None):
        super().__init__()
        self.input_files = input_files
        self.output_dir = output_dir
        self.output_format = output_format
        self.quality = quality
        self.resize_settings = resize_settings

    def run(self):
        try:
            total_files = len(self.input_files)
            processed_files = 0
            self.status_update.emit("Preparing to convert...")
            
            # Get file extension for output format
            if self.output_format == 'WebP':
                extension = '.webp'
                save_format = 'WebP'
            elif self.output_format == 'JPEG':
                extension = '.jpg'
                save_format = 'JPEG'
            elif self.output_format == 'PNG':
                extension = '.png'
                save_format = 'PNG'
            elif self.output_format == 'AVIF':
                # Double-check AVIF support again to be safe
                if not AVIF_SUPPORT:
                    self.error.emit("AVIF support is not available. Please install pillow-avif package.")
                    return
                extension = '.avif'
                save_format = 'AVIF'
            
            # Use a thread pool for parallel processing
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                
                # Function to convert a single file
                def convert_file(file_path):
                    try:
                        # Open the image
                        with Image.open(file_path) as img:
                            # Store original dimensions
                            original_width, original_height = img.size
                            
                            # Resize if needed
                            if self.resize_settings:
                                target_width = self.resize_settings['width']
                                target_height = self.resize_settings['height']
                                
                                if self.resize_settings['keep_aspect_ratio']:
                                    # Calculate aspect ratio
                                    aspect_ratio = original_width / original_height
                                    
                                    # Determine dimensions based on aspect ratio
                                    if original_width > original_height:  # Landscape
                                        new_width = target_width
                                        new_height = int(target_width / aspect_ratio)
                                    else:  # Portrait or square
                                        new_height = target_height
                                        new_width = int(target_height * aspect_ratio)
                                else:
                                    new_width = target_width
                                    new_height = target_height
                                
                                img = img.resize((new_width, new_height), Image.LANCZOS)
                                # Update original dimensions to these new resized dimensions
                                original_width, original_height = new_width, new_height
                            
                            # Determine output filename
                            base_name = os.path.splitext(os.path.basename(file_path))[0]
                            output_path = os.path.join(self.output_dir, f"{base_name}{extension}")
                            
                            # Convert color mode if needed
                            if self.output_format == 'JPEG' and img.mode == 'RGBA':
                                img = img.convert('RGB')
                            
                            # Special handling for AVIF to avoid green bar artifacts
                            if self.output_format == 'AVIF' and AVIF_SUPPORT:
                                # Get current dimensions
                                width, height = img.size
                                
                                # Calculate new dimensions divisible by 8
                                new_width = (width + 7) // 8 * 8
                                new_height = (height + 7) // 8 * 8
                                
                                # Check if we need padding
                                if new_width != width or new_height != height:
                                    # Create a new image with the padded dimensions
                                    # Use magenta color for padding to make it clearly visible during development
                                    padded_img = Image.new(img.mode, (new_width, new_height), color=(255, 0, 255) if img.mode in ('RGB', 'RGBA') else 255)
                                    
                                    # Paste the original image into the padded image
                                    padded_img.paste(img, (0, 0))
                                    
                                    # Save the padded image to a temporary file
                                    temp_path = output_path + ".tmp"
                                    padded_img.save(temp_path, format='AVIF', quality=self.quality)
                                    
                                    # Reopen and crop back to original dimensions
                                    with Image.open(temp_path) as avif_img:
                                        cropped_img = avif_img.crop((0, 0, original_width, original_height))
                                        cropped_img.save(output_path, format='AVIF', quality=self.quality)
                                    
                                    # Remove temporary file
                                    try:
                                        os.remove(temp_path)
                                    except:
                                        pass  # If we can't remove it, not a big deal
                                else:
                                    # No padding needed, dimensions already divisible by 8
                                    img.save(output_path, format='AVIF', quality=self.quality)
                            # Save with appropriate options for other formats
                            elif self.output_format in ['WebP', 'JPEG']:
                                img.save(output_path, format=save_format, quality=self.quality)
                            elif self.output_format == 'PNG':
                                # For PNG, quality is compression level (0-9)
                                compression_level = 9 - int(self.quality / 11.1)  # Map 0-100 to 9-0
                                img.save(output_path, format='PNG', optimize=True, 
                                        compress_level=min(9, max(0, compression_level)))
                            
                            return True
                    except Exception as e:
                        return f"Error converting {os.path.basename(file_path)}: {str(e)}"
                
                # Submit all conversion tasks
                for file_path in self.input_files:
                    futures.append(executor.submit(convert_file, file_path))
                
                # Process results as they complete
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    result = future.result()
                    if result is not True:
                        self.error.emit(result)
                        return
                    
                    processed_files += 1
                    progress_value = int((processed_files / total_files) * 100)
                    self.progress.emit(progress_value)
                    self.status_update.emit(f"Converting files: {processed_files}/{total_files}")
            
            self.status_update.emit(f"Successfully converted {processed_files} files!")
            self.progress.emit(100)
            self.finished.emit()
            
        except FileNotFoundError:
            self.error.emit("File not found.")
        except PermissionError:
            self.error.emit("Permission denied.")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Set application style
    app.setStyle('Fusion')
    ex = ImageResizerApp()
    ex.show()
    sys.exit(app.exec_())
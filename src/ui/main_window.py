"""Main window for the Asset Manager application."""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                           QFileDialog, QMessageBox, QFrame, QProgressBar, 
                           QHBoxLayout, QSizePolicy, QGridLayout, QTabWidget, 
                           QCheckBox, QGroupBox, QRadioButton, QComboBox, QSpinBox)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QThread
from .components import DropArea, MultiDropArea
from ..workers.image_workers import ImageResizerWorker, ImageConverterWorker
import os

class ImageResizerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.apply_stylesheet()

    def apply_stylesheet(self):
        """Apply the application's stylesheet."""
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
        """Create a styled button."""
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
        """Create a styled label."""
        label = QLabel(text, self)
        label.setFont(QFont('Roboto', 12))
        label.setWordWrap(True)
        return label

    def initUI(self):
        """Initialize the user interface."""
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
        
        # Set up tabs
        self.setup_pwa_tab()
        self.setup_converter_tab()
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

    def setup_pwa_tab(self):
        """Set up the PWA Icon Generator tab."""
        layout = QVBoxLayout()
        
        # Title and description
        title_label = QLabel("PWA Asset Generator", self)
        title_label.setFont(QFont('Roboto', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #1976D2; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        desc_label = QLabel("Generate all the icon sizes you need for your Progressive Web App", self)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #666666; margin-bottom: 20px;")
        layout.addWidget(desc_label)

        # Drop area
        self.drop_area = DropArea(self)
        self.drop_area.dropped.connect(self.set_input_image)
        layout.addWidget(self.drop_area)

        # Input and output sections
        self.setup_input_section(layout)
        self.add_separator(layout)
        self.setup_output_section(layout)
        self.add_separator(layout)

        # Progress section
        self.setup_progress_section(layout)

        # Resize button
        self.resize_button = self.create_button(
            'Generate Icons', 
            self.start_resizing, 
            "\nmargin-top: 30px;\nmargin-bottom: 30px;"
        )
        layout.addWidget(self.resize_button, alignment=Qt.AlignCenter)
        
        # Status
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #666666;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.pwa_tab.setLayout(layout)

    def setup_converter_tab(self):
        """Set up the Image Format Converter tab."""
        layout = QVBoxLayout()
        
        # Title and description
        title_label = QLabel("Image Format Converter", self)
        title_label.setFont(QFont('Roboto', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #1976D2; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        desc_label = QLabel("Convert your images to different formats with optimal compression", self)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #666666; margin-bottom: 20px;")
        layout.addWidget(desc_label)

        # Drop area
        self.converter_drop_area = MultiDropArea(self)
        self.converter_drop_area.dropped.connect(self.set_converter_input_files)
        layout.addWidget(self.converter_drop_area)

        # Setup input and output sections
        self.setup_converter_input_section(layout)
        self.setup_converter_output_section(layout)
        
        # Progress section
        self.setup_converter_progress_section(layout)
        
        # Convert button
        self.convert_button = self.create_button(
            'Convert Images', 
            self.start_conversion,
            "\nmargin-top: 30px;\nmargin-bottom: 30px;"
        )
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

    def setup_input_section(self, layout):
        """Set up the input section of the PWA tab."""
        input_layout = QHBoxLayout()
        self.input_label = self.create_label("Input Image: Not selected")
        self.input_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        input_layout.addWidget(self.input_label)
        self.input_button = self.create_button('Select Input Image', self.select_input_image)
        input_layout.addWidget(self.input_button)
        layout.addLayout(input_layout)

    def setup_output_section(self, layout):
        """Set up the output section of the PWA tab."""
        output_layout = QHBoxLayout()
        self.output_label = self.create_label("Output Directory: Not selected")
        self.output_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        output_layout.addWidget(self.output_label)
        self.output_button = self.create_button('Select Output Directory', self.select_output_directory)
        output_layout.addWidget(self.output_button)
        layout.addLayout(output_layout)

    def setup_progress_section(self, layout):
        """Set up the progress section of the PWA tab."""
        self.progress_label = QLabel("Ready to generate icons", self)
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

    def setup_converter_input_section(self, layout):
        """Set up the input section of the converter tab."""
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout()
        
        # Single file or multiple files selection
        file_select_layout = QHBoxLayout()
        self.single_file_radio = QRadioButton("Single File")
        self.single_file_radio.setChecked(True)
        self.single_file_radio.toggled.connect(self.toggle_input_mode)
        self.multiple_files_radio = QRadioButton("Multiple Files")
        
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

    def setup_converter_output_section(self, layout):
        """Set up the output section of the converter tab."""
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        
        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItem("WebP (best quality/size balance)")
        self.format_combo.addItem("JPEG (smaller files)")
        self.format_combo.addItem("PNG (lossless quality)")
        
        try:
            from pillow_avif import AvifImagePlugin
            self.format_combo.addItem("AVIF (best compression)")
            self.has_avif_support = True
        except ImportError:
            self.format_combo.addItem("AVIF (not available - click for info)")
            self.has_avif_support = False
            
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
        
        # Resize settings
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

    def setup_converter_progress_section(self, layout):
        """Set up the progress section of the converter tab."""
        self.converter_progress_label = QLabel("Ready to convert", self)
        layout.addWidget(self.converter_progress_label)
        
        self.converter_progress_bar = QProgressBar(self)
        self.converter_progress_bar.setMaximum(100)
        self.converter_progress_bar.setValue(0)
        layout.addWidget(self.converter_progress_bar)

    def add_separator(self, layout):
        """Add a horizontal separator line to the layout."""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("margin-top: 10px; margin-bottom: 10px;")
        layout.addWidget(separator)

    def select_input_image(self):
        """Handle input image selection."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Input Image", "", 
            "Image files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.set_input_image(file_path)
    
    def set_input_image(self, file_path):
        """Set the input image and update UI."""
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
        """Handle output directory selection."""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_directory = directory
            self.output_label.setText(f"Output Directory: {os.path.basename(directory)}")
            self.status_label.setText(f"Output folder set to '{os.path.basename(directory)}'")

    def start_resizing(self):
        """Start the icon generation process."""
        if not self.input_image_path:
            QMessageBox.warning(self, "Warning", "Please select an input image.")
            return
            
        # If output directory is not selected, use input image's directory
        if not self.output_directory:
            self.output_directory = os.path.dirname(self.input_image_path)
            dir_name = os.path.basename(self.output_directory)
            self.output_label.setText(f"Output Directory: {dir_name}")
            self.status_label.setText(f"Using input image directory as output: '{dir_name}'")
        
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

    def update_progress(self, value):
        """Update the progress bar."""
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        """Update the status label."""
        self.status_label.setText(message)

    def on_resize_finished(self):
        """Handle completion of the resize operation."""
        QMessageBox.information(self, "Success", "Icons generated successfully!")
        self.reset_input()
        self.thread.quit()
        self.thread.wait()

    def on_resize_error(self, error_message):
        """Handle errors in the resize operation."""
        QMessageBox.critical(self, "Error", error_message)
        self.thread.quit()
        self.thread.wait()
        self.reset_ui()

    def reset_input(self):
        """Reset all input fields and UI elements."""
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
        """Re-enable UI elements."""
        self.resize_button.setEnabled(True)
        self.input_button.setEnabled(True)
        self.output_button.setEnabled(True)

    def toggle_input_mode(self):
        """Toggle between single and multiple file input modes."""
        if self.single_file_radio.isChecked():
            self.converter_input_button.setText('Select Input File')
        else:
            self.converter_input_button.setText('Select Input Files')

        # Clear current selection if switching modes
        if self.single_file_radio.isChecked() and len(self.converter_input_files) > 1:
            self.converter_input_files = []
            self.converter_input_label.setText("Input File(s): Not selected")
        elif self.multiple_files_radio.isChecked() and len(self.converter_input_files) == 1:
            self.converter_input_files = []
            self.converter_input_label.setText("Input File(s): Not selected")

    def toggle_resize_options(self, checked):
        """Enable/disable resize options."""
        self.width_spinbox.setEnabled(checked)
        self.height_spinbox.setEnabled(checked)
        self.keep_aspect_ratio.setEnabled(checked)

    def update_quality_options(self, index):
        """Update quality settings based on selected format."""
        # Adjust quality defaults based on format
        if index == 0:  # WebP
            self.quality_slider.setValue(80)
        elif index == 1:  # JPEG
            self.quality_slider.setValue(85)
        elif index == 2:  # PNG
            self.quality_slider.setValue(100)
        elif index == 3:  # AVIF or AVIF info
            if hasattr(self, 'has_avif_support') and self.has_avif_support:
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
        """Handle converter input selection."""
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
                # Update the drop area with preview or count information
                self.converter_drop_area.update_preview(file_paths)

    def select_converter_output(self):
        """Handle converter output directory selection."""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.converter_output_dir = directory
            self.converter_output_label.setText(f"Output Directory: {os.path.basename(directory)}")
            self.converter_status_label.setText(f"Output folder set to '{os.path.basename(directory)}'")

    def start_conversion(self):
        """Start the image conversion process."""
        if not self.converter_input_files:
            QMessageBox.warning(self, "Warning", "Please select input file(s).")
            return
            
        # If output directory is not selected, check if we can use the input directory
        if not self.converter_output_dir:
            # For single file, use its directory
            if len(self.converter_input_files) == 1:
                self.converter_output_dir = os.path.dirname(self.converter_input_files[0])
                dir_name = os.path.basename(self.converter_output_dir)
                self.converter_output_label.setText(f"Output Directory: {dir_name}")
                self.converter_status_label.setText(f"Using input file directory as output: '{dir_name}'")
            # For multiple files, check if they're all from the same directory
            else:
                # Get unique directories
                input_dirs = {os.path.dirname(f) for f in self.converter_input_files}
                if len(input_dirs) == 1:
                    # All files are from the same directory
                    self.converter_output_dir = list(input_dirs)[0]
                    dir_name = os.path.basename(self.converter_output_dir)
                    self.converter_output_label.setText(f"Output Directory: {dir_name}")
                    self.converter_status_label.setText(f"Using common input directory as output: '{dir_name}'")
                else:
                    # Files from different directories
                    QMessageBox.warning(
                        self, 
                        "Output Directory Required", 
                        "Input files are from different directories. Please select an output directory."
                    )
                    return
        
        # Get conversion settings
        format_index = self.format_combo.currentIndex()
        
        # Check if AVIF is selected but not supported
        if format_index == 3 and not hasattr(self, 'has_avif_support'):
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
        elif hasattr(self, 'has_avif_support') and format_index == 3:
            output_format = 'AVIF'
        
        quality = self.quality_slider.value()
        
        resize_settings = None
        if self.resize_checkbox.isChecked():
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

    def update_converter_progress(self, value):
        """Update the converter progress bar."""
        self.converter_progress_bar.setValue(value)
    
    def update_converter_status(self, message):
        """Update the converter status label."""
        self.converter_status_label.setText(message)

    def on_conversion_finished(self):
        """Handle completion of the conversion operation."""
        QMessageBox.information(self, "Success", "Images converted successfully!")
        self.reset_converter()
        self.convert_thread.quit()
        self.convert_thread.wait()

    def on_conversion_error(self, error_message):
        """Handle errors in the conversion operation."""
        QMessageBox.critical(self, "Error", error_message)
        self.convert_thread.quit()
        self.convert_thread.wait()
        self.reset_converter_ui()
    
    def reset_converter(self):
        """Reset all converter-related inputs and UI elements."""
        self.converter_input_files = []
        self.converter_output_dir = ""
        self.converter_input_label.setText("Input File(s): Not selected")
        self.converter_output_label.setText("Output Directory: Not selected")
        self.converter_progress_bar.setValue(0)
        self.converter_progress_label.setText("Ready to convert")
        self.converter_status_label.setText("")
        self.converter_drop_area.setText("Drop Image(s) Here or Click 'Select Input'")
        self.converter_drop_area.setPixmap(QPixmap())
        self.reset_converter_ui()
    
    def reset_converter_ui(self):
        """Re-enable converter UI elements."""
        self.convert_button.setEnabled(True)
        self.converter_input_button.setEnabled(True)
        self.converter_output_button.setEnabled(True)

    def set_converter_input_files(self, file_paths):
        """Handle dropped files in the converter."""
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
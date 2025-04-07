"""UI Components for the Asset Manager application."""

from PyQt5.QtWidgets import QLabel, QMessageBox
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal

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
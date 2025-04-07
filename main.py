"""
Asset Manager Application
A tool for generating PWA assets and converting image formats.
"""

import sys
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import ImageResizerApp

def main():
    app = QApplication(sys.argv)
    # Set application style
    app.setStyle('Fusion')
    ex = ImageResizerApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
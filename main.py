import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle('Prodmax')
label = QLabel('Hello, World!', parent=window)
window.show()
window.setGeometry(100, 100, 1000, 800)
sys.exit(app.exec_())
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit
import requests

#############################################################################
# Setting up PyQt5 Application
#############################################################################

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle('Prodmax')
window.setGeometry(100, 100, 1000, 800)

response = requests.get("http://localhost:8000/messages")
messages = response.json()

text_edit = QTextEdit(parent=window)
text_edit.setReadOnly(True)
text_edit.setGeometry(50, 50, 900, 700)
text_edit.setText("\n".join(messages))

window.show()
sys.exit(app.exec_())
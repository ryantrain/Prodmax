import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit
from database import supabase

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle('Prodmax')

response = supabase.table("messages").select("*").execute()
messages = response.data

text = messages[0]['sender'] + ": " + messages[0]['content']

text_edit = QTextEdit(parent=window)
text_edit.setText(text)
text_edit.setReadOnly(True)
text_edit.setGeometry(50, 50, 900, 700)

window.setGeometry(100, 100, 1000, 800)
window.show()
sys.exit(app.exec_())
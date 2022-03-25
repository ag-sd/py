from PyQt5.QtGui import QFontDatabase, QTextCursor
from PyQt5.QtWidgets import QDialog, QComboBox, QTextEdit, QVBoxLayout

import TransCoda


class TerminalView(QDialog):
    def __init__(self):
        super().__init__()
        self.file_selector = QComboBox()
        self.text_box = QTextEdit()
        self.logs = {}
        self.init_ui()

    def init_ui(self):
        self.text_box.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self.text_box.setStyleSheet("QTextEdit{background: back; color: grey; font-size: 11.5px;}")
        self.file_selector.currentTextChanged.connect(self.file_selector_changed)
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(self.file_selector)
        layout.addWidget(self.text_box)
        self.setLayout(layout)
        self.setModal(False)
        self.setMinimumSize(800, 450)
        self.setWindowIcon(TransCoda.theme.ico_app_icon)

    def log_message(self, message):
        _file = message['file']
        _message = self.create_message(message['time'], message['message'])
        if _file in self.logs:
            self.logs[_file].append(_message)
        else:
            self.logs[_file] = [_message]
            self.file_selector.addItem(_file)

        if self.file_selector.currentText() == _file:
            self.text_box.moveCursor(QTextCursor.End)
            self.text_box.insertPlainText(_message)
            self.text_box.moveCursor(QTextCursor.End)

    def file_selector_changed(self):
        self.text_box.clear()
        self.text_box.insertPlainText("".join(self.logs[self.file_selector.currentText()]))

    @staticmethod
    def create_message(time, message):
        return f"{time}:{message}"
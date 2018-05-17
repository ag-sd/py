from PyQt5.QtWidgets import \
    (QWidget,
     QLabel,
     QLineEdit,
     QFileDialog,
     QPushButton,
     QHBoxLayout,
     QApplication)
from PyQt5.QtCore import (QDir)
import sys


class FileChooser(QWidget):

    def __init__(self, label, cue, _dir, lbl_align_right=False):
        super().__init__()
        self.label = label
        self.cue = cue
        self.dir = _dir
        self.selection = ''
        self.text = QLineEdit()
        self.lbl_align_right = lbl_align_right
        self.setLayout(self.get_layout())

    def get_layout(self):
        self.text.setReadOnly(True)
        self.text.setObjectName("txtAddress")
        button = QPushButton("...")
        button.clicked.connect(lambda: self.browse_for_item(self.text))
        width = button.fontMetrics().boundingRect("...").width() + 12
        button.setMaximumWidth(width)
        button.setMaximumHeight(self.text.height())
        layout = QHBoxLayout()
        if not self.lbl_align_right:
            layout.addWidget(QLabel(self.label))
        layout.addWidget(self.text)
        layout.addWidget(button)
        if self.lbl_align_right:
            layout.addWidget(QLabel(self.label))
        layout.setContentsMargins(0, 0, 0, 0)
        return layout

    def browse_for_item(self, text):
        if self.dir:
            file = QFileDialog.getExistingDirectory(caption=self.cue)
        else:
            file, _filter = QFileDialog.getOpenFileName(caption=self.cue)

        self.selection = QDir.toNativeSeparators(file)
        text.setText(self.selection)

    def getSelection(self):
        return self.selection

    def setSelection(self, selection):
        self.selection = selection
        self.text.setText(selection)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FileChooser("label", "cue", True)
    ex.show()
    sys.exit(app.exec_())

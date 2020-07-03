import json
import os
import sys
from functools import partial

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPainter
from PyQt5.QtWidgets import QDialog, QApplication, QVBoxLayout, QTreeView, QComboBox, QHBoxLayout, \
    QDialogButtonBox, QStyle, QStyleOptionComboBox, QLineEdit, QGroupBox, QLabel, QWidget, \
    QGridLayout

from CustomUI import QHLine


def get_config_file():
    return os.path.join(os.path.dirname(__file__), "resource/encoders.json")


class EncoderSelector(QComboBox):

    encoder_changed = pyqtSignal('PyQt_PyObject', 'PyQt_PyObject')

    def __init__(self, model):
        super().__init__()
        self.tree_view = QTreeView(self)
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)
        self.tree_view.setSelectionBehavior(QTreeView.SelectRows)
        self.tree_view.setWordWrap(True)
        self.tree_view.setHeaderHidden(True)
        self.setView(self.tree_view)
        self.setModel(model)
        self.tree_view.expandAll()
        self.selected_encoder = self.currentText()

    def paintEvent(self, event):
        style = QApplication.style()
        opt = QStyleOptionComboBox()
        opt.rect = self.rect()
        self.initStyleOption(opt)
        painter = QPainter(self)
        painter.save()
        style.drawComplexControl(QStyle.CC_ComboBox, opt, painter)
        opt.currentText = self._encoder_path()
        style.drawControl(QStyle.CE_ComboBoxLabel, opt, painter)
        painter.restore()

    def hidePopup(self):
        super(EncoderSelector, self).hidePopup()
        selected_index = self.tree_view.selectionModel().currentIndex()
        if selected_index:
            self.selected_encoder = self.tree_view.model().get_item(selected_index)
            self.encoder_changed.emit(self._encoder_path(), self._encoder_details())

    def _encoder_path(self):
        match = self.model().match(self.model().index(0, 0), Qt.UserRole + 1, self.selected_encoder, 1,
                                   Qt.MatchEndsWith | Qt.MatchRecursive)
        if match:
            return match[0].data(Qt.UserRole + 1)

    def _encoder_details(self):
        match = self.model().match(self.model().index(0, 0), Qt.UserRole + 1, self.selected_encoder, 1,
                                   Qt.MatchEndsWith | Qt.MatchRecursive)
        if match:
            return match[0].data(Qt.UserRole + 2)


class EncoderModel(QStandardItemModel):
    def __init__(self, json_config, disable_selections=False):
        super().__init__()
        self.json = json_config
        self.disable_selections = disable_selections
        self._build_descendents(self.invisibleRootItem(), self.json, disable_selections)

    def get_item(self, model_index):
        item = self.itemFromIndex(model_index)
        return item.text()

    def get_json(self):
        return json.dumps(self.json, indent=4)

    def set_json(self, _json):
        self.json = json.loads(_json)
        self.clear()
        self._build_descendents(self.invisibleRootItem(), self.json, self.disable_selections)

    def select_encoder(self, encoder_name):
        return self.findItems(encoder_name, Qt.MatchExactly | Qt.MatchRecursive)

    def get_encoder_config(self, encoder_name):
        self._find_encoder(self.json, encoder_name)

    @staticmethod
    def _find_encoder(_json, encoder_name):
        # Does a Depth first search for the selected encoder
        for key in _json:
            if key == encoder_name:
                return _json[key]
            else:
                EncoderModel.find_encoder(_json[key], encoder_name)
        return None

    @staticmethod
    def _build_descendents(parent, _json, disable_selections):
        encoder_keys = {"extension", "executable", "command"}
        intersection = set(_json.keys()) & encoder_keys
        if not intersection:
            # add node and build further
            for key in _json:
                section_root = QStandardItem(key)
                parent.appendRow(section_root)
                if disable_selections:
                    parent.setSelectable(False)
                EncoderModel._build_descendents(section_root, _json[key], disable_selections)
        else:
            if len(intersection) < 3:
                raise SyntaxError(f"Missing value(s) {encoder_keys - intersection} in node {parent.text()}")
            else:
                path = ""
                item = parent
                while item.parent() is not None:
                    path = f" → {item.text()}" + path
                    item = item.parent()
                path = f"{item.text()}" + path
                parent.setData(path, Qt.UserRole + 1)
                parent.setData(_json, Qt.UserRole + 2)


class EncoderView(QWidget):
    def __init__(self, encoder=None, caption="Encoder Details", ):
        super().__init__()
        self._init_ui(caption, encoder)

    def update_view(self, caption, encoder):
        self._init_ui(caption, encoder)

    def _init_ui(self, caption, encoder):
        extension = ""
        executable = ""
        command = ""
        if encoder:
            extension = encoder["extension"]
            executable = encoder["executable"]
            command = encoder["command"]

        layout = QGridLayout()

        layout.addWidget(QLabel("Extension"), 0, 0)
        layout.addWidget(QLineEdit(extension), 0, 1)

        layout.addWidget(QLabel("Executable"), 1, 0)
        layout.addWidget(QLineEdit(executable), 1, 1)

        layout.addWidget(QLabel("Command"), 2, 0)
        layout.addWidget(QLineEdit(command), 2, 1)
        group_box = QGroupBox(caption)
        group_box.setLayout(layout)

        main_layout = QHBoxLayout()
        main_layout.addWidget(group_box)
        self.setLayout(main_layout)


class TransCodaEditor(QDialog):
    def __init__(self):
        super().__init__()
        with open(get_config_file()) as json_file:
            encoder_model = EncoderModel(json.load(json_file), disable_selections=True)
            self.encoder = EncoderSelector(encoder_model)
        self.details = EncoderView()
        self._init_ui()

    def _init_ui(self):
        self.encoder.encoder_changed.connect(self._get_encoder_details)
        # self.encoder.currentTextChanged.connect(partial(self._get_encoder_details,
        #                                                 self.encoder.currentData(Qt.UserRole + 1)))

        buttons = QDialogButtonBox()
        buttons.addButton(QDialogButtonBox.Save)
        # buttons.accepted.connect(partial(self._button_actions, "save"))

        v_layout = QVBoxLayout()
        v_layout.addWidget(self.encoder, 1)
        v_layout.addWidget(self.details)
        v_layout.addWidget(QHLine())
        v_layout.addWidget(buttons)

        self.setLayout(v_layout)
        self.setWindowTitle("Trans:Coda Encoder Editor")
        self.setMinimumWidth(450)
        self.exec_()

    def _get_encoder_details(self, path, encoder):
        self.details.update_view("ENcoder Details", encoder)



# class TransCodaEditor(QDialog):
#     def __init__(self):
#         super().__init__()
#         with open(get_config_file()) as json_file:
#             self.json = json.load(json_file)
#         model = EncoderModel(self.json, disable_selections=True)
#         self.encoder_selector = EncoderSelector(model)
#         self.encoder_selector.encoder_changed.connect(self._encoder_changed)
#         self.editor = QsciScintilla()
#         self.toolbar = QToolBar()
#         self._init_ui()
#
#     def _init_ui(self):
#         self._setup_editor()
#         buttons = QDialogButtonBox()
#         buttons.addButton(QDialogButtonBox.Close)
#         buttons.addButton(QDialogButtonBox.Save)
#         buttons.accepted.connect(partial(self._button_actions, "save"))
#         buttons.rejected.connect(partial(self._button_actions, "cancel"))
#
#         h_layout = QHBoxLayout()
#         h_layout.setContentsMargins(5, 0, 5, 5)
#         h_layout.addWidget(self.encoder_selector, 1)
#         h_layout.addWidget(buttons)
#
#         layout = QVBoxLayout()
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.addWidget(self.editor)
#         layout.addWidget(QHLine())
#         layout.addLayout(h_layout)
#
#         self.setLayout(layout)
#         self.setWindowTitle("Trans:Coda Encoder Editor")
#         self.setMinimumSize(640, 480)
#         self.exec_()
#
#     def _setup_editor(self):
#         font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
#         self.editor.setFont(font)
#         self.editor.setBraceMatching(QsciScintilla.SloppyBraceMatch)
#         self.editor.setCaretLineVisible(True)
#         self.editor.setCaretLineBackgroundColor(QColor("#ffe4e4"))
#         self.editor.setMarginWidth(0, QFontMetrics(font).width("000") + 6)
#         self.editor.setMarginLineNumbers(0, True)
#         self.editor.setMarginsFont(font)
#         self.editor.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 0)
#         self.editor.setText(json.dumps(self.json, indent=4))
#         self.editor.setIndentationsUseTabs(False)
#         self.editor.setTabWidth(4)
#         self.editor.setIndentationGuides(True)
#         self.editor.setAutoIndent(True)
#         lexer = QsciLexerJSON()
#         lexer.setDefaultFont(font)
#         self.editor.setLexer(lexer)
#
#     def _encoder_changed(self, encoder_path):
#         keys = encoder_path.split("→")
#         for key in keys:
#             print(key.strip())
#             self.editor.findFirst(key.strip(), False, False, False, True)
#
#     def _button_actions(self, action):
#         if action == "save":
#             try:
#                 # Validate the configuration
#                 EncoderModel(json.loads(self.editor.text()))
#
#                 config_file = get_config_file()
#                 with open(config_file, "r+") as json_file:
#                     # Create a copy of the current configuration
#                     backup_config_file = config_file + f".{datetime.now()}"
#                     shutil.copy(config_file, backup_config_file)
#                     # Save the config to the file
#                     json_file.seek(0)
#                     json_file.write(self.editor.text())
#                     json_file.truncate()
#                     # Update the view
#                     self.tree_view.model().set_json(self.editor.text())
#                     self.tree_view.expandAll()
#             except SyntaxError as s:
#                 QMessageBox.critical(self, "Error! Malformed input received", str(s))
#             except JSONDecodeError as j:
#                 QMessageBox.critical(self, "Error! Malformed input received", str(j))
#         elif action == "cancel":
#             self.close()


# class TransCodaEditor1(QDialog):
#     def __init__(self):
#         super().__init__()
#         self.editor = QsciScintilla()
#         with open(get_config_file()) as json_file:
#             self.model = EncoderModel(json.load(json_file))
#         self.tree_view = EncoderTreeView()
#         self.tree_view.setModel(self.model)
#         self.tree_view.expandAll()
#         self.history = QListWidget()
#
#         self.init_ui()
#
#     def init_ui(self):
#         font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
#         self.editor.setFont(font)
#         self.editor.setBraceMatching(QsciScintilla.SloppyBraceMatch)
#         self.editor.setCaretLineVisible(True)
#         self.editor.setCaretLineBackgroundColor(QColor("#ffe4e4"))
#         self.editor.setMarginWidth(0, QFontMetrics(font).width("000") + 6)
#         self.editor.setMarginLineNumbers(0, True)
#         self.editor.setMarginsFont(font)
#         self.editor.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 0)
#         self.editor.setText(self.tree_view.model().get_json())
#         self.editor.setIndentationsUseTabs(False)
#         self.editor.setTabWidth(4)
#         self.editor.setIndentationGuides(True)
#         self.editor.setAutoIndent(True)
#
#         lexer = QsciLexerJSON()
#         lexer.setDefaultFont(font)
#         self.editor.setLexer(lexer)
#
#         selection_model = self.tree_view.selectionModel()
#         selection_model.selectionChanged.connect(self.selection_changed)
#
#         buttons = QDialogButtonBox()
#         buttons.addButton(QDialogButtonBox.Close)
#         buttons.addButton(QDialogButtonBox.Save)
#         buttons.accepted.connect(partial(self.button_actions, "save"))
#         buttons.rejected.connect(partial(self.button_actions, "cancel"))
#         right_layout = QVBoxLayout()
#         right_layout.addWidget(self.editor)
#         right_layout.addWidget(QHLine())
#         right_layout.addWidget(buttons)
#         left_layout = QVBoxLayout()
#         left_layout.addWidget(QLabel("Encoder Hierearchy"))
#         left_layout.addWidget(self.tree_view)
#         left_layout.addWidget(QLabel("History"))
#         left_layout.addWidget(self.history)
#         layout = QHBoxLayout()
#         layout.addLayout(left_layout, 1)
#         layout.addLayout(right_layout, 3)
#
#         self.setLayout(layout)
#         self.setWindowTitle("Trans:Coda Encoder Editor")
#         self.setMinimumSize(800, 550)
#         self.exec_()
#
#     def selection_changed(self, selected, deselected):
#         indices = selected.indexes()
#         if len(indices):
#             text = self.tree_view.model().get_item(indices[0])
#             self.editor.findFirst(text, False, False, False, True)
#
#     def button_actions(self, action):
#         if action == "save":
#             try:
#                 # Validate the configuration
#                 EncoderModel(json.loads(self.editor.text()))
#
#                 config_file = get_config_file()
#                 with open(config_file, "r+") as json_file:
#                     # Create a copy of the current configuration
#                     backup_config_file = config_file + f".{datetime.now()}"
#                     shutil.copy(config_file, backup_config_file)
#                     # Save the config to the file
#                     json_file.seek(0)
#                     json_file.write(self.editor.text())
#                     json_file.truncate()
#                     # Update the view
#                     self.tree_view.model().set_json(self.editor.text())
#                     self.tree_view.expandAll()
#             except SyntaxError as s:
#                 QMessageBox.critical(self, "Error! Malformed input received", str(s))
#             except JSONDecodeError as j:
#                 QMessageBox.critical(self, "Error! Malformed input received", str(j))
#         elif action == "cancel":
#             self.close()


def main():
    app = QApplication(sys.argv)
    ex = TransCodaEditor()
    # # with open(os.path.join(os.path.dirname(__file__), "resource/encoders.json")) as json_file:
    # #     model = EncoderModel(json.load(json_file), disable_selections=True)
    # combo = EncoderSelector()
    # combo.setMinimumWidth(300)
    # combo.show()
    # combo.set_encoder("baz")
    # enc = {
    #     "extension": "Fpp",
    #     "executable": "Fpp",
    #     "command": "Fpp"
    # }
    # label = EncoderView(enc)
    # # label.resize(1, 1)
    # # label.setFrameStyle(QFrame.Plain)
    # # # label.setBackgroundMode(Qt.FixedColor)
    # # # label.setPaletteBackgroundColor(QColor("red"))
    # # label.setText(
    # #     "<table width=\"100%\" border=1><tr><td width=\"10%\">aaa<br>ccc<br>ddd</td><td>bbb</td></tr></table>")
    # label.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

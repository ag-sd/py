import json
import os
import sys
from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPainter, QIcon
from PyQt5.QtWidgets import QDialog, QApplication, QTreeView, QComboBox, QHBoxLayout, \
    QStyle, QStyleOptionComboBox, QLineEdit, QGroupBox, QLabel, QWidget, \
    QGridLayout, QToolBar, QPushButton, QVBoxLayout, QDialogButtonBox

import CommonUtils
from CustomUI import QHLine


def get_config_file():
    return os.path.join(os.path.dirname(__file__), "resource/encoders.json")


def backup_config_file():
    file = get_config_file()
    backup = file + ".bak" + datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    os.rename(file, backup)
    return backup


class EncoderSelector(QComboBox):
    __PATH_SEPARATOR__ = " → "

    class EncoderModel(QStandardItemModel):
        def __init__(self, json_file, disable_selections=False):
            super().__init__()
            self.disable_selections = disable_selections
            self.json_file = json_file
            self.json = None
            self.reload()

        def reload(self):
            with open(self.json_file) as config:
                self.json = json.load(config)
                self.beginResetModel()
                self.clear()
                self._build_descendents(self.invisibleRootItem(), self.json, self.disable_selections)
                self.endResetModel()

        def get_item(self, model_index):
            item = self.itemFromIndex(model_index)
            return item.text()

        def del_item(self, media_type, encoder_group, name):
            del self.json[media_type][encoder_group][name]
            # Clean up ancestors if they dont have any children
            if len(self.json[media_type][encoder_group].keys()) == 0:
                del self.json[media_type][encoder_group]
            if len(self.json[media_type].keys()) == 0:
                del self.json[media_type]

        def add_item(self, media_type, group, name, extension, executable, command):
            if not self.json[media_type]:
                self.json[media_type] = {}
            if not self.json[media_type][group]:
                self.json[media_type][group] = {}
            self.json[media_type][group][name] = {
                "extension": extension,
                "executable": executable,
                "command": command
            }

        def backup_and_save(self):
            # Backup current config
            backup_config_file()
            # Save new config
            with open(self.json_file, "w") as config:
                json.dump(self.json, config, indent=4)
            self.reload()

        #
        # def get_json(self):
        #     return json.dumps(self.json, indent=4)
        #
        # def set_json(self, _json):
        #     self.json = json.loads(_json)
        #     self.clear()
        #     self._build_descendents(self.invisibleRootItem(), self.json, self.disable_selections)
        #
        # def select_encoder(self, encoder_name):
        #     return self.findItems(encoder_name, Qt.MatchExactly | Qt.MatchRecursive)
        #
        # def get_encoder_config(self, encoder_name):
        #     self._find_encoder(self.json, encoder_name)
        #
        # @staticmethod
        # def _find_encoder(_json, encoder_name):
        #     # Does a Depth first search for the selected encoder
        #     for key in _json:
        #         if key == encoder_name:
        #             return _json[key]
        #         else:
        #             EncoderSelector.EncoderModel.find_encoder(_json[key], encoder_name)
        #     return None

        # def _start_rebuild(self):


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
                    EncoderSelector.EncoderModel._build_descendents(section_root, _json[key], disable_selections)
            else:
                if len(intersection) < 3:
                    raise SyntaxError(f"Missing value(s) {encoder_keys - intersection} in node {parent.text()}")
                else:
                    path = ""
                    item = parent
                    while item.parent() is not None:
                        path = f"{EncoderSelector.__PATH_SEPARATOR__}{item.text()}" + path
                        item = item.parent()
                    path = f"{item.text()}" + path
                    parent.setData(path, Qt.UserRole + 1)
                    parent.setData(_json, Qt.UserRole + 2)

    encoder_changed = pyqtSignal('PyQt_PyObject', 'PyQt_PyObject')

    def __init__(self):
        super().__init__()
        self.tree_view = QTreeView(self)
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)
        self.tree_view.setSelectionBehavior(QTreeView.SelectRows)
        self.tree_view.setWordWrap(True)
        self.tree_view.setHeaderHidden(True)
        self.setView(self.tree_view)
        self.encoder_model = EncoderSelector.EncoderModel(get_config_file(), disable_selections=True)
        self.setModel(self.encoder_model)
        self.refresh_encoders()
        self._selected_encoder = ""

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
            self._selected_encoder = self.tree_view.model().get_item(selected_index)
            self.encoder_changed.emit(self._encoder_path(), self._encoder_details())

    def get_encoder(self):
        return self._encoder_path(), self._encoder_details()

    def add_encoder(self, media_type, encoder_group, name, extension, executable, command):
        self.encoder_model.add_item(media_type, encoder_group, name, extension, executable, command)
        self.encoder_model.backup_and_save()
        self.refresh_encoders()

    def del_encoder(self, media_type, encoder_group, name):
        self.encoder_model.del_item(media_type, encoder_group, name)
        self.encoder_model.backup_and_save()
        self.refresh_encoders()

    def update_encoder(self, media_type, encoder_group, name, extension, executable, command):
        self.encoder_model.del_item(media_type, encoder_group, name)
        self.encoder_model.add_item(media_type, encoder_group, name, extension, executable, command)
        self.encoder_model.backup_and_save()
        self.refresh_encoders()

    def refresh_encoders(self):
        self.encoder_model.reload()
        self.tree_view.expandAll()

    def _encoder_path(self):
        match = self.model().match(self.model().index(0, 0), Qt.UserRole + 1, self._selected_encoder, 1,
                                   Qt.MatchEndsWith | Qt.MatchRecursive)
        if match:
            return match[0].data(Qt.UserRole + 1)

    def _encoder_details(self):
        match = self.model().match(self.model().index(0, 0), Qt.UserRole + 1, self._selected_encoder, 1,
                                   Qt.MatchEndsWith | Qt.MatchRecursive)
        if match:
            return match[0].data(Qt.UserRole + 2)


class EncoderView(QDialog):
    def __init__(self):
        super().__init__()
        self.txt_extension = QLineEdit()
        self.txt_executable = QLineEdit()
        self.txt_command = QLineEdit()
        self.txt_name = QLineEdit(placeholderText="Encoder Name")
        self.group_box = QGroupBox()
        self.media_type = QComboBox()
        self.txt_encoder_group = QLineEdit()
        self.details = {}
        self._init_ui()

    def update_view(self, action, encoder_path=None, encoder=None):
        self.txt_extension.setText("")
        self.txt_executable.setText("")
        self.txt_command.setText("")
        self.txt_encoder_group.setText("")
        self.setWindowTitle(action)
        if encoder_path:
            path = encoder_path.split(EncoderSelector.__PATH_SEPARATOR__)
            self.txt_encoder_group.setText(path[1])
            self.group_box.setTitle(path[2])
            index = self.media_type.findText(path[0], Qt.MatchFixedString)
            if index >= 0:
                self.media_type.setCurrentIndex(index)
            else:
                self.media_type.addItem(path[0])
                self.media_type.setCurrentIndex(self.media_type.findText(path[0], Qt.MatchFixedString))
        else:
            self.txt_name.setVisible(True)
            self.group_box.setTitle("")
        if encoder:
            self.txt_extension.setText(encoder["extension"])
            self.txt_executable.setText(encoder["executable"])
            self.txt_command.setText(encoder["command"])
            self.txt_name.setVisible(False)

    def _init_ui(self):
        layout = QGridLayout()

        self.media_type.addItems(["Audio", "Video"])
        self.media_type.setEditable(True)

        layout.addWidget(QLabel("Extension"), 1, 0)
        layout.addWidget(self.txt_extension, 1, 1)

        layout.addWidget(QLabel("Executable"), 2, 0)
        layout.addWidget(self.txt_executable, 2, 1)

        layout.addWidget(QLabel("Command"), 3, 0)
        layout.addWidget(self.txt_command, 3, 1)

        layout.addWidget(QLabel("Encoder Group"), 4, 0)
        layout.addWidget(self.txt_encoder_group, 4, 1)

        layout.addWidget(QLabel("Media Type"), 5, 0)
        layout.addWidget(self.media_type, 5, 1)

        self.group_box.setLayout(layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        layout.addWidget(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.txt_name)
        main_layout.addWidget(self.group_box)
        main_layout.addWidget(QHLine())
        main_layout.addWidget(buttons)

        self.setLayout(main_layout)
        self.setMinimumWidth(400)

    def accept(self):
        self.details = {
            "media_type": self.media_type.currentText(),
            "encoder_group": self.txt_encoder_group.text(),
            "command": self.txt_command.text(),
            "executable": self.txt_executable.text(),
            "extension": self.txt_extension.text()
        }
        super().accept()

    def reject(self):
        self.details = {}
        super().reject()

    def get_details(self):
        if self.details:
            return self.details["media_type"], self.details["encoder_group"], self.details["command"], \
                   self.details["executable"], self.details["extension"]
        else:
            return None, None, None, None, None


class TransCodaEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.encoder = EncoderSelector()
        self.encoder_view = EncoderView()
        self.actions = QToolBar()
        self.add_action = CommonUtils.create_toolbar_action("Add Encoder", QIcon.fromTheme("list-add"),
                                                            self.action_add, "Add")
        self.del_action = CommonUtils.create_toolbar_action("Delete Encoder", QIcon.fromTheme("list-remove"),
                                                            self.action_del, "Delete")
        self.mod_action = CommonUtils.create_toolbar_action("Edit Encoder", QIcon.fromTheme("accessories-text-editor"),
                                                            self.action_mod, "Edit")
        self.ref_action = CommonUtils.create_toolbar_action("Refresh Encoder", QIcon.fromTheme("view-refresh"),
                                                            self.action_ref, "Refresh")
        self._init_ui()

    def _init_ui(self):
        self.encoder.encoder_changed.connect(self.configure_toolbar)
        self.actions.setOrientation(Qt.Horizontal)
        self.actions.addActions([self.add_action, self.del_action, self.mod_action, self.ref_action])
        self.actions.setContentsMargins(0, 0, 0, 0)
        q_size = QSize(16, 16)
        self.actions.setIconSize(q_size)
        self.configure_toolbar(None)

        h_layout = QHBoxLayout()
        h_layout.addWidget(QWidget(), 1)
        h_layout.addWidget(self.actions)
        v_layout = QVBoxLayout()
        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.encoder)
        self.setMinimumWidth(400)

        self.setLayout(v_layout)

    def action_add(self):
        self.encoder_view.update_view("Add Encoder")
        if self.encoder_view.exec() == QDialog.Accepted:
            media_type, encoder_group, name, command, executable, extension = self.encoder_view.get_details()
            self.encoder.add_encoder(media_type, encoder_group, name, command, executable, extension)

    def action_del(self):
        path, _ = self.encoder.get_encoder()
        tokens = path.split(EncoderSelector.__PATH_SEPARATOR__)
        self.encoder.del_encoder(tokens[0], tokens[1], tokens[2])

    def action_mod(self):
        path, encoder = self.encoder.get_encoder()
        self.encoder_view.update_view("Modify Encoder", encoder_path=path, encoder=encoder)
        if self.encoder_view.exec() == QDialog.Accepted:
            media_type, encoder_group, name, command, executable, extension = self.encoder_view.get_details()
            self.encoder.update_encoder(media_type, encoder_group, name, command, executable, extension)

    def action_ref(self):
        self.encoder.refresh_encoders()

    def configure_toolbar(self, encoder):
        self.mod_action.setEnabled(True if encoder else False)
        self.del_action.setEnabled(True if encoder else False)




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
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

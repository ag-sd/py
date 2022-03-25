import json
import os
import sys
from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPainter
from PyQt5.QtWidgets import QDialog, QApplication, QTreeView, QComboBox, QHBoxLayout, \
    QStyle, QStyleOptionComboBox, QLineEdit, QGroupBox, QLabel, QWidget, \
    QGridLayout, QToolBar, QVBoxLayout, QDialogButtonBox

import CommonUtils
import TransCoda
from CustomUI import QHLine


def get_config_file():
    return os.path.join(os.path.dirname(__file__), "../resource/encoders.json")


def backup_config_file():
    file = get_config_file()
    backup = file + ".backup-" + datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    os.rename(file, backup)
    return backup


class EncoderSelector(QComboBox):
    __PATH_SEPARATOR__ = " → "
    _PATH_ROLE = 1
    _DETAILS_ROLE = 2

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
            if item:
                return item.text()
            return None

        def del_item(self, media_type, encoder_group, name):
            del self.json[media_type][encoder_group][name]
            # Clean up ancestors if they dont have any children
            if len(self.json[media_type][encoder_group].keys()) == 0:
                del self.json[media_type][encoder_group]
            if len(self.json[media_type].keys()) == 0:
                del self.json[media_type]

        def add_item(self, media_type, group, name, extension, executable, command):
            if media_type not in self.json:
                self.json[media_type] = {}
            if group not in self.json[media_type]:
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
                    parent.setData(path, Qt.UserRole + EncoderSelector._PATH_ROLE)
                    parent.setData(_json, Qt.UserRole + EncoderSelector._DETAILS_ROLE)

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
            encoder = self.tree_view.model().get_item(selected_index)
            if encoder:
                self._selected_encoder = encoder
                self.encoder_changed.emit(self._encoder_path(), self._encoder_details())

    def get_encoder(self):
        return self._encoder_path(), self._encoder_details()

    def add_encoder(self, media_type, encoder_group, name, command, executable, extension):
        self.encoder_model.add_item(media_type, encoder_group, name, extension, executable, command)
        self.encoder_model.backup_and_save()
        self.refresh_encoders()

    def del_encoder(self, media_type, encoder_group, name):
        self.encoder_model.del_item(media_type, encoder_group, name)
        self.encoder_model.backup_and_save()
        self.refresh_encoders()

    def update_encoder(self, media_type, encoder_group, name, command, executable, extension):
        self.encoder_model.del_item(media_type, encoder_group, name)
        self.encoder_model.add_item(media_type, encoder_group, name, extension, executable, command)
        self.encoder_model.backup_and_save()
        self.refresh_encoders()

    def refresh_encoders(self):
        self.encoder_model.reload()
        self.tree_view.expandAll()

    def select_encoder(self, encoder_name):
        match = self._find_encoder(encoder_name)
        if match:
            self._selected_encoder = encoder_name
        self.encoder_changed.emit(self._encoder_path(), self._encoder_details())

    def _encoder_path(self):
        if self._selected_encoder:
            match = self._find_encoder(self._selected_encoder)
            if match:
                return match[0].data(Qt.UserRole + self._PATH_ROLE)
        return None

    def _encoder_details(self):
        if self._selected_encoder:
            match = self._find_encoder(self._selected_encoder)
            if match:
                return match[0].data(Qt.UserRole + self._DETAILS_ROLE)
        return None

    def _find_encoder(self, encoder_name):
        return self.model().match(self.model().index(0, 0), Qt.UserRole + self._PATH_ROLE, encoder_name, 1,
                                  Qt.MatchEndsWith | Qt.MatchRecursive)


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
            self.txt_name.setText(path[2])
            index = self.media_type.findText(path[0], Qt.MatchFixedString)
            if index >= 0:
                self.media_type.setCurrentIndex(index)
            else:
                self.media_type.addItem(path[0])
                self.media_type.setCurrentIndex(self.media_type.findText(path[0], Qt.MatchFixedString))
        else:
            self.txt_name.setVisible(True)
            self.group_box.setTitle("")
            self.txt_name.setText("")
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
        self.setWindowIcon(TransCoda.theme.ico_app_icon)

    def accept(self):
        self.details = {
            "media_type": self.media_type.currentText(),
            "encoder_group": self.txt_encoder_group.text(),
            "command": self.txt_command.text(),
            "executable": self.txt_executable.text(),
            "extension": self.txt_extension.text(),
            "name": self.txt_name.text()
        }
        super().accept()

    def reject(self):
        self.details = {}
        super().reject()

    def get_details(self):
        if self.details:
            return self.details["media_type"], self.details["encoder_group"], self.details["name"], \
                   self.details["command"], self.details["executable"], self.details["extension"]
        else:
            return None, None, None, None, None, None


class TransCodaEditor(QWidget):
    encoder_changed = pyqtSignal('PyQt_PyObject', 'PyQt_PyObject')

    def __init__(self, caption="Trans:Coda Editor"):
        super().__init__()
        self.encoder = EncoderSelector()
        self.encoder_view = EncoderView()
        self.actions = QToolBar()
        self.caption = caption
        self.add_action = CommonUtils.create_action(tooltip="Add Encoder", icon=TransCoda.theme.ico_add_item,
                                                    func=self.action_add, name="Add", parent=self)
        self.del_action = CommonUtils.create_action(tooltip="Delete Encoder", icon=TransCoda.theme.ico_clear,
                                                    func=self.action_del, name="Delete", parent=self)
        self.mod_action = CommonUtils.create_action(tooltip="Edit Encoder",
                                                    icon=TransCoda.theme.ico_edit,
                                                    func=self.action_mod, name="Edit", parent=self)
        self.ref_action = CommonUtils.create_action(tooltip="Refresh Encoder", icon=TransCoda.theme.ico_refresh,
                                                    func=self.action_ref, name="Refresh", parent=self)
        self._init_ui()

    def _init_ui(self):
        self.encoder.encoder_changed.connect(self._configure_toolbar)
        self.actions.setOrientation(Qt.Horizontal)
        self.actions.addActions([self.add_action, self.del_action, self.mod_action, self.ref_action])
        self.actions.setContentsMargins(0, 0, 0, 0)
        q_size = QSize(16, 16)
        self.actions.setIconSize(q_size)
        self._configure_toolbar(None, None)

        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.addWidget(QLabel(f"<u>{self.caption}</u>"), 1)
        h_layout.addWidget(self.actions)
        v_layout = QVBoxLayout()
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.encoder)
        self.setMinimumWidth(400)

        self.setLayout(v_layout)

    def action_add(self, _):
        self.encoder_view.update_view("Add Encoder")
        if self.encoder_view.exec() == QDialog.Accepted:
            media_type, encoder_group, name, command, executable, extension = self.encoder_view.get_details()
            self.encoder.add_encoder(media_type, encoder_group, name, command, executable, extension)

    def action_del(self, _):
        path, _ = self.encoder.get_encoder()
        tokens = path.split(EncoderSelector.__PATH_SEPARATOR__)
        self.encoder.del_encoder(tokens[0], tokens[1], tokens[2])

    def action_mod(self, _):
        path, encoder = self.encoder.get_encoder()
        self.encoder_view.update_view("Modify Encoder", encoder_path=path, encoder=encoder)
        if self.encoder_view.exec() == QDialog.Accepted:
            media_type, encoder_group, name, command, executable, extension = self.encoder_view.get_details()
            self.encoder.update_encoder(media_type, encoder_group, name, command, executable, extension)

    def action_ref(self, _):
        self.encoder.refresh_encoders()

    def select_encoder(self, encoder_name):
        return self.encoder.select_encoder(encoder_name)

    def _configure_toolbar(self, path, encoder):
        self.mod_action.setEnabled(True if encoder else False)
        self.del_action.setEnabled(True if encoder else False)
        if encoder:
            self.encoder_changed.emit(path, encoder)


def main():
    app = QApplication(sys.argv)
    ex = TransCodaEditor()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

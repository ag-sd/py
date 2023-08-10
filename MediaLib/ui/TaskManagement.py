import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QApplication, QTableWidget, QHBoxLayout, QTableWidgetItem, QAbstractItemView, \
    QHeaderView

import MediaLib
from MediaLib.runtime.library import LibraryManagement


class TaskManager(QDialog):
    def __init__(self):
        super().__init__()
        self.task_list = QTableWidget()
        self._init_ui()
        self._populate_tasks()

    def _init_ui(self):
        layout = QHBoxLayout()
        layout.addWidget(self.task_list)
        layout.setContentsMargins(1, 0, 1, 1)
        self.setLayout(layout)

        self.task_list.setAlternatingRowColors(True)
        self.task_list.setShowGrid(False)
        self.task_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.task_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.task_list.verticalHeader().setDefaultSectionSize(self.task_list.verticalHeader().fontMetrics().height() + 3)
        self.task_list.verticalHeader().hide()
        self.task_list.horizontalHeader().setHighlightSections(False)
        self.task_list.horizontalHeader().setSectionsMovable(False)
        self.task_list.horizontalHeader().setSectionsClickable(True)
        self.task_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.task_list.horizontalHeader().setCascadingSectionResizes(True)
        self.task_list.setSortingEnabled(True)

        self.setModal(False)
        self.setMinimumSize(300, 400)
        self.setWindowTitle(f"{MediaLib.__APP_NAME__}: Task Manager")

    def _populate_tasks(self):
        tasks = LibraryManagement.get_currently_running_tasks()
        self.task_list.clear()
        self.task_list.setRowCount(len(tasks))
        self.task_list.setColumnCount(4)

        for i in range(0, len(tasks)):
            self.task_list.setItem(i, 0, QTableWidgetItem(tasks[i].task_id))
            self.task_list.setItem(i, 1, QTableWidgetItem(tasks[i].status.name))
            self.task_list.setItem(i, 2, QTableWidgetItem(str(tasks[i].percent)))
            self.task_list.setItem(i, 3, QTableWidgetItem(str(tasks[i].event_time)))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TaskManager()
    ex.show()
    sys.exit(app.exec_())
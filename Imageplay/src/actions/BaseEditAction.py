from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction


class BaseEditAction(QAction):
    def __init__(self, name, tooltip, icon=None):
        super().__init__()
        self._name = name
        if icon is None:
            # Use default
            self.setIcon(QIcon("resources/default_action.svg"))
        else:
            self.setIcon(icon)
        self.setToolTip(tooltip)

    """
        Return the name of this action
    """
    def get_name(self):
        return self._name

    """
        Setup takes as input an imageWidget and does any setup needed, like
        displaying any additional toolbars in the widget
    """
    def setup(self, image_widget):
        raise NotImplementedError

    """
        Perform the necessary action as the user wishes to commit their changes
    """
    def apply(self, image_widget):
        raise NotImplementedError

    """
        Perform necessary cleanup actions. This could be called on apply or cancel
    """
    def cleanup(self, image_widget):
        raise NotImplementedError

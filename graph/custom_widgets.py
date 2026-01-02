from NodeGraphQt import NodeBaseWidget
from NodeGraphQt.constants import Z_VAL_NODE_WIDGET
from PyQt5 import QtWidgets, QtCore, QtGui


from graph.db_node_support import SearchListDialog


# support for searchable combo box
class NodeSearchMenu(NodeBaseWidget):
    def __init__(self, parent=None, name='', label='', items=None):
        super().__init__(parent, name, label)
        self.setZValue(Z_VAL_NODE_WIDGET + 1)

        self._items = items or []

        self._button = QtWidgets.QToolButton()
        self._button.setMinimumHeight(24)
        self._button.setMinimumWidth(120)
        self._button.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )
        self._button.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self._button.clicked.connect(self._open_dialog)
        self.set_custom_widget(self._button)

    @property
    def type_(self):
        return 'SearchMenuNodeWidget'

    def _open_dialog(self):
        dialog = SearchListDialog(self._items, self.parent())
        pos = QtGui.QCursor.pos()
        dialog.move(pos)

        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        value = dialog.selected()
        if value:
            self.set_value(value)
            self.on_value_changed()

    def get_value(self):
        return self.get_custom_widget().text()

    def set_value(self, value):
        self.get_custom_widget().setText(str(value))

    def add_items(self, items):
        self._items.extend(items)

    def clear(self):
        self._items.clear()
        self.set_value('')


color_hex_swapper = {'#ffcc00': '#00ccff', '#00ccff': '#ffcc00'}


class ToggleExtraButton(NodeBaseWidget):
    def __init__(self, parent=None, name='toggle_extra', label=''):
        super().__init__(parent, name, label)
        self.set_name('toggle_extra')
        self.set_label('')
        btn = QtWidgets.QToolButton()
        btn.setCheckable(True)
        btn.setFixedSize(10, 10)
        btn.setStyleSheet("""
        QToolButton {
            background-color: #333;
        }
        QToolButton:checked {
            background-color: #2e7d32;
        }
        """)

        self._btn = btn
        self.set_custom_widget(btn)

    def set_value(self, value):
        self._btn.setText(value)

    def get_value(self):
        return self._btn.text()


class IntSpinNodeWidget(NodeBaseWidget):
    def __init__(self, prop, parent=None, minimum=0, maximum=100):          # TODO need harvest all examples per arg to see if negative allowed
        super().__init__(parent)

        self.set_name(prop)
        self.set_label(prop)

        self.spin = QtWidgets.QSpinBox()
        self.spin.setRange(minimum, maximum)
        self.spin.valueChanged.connect(self._on_changed)

        self.set_custom_widget(self.spin)

    def get_value(self):
        return int(self.spin.value())

    def set_value(self, value):
        self.spin.blockSignals(True)
        self.spin.setValue(0 if value is None else int(value))
        self.spin.blockSignals(False)

    def _on_changed(self, v):
        self.value_changed.emit(self.get_name(), int(v))


class FloatSpinNodeWidget(NodeBaseWidget):
    def __init__(self, prop, parent=None):
        super().__init__(parent)

        self.set_name(prop)
        self.set_label(prop)

        self.spin = QtWidgets.QDoubleSpinBox()
        self.spin.setDecimals(3)
        self.spin.setSingleStep(0.01)
        self.spin.valueChanged.connect(self._on_changed)

        self.set_custom_widget(self.spin)

    def _on_changed(self, v):
        self.value_changed.emit(self.get_name(), float(v))

    def get_value(self):
        return float(self.spin.value())

    def set_value(self, value):
        self.spin.blockSignals(True)
        self.spin.setValue(0.0 if value is None else float(value))
        self.spin.blockSignals(False)

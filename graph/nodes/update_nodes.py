from PyQt5 import QtCore, QtWidgets


from NodeGraphQt import BaseNode
from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
from NodeGraphQt.constants import NodePropWidgetEnum

from ORM import update_delete_transform


class ReadOnlyTwoColTable(NodeBaseWidget):
    value_changed = QtCore.pyqtSignal(str, object)

    def __init__(self, parent=None, name='changes', label='', max_height=140):
        super(ReadOnlyTwoColTable, self).__init__(parent, name, label)
        self._data = []

        table = QtWidgets.QTableWidget(0, 2)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.setFocusPolicy(QtCore.Qt.NoFocus)
        table.horizontalHeader().setVisible(False)
        table.verticalHeader().setVisible(False)

        table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.set_custom_widget(table)

    def get_value(self):
        return self._data

    def set_value(self, value):
        self._data = value or []
        table = self.get_custom_widget()
        table.setRowCount(len(self._data))
        for r, (left, right) in enumerate(self._data):
            it0 = table.item(r, 0) or QtWidgets.QTableWidgetItem()
            it1 = table.item(r, 1) or QtWidgets.QTableWidgetItem()
            it0.setFlags(it0.flags() & ~QtCore.Qt.ItemIsEditable)
            it1.setFlags(it1.flags() & ~QtCore.Qt.ItemIsEditable)
            it0.setText("" if left is None else str(left))
            it1.setText("" if right is None else str(right))
            table.setItem(r, 0, it0)
            table.setItem(r, 1, it1)

        table.resizeColumnsToContents()


class ReadOnlySqlText(NodeBaseWidget):
    value_changed = QtCore.pyqtSignal(str, object)

    def __init__(self, parent=None, name='sql', label=''):
        super(ReadOnlySqlText, self).__init__(parent, name, label)
        self._sql = ""
        w = QtWidgets.QPlainTextEdit()
        w.setReadOnly(True)
        w.setMinimumHeight(70)
        self.set_custom_widget(w)

    def get_value(self):
        return self._sql

    def set_value(self, value):
        self._sql = value or ""
        self.get_custom_widget().setPlainText(self._sql)


class WhereNode(BaseNode):
    __identifier__ = 'db.where'
    NODE_NAME = 'Where Node'
    sql_output_triggerable = False

    def __init__(self):
        super(WhereNode, self).__init__()

        self.add_custom_widget(ReadOnlySqlText(self.view, name="sql", label="SQL"),
                               widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)
        self.add_custom_widget(ReadOnlyTwoColTable(self.view, name="changes", label="Changes"),
                               widget_type=NodePropWidgetEnum.HIDDEN.value)
        self.sql_output_triggerable = True

    def set_sql(self, sql: str):
        self.get_widget("sql").set_value(sql)

    def apply_and_populate(self):
        sql = self.get_widget("sql").get_value()
        pairs = update_delete_transform(sql)
        self.get_widget("changes").set_value(pairs)

    def set_property(self, name, value, push_undo=True):
        super().set_property(name=name, value=value, push_undo=True)
        if self.sql_output_triggerable:
            if name == 'sql':
                self.apply_and_populate()

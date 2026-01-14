import sqlite3

from PyQt5 import QtCore, QtWidgets


from NodeGraphQt import BaseNode
from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
from NodeGraphQt.constants import NodePropWidgetEnum
from PyQt5.QtGui import QPalette, QColor, QFontMetrics

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
    sql_error = False

    def __init__(self):
        super(WhereNode, self).__init__()

        self.add_custom_widget(ReadOnlySqlText(self.view, name="sql", label="SQL"),
                               widget_type=NodePropWidgetEnum.QTEXT_EDIT.value)
        self.add_custom_widget(ReadOnlyTwoColTable(self.view, name="changes", label="Changes"),
                               widget_type=NodePropWidgetEnum.HIDDEN.value)
        self.input_text_widget = self.get_widget('sql').get_custom_widget()
        self.default_palette = self.input_text_widget.palette()
        self.sql_output_triggerable = True

    def set_sql(self, sql: str):
        self.get_widget("sql").set_value(sql)

    def apply_and_populate(self):
        sql = self.get_widget("sql").get_value()
        try:
            column_output_tuples = update_delete_transform(sql)
        except (TypeError, KeyError, sqlite3.Warning) as e:
            self.sql_output_triggerable = False
            self.color_as_error()
            error_tuples = self.format_error_for_table(str(e))
            self.get_widget("changes").set_value(error_tuples)
            self.sql_error = True
            self.sql_output_triggerable = True
            return
        if self.sql_error:
            self.sql_error = False
            self.reset_color()
        self.get_widget("changes").set_value(column_output_tuples)

    def set_property(self, name, value, push_undo=True):
        super().set_property(name=name, value=value, push_undo=True)
        if self.sql_output_triggerable:
            if name == 'sql':
                self.apply_and_populate()

    def color_as_error(self):
        error_palette = self.input_text_widget.palette()
        error_palette.setColor(QPalette.ColorRole.Base, QColor("#FDE8E8"))      # bg
        error_palette.setColor(QPalette.ColorRole.Text, QColor("#9B1C1C"))      # text
        error_palette.setColor(QPalette.ColorRole.Highlight, QColor("#F05252"))     # selectText
        self.input_text_widget.setPalette(error_palette)

    def reset_color(self):
        self.input_text_widget.setPalette(self.default_palette)

    def format_error_for_table(self, error_message):
        column_widget = self.get_widget("changes").get_custom_widget()
        widget_width = column_widget.width()
        metrics = QFontMetrics(column_widget.font())
        available_space = widget_width - 10
        lines = self.split_text_to_fit(error_message, available_space, metrics)
        return [(i, '') for i in lines]


    @staticmethod
    def split_text_to_fit(text, max_width, metrics):
        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if metrics.horizontalAdvance(test_line) <= max_width:       # pixel width
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

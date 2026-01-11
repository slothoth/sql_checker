from NodeGraphQt import NodeBaseWidget
from NodeGraphQt.constants import Z_VAL_NODE_WIDGET, ViewerEnum

from PyQt5 import QtWidgets, QtCore, QtGui


class ArgReportNodeBaseWidget(NodeBaseWidget):
    val_accept = ''

    def update_args(self, text):
        arg_params = self.node.get_property('arg_params') or {}
        prop_name = self.get_name()
        if prop_name in arg_params:
            arg_params[prop_name] = text

    def update_available_vals(self, text):
        print()


class IntSpinNodeWidget(ArgReportNodeBaseWidget):
    val_accept = int

    def __init__(self, prop, parent=None, minimum=0, maximum=100):
        super().__init__(parent)

        self.set_name(prop)
        self.set_label(prop)

        self.spin = QtWidgets.QSpinBox()
        self.spin.setRange(minimum, maximum)
        self.spin.valueChanged.connect(self._on_changed)

        self.spin.setStyleSheet("""
                    QSpinBox {
                        background-color: #353535;
                        border: 1px solid #1a1a1a;
                        color: #eeeeee;
                        border-radius: 2px;
                        padding-right: 15px; /* make room for buttons */
                    }
                    QSpinBox::up-button {
                        subcontrol-origin: border;
                        subcontrol-position: top right;
                        width: 16px;
                        border-left: 1px solid #1a1a1a;
                        border-bottom: 1px solid #1a1a1a;
                        background-color: #444444;
                    }
                    QSpinBox::down-button {
                        subcontrol-origin: border;
                        subcontrol-position: bottom right;
                        width: 16px;
                        border-left: 1px solid #1a1a1a;
                        background-color: #444444;
                    }
                    QSpinBox::up-arrow {
                        image: none;
                        border-left: 4px solid none;
                        border-right: 4px solid none;
                        border-bottom: 5px solid #bbb; /* This creates a triangle */
                        width: 0;
                        height: 0;
                    }
                    QSpinBox::down-arrow {
                        image: none;
                        border-left: 4px solid none;
                        border-right: 4px solid none;
                        border-top: 5px solid #bbb; /* This creates a triangle */
                        width: 0;
                        height: 0;
                    }
                    /* Hover effects */
                    QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                        background-color: #555555;
                    }
                    QSpinBox::up-arrow:hover { border-bottom-color: #ffffff; }
                    QSpinBox::down-arrow:hover { border-top-color: #ffffff; }
                """)

        self.set_custom_widget(self.spin)

    def get_value(self):
        return int(self.spin.value())

    def set_value(self, value):
        self.spin.blockSignals(True)
        self.spin.setValue(0 if value is None else int(value))
        self.spin.blockSignals(False)
        self.on_value_changed()
        self.update_args(value)

    def _on_changed(self, v):
        self.value_changed.emit(self.get_name(), int(v))


class FloatSpinNodeWidget(ArgReportNodeBaseWidget):
    val_accept = float

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
        self.on_value_changed()
        self.update_args(value)


class ExpandingLineEdit(ArgReportNodeBaseWidget):
    val_accept = str

    def __init__(self, parent=None, name='', label='', text='', check_if_edited=False):
        super(ExpandingLineEdit, self).__init__(parent, name, label)
        self.set_name(name)

        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setText(text)
        self.line_edit.textChanged.connect(self._on_text_changed)
        text_input_style(self.line_edit)
        if check_if_edited:
            self.line_edit.user_edited = False
            self.line_edit.textEdited.connect(self.on_user_edit)
        self.set_custom_widget(self.line_edit)

    @property
    def type_(self):
        return 'ExpandingLineEdit'

    def _on_text_changed(self, text):
        print('')

    def set_value(self, text):
        if text != self.get_value():
            self.get_custom_widget().setText(text)
            self.on_value_changed()
            self.update_args(text)
            self.update_available_vals(text)

    def get_value(self):
        return self.line_edit.text()

    def on_user_edit(self):
        self.line_edit.user_edited = True

    def update_from_state(self, new_value):
        if not self.line_edit.user_edited:
            self.line_edit.setText(new_value)
            return True
        return False




class DropDownLineEdit(ArgReportNodeBaseWidget):
    val_accept = str
    current_suggestions = []

    def __init__(self, parent=None, name='', label='', text='', suggestions=None, check_if_edited=False):
        super().__init__(parent, name, label)
        self.set_name(name)

        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setText(text)

        self._completer_model = QtCore.QStringListModel()
        self._completer = QtWidgets.QCompleter(self._completer_model)
        self._completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._completer.setFilterMode(QtCore.Qt.MatchContains)
        self._completer.setCompletionMode(
            QtWidgets.QCompleter.PopupCompletion
        )
        self.line_edit.setCompleter(self._completer)

        if suggestions:
            self.set_suggestions(suggestions)

        text_input_style(self.line_edit)
        self.line_edit.editingFinished.connect(self.on_value_changed)
        # self.line_edit.clearFocus()

        if check_if_edited:
            self.line_edit.user_edited = False
            self.line_edit.textEdited.connect(self.on_user_edit)

        self.set_custom_widget(self.line_edit)


    @property
    def type_(self):
        return 'DropDownLineEdit'

    def _on_text_changed(self, text):
        self.set_value(text)

    def set_value(self, text):
        if text != self.get_value():
            self.get_custom_widget().setText(text)
            self.on_value_changed()
            self.update_args(text)
            self.update_available_vals(text)

    def get_value(self):
        return str(self.get_custom_widget().text())

    def on_user_edit(self):
        self.line_edit.user_edited = True

    def update_from_state(self, new_value):
        if not self.line_edit.user_edited:
            self.line_edit.setText(new_value)
            return True
        return False

    def set_suggestions(self, suggestions):
        self._completer_model.setStringList(suggestions)
        self.current_suggestions = suggestions

    def add_new_suggestions(self, new_suggestions):
        combined_suggestions = self.current_suggestions + new_suggestions
        self.set_suggestions(combined_suggestions)


class BoolCheckNodeWidget(ArgReportNodeBaseWidget):
    val_accept = bool

    def __init__(self, prop, parent=None):
        super().__init__(parent)

        self.set_name(prop)
        self.set_label(prop)

        self.check = QtWidgets.QCheckBox()
        self.check.stateChanged.connect(self._on_changed)

        self.set_custom_widget(self.check)

    def _on_changed(self, state):
        self.value_changed.emit(self.get_name(), bool(state))

    def get_value(self):
        return bool(self.check.isChecked())

    def set_value(self, value):
        self.check.blockSignals(True)
        self.check.setChecked(False if value is None else bool(value))
        self.check.blockSignals(False)
        self.on_value_changed()
        self.update_args(value)


def text_input_style(widget):
    bg_color = ViewerEnum.BACKGROUND_COLOR.value
    text_color = tuple(map(lambda i, j: i - j, (255, 255, 255),
                           bg_color))
    text_sel_color = text_color
    style_dict = {
        'QLineEdit': {
            'background': 'rgba({0},{1},{2},20)'.format(*bg_color),
            'border': '1px solid rgb({0},{1},{2})'
            .format(*ViewerEnum.GRID_COLOR.value),
            'border-radius': '3px',
            'color': 'rgba({0},{1},{2},150)'.format(*text_color),
            'selection-background-color': 'rgba({0},{1},{2},100)'
            .format(*text_sel_color),
        }
    }
    stylesheet = ''
    for css_class, css in style_dict.items():
        style = '{} {{\n'.format(css_class)
        for elm_name, elm_val in css.items():
            style += '  {}:{};\n'.format(elm_name, elm_val)
        style += '}\n'
        stylesheet += style
    widget.setStyleSheet(stylesheet)
    #widget.setAlignment(QtCore.Qt.AlignCenter)

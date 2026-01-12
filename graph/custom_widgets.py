from NodeGraphQt import NodeBaseWidget
from NodeGraphQt.constants import Z_VAL_NODE_WIDGET, ViewerEnum

from PyQt5 import QtWidgets, QtCore, QtGui
import os


class ArgReportNodeBaseWidget(NodeBaseWidget):
    val_accept = ''

    def update_args(self, text):
        arg_params = self.node.get_property('arg_params') or {}
        prop_name = self.get_name()
        if prop_name in arg_params:
            arg_params[prop_name] = text


class IntSpinNodeWidget(ArgReportNodeBaseWidget):
    val_accept = int

    def __init__(self, prop, parent=None, minimum=0, maximum=100):
        super().__init__(parent)

        self.set_name(prop)
        self.set_label(prop)

        self.spin = QtWidgets.QSpinBox()
        self.spin.setRange(minimum, maximum)
        self.spin.valueChanged.connect(self._on_changed)
        # style sheet needed as otherwise arrows move based on zoom
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
                        border-bottom: 5px solid #bbb;
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


class SuggestorPopulatorWidget(ArgReportNodeBaseWidget):
    committed = QtCore.pyqtSignal(object)

    def _commit(self):
        v = self.get_value()
        self.on_value_changed()
        self.committed.emit(self)


class ExpandingLineEdit(SuggestorPopulatorWidget):
    val_accept = str
    line_edit = None

    def __init__(self, parent=None, name='', label='', text='', check_if_edited=False):
        super().__init__(parent, name, label)
        self.set_name(name)

        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setText(text)
        text_input_style(self.line_edit)

        self.line_edit.editingFinished.connect(self._commit)

        if check_if_edited:
            self.line_edit.user_edited = False
            self.line_edit.textEdited.connect(self.on_user_edit)

        self.set_custom_widget(self.line_edit)

    @property
    def type_(self):
        return 'ExpandingLineEdit'

    def set_value(self, text):
        if text != self.get_value():
            self.get_custom_widget().setText(text)
            self.on_value_changed()
            self._commit()

    def get_value(self):
        return self.line_edit.text()

    def on_user_edit(self):
        self.line_edit.user_edited = True

    def update_from_state(self, new_value):
        if not self.line_edit.user_edited:
            self.line_edit.setText(new_value)
            return True
        return False


class DropDownLineEdit(ExpandingLineEdit):
    current_suggestions = []

    def __init__(self, parent=None, name='', label='', text='', suggestions=None, check_if_edited=False):
        super().__init__(parent, name, label)

        self._base_suggestions = list(suggestions or [])
        self._prefix = _common_prefix(self._base_suggestions)
        self._full_value = str(text or '')

        self._completer_model = _PrefixDisplayStringListModel(self._prefix)
        self._completer = QtWidgets.QCompleter(self._completer_model)
        self._completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._completer.setFilterMode(QtCore.Qt.MatchContains)
        self._completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)

        if hasattr(self._completer, "setCompletionRole"):
            self._completer.setCompletionRole(QtCore.Qt.UserRole)
        else:
            self._completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
            print()

        popup = QtWidgets.QListView()
        popup.setTextElideMode(QtCore.Qt.ElideNone)
        popup.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self._completer.setPopup(popup)

        self.line_edit.setCompleter(self._completer)

        m = self._completer_model
        m.modelReset.connect(self._resize_completer_popup)
        m.dataChanged.connect(self._resize_completer_popup)
        m.rowsInserted.connect(self._resize_completer_popup)
        m.rowsRemoved.connect(self._resize_completer_popup)

        self.line_edit.installEventFilter(self)
        self.line_edit.textEdited.connect(self._on_text_edited)

        self.set_static_suggestions(self._base_suggestions)
        self._apply_display_text()

    def eventFilter(self, obj, event):
        if obj is self.line_edit:
            t = event.type()
            if t == QtCore.QEvent.FocusIn:
                self.line_edit.setText(self._full_value)
            elif t == QtCore.QEvent.FocusOut:
                self._full_value = self.line_edit.text()
                self._apply_display_text()
        return super().eventFilter(obj, event)

    def _on_text_edited(self, txt):
        self._full_value = txt

    def _apply_display_text(self):
        if self.line_edit.hasFocus():
            self.line_edit.setText(self._full_value)
        else:
            self.line_edit.setText(_strip_prefix(self._full_value, self._prefix))

    @property
    def type_(self):
        return 'DropDownLineEdit'

    def set_value(self, text):
        text = '' if text is None else str(text)
        if text != self._full_value:
            self._full_value = text
            self._apply_display_text()
            self.on_value_changed()
            self._commit()

    def get_value(self):
        return self._full_value

    def set_static_suggestions(self, suggestions):
        self._static_suggestions = list(suggestions or [])
        self._prefix = _common_prefix(self._static_suggestions)
        self._completer_model.prefix = self._prefix
        self.set_dynamic_suggestions([])
        self._resize_completer_popup()
        self._apply_display_text()

    def set_dynamic_suggestions(self, dynamic):
        seen = set()
        out = []
        for s in self._static_suggestions + list(dynamic or []):
            if not s:
                continue
            s = str(s)
            if s in seen:
                continue
            seen.add(s)
            out.append(s)
        self._completer_model.setStringList(out)

    def _resize_completer_popup(self, *args):       # ensures popup is sized to accomodate longest entry
        view = self._completer.popup()
        model = self._completer_model
        if model.rowCount() == 0:
            return

        fm = QtGui.QFontMetrics(view.font())
        longest = 0
        for r in range(model.rowCount()):
            s = model.data(model.index(r, 0), QtCore.Qt.DisplayRole)
            if s is None:
                continue
            longest = max(longest, fm.horizontalAdvance(str(s)))

        frame = view.frameWidth() * 2
        margins = view.contentsMargins().left() + view.contentsMargins().right()
        scrollbar = view.verticalScrollBar().sizeHint().width()
        padding = 24

        w = longest + frame + margins + scrollbar + padding
        w = max(w, self.line_edit.width())

        screen = QtWidgets.QApplication.screenAt(self.line_edit.mapToGlobal(QtCore.QPoint(0, 0)))
        if screen:
            avail = screen.availableGeometry()
            max_w = avail.right() - self.line_edit.mapToGlobal(QtCore.QPoint(0, 0)).x()
            w = min(w, max_w)

        view.setMinimumWidth(w)
        view.setFixedWidth(w)


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


def _common_prefix(values):
    vals = [str(v) for v in values if v]
    if len(vals) < 2:
        return ''
    p = os.path.commonprefix(vals)
    if not p:
        return ''
    if '_' in p:
        p = p[:p.rfind('_') + 1]
    if len(p) < 2:
        return ''
    if any(v == p for v in vals):
        return ''
    return p


def _strip_prefix(s, prefix):
    s = '' if s is None else str(s)
    if prefix and s.startswith(prefix):
        return s[len(prefix):]
    return s


class _PrefixDisplayStringListModel(QtCore.QStringListModel):       # strip prefix if present in all suggestions
    def __init__(self, prefix='', parent=None):
        super().__init__(parent)
        self.prefix = prefix

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        full = super().data(index, QtCore.Qt.DisplayRole)
        if role == QtCore.Qt.DisplayRole:
            return _strip_prefix(full, self.prefix)
        if role == QtCore.Qt.UserRole:
            return full
        return super().data(index, role)


from PyQt5 import QtWidgets, QtCore, QtGui
from collections import Counter
import json

from NodeGraphQt import NodeBaseWidget
from graph.utils import resource_path


with open(resource_path('resources/style_sheets.json')) as f:
    styles = json.load(f)


class ArgReportWidget(NodeBaseWidget):
    val_accept = ''
    style_dict = {}
    default_style = {}
    widget_string_type = ''
    style_key = ''

    def update_args(self, text):
        arg_params = self.node.get_property('arg_params') or {}
        prop_name = self.get_name()
        if prop_name in arg_params:
            arg_params[prop_name] = text

    def adjust_color(self, widget, is_valid=True):
        style_key = 'localise' if self.localise else 'basic'
        if not is_valid:
            style_key += '_error'
        if self.style_key != style_key:
            self.style_key = style_key
            widget.setStyleSheet(styles[style_key])


class IntSpinNodeWidget(ArgReportWidget):
    val_accept = int
    widget_string_type = 'QSpinBox'

    def __init__(self, prop, parent=None, minimum=-100, maximum=100):
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
                        padding-right: 15px;
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
                        border-top: 5px solid #bbb; 
                        width: 0;
                        height: 0;
                    }
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


class FloatSpinNodeWidget(ArgReportWidget):
    val_accept = float
    widget_string_type = 'QDoubleSpinBox'

    def __init__(self, prop, parent=None, minimum=-100, maximum=100):
        super().__init__(parent)

        self.set_name(prop)
        self.set_label(prop)

        self.spin = QtWidgets.QDoubleSpinBox()
        self.spin.setDecimals(3)
        self.spin.setSingleStep(0.01)
        self.spin.setRange(minimum, maximum)
        self.spin.valueChanged.connect(self._on_changed)

        self.spin.setStyleSheet("""
                            QDoubleSpinBox {
                                background-color: #353535;
                                border: 1px solid #1a1a1a;
                                color: #eeeeee;
                                border-radius: 2px;
                                padding-right: 15px;
                            }
                            QDoubleSpinBox::up-button {
                                subcontrol-origin: border;
                                subcontrol-position: top right;
                                width: 16px;
                                border-left: 1px solid #1a1a1a;
                                border-bottom: 1px solid #1a1a1a;
                                background-color: #444444;
                            }
                            QDoubleSpinBox::down-button {
                                subcontrol-origin: border;
                                subcontrol-position: bottom right;
                                width: 16px;
                                border-left: 1px solid #1a1a1a;
                                background-color: #444444;
                            }
                            QDoubleSpinBox::up-arrow {
                                image: none;
                                border-left: 4px solid none;
                                border-right: 4px solid none;
                                border-bottom: 5px solid #bbb;
                                width: 0;
                                height: 0;
                            }
                            QDoubleSpinBox::down-arrow {
                                image: none;
                                border-left: 4px solid none;
                                border-right: 4px solid none;
                                border-top: 5px solid #bbb; 
                                width: 0;
                                height: 0;
                            }
                            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                                background-color: #555555;
                            }
                            QDoubleSpinBox::up-arrow:hover { border-bottom-color: #ffffff; }
                            QDoubleSpinBox::down-arrow:hover { border-top-color: #ffffff; }
                        """)

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


class BoolCheckNodeWidget(ArgReportWidget):
    val_accept = bool
    widget_string_type = 'QCheckBox'

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


class SuggestorPopulatorWidget(ArgReportWidget):
    committed = QtCore.pyqtSignal(object)

    def _commit(self):
        self.on_value_changed()
        self.committed.emit(self)


class ExpandingLineEdit(SuggestorPopulatorWidget):
    val_accept = str
    line_edit = None
    style_dict = {}
    default_style = {}
    widget_string_type = 'QLineEdit'

    def __init__(self, parent=None, name='', label='', text='', check_if_edited=False, localise=False):
        super().__init__(parent, name, label)
        self.set_name(name)

        self.line_edit = FocusAwareLineEdit()
        self.line_edit.setText(text)

        self.localise = localise
        self.adjust_color(self.line_edit, True)
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
            self._commit()

    def get_value(self):
        return self.line_edit.text()

    def on_user_edit(self):
        self.line_edit.user_edited = True

    def update_from_state(self, new_value):
        if not self.line_edit.user_edited:
            self.line_edit.setText(new_value)
            self.on_value_changed()
            return True
        return False


class DropDownLineEdit(ExpandingLineEdit):
    current_suggestions = []
    _static_suggestions = []
    value_changed = QtCore.pyqtSignal(str, str)  # name, value

    def __init__(self, parent=None, name='', label='', text='', suggestions=None, check_if_edited=False, localise=False):
        super().__init__(parent, name, label)

        self._name = name
        self._label = label

        self._base_suggestions = list(suggestions or [])
        self._prefix = _majority_prefix(self._base_suggestions)
        self._full_value = str(text or '')

        self._completer_model = _PrefixDisplayStringListModel(self._prefix)
        self._completer = QtWidgets.QCompleter(self._completer_model)
        self._completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._completer.setFilterMode(QtCore.Qt.MatchContains)
        self._completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)

        if hasattr(self._completer, "setCompletionRole"):
            self._completer.setCompletionRole(QtCore.Qt.UserRole)

        self._completer.activated[QtCore.QModelIndex].connect(self.on_item_selected)

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

        self.line_edit.textEdited.connect(self._on_text_edited)

        # 2. Handle Focus events for Text Swapping
        self.line_edit.focus_in.connect(self._on_focus_gained)
        self.line_edit.focus_out.connect(self._on_focus_lost)

        self.set_static_suggestions(self._base_suggestions)

    def _format_display_text(self, text):
        """Returns the text to display based on current focus state."""
        if self.line_edit.hasFocus():
            return text
        return _strip_prefix(text, self._prefix)

    def amend_display_text(self, val):
        val = val if self.line_edit.hasFocus() else _strip_prefix(val, self._prefix)
        return val

        # --- Events ---
    def _on_focus_gained(self):
        """Expand to full value for editing."""
        self.line_edit.setText(self._full_value)

    def _on_focus_lost(self):
        """Shrink to short value for display."""
        short_text = _strip_prefix(self._full_value, self._prefix)
        self.line_edit.setText(short_text)

    def _on_text_edited(self, text):
        self._full_value = text
        self.value_changed.emit(self.get_name(), self._full_value)
        QtCore.QTimer.singleShot(0, self._force_completion_update)

    def on_item_selected(self, index):
        """Handle selection from the autocomplete dropdown."""
        full_val = index.data(QtCore.Qt.UserRole)
        self._full_value = full_val

        self.line_edit.setText(self._full_value)
        self.value_changed.emit(self.get_name(), self._full_value)

    # ------------ public methods ---------------

    @property
    def type_(self):
        return 'DropDownLineEdit'

    def get_name(self):
        return self._name

    def get_value(self):
        return self._full_value

    def set_value(self, text):
        text = str(text or '')
        self._full_value = text
        self.line_edit.setText(self._format_display_text(text))
        self._commit()

    def _force_completion_update(self):             # we need to reopen popup as focus is stolen on typing
        if not self._full_value:
            return
        completer = self.line_edit.completer()
        if completer:
            completer.setCompletionPrefix(self._full_value)
            completer.complete()

    # --------- suggestions ----------------

    def set_static_suggestions(self, suggestions):
        self._static_suggestions = list(suggestions or [])
        self._prefix = _majority_prefix(self._static_suggestions)
        self._completer_model.prefix = self._prefix
        self.set_dynamic_suggestions([])
        self._resize_completer_popup()

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


def _majority_prefix(values, min_ratio=0.8, require_delim='_', max_parts=2):
    vals = [str(v) for v in values if v]
    if not vals:
        return ''

    counts = Counter()
    for s in vals:
        if require_delim and require_delim not in s:
            continue
        parts = s.split(require_delim)
        for k in range(1, min(max_parts, len(parts) - 1) + 1):
            p = require_delim.join(parts[:k]) + require_delim
            counts[p] += 1

    if not counts:
        return ''

    prefix, hits = counts.most_common(1)[0]
    if hits / len(vals) < float(min_ratio):
        return ''
    return prefix


def _strip_prefix(s, prefix):
    s = '' if s is None else str(s)
    if prefix and s.startswith(prefix):
        return s[len(prefix):]
    return s


class FocusAwareLineEdit(QtWidgets.QLineEdit):
    """
    A LineEdit override to emit signals on focus in and out.
    """
    focus_in = QtCore.pyqtSignal()
    focus_out = QtCore.pyqtSignal()

    def focusInEvent(self, event):
        self.focus_in.emit()
        super(FocusAwareLineEdit, self).focusInEvent(event)

    def focusOutEvent(self, event):
        self.focus_out.emit()
        super(FocusAwareLineEdit, self).focusOutEvent(event)


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


# style sheets, migrate to json later?
spin_styling = {
            'QSpinBox': {
                'background-color': '#353535',
                'border': '1px solid #1a1a1a',
                'color': '#eeeeee',
                'border-radius': '2px',
                'padding-right': '15px'
            },
            'QSpinBox::up-button': {
                'subcontrol-origin': 'border',
                'subcontrol-position': 'top right',
                'width': '16px',
                'border-left': '1px solid #1a1a1a',
                'border-bottom': '1px solid #1a1a1a',
                'background-color': '#444444'
            },
            'QSpinBox::down-button': {
                'subcontrol-origin': 'border',
                'subcontrol-position': 'bottom right',
                'width': '16px',
                'border-left': '1px solid #1a1a1a',
                'background-color': '#444444'
            },
            'QSpinBox::up-arrow': {
                'image': 'none',
                'border-left': '4px solid none',
                'border-right': '4px solid none',
                'border-top': '5px solid #bbb',
                'width': '0',
                'height': '0'
            },
            'QSpinBox::down-arrow': {
                'image': 'none',
                'border-left': '4px solid none',
                'border-right': '4px solid none',
                'border-top': '5px solid #bbb',
                'width': '0',
                'height': '0'
            },
            'QSpinBox::up-button:hover, QSpinBox::down-button:hover': {
                'background-color': '#555555'
            },
            'QSpinBox::up-arrow:hover': {
                'border-bottom-color': '#ffffff'
            },
            'QSpinBox::down-arrow:hover': {
                'border-top-color': '#ffffff'
            }
        }
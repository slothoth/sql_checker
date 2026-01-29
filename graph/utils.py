import os
import sys
import logging

log = logging.getLogger(__name__)


def to_number(x):
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        s = x.strip()
        try:
            i = int(s)
            return i
        except ValueError:
            try:
                return float(s)
            except ValueError:
                return 'failed'


def flatten(xss):
    return [x for xs in xss for x in xs]


def flatten_avoid_string(items):
    out = []
    if isinstance(items, str):
        return items
    for x in items:
        if isinstance(x, (list, tuple)):
            out.extend(flatten(x))
        else:
            out.append(x)
    return out


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def check_civ_install_works(path):
    check_passed = True
    if not os.path.exists(f"{path}/Base/Assets/schema/gameplay"):
        check_passed = False
    return check_passed


def check_civ_config_works(path):
    check_passed = True
    if not os.path.exists(f"{path}/Mods.sqlite"):
        check_passed = False
    return check_passed


def check_workshop_works(path):
    if '1295660' in path:
        return True
    return False


class LogPushSingleton:
    def __init__(self):
        self.log_widget = None

    def set_log_widget(self, log_widget):
        if self.log_widget is not None:
            log.error('trying to reset log window, shouldnt happen')
        else:
            self.log_widget = log_widget

    def push_to_log(self, message, other_log):
        other_log.info(f'Pushed to log: {message}')
        log_display = self.log_widget
        if log_display is not None:         # rare occassions where it gets wiped by C++. Not good, but dont crash
            log_display.appendPlainText(str(message) + '\n')  # ensure plain text insertion so the highlighter can run
            cursor = log_display.textCursor()  # keep view scrolled to bottom
            log_display.setTextCursor(cursor)


LogPusher = LogPushSingleton()

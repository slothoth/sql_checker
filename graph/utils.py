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
        log_display.appendPlainText(str(message) + '\n')  # ensure plain text insertion so the highlighter can run
        cursor = log_display.textCursor()  # keep view scrolled to bottom
        log_display.setTextCursor(cursor)

LogPusher = LogPushSingleton()

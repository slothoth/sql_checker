from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt5.QtCore import QRegularExpression


class LogHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self.rules = []

        fmt_error = QTextCharFormat()
        fmt_error.setForeground(QColor("#cc0000"))
        red_rules = [r"NOT NULL constraint failed.*", r"constraint failed.*", r"-{5,}\s*Error Summary\s*-{5,}",
                     r"There wasn't", r"FOREIGN KEY", r"There were ^[1-9][0-9]*$",
                     r"had problem"]
        for i in red_rules:
            self.rules.append((QRegularExpression(i, QRegularExpression.CaseInsensitiveOption), fmt_error))

        fmt_sql = QTextCharFormat()
        fmt_sql.setForeground(QColor("#6a0dad"))
        syntax_rules = [r"\bINSERT INTO\b.*", r"\bUPDATE\b.*", r"\bDELETE FROM\b.*"]
        for i in syntax_rules:
            self.rules.append((QRegularExpression(i, QRegularExpression.CaseInsensitiveOption), fmt_sql))

        # positive!
        todo = ['Valid mod setup']

        fmt_header = QTextCharFormat()
        fmt_header.setForeground(QColor("#0047ab"))
        fmt_header.setFontWeight(75)
        self.rules.append((QRegularExpression(r"^---------.*", QRegularExpression.CaseInsensitiveOption), fmt_header))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)

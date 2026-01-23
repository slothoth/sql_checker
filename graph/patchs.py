from PyQt5 import QtWidgets, QtCore


def _patched_size_hint(self, *args):
    base = QtWidgets.QGroupBox.sizeHint(self)

    title = self.title()
    if not title:
        return base

    fm = self.fontMetrics()
    title_width = fm.horizontalAdvance(title)

    margins = self.layout().contentsMargins()
    width = max(base.width(), title_width + margins.left() + margins.right() + 8)

    return QtCore.QSize(width, base.height())

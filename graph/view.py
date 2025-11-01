from PyQt5.QtCore import Qt, QRectF, QLineF, pyqtSignal, QPointF
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QFont, QPainterPath

from PyQt5.QtWidgets import (QGraphicsView, QGraphicsItem, QGraphicsObject, QGraphicsTextItem,
                             QGraphicsLineItem, QDialog, QFormLayout, QLineEdit, QDialogButtonBox)


class NodeEditDialog(QDialog):
    def __init__(self, text1, text2, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Node")
        self.text1_edit = QLineEdit(text1)
        self.text2_edit = QLineEdit(text2)
        layout = QFormLayout(self)
        layout.addRow("Field 1:", self.text1_edit)
        layout.addRow("Field 2:", self.text2_edit)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_data(self):
        return self.text1_edit.text(), self.text2_edit.text()


class EdgeItem(QGraphicsLineItem):
    def __init__(self, start_node, start_field_index, end_node, parent=None):
        super().__init__(parent)
        self.start_node = start_node
        self.start_field_index = start_field_index
        self.end_node = end_node
        self.setPen(QPen(QColor("#333"), 2))
        self.setZValue(-1)

        self.start_node.position_changed.connect(self.update_position)
        self.end_node.position_changed.connect(self.update_position)
        self.update_position()

    def update_position(self):
        start_point = self.start_node.get_field_scene_pos(self.start_field_index)
        end_rect = self.end_node.sceneBoundingRect()
        end_point = QPointF(end_rect.left(), end_rect.center().y())
        self.setLine(QLineF(start_point, end_point))


class NodeItem(QGraphicsObject):
    position_changed = pyqtSignal()
    NODE_WIDTH = 150
    HEADER_HEIGHT = 25
    PADDING = 5
    LINE_SPACING = 5

    def __init__(self, node_id, texts=None, parent=None):
        super().__init__(parent)
        self.node_id = node_id
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.edges = []

        if texts is None:
            texts = ["Title", "Description"]

        self.text_items = []
        y = self.PADDING / 2

        for i, text in enumerate(texts):
            item = QGraphicsTextItem(self)
            item.setPlainText(text)
            item.setTextInteractionFlags(Qt.TextEditorInteraction)
            if i == 0:
                item.setDefaultTextColor(Qt.white)
                item.setFont(QFont("Inter", 10, QFont.Bold))
            else:
                item.setDefaultTextColor(Qt.black)
                item.setFont(QFont("Inter", 9))
            item.setTextWidth(self.NODE_WIDTH - 2 * self.PADDING)
            item.setPos(self.PADDING, y)
            self.text_items.append(item)
            y += item.boundingRect().height() + self.LINE_SPACING

        total_height = y + self.PADDING
        self.NODE_HEIGHT = max(total_height, self.HEADER_HEIGHT + 2 * self.PADDING)

    def boundingRect(self):
        return QRectF(0, 0, self.NODE_WIDTH, self.NODE_HEIGHT).adjusted(-1, -1, 1, 1)

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(QPen(QColor("#333"), 1))
        painter.drawRoundedRect(0, 0, self.NODE_WIDTH, self.NODE_HEIGHT, 8, 8)
        painter.setBrush(QBrush(QColor("#4a90e2")))
        painter.setPen(Qt.NoPen)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.NODE_WIDTH, self.HEADER_HEIGHT, 8, 8)
        path.addRect(0, self.HEADER_HEIGHT - 8, self.NODE_WIDTH, 8)
        painter.drawPath(path)
        if self.isSelected():
            painter.setPen(QPen(QColor("#f5a623"), 2, Qt.DotLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(0, 0, self.NODE_WIDTH, self.NODE_HEIGHT, 8, 8)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.position_changed.emit()
        return super().itemChange(change, value)

    def relayout(self):
        y = self.PADDING / 2
        for item in self.text_items:
            item.setPos(self.PADDING, y)
            y += item.boundingRect().height() + self.LINE_SPACING
        self.NODE_HEIGHT = max(y + self.PADDING, self.HEADER_HEIGHT + 2 * self.PADDING)

    def get_field_scene_pos(self, index):
        if 0 <= index < len(self.text_items):
            item = self.text_items[index]
            rect = item.boundingRect()
            right_edge = item.mapToScene(QPointF(rect.right(), rect.center().y()))
            return right_edge
        return self.mapToScene(QPointF(self.NODE_WIDTH, self.NODE_HEIGHT / 2))


class GraphView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

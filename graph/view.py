from PyQt5.QtCore import Qt, QRectF, QLineF, pyqtSignal, QPointF
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QFont, QPainterPath, QPolygonF

from PyQt5.QtWidgets import (QGraphicsView, QGraphicsItem, QGraphicsObject, QGraphicsTextItem,
                             QGraphicsLineItem, QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
                             QWidget, QVBoxLayout, QComboBox, QListWidget)


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
    def __init__(self, start_node, start_field_index, end_node, end_field_index=0, parent=None):
        super().__init__(parent)
        self.start_node = start_node
        self.start_field_index = start_field_index
        self.end_node = end_node
        self.end_field_index = end_field_index
        self.setPen(QPen(QColor("#333"), 2))
        self.setZValue(-1)

        self.start_node.position_changed.connect(self.update_position)
        self.end_node.position_changed.connect(self.update_position)
        self.update_position()

    def update_position(self):
        start_point = self.start_node.get_field_scene_pos(self.start_field_index, right=True)
        end_point = self.end_node.get_field_scene_pos(self.end_field_index, right=False)
        self.setLine(QLineF(start_point, end_point))


class ExpanderButton(QGraphicsObject):
    """A clickable button that shows an arrow indicating expansion state."""
    clicked = pyqtSignal(bool)  # emits current state (True=Open, False=Closed)

    def __init__(self, parent=None, width=150):
        super().__init__(parent)
        self.width = width
        self.is_expanded = False
        self.height = 20
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)  # Button shouldn't be selected alone

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget):
        # Draw a subtle separator line
        painter.setPen(QPen(QColor("#ddd"), 1))
        painter.drawLine(5, 0, self.width - 5, 0)

        # Draw the arrow
        painter.setBrush(QBrush(QColor("#666")))
        painter.setPen(Qt.NoPen)

        center_x = self.width / 2
        center_y = self.height / 2

        arrow = QPolygonF()
        if self.is_expanded:
            # Arrow pointing Down
            arrow.append(QPointF(center_x - 4, center_y - 2))
            arrow.append(QPointF(center_x + 4, center_y - 2))
            arrow.append(QPointF(center_x, center_y + 4))
        else:
            # Arrow pointing Right
            arrow.append(QPointF(center_x - 2, center_y - 4))
            arrow.append(QPointF(center_x - 2, center_y + 4))
            arrow.append(QPointF(center_x + 4, center_y))

        painter.drawPolygon(arrow)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_expanded = not self.is_expanded
            self.clicked.emit(self.is_expanded)
            self.update()  # Redraw arrow
            event.accept()
        else:
            super().mousePressEvent(event)


class NodeItem(QGraphicsObject):
    position_changed = pyqtSignal()
    NODE_WIDTH = 150
    HEADER_HEIGHT = 25
    PADDING = 5
    LINE_SPACING = 5

    def __init__(self, node_id, primary_texts=None, secondary_texts=None, parent=None):
        super().__init__(parent)
        self.node_id = node_id
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)

        # Data storage
        self.primary_texts = primary_texts if primary_texts else ["Title", "Primary Field"]
        self.secondary_texts = secondary_texts if secondary_texts else []

        self.primary_items = []
        self.secondary_items = []
        self.edges = []

        # 1. Create Primary Items
        for i, text in enumerate(self.primary_texts):
            item = self._create_text_item(text, is_header=(i == 0))
            self.primary_items.append(item)

        # 2. Create Expander Button (only if we have secondary text)
        self.expander = None
        if self.secondary_texts:
            self.expander = ExpanderButton(self, self.NODE_WIDTH)
            self.expander.clicked.connect(self.on_expand_toggled)

        # 3. Create Secondary Items (Initially hidden)
        for text in self.secondary_texts:
            item = self._create_text_item(text, is_header=False)
            item.setVisible(False)  # Start hidden
            self.secondary_items.append(item)

        # Calculate initial layout
        self.NODE_HEIGHT = 0  # Will be set in relayout
        self.relayout()

    def _create_text_item(self, text, is_header=False):
        item = QGraphicsTextItem(self)
        item.setPlainText(text)
        item.setTextInteractionFlags(Qt.TextEditorInteraction)
        item.setTextWidth(self.NODE_WIDTH - 2 * self.PADDING)

        if is_header:
            item.setDefaultTextColor(Qt.white)
            item.setFont(QFont("Inter", 10, QFont.Bold))
        else:
            item.setDefaultTextColor(Qt.black)
            item.setFont(QFont("Inter", 9))
        return item

    def on_expand_toggled(self, is_open):
        """Slot called when the little arrow is clicked"""
        self.prepareGeometryChange()  # CRITICAL: Tells the scene the size is changing

        for item in self.secondary_items:
            item.setVisible(is_open)

        self.relayout()
        self.update()  # Trigger repaint of the background rect

    def relayout(self):
        """Calculates positions based on what is currently visible."""
        y = self.PADDING / 2

        # 1. Layout Primary
        for item in self.primary_items:
            item.setPos(self.PADDING, y)
            y += item.boundingRect().height() + self.LINE_SPACING

        # 2. Layout Expander (if it exists)
        if self.expander:
            # Add a little extra space before the button
            self.expander.setPos(0, y)
            y += self.expander.height  # Expander has fixed height

            # 3. Layout Secondary (if expanded)
            if self.expander.is_expanded:
                for item in self.secondary_items:
                    item.setPos(self.PADDING, y)
                    y += item.boundingRect().height() + self.LINE_SPACING

        total_height = y + self.PADDING
        self.NODE_HEIGHT = max(total_height, self.HEADER_HEIGHT + 2 * self.PADDING)

    def boundingRect(self):
        return QRectF(0, 0, self.NODE_WIDTH, self.NODE_HEIGHT).adjusted(-1, -1, 1, 1)

    def paint(self, painter, option, widget):
        # Background
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(QPen(QColor("#333"), 1))
        painter.drawRoundedRect(0, 0, self.NODE_WIDTH, self.NODE_HEIGHT, 8, 8)

        # Header
        painter.setBrush(QBrush(QColor("#4a90e2")))
        painter.setPen(Qt.NoPen)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.NODE_WIDTH, self.HEADER_HEIGHT, 8, 8)
        path.addRect(0, self.HEADER_HEIGHT - 8, self.NODE_WIDTH, 8)
        painter.drawPath(path)

        # Selection Outline
        if self.isSelected():
            painter.setPen(QPen(QColor("#f5a623"), 2, Qt.DotLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(0, 0, self.NODE_WIDTH, self.NODE_HEIGHT, 8, 8)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.position_changed.emit()
        return super().itemChange(change, value)

    # Helper to get connection points for wires
    def get_field_scene_pos(self, index, right=True):
        # Map index to the correct list (primary or secondary)
        target_item = None

        if index < len(self.primary_items):
            target_item = self.primary_items[index]
        else:
            sec_index = index - len(self.primary_items)
            if 0 <= sec_index < len(self.secondary_items) and self.secondary_items[sec_index].isVisible():
                target_item = self.secondary_items[sec_index]

        if target_item:
            rect = target_item.boundingRect()
            x = rect.right() if right else rect.left()
            point = target_item.mapToScene(QPointF(x, rect.center().y()))
            return point

        # Fallback to center of node if index invalid or hidden
        rect = self.boundingRect()
        x = rect.right() if right else rect.left()
        return self.mapToScene(QPointF(x, rect.center().y()))


class GraphView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)


class GraphDropdownView(QWidget):
    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.dropdown = QComboBox()
        self.view = GraphView(controller)
        layout.addWidget(self.dropdown)
        layout.addWidget(self.view)
        self.views = {}
        self.dropdown.currentIndexChanged.connect(self.switch_view)

    def load_views(self, views):
        self.views.clear()
        self.dropdown.clear()
        for v in views:
            self.views[v["name"]] = v
            self.dropdown.addItem(v["name"])
        if views:
            self.switch_view(0)

    def switch_view(self, index):
        name = self.dropdown.itemText(index)
        if not name:
            return
        data = self.views[name]
        self.view.scene().load_graph_data(data)
        # self.view.scene().sort_graph()


class NodeSearchDialog(QDialog):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search Nodes")
        self.search = QLineEdit()
        self.list = QListWidget()
        self.list.addItems(items)
        self.search.textChanged.connect(self.filter)
        ok = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok.accepted.connect(self.accept)
        ok.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.search)
        layout.addWidget(self.list)
        layout.addWidget(ok)

    def filter(self, text):
        for i in range(self.list.count()):
            item = self.list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def selected(self):
        item = self.list.currentItem()
        return item.text() if item else None

class DragHandle(QGraphicsObject):
    dragged = pyqtSignal(str, QPointF)

    def __init__(self, field_name, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.setCursor(Qt.OpenHandCursor)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.start = None

    def boundingRect(self):
        return QRectF(0, 0, 14, 14)

    def paint(self, p, o, w):
        p.setBrush(QColor("#777"))
        p.setPen(Qt.NoPen)
        p.drawEllipse(0, 0, 14, 14)

    def mousePressEvent(self, e):
        self.setCursor(Qt.ClosedHandCursor)
        self.start = e.scenePos()

    def mouseMoveEvent(self, e):
        if (e.scenePos() - self.start).manhattanLength() > 10:
            self.dragged.emit(self.field_name, e.scenePos())

    def mouseReleaseEvent(self, e):
        self.setCursor(Qt.OpenHandCursor)
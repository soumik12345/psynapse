from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsScene


class NodeScene(QGraphicsScene):
    """Custom graphics scene for node editor."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Scene dimensions
        self.setSceneRect(-5000, -5000, 10000, 10000)

        # Grid settings
        self.grid_size = 20
        self.grid_squares = 5

        # Colors
        self._color_background = QColor("#393939")
        self._color_light = QColor("#2f2f2f")
        self._color_dark = QColor("#292929")

        # Pen for grid
        self._pen_light = QPen(self._color_light)
        self._pen_light.setWidth(1)
        self._pen_dark = QPen(self._color_dark)
        self._pen_dark.setWidth(2)

        self.setBackgroundBrush(self._color_background)

    def drawBackground(self, painter: QPainter, rect):
        """Draw grid background."""
        super().drawBackground(painter, rect)

        # Create grid
        left = int(rect.left())
        right = int(rect.right())
        top = int(rect.top())
        bottom = int(rect.bottom())

        first_left = left - (left % self.grid_size)
        first_top = top - (top % self.grid_size)

        # Compute lines to draw
        lines_light = []
        lines_dark = []

        for x in range(first_left, right, self.grid_size):
            if x % (self.grid_size * self.grid_squares) != 0:
                lines_light.append((x, top, x, bottom))
            else:
                lines_dark.append((x, top, x, bottom))

        for y in range(first_top, bottom, self.grid_size):
            if y % (self.grid_size * self.grid_squares) != 0:
                lines_light.append((left, y, right, y))
            else:
                lines_dark.append((left, y, right, y))

        # Draw lines
        painter.setPen(self._pen_light)
        for line in lines_light:
            painter.drawLine(line[0], line[1], line[2], line[3])

        painter.setPen(self._pen_dark)
        for line in lines_dark:
            painter.drawLine(line[0], line[1], line[2], line[3])

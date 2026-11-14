"""Turtle üçün ağ kətan; hərəkəti ardıcıl göstərir və Assets/turtle.jpg ikonunu dəstəkləyir."""
import os
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Ellipse, Line, Rectangle, PushMatrix, PopMatrix, Rotate
from kivy.metrics import dp
from kivy.uix.widget import Widget


class TurtleCanvas(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.items = []
        self.bg = (1, 1, 1, 1)
        self.turtle = None
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(root, "Assets", "turtle.jpg")
        try:
            self.turtle_texture = CoreImage(icon_path).texture if os.path.isfile(icon_path) else None
        except Exception:
            self.turtle_texture = None
        self.bind(pos=self.redraw, size=self.redraw)

    def apply(self, command):
        kind = command[0]
        if kind == "clear":
            self.items = []
            if len(command) > 1 and command[1] is not None:
                self.bg = command[1]
        elif kind in ("line", "dot"):
            self.items.append(command)
        elif kind == "turtle":
            self.turtle = command[1:]
        self.redraw()

    def _point(self, point):
        return (self.center_x + dp(point[0]), self.center_y + dp(point[1]))

    def redraw(self, *_args):
        self.canvas.clear()
        with self.canvas:
            Color(*self.bg)
            Rectangle(pos=self.pos, size=self.size)
            for item in self.items:
                if item[0] == "line":
                    _, start, end, color, width = item
                    Color(*color)
                    Line(points=self._point(start) + self._point(end), width=max(1, dp(width)))
                elif item[0] == "dot":
                    _, point, color, size = item
                    x, y = self._point(point)
                    Color(*color)
                    Ellipse(pos=(x - dp(size) / 2, y - dp(size) / 2),
                            size=(dp(size), dp(size)))
            if self.turtle and self.turtle[3]:
                x, y = self._point(self.turtle[:2])
                size = dp(34)
                if self.turtle_texture:
                    PushMatrix()
                    Rotate(angle=-float(self.turtle[2]), origin=(x, y))
                    Color(1, 1, 1, 1)
                    Rectangle(texture=self.turtle_texture,
                              pos=(x - size / 2, y - size / 2),
                              size=(size, size))
                    PopMatrix()
                else:
                    Color(0.1, 0.1, 0.1, 1)
                    Ellipse(pos=(x - dp(5), y - dp(5)), size=(dp(10), dp(10)))

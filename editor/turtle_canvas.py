"""Kivy üzərində Turtle qrafikası üçün görüntü sahəsi."""
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.widget import Widget


class TurtleCanvas(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.items = []
        self.bg = (0.04, 0.06, 0.10, 1)
        self.turtle = None
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
                    Line(points=self._point(start) + self._point(end),
                         width=max(1, dp(width)))
                elif item[0] == "dot":
                    _, point, color, size = item
                    x, y = self._point(point)
                    Color(*color)
                    Ellipse(pos=(x - dp(size) / 2, y - dp(size) / 2),
                            size=(dp(size), dp(size)))
            if self.turtle and self.turtle[3]:
                x, y = self._point(self.turtle[:2])
                Color(1, 0.85, 0.2, 1)
                Ellipse(pos=(x - dp(4), y - dp(4)), size=(dp(8), dp(8)))

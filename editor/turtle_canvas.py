"""Turtle üçün ağ kətan; əmrləri növbə ilə çəkir və xüsusi JPG ikonunu göstərə bilir."""
import os
from kivy.graphics import Color, Ellipse, Line, Rectangle, PushMatrix, PopMatrix, Rotate
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.uix.image import Image


class TurtleCanvas(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.items = []
        self.bg = (1, 1, 1, 1)
        self.turtle = None
        self.bind(pos=self.redraw, size=self.redraw)
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(root, "Assets", "turtle.jpg")
        self.turtle_icon = Image(source=icon_path, size_hint=(None, None),
                                 size=(dp(34), dp(34)), allow_stretch=True,
                                 keep_ratio=True, opacity=0)
        self.add_widget(self.turtle_icon)
        self.turtle_icon.canvas.before.add(PushMatrix())
        self._rotation = Rotate(angle=0, origin=self.turtle_icon.center)
        self.turtle_icon.canvas.before.add(self._rotation)
        self.turtle_icon.canvas.after.add(PopMatrix())

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
        if self.turtle:
            x, y = self._point(self.turtle[:2])
            self.turtle_icon.center = (x, y)
            self.turtle_icon.opacity = 1 if self.turtle[3] else 0
            self._rotation.origin = self.turtle_icon.center
            self._rotation.angle = -float(self.turtle[2])

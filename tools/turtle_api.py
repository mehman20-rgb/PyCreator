"""PyCreator üçün Kivy-yə uyğun, Tkinter tələb etməyən Turtle API."""
import math
import queue

_commands = queue.Queue()


def _emit(command, *values):
    _commands.put((command,) + values)


def drain_commands(limit=5000):
    items = []
    for _ in range(limit):
        try:
            items.append(_commands.get_nowait())
        except queue.Empty:
            break
    return items


def reset_canvas():
    while True:
        try:
            _commands.get_nowait()
        except queue.Empty:
            break
    _emit("clear", (0.04, 0.06, 0.10, 1))


class Turtle:
    def __init__(self, shape="classic", visible=True, **kwargs):
        self._x = 0.0
        self._y = 0.0
        self._heading = 0.0
        self._down = True
        self._color = (0.15, 0.72, 1.0, 1)
        self._width = 2.0
        self._visible = visible
        _emit("turtle", self._x, self._y, self._heading, self._visible)

    def _move(self, x, y):
        old = (self._x, self._y)
        self._x, self._y = float(x), float(y)
        if self._down:
            _emit("line", old, (self._x, self._y), self._color, self._width)
        _emit("turtle", self._x, self._y, self._heading, self._visible)

    def forward(self, distance):
        r = math.radians(self._heading)
        self._move(self._x + math.cos(r) * distance,
                   self._y + math.sin(r) * distance)

    fd = forward

    def backward(self, distance):
        self.forward(-distance)

    bk = backward
    back = backward

    def right(self, angle):
        self._heading = (self._heading - float(angle)) % 360
        _emit("turtle", self._x, self._y, self._heading, self._visible)

    rt = right

    def left(self, angle):
        self.right(-float(angle))

    lt = left

    def goto(self, x, y=None):
        if y is None:
            x, y = x
        self._move(x, y)

    setpos = goto
    setposition = goto

    def setx(self, x):
        self._move(x, self._y)

    def sety(self, y):
        self._move(self._x, y)

    def setheading(self, angle):
        self._heading = float(angle) % 360
        _emit("turtle", self._x, self._y, self._heading, self._visible)

    seth = setheading

    def home(self):
        self.setheading(0)
        self.goto(0, 0)

    def penup(self):
        self._down = False

    pu = penup
    up = penup

    def pendown(self):
        self._down = True

    pd = pendown
    down = pendown

    def isdown(self):
        return self._down

    def pencolor(self, *color):
        if len(color) == 1:
            color = color[0]
        if isinstance(color, str):
            names = {"black": (0,0,0,1), "white": (1,1,1,1),
                     "red": (1,0.1,0.1,1), "green": (0.1,0.8,0.2,1),
                     "blue": (0.1,0.3,1,1), "yellow": (1,0.85,0.1,1),
                     "orange": (1,0.45,0.05,1), "purple": (0.65,0.25,0.9,1),
                     "cyan": (0,0.9,0.9,1), "pink": (1,0.35,0.65,1)}
            self._color = names.get(color.lower(), self._color)
        elif isinstance(color, (tuple, list)):
            vals = tuple(float(v) for v in color)
            if max(vals) > 1:
                vals = tuple(v / 255 for v in vals)
            self._color = vals[:3] + (1,)
        return self._color

    color = pencolor

    def pensize(self, width=None):
        if width is not None:
            self._width = max(1.0, float(width))
        return self._width

    width = pensize

    def speed(self, value=None):
        return value if value is not None else 0

    def hideturtle(self):
        self._visible = False
        _emit("turtle", self._x, self._y, self._heading, False)

    ht = hideturtle

    def showturtle(self):
        self._visible = True
        _emit("turtle", self._x, self._y, self._heading, True)

    st = showturtle

    def position(self):
        return (self._x, self._y)

    pos = position

    def xcor(self):
        return self._x

    def ycor(self):
        return self._y

    def heading(self):
        return self._heading

    def distance(self, x, y=None):
        if y is None:
            x, y = x
        return math.hypot(float(x) - self._x, float(y) - self._y)

    def circle(self, radius, extent=360, steps=None):
        count = steps or max(12, int(abs(extent) / 5))
        step = float(extent) / count
        length = 2 * math.pi * abs(radius) * abs(step) / 360
        direction = 1 if radius >= 0 else -1
        for _ in range(count):
            self.left(step)
            self.forward(length * direction)

    def dot(self, size=6, *color):
        if color:
            self.pencolor(*color)
        _emit("dot", (self._x, self._y), self._color, max(2, float(size)))

    def clear(self):
        _emit("clear", None)
        _emit("turtle", self._x, self._y, self._heading, self._visible)

    def reset(self):
        self._x, self._y, self._heading = 0.0, 0.0, 0.0
        self._down, self._color, self._width = True, (0.15, 0.72, 1.0, 1), 2.0
        _emit("clear", None)
        _emit("turtle", self._x, self._y, self._heading, self._visible)

    def stamp(self):
        _emit("dot", (self._x, self._y), self._color, 8)
        return 1

    def undo(self):
        return None


class _Screen:
    def bgcolor(self, color=None):
        if color is not None:
            names = {"black": (0,0,0,1), "white": (1,1,1,1),
                     "navy": (0.02,0.05,0.12,1), "lightblue": (0.65,0.85,1,1)}
            rgba = names.get(str(color).lower(), (0.04,0.06,0.10,1))
            _emit("clear", rgba)
        return None

    def clearscreen(self):
        _emit("clear", None)

    def reset(self):
        reset_canvas()
        _default.reset()

    def title(self, *_args):
        return None

    def setup(self, *_args, **_kwargs):
        return None

    def tracer(self, *_args, **_kwargs):
        return None

    def update(self):
        return None

    def mainloop(self):
        return None

    def bye(self):
        _emit("clear", None)


_default = Turtle()
_screen = _Screen()


def Screen():
    return _screen


def getscreen():
    return _screen


def TurtleScreen(*_args, **_kwargs):
    return _screen


def done():
    return None


def mainloop():
    return None


def forward(distance): return _default.forward(distance)
def fd(distance): return _default.forward(distance)
def backward(distance): return _default.backward(distance)
def back(distance): return _default.backward(distance)
def bk(distance): return _default.backward(distance)
def left(angle): return _default.left(angle)
def lt(angle): return _default.left(angle)
def right(angle): return _default.right(angle)
def rt(angle): return _default.right(angle)
def goto(x, y=None): return _default.goto(x, y)
def setpos(x, y=None): return _default.goto(x, y)
def setposition(x, y=None): return _default.goto(x, y)
def setheading(angle): return _default.setheading(angle)
def seth(angle): return _default.setheading(angle)
def penup(): return _default.penup()
def pu(): return _default.penup()
def up(): return _default.penup()
def pendown(): return _default.pendown()
def pd(): return _default.pendown()
def down(): return _default.pendown()
def isdown(): return _default.isdown()
def color(*args): return _default.pencolor(*args)
def pencolor(*args): return _default.pencolor(*args)
def pensize(width=None): return _default.pensize(width)
def width(width=None): return _default.pensize(width)
def speed(value=None): return _default.speed(value)
def hideturtle(): return _default.hideturtle()
def ht(): return _default.hideturtle()
def showturtle(): return _default.showturtle()
def st(): return _default.showturtle()
def home(): return _default.home()
def position(): return _default.position()
def pos(): return _default.position()
def xcor(): return _default.xcor()
def ycor(): return _default.ycor()
def heading(): return _default.heading()
def distance(x, y=None): return _default.distance(x, y)
def circle(radius, extent=360, steps=None): return _default.circle(radius, extent, steps)
def dot(size=6, *color): return _default.dot(size, *color)
def clear(): return _default.clear()
def reset():
    reset_canvas()
    return _default.reset()
def bgcolor(color=None): return _screen.bgcolor(color)
def clearscreen(): return _screen.clearscreen()
def title(value): return _screen.title(value)
def setup(*args, **kwargs): return _screen.setup(*args, **kwargs)
def tracer(*args, **kwargs): return _screen.tracer(*args, **kwargs)
def update(): return _screen.update()
def bye(): return _screen.bye()
def reset_turtle(): return reset()
def stamp(): return _default.stamp()

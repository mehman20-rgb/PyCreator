"""Turtle qrafikası üçün ayrıca ağ tam ekran."""
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from editor.turtle_canvas import TurtleCanvas
from ui.theme import ACCENT, PANEL2, Btn


class TurtleScreen(BoxLayout):
    def __init__(self, close_callback, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(4), padding=dp(5), **kwargs)
        self.close_callback = close_callback
        self.canvas_widget = TurtleCanvas()
        header = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        header.add_widget(Label(text="TURTLE", color=(0.3, 0.35, 0.4, 1), font_size=sp(13), halign="left"))
        clear = Btn("Təmizlə", base=PANEL2, size_hint_x=None, width=dp(88))
        back = Btn("Geri", base=ACCENT, size_hint_x=None, width=dp(70))
        clear.bind(on_release=lambda *_: self.clear())
        back.bind(on_release=lambda *_: self.close_callback())
        header.add_widget(clear)
        header.add_widget(back)
        self.add_widget(header)
        self.add_widget(self.canvas_widget)

    def clear(self):
        self.canvas_widget.items = []
        self.canvas_widget.turtle = None
        self.canvas_widget.bg = (1, 1, 1, 1)
        self.canvas_widget.redraw()

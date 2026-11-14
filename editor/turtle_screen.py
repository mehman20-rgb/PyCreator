"""Turtle üçün ağ iş sahəsi və aşağıda 25% terminal."""
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from editor.turtle_canvas import TurtleCanvas
from ui.theme import ACCENT, PANEL2, MONO, Btn


class TurtleScreen(BoxLayout):
    def __init__(self, close_callback, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(4), padding=dp(5), **kwargs)
        self.close_callback = close_callback
        header = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        header.add_widget(Label(text="TURTLE", color=(0.3, 0.35, 0.4, 1),
                                font_size=sp(13), halign="left"))
        clear = Btn("Təmizlə", base=PANEL2, size_hint_x=None, width=dp(88))
        back = Btn("Geri", base=ACCENT, size_hint_x=None, width=dp(70))
        clear.bind(on_release=lambda *_: self.clear())
        back.bind(on_release=lambda *_: self.close_callback())
        header.add_widget(clear)
        header.add_widget(back)
        self.add_widget(header)

        self.canvas_widget = TurtleCanvas(size_hint_y=0.75)
        self.add_widget(self.canvas_widget)

        terminal_box = BoxLayout(orientation="vertical", size_hint_y=0.25,
                                 spacing=dp(3), padding=(dp(5), dp(3)))
        terminal_box.canvas.before.clear()
        from kivy.graphics import Color, Rectangle
        with terminal_box.canvas.before:
            Color(0.025, 0.035, 0.05, 1)
            self._terminal_bg = Rectangle(pos=terminal_box.pos, size=terminal_box.size)
        terminal_box.bind(pos=lambda w, *_: setattr(self._terminal_bg, "pos", w.pos),
                          size=lambda w, *_: setattr(self._terminal_bg, "size", w.size))
        term_head = BoxLayout(size_hint_y=None, height=dp(26))
        term_head.add_widget(Label(text="TERMINAL  /  OUTPUT & ERRORS",
                                   color=(0.65, 0.72, 0.8, 1), font_size=sp(11),
                                   halign="left"))
        clear_log = Btn("⌫", base=PANEL2, size_hint_x=None, width=dp(38),
                        height=dp(25))
        clear_log.bind(on_release=lambda *_: setattr(self.terminal, "text", ""))
        term_head.add_widget(clear_log)
        terminal_box.add_widget(term_head)

        self.terminal = TextInput(readonly=True, multiline=True, font_name=MONO,
                                  font_size=sp(12), background_color=(0.025, 0.035, 0.05, 1),
                                  foreground_color=(0.78, 0.9, 0.82, 1),
                                  cursor_color=(0, 0, 0, 0))
        terminal_box.add_widget(self.terminal)
        self.add_widget(terminal_box)

    def clear(self):
        self.canvas_widget.items = []
        self.canvas_widget.turtle = None
        self.canvas_widget.bg = (1, 1, 1, 1)
        self.canvas_widget.redraw()

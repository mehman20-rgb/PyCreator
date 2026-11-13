"""Ayrıca açılan tam ekran, qara nəticə/runner səhifəsi."""
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from ui.theme import ACCENT, RED, PANEL2, MONO, Btn


class RunnerScreen(BoxLayout):
    def __init__(self, editor, close_callback, **kwargs):
        super().__init__(orientation="vertical", padding=dp(10), spacing=dp(8),
                         **kwargs)
        self.editor = editor
        self.close_callback = close_callback
        self.console = editor.console
        self.input_row = editor.input_row
        self.input_field = editor.input_field
        self.canvas.before.clear()
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(0, 0, 0, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_bg, size=self._sync_bg)

        header = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        header.add_widget(Label(text="RUNNER", color=(0.65, 0.7, 0.75, 1),
                                font_size=sp(13), halign="left",
                                valign="middle", text_size=(None, None)))
        stop = Btn("■ Dayan", base=RED, size_hint_x=None, width=dp(92))
        close = Btn("Bağla", base=PANEL2, size_hint_x=None, width=dp(76))
        stop.bind(on_release=lambda *_: self.editor.runner.stop())
        close.bind(on_release=lambda *_: self.close_callback())
        header.add_widget(stop)
        header.add_widget(close)
        self.add_widget(header)

        self.console.background_color = (0, 0, 0, 1)
        self.console.foreground_color = (0.78, 0.96, 0.82, 1)
        self.console.font_name = MONO
        self.console.font_size = sp(14)
        self.console.size_hint_y = 1
        self.add_widget(self.console)

        send = Btn("Göndər", base=ACCENT, size_hint_x=None, width=dp(96))
        send.bind(on_release=lambda *_: self.editor._send_input())
        self.input_field.size_hint_x = 1
        self.input_row.add_widget(send)
        self.input_row.size_hint_y = None
        self.add_widget(self.input_row)

    def _sync_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

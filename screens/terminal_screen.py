"""Terminal ekranı üçün çıxış/input paneli; icra mühərriki xaricdən verilir."""
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput

from ui.theme import MONO, Btn, make_label


class TerminalScreen(BoxLayout):
    def __init__(self, on_execute=None, on_stop=None, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(6), padding=dp(8), **kwargs)
        self.on_execute=on_execute
        self.on_stop=on_stop
        self.add_widget(make_label("Python Terminal", size=18, bold=True, height=34))
        self.source=TextInput(text='print("Salam, PyCreator!")', multiline=True,
                              font_name=MONO,font_size=sp(14),write_tab=False)
        self.add_widget(self.source)
        row=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(6))
        run=Btn("▶ İşlət")
        stop=Btn("■ Dayan")
        clear=Btn("Təmizlə")
        if on_execute:
            run.bind(on_release=lambda *_: on_execute(self.source.text))
        if on_stop:
            stop.bind(on_release=lambda *_: on_stop())
        clear.bind(on_release=lambda *_: setattr(self.output,"text",""))
        row.add_widget(run); row.add_widget(stop); row.add_widget(clear)
        self.add_widget(row)
        self.output=TextInput(readonly=True,font_name=MONO,font_size=sp(12),size_hint_y=.45)
        self.add_widget(self.output)

    def append_output(self, text):
        self.output.text += str(text)

    def clear_output(self):
        self.output.text=""

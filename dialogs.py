"""Kiçik dialoq pəncərələri: mətn soruş, təsdiq al, məlumat göstər."""
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

from theme import GREEN, RED, Btn, make_label


def _open(title, content, height):
    popup = Popup(title=title, content=content, size_hint=(0.92, None),
                  height=dp(height), auto_dismiss=True)
    popup.open()
    return popup


def ask_text(title, hint, default, on_ok, ok_text="Yaddaşa ver"):
    """Bir sətir mətn soruşur; boş deyilsə on_ok(mətn) çağırılır."""
    box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
    field = TextInput(text=default, hint_text=hint, multiline=False, write_tab=False,
                      size_hint_y=None, height=dp(46), font_size=sp(16))
    row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
    cancel = Btn("Ləğv et")
    ok = Btn(ok_text, base=GREEN)
    row.add_widget(cancel)
    row.add_widget(ok)
    box.add_widget(field)
    box.add_widget(row)
    popup = _open(title, box, 190)

    def done(*_):
        value = field.text.strip()
        popup.dismiss()
        if value:
            on_ok(value)

    field.bind(on_text_validate=done)
    ok.bind(on_release=done)
    cancel.bind(on_release=lambda *_: popup.dismiss())
    Clock.schedule_once(lambda _dt: setattr(field, "focus", True), 0.2)


def confirm(title, message, on_yes, yes_text="Bəli", danger=False):
    box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
    box.add_widget(make_label(message, size=15))
    row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
    no = Btn("Xeyr")
    yes = Btn(yes_text, base=RED if danger else GREEN)
    row.add_widget(no)
    row.add_widget(yes)
    box.add_widget(row)
    popup = _open(title, box, 210)

    def done(*_):
        popup.dismiss()
        on_yes()

    yes.bind(on_release=done)
    no.bind(on_release=lambda *_: popup.dismiss())


def info(title, message):
    box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
    box.add_widget(make_label(message, size=15))
    ok = Btn("Oldu", base=GREEN)
    box.add_widget(ok)
    popup = _open(title, box, 220)
    ok.bind(on_release=lambda *_: popup.dismiss())

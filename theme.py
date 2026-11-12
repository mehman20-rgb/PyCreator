"""Rənglər, şriftlər və təkrar istifadə olunan sadə vidjetlər."""
import os

from kivy.core.text import LabelBase
from kivy.metrics import dp, sp
from kivy.uix.button import Button
from kivy.uix.label import Label

BG = (0.07, 0.08, 0.10, 1)
PANEL = (0.11, 0.13, 0.17, 1)
PANEL2 = (0.16, 0.19, 0.25, 1)
ACCENT = (0.20, 0.50, 0.95, 1)
GREEN = (0.15, 0.62, 0.35, 1)
RED = (0.78, 0.25, 0.25, 1)
TEXT = (0.92, 0.93, 0.95, 1)
MUTED = (0.60, 0.65, 0.72, 1)

MONO = "Mono"


def register_fonts(base_dir):
    """Azərbaycan hərfləri (ə, ı, ş, ç, ğ, ö, ü) üçün DejaVu şriftini əsas şrift edir."""
    a = os.path.join(base_dir, "assets")
    LabelBase.register(
        name="Roboto",
        fn_regular=os.path.join(a, "DejaVuSans.ttf"),
        fn_bold=os.path.join(a, "DejaVuSans-Bold.ttf"))
    LabelBase.register(
        name=MONO,
        fn_regular=os.path.join(a, "DejaVuSansMono.ttf"),
        fn_bold=os.path.join(a, "DejaVuSansMono-Bold.ttf"))


class Btn(Button):
    """Düz rəngli düymə; basıldıqda rəngi açılır."""

    def __init__(self, text="", base=PANEL2, **kw):
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(46))
        kw.setdefault("font_size", sp(15))
        super().__init__(text=text, background_normal="", background_down="",
                         background_color=base, color=TEXT, **kw)
        self.base = base
        self.bind(state=self._on_state)

    def _on_state(self, _widget, state):
        if state == "down":
            self.background_color = tuple(min(1.0, c + 0.18) for c in self.base[:3]) + (1,)
        else:
            self.background_color = self.base


def make_label(text="", size=15, color=TEXT, height=None, bold=False, **kw):
    """Mətni sola yaslanan, sətirə bölünən etiket."""
    lbl = Label(text=text, font_size=sp(size), color=color, bold=bold,
                halign="left", valign="middle", **kw)
    lbl.bind(width=lambda w, _v: setattr(w, "text_size", (w.width, None if height is None else w.height)))
    if height is not None:
        lbl.size_hint_y = None
        lbl.height = dp(height)
    else:
        lbl.size_hint_y = None
        lbl.bind(texture_size=lambda w, ts: setattr(w, "height", max(dp(24), ts[1] + dp(6))))
    return lbl

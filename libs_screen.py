"""Kitabxana meneceri ekranı: ad yaz, Quraşdır bas; siyahıdan sil."""
import queue
import threading

from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

import dialogs
from pkgman import PackageManager, PkgError, parse_requirement
from theme import GREEN, MONO, MUTED, PANEL2, RED, Btn, make_label

POPULAR = ["requests", "rich", "beautifulsoup4", "colorama", "tqdm", "python-dateutil",
           "pytz", "tabulate", "humanize", "emoji", "pyfiglet", "attrs"]
SKIP_WORDS = {"pip", "pip3", "install", "-r", "-u", "--upgrade"}


def parse_names(text):
    """'pip install requests==2.0, rich' -> ['requests', 'rich']"""
    names = []
    for token in text.replace(",", " ").split():
        if token.lower() in SKIP_WORDS:
            continue
        name, _ = parse_requirement(token)
        if name and name not in names:
            names.append(name)
    return names


class LibsScreen(BoxLayout):
    def __init__(self, site_dir, **kw):
        super().__init__(orientation="vertical", spacing=dp(8), padding=(dp(8), dp(6)), **kw)
        self._q = queue.Queue()
        self.busy = False
        self.pm = PackageManager(site_dir, log=lambda msg: self._q.put(("log", msg)))
        self._build()
        self.refresh()
        Clock.schedule_interval(self._poll, 0.05)

    def _build(self):
        self.add_widget(make_label(
            "Kitabxana adını yaz (bir neçə ad üçün boşluq və ya vergül işlət). "
            "Python-un hazır modulları (os, json, math, random...) quraşdırma tələb etmir. "
            "numpy/pandas kimi C kodlu kitabxanalar bu üsulla işləmir.",
            size=13, color=MUTED))

        row = BoxLayout(size_hint_y=None, height=dp(70), spacing=dp(6))
        self.field = TextInput(hint_text="məsələn: requests rich", multiline=True,
                               font_name=MONO, font_size=sp(15), write_tab=False)
        self.install_btn = Btn("Quraşdır", base=GREEN, size_hint_x=None, width=dp(120),
                               height=dp(70))
        self.install_btn.bind(on_release=lambda *_: self.install())
        row.add_widget(self.field)
        row.add_widget(self.install_btn)
        self.add_widget(row)

        self.add_widget(self._build_chips())
        self.add_widget(make_label("Quraşdırılmışlar", size=15, bold=True, height=28))

        scroll = ScrollView()
        self.listing = GridLayout(cols=1, spacing=dp(4), size_hint_y=None)
        self.listing.bind(minimum_height=self.listing.setter("height"))
        scroll.add_widget(self.listing)
        self.add_widget(scroll)

        self.log = TextInput(readonly=True, font_name=MONO, font_size=sp(12),
                             size_hint_y=None, height=dp(110),
                             background_color=(0.03, 0.04, 0.05, 1),
                             foreground_color=(0.78, 0.96, 0.82, 1), cursor_color=(0, 0, 0, 0))
        self.add_widget(self.log)

    def _build_chips(self):
        scroll = ScrollView(size_hint_y=None, height=dp(40), do_scroll_y=False, bar_width=0)
        grid = GridLayout(rows=1, size_hint_x=None, spacing=dp(4))
        grid.bind(minimum_width=grid.setter("width"))
        for name in POPULAR:
            b = Btn(name, base=PANEL2, size_hint_x=None, width=dp(24 + 9 * len(name)),
                    height=dp(40), font_size=sp(13))
            b.bind(on_release=lambda _w, n=name: self._add_name(n))
            grid.add_widget(b)
        scroll.add_widget(grid)
        return scroll

    def _add_name(self, name):
        current = self.field.text.strip()
        if name not in current.replace(",", " ").split():
            self.field.text = (current + " " + name).strip()

    # ---------- siyahı ----------
    def refresh(self):
        self.listing.clear_widgets()
        items = self.pm.installed()
        if not items:
            self.listing.add_widget(make_label("Hələ heç nə quraşdırılmayıb.", size=14, color=MUTED))
            return
        for name, version in items:
            row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
            row.add_widget(make_label("%s  %s" % (name, version), size=15, height=46))
            rm = Btn("Sil", base=RED, size_hint_x=None, width=dp(72), height=dp(40))
            rm.bind(on_release=lambda _w, n=name: self._ask_remove(n))
            row.add_widget(rm)
            self.listing.add_widget(row)

    def _ask_remove(self, name):
        if self.busy:
            return
        dialogs.confirm("Silinsin?", "'%s' kitabxanası silinəcək." % name,
                        lambda: self._remove(name), yes_text="Sil", danger=True)

    def _remove(self, name):
        try:
            self.pm.remove(name)
        except PkgError as err:
            self._say("✕ %s" % err)
        self.refresh()

    # ---------- quraşdırma ----------
    def install(self):
        names = parse_names(self.field.text)
        if self.busy:
            return
        if not names:
            self._say("Əvvəlcə kitabxana adını yaz.")
            return
        self.busy = True
        self.install_btn.disabled = True
        self.log.text = ""
        threading.Thread(target=self._work, args=(names,), daemon=True).start()

    def _work(self, names):
        for name in names:
            try:
                installed = self.pm.install(name)
                if installed:
                    self._q.put(("log", "✓ Hazırdır: %s" % ", ".join(installed)))
                else:
                    self._q.put(("log", "✓ %s artıq quraşdırılıb." % name))
            except PkgError as err:
                self._q.put(("log", "✕ %s: %s" % (name, err)))
            except Exception as err:  # gözlənilməz xəta proqramı çökdürməsin
                self._q.put(("log", "✕ %s: %s" % (name, err)))
        self._q.put(("done",))

    def _say(self, text):
        self.log.text += text + "\n"
        self.log.cursor = self.log.get_cursor_from_index(len(self.log.text))

    def _poll(self, _dt):
        for _ in range(100):
            try:
                item = self._q.get_nowait()
            except queue.Empty:
                break
            if item[0] == "log":
                self._say(item[1])
            elif item[0] == "done":
                self.busy = False
                self.install_btn.disabled = False
                self.field.text = ""
                self.refresh()

"""Kod redaktoru, simvol sətri, nəticə konsolu və input() sahəsi."""
import os
import queue

from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from ui import dialogs
from core.runner import Runner
from tools import turtle_api
from ui.theme import ACCENT, GREEN, MONO, MUTED, PANEL, PANEL2, RED, TEXT, Btn, make_label

try:
    from kivy.uix.codeinput import CodeInput
    from pygments.lexers import PythonLexer
    _BASE = CodeInput
    _HIGHLIGHT = True
except Exception:  # pygments yoxdursa adi redaktor istifadə olunur
    _BASE = TextInput
    _HIGHLIGHT = False

STARTER = "# Kodu yaz və ▶ İşlət düyməsinə bas\nprint('Salam, dünya!')\n"
MAX_CONSOLE = 100000
SYMBOLS = [
    ("Tab", "    "), ("( )", "()"), ("[ ]", "[]"), ("{ }", "{}"), ('" "', '""'), ("' '", "''"),
    (":", ":"), ("=", "="), ("#", "#"), (".", "."), (",", ","), ("_", "_"), ("+", "+"),
    ("-", "-"), ("*", "*"), ("/", "/"), ("<", "<"), (">", ">"), ("!", "!"), ("%", "%"),
    ("\\", "\\"),
]


class _AutoIndent:
    """Enter basanda əvvəlki sətrin boşluğunu saxlayır; ':' ilə bitibsə 4 boşluq əlavə edir."""

    def insert_text(self, substring, from_undo=False):
        if substring == "\n" and not from_undo:
            line = self.text[:self.cursor_index()].rsplit("\n", 1)[-1]
            indent = len(line) - len(line.lstrip(" "))
            if line.rstrip().endswith(":"):
                indent += 4
            substring = "\n" + " " * indent
        return super().insert_text(substring, from_undo=from_undo)


class CodeBox(_AutoIndent, _BASE):
    pass


def _make_code_box():
    # Tünd göy redaktor fonu; sintaksis rəngləri olduğu kimi saxlanılır.
    kw = dict(font_name=MONO, font_size=sp(14), do_wrap=False, cursor_color=ACCENT,
              background_color=(0.025, 0.04, 0.075, 1))
    if _HIGHLIGHT:
        kw.update(lexer=PythonLexer(), style_name="monokai")
    else:
        kw.update(foreground_color=TEXT)
    return CodeBox(**kw)


class EditorScreen(BoxLayout):
    def __init__(self, data_dir, code_dir, **kw):
        super().__init__(orientation="vertical", spacing=dp(6),
                         padding=(dp(8), dp(6)), **kw)
        self.data_dir = data_dir
        self.code_dir = code_dir
        self.name = None
        self._q = queue.Queue()
        self.runner = Runner(
            lambda text: self._q.put(("out", text)),
            lambda prompt: self._q.put(("input", prompt)),
            lambda status, secs: self._q.put(("done", status, secs)))
        self._build()
        self._restore()
        Clock.schedule_interval(self._poll, 0.05)

    # ---------- quruluş ----------
    def _build(self):
        top = BoxLayout(size_hint_y=None, height=dp(42))
        top.add_widget(BoxLayout())
        controls = BoxLayout(size_hint_x=None, width=dp(154), spacing=dp(4),
                             padding=dp(3))
        controls.canvas.before.clear()
        self.run_btn = Btn("▶", base=GREEN, size_hint_x=None, width=dp(38))
        self.stop_btn = Btn("■", base=RED, disabled=True, size_hint_x=None, width=dp(38))
        new_btn = Btn("+", size_hint_x=None, width=dp(34))
        save_btn = Btn("▣", size_hint_x=None, width=dp(34))
        self.run_btn.bind(on_release=lambda *_: self.run())
        self.stop_btn.bind(on_release=lambda *_: self.runner.stop())
        new_btn.bind(on_release=lambda *_: self.new_file())
        save_btn.bind(on_release=lambda *_: self.save())
        for b in (self.run_btn, self.stop_btn, new_btn, save_btn):
            controls.add_widget(b)
        top.add_widget(controls)
        self.add_widget(top)

        self.title = make_label("", size=13, color=MUTED, height=22)
        self.add_widget(self.title)

        self.add_widget(self._build_symbols())

        self.code = _make_code_box()
        self.code.size_hint_y = 1
        self.add_widget(self.code)

        # Nəticə konsolu ayrıca tam ekran Runner səhifəsində göstərilir.
        self.console = TextInput(
            readonly=True, font_name=MONO, font_size=sp(13),
            background_color=(0, 0, 0, 1), foreground_color=(0.78, 0.96, 0.82, 1),
            cursor_color=(0, 0, 0, 0))
        self.input_row = BoxLayout(size_hint_y=None, height=0, opacity=0,
                                   disabled=True, spacing=dp(6))
        self.input_field = TextInput(multiline=False, hint_text="Cavabını yaz və Göndər",
                                     font_name=MONO, font_size=sp(15), write_tab=False)
        self.input_row.add_widget(self.input_field)

    def _build_symbols(self):
        scroll = ScrollView(size_hint_y=None, height=dp(40), do_scroll_y=False, bar_width=0)
        grid = GridLayout(rows=1, size_hint_x=None, spacing=dp(4))
        grid.bind(minimum_width=grid.setter("width"))
        for label, text in SYMBOLS:
            b = Btn(label, base=PANEL2, size_hint_x=None, width=dp(54), height=dp(40))
            b.bind(on_release=lambda _w, t=text: self._insert(t))
            grid.add_widget(b)
        scroll.add_widget(grid)
        return scroll

    def _insert(self, text):
        self.code.insert_text(text)
        if len(text) == 2 and text[0] in "([{\"'":
            self.code.do_cursor_movement("cursor_left")
        Clock.schedule_once(lambda _dt: setattr(self.code, "focus", True), 0.05)

    # ---------- işə salma ----------
    def run(self):
        if self.runner.running:
            return
        self.persist()
        self.console.text = ""
        source = self.code.text
        self._uses_turtle = ("import turtle" in source or "from turtle import" in source)
        self._uses_3d = ("import py3d" in source or "from py3d import" in source)
        if self._uses_turtle and getattr(self, "turtle_terminal", None):
            self.turtle_terminal.text = ""
        self.code.size_hint_y = 1
        if self._uses_turtle:
            turtle_api.reset()
        self._set_running(True)
        if self._uses_turtle and hasattr(self, "show_turtle"):
            self.show_turtle()
        elif self._uses_3d and hasattr(self, "show_3d"):
            self.show_3d()
        elif hasattr(self, "show_runner"):
            self.show_runner()
        self.runner.start(source, self.name or "adsiz")

    def _set_running(self, running):
        self.run_btn.disabled = running
        self.stop_btn.disabled = not running
        if not running:
            self._hide_input()

    def _show_input(self, prompt):
        self.input_row.height = dp(46)
        self.input_row.opacity = 1
        self.input_row.disabled = False
        self.input_field.text = ""
        if hasattr(self, "show_runner"):
            self.show_runner()
        Clock.schedule_once(lambda _dt: setattr(self.input_field, "focus", True), 0.1)

    def _hide_input(self):
        self.input_row.height = 0
        self.input_row.opacity = 0
        self.input_row.disabled = True
        self.input_field.focus = False

    def _send_input(self):
        text = self.input_field.text
        self._hide_input()
        self.runner.provide_input(text)

    # ---------- işçi thread-dən gələn hadisələr ----------
    def _poll(self, _dt):
        chunks = []
        for _ in range(400):
            try:
                item = self._q.get_nowait()
            except queue.Empty:
                break
            kind = item[0]
            if kind == "out":
                chunks.append(item[1])
            elif kind == "input":
                self._flush(chunks)
                self._show_input(item[1])
            elif kind == "done":
                self._flush(chunks)
                self._finish(item[1], item[2])
        self._flush(chunks)
        for command in turtle_api.drain_commands(limit=1):
            if getattr(self, "turtle_canvas", None):
                self.turtle_canvas.apply(command)

    def _flush(self, chunks):
        if chunks:
            self._append("".join(chunks))
            del chunks[:]

    def _append(self, text):
        target = self.console
        if self._uses_turtle and getattr(self, "turtle_terminal", None):
            target = self.turtle_terminal
        value = target.text + text.replace("\r", "")
        if len(value) > MAX_CONSOLE:
            value = value[-int(MAX_CONSOLE * 0.8):]
        target.text = value
        target.cursor = target.get_cursor_from_index(len(value))

    def _finish(self, status, secs):
        self._set_running(False)
        if status == "ok":
            self._append("\n[Bitdi · %.1f san]\n" % secs)
        elif status == "stopped":
            self._append("\n[Dayandırıldı]\n")
        else:
            self._append("\n[Xəta ilə bitdi]\n")

    # ---------- fayllar ----------
    def _path(self, name):
        return os.path.join(self.code_dir, name)

    def _scratch(self):
        return os.path.join(self.data_dir, ".scratch.py")

    def _state(self):
        return os.path.join(self.data_dir, ".state")

    def _set_name(self, name):
        self.name = name
        self.title.text = ("Fayl: %s" % name) if name else "Fayl: adsız (hələ saxlanmayıb)"

    def _write(self, path):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.code.text)

    def persist(self):
        """Cari kodu qoruyur: adlı faylı yeniləyir, adsızı müvəqqəti fayla yazır."""
        try:
            self._write(self._path(self.name) if self.name else self._scratch())
            with open(self._state(), "w", encoding="utf-8") as fh:
                fh.write(self.name or "")
        except OSError:
            pass

    def _restore(self):
        name = ""
        try:
            with open(self._state(), encoding="utf-8") as fh:
                name = fh.read().strip()
        except OSError:
            pass
        path = self._path(name) if name else self._scratch()
        try:
            with open(path, encoding="utf-8") as fh:
                self.code.text = fh.read()
            self._set_name(name or None)
        except OSError:
            self.code.text = STARTER
            self._set_name(None)

    def save(self):
        if self.name:
            self.persist()
            self._append_status("Saxlandı: %s" % self.name)
        else:
            dialogs.ask_text("Fayl adı", "məsələn: salam.py", "", self._save_as)

    def _save_as(self, name):
        name = name.replace("/", "_").replace("\\", "_")
        if "." not in name:
            name += ".py"
        self._set_name(name)
        self.persist()
        self._append_status("Saxlandı: %s" % name)

    def _append_status(self, text):
        self.title.text = "%s  ✓ %s" % (("Fayl: %s" % self.name) if self.name else "Fayl", text)

    def new_file(self):
        self.persist()
        self._set_name(None)
        self.code.text = STARTER
        self.console.text = ""

    def open_file(self, name):
        """Fayllar ekranından çağırılır."""
        self.persist()
        try:
            with open(self._path(name), encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            dialogs.info("Xəta", "Fayl açıla bilmədi: %s" % name)
            return False
        self.code.text = text
        self._set_name(name)
        self.console.text = ""
        self.persist()
        return True

    def forget(self, name):
        """Fayl silindikdə redaktor həmin faylı göstərirsə adsız rejimə keçir."""
        if self.name == name:
            self._set_name(None)

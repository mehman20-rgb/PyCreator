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
    """Bir toxunuşla görünən kursoru yerləşdirir, iki toxunuşla klaviaturanı açır."""

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.readonly:
            if getattr(touch, "is_double_tap", False):
                self.cursor = self.get_cursor_from_xy(*touch.pos)
                self.focus = True
                self.show_keyboard()
                # FocusBehavior toxunuş bitəndə widget-i defokuslamasın.
                self.ignored_touch.append(touch)
                return True

            # Managed rejimində fokus/kursor görünür, amma ilk toxunuş klaviaturanı açmır.
            if self.keyboard_mode == "managed" and self._keyboard is None:
                self.cursor = self.get_cursor_from_xy(*touch.pos)
                self.focus = True
                return False
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        # Klaviatura bağlı olanda toxunma hərəkətini ScrollView idarə etsin.
        if self.keyboard_mode == "managed" and self.focus and self._keyboard is None:
            return False
        return super().on_touch_move(touch)


def _make_code_box():
    # Tünd göy redaktor fonu; sintaksis rəngləri olduğu kimi saxlanılır.
    kw = dict(font_name=MONO, font_size=sp(14), do_wrap=False, cursor_color=ACCENT,
              keyboard_mode="managed",
              background_color=(0.025, 0.04, 0.075, 1))
    if _HIGHLIGHT:
        kw.update(lexer=PythonLexer(), style_name="monokai")
    else:
        kw.update(foreground_color=TEXT)
    return CodeBox(**kw)


class EditorScreen(BoxLayout):
    def __init__(self, data_dir, code_dir, storage_manager=None, **kw):
        super().__init__(orientation="vertical", spacing=dp(6),
                         padding=(dp(8), dp(6)), **kw)
        self.data_dir = data_dir
        self.code_dir = code_dir
        self.storage_manager = storage_manager
        self._saved_uri = None
        self.name = None
        self.has_run_once = False
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

        # Uzun kod sətirləri kəsilmədən üfüqi, çoxsətirli kod isə şaquli sürüşdürülür.
        self.editor_scroll = ScrollView(
            size_hint=(1, 1), do_scroll_x=True, do_scroll_y=True,
            bar_width=dp(3), scroll_type=["bars", "content"])
        self.code = _make_code_box()
        self.code.size_hint = (None, None)
        self.editor_scroll.add_widget(self.code)
        self.add_widget(self.editor_scroll)
        self._resize_code_trigger = Clock.create_trigger(self._sync_code_extent, 0)
        self.code.bind(text=lambda *_: self._resize_code_trigger())
        self.editor_scroll.bind(size=lambda *_: self._resize_code_trigger())
        self._resize_code_trigger()

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
        scroll = ScrollView(
            size_hint_y=None, height=dp(40), do_scroll_x=True,
            do_scroll_y=False, bar_width=0)
        grid = GridLayout(rows=1, size_hint_x=None, spacing=dp(4))
        grid.bind(minimum_width=grid.setter("width"))

        # Mövcud Tab düyməsi birinci qalır.
        label, symbol_text = SYMBOLS[0]
        tab_button = Btn(label, base=PANEL2, size_hint_x=None,
                         width=dp(54), height=dp(40))
        tab_button.bind(on_release=lambda _w, t=symbol_text: self._insert(t))
        grid.add_widget(tab_button)

        # Kompüterdəki Ctrl qısayollarının mobil qarşılığı.
        shortcuts = (
            ("Ctrl+Z", "undo"),
            ("Ctrl+C", "copy"),
            ("Ctrl+V", "paste"),
            ("Ctrl+X", "cut"),
            ("Ctrl+A", "select_all"),
        )
        for label, action in shortcuts:
            button = Btn(
                label, base=ACCENT, size_hint_x=None, width=dp(68),
                height=dp(40), font_size=sp(11))
            button.bind(on_release=lambda _w, a=action: self._shortcut(a))
            grid.add_widget(button)

        for label, text in SYMBOLS[1:]:
            button = Btn(label, base=PANEL2, size_hint_x=None,
                         width=dp(54), height=dp(40))
            button.bind(on_release=lambda _w, t=text: self._insert(t))
            grid.add_widget(button)
        scroll.add_widget(grid)
        return scroll

    def _shortcut(self, action):
        """Ctrl+Z/C/V/X/A əməliyyatlarını TextInput-un daxili API-si ilə icra edir."""
        code = self.code
        keep_focus = code.focus
        if action == "undo":
            code.do_undo()
        elif action == "copy":
            code.copy()
        elif action == "paste":
            code.paste()
        elif action == "cut":
            code.cut()
        elif action == "select_all":
            code.select_all()

        # Toolbar əməliyyatları öz-özünə Android klaviaturasını açmamalıdır.
        if not keep_focus:
            code.focus = False
        self._resize_code_trigger()

    def _insert(self, text):
        keep_focus = self.code.focus
        self.code.insert_text(text)
        if len(text) == 2 and text[0] in "([{\\\"'":
            self.code.do_cursor_movement("cursor_left")
        if not keep_focus:
            self.code.focus = False
        self._resize_code_trigger()

    def _sync_code_extent(self, *_):
        """TextInput ölçüsünü ən uzun sətirə və ümumi sətir sayına uyğunlaşdırır."""
        if not hasattr(self, "code") or not hasattr(self, "editor_scroll"):
            return
        source = self.code.text or ""
        lines = source.splitlines() or [""]
        if source.endswith(chr(10)):
            lines.append("")
        try:
            widest = max(
                (self.code._get_text_width(line, self.code.tab_width, None)
                 for line in lines),
                default=0)
        except Exception:
            widest = max((len(line.expandtabs(4)) for line in lines), default=0)
            widest *= self.code.font_size * 0.62

        padding = self.code.padding
        left, top, right, bottom = padding
        line_height = self.code.line_height + self.code.line_spacing
        content_width = widest + left + right + dp(16)
        content_height = len(lines) * line_height + top + bottom + dp(8)
        self.code.width = max(self.editor_scroll.width, content_width)
        self.code.height = max(self.editor_scroll.height, content_height)

    # ---------- işə salma ----------
    def run(self):
        if self.runner.running:
            return
        self.has_run_once = True
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
        """İş sessiyasını daxili müvəqqəti faylda saxlayır; test faylını dəyişmir."""
        try:
            self._write(self._scratch())
            with open(self._state(), "w", encoding="utf-8") as fh:
                fh.write(self.name or "")
            with open(os.path.join(self.data_dir, ".external_uri"), "w", encoding="utf-8") as fh:
                fh.write(self._saved_uri or "")
        except OSError:
            pass

    def _restore(self):
        name = ""
        try:
            with open(self._state(), encoding="utf-8") as fh:
                name = fh.read().strip()
        except OSError:
            pass
        try:
            with open(os.path.join(self.data_dir, ".external_uri"), encoding="utf-8") as fh:
                self._saved_uri = fh.read().strip() or None
        except OSError:
            self._saved_uri = None
        try:
            with open(self._scratch(), encoding="utf-8") as fh:
                self.code.text = fh.read()
            self._set_name(name or None)
            return
        except OSError:
            pass
        if name:
            try:
                with open(self._path(name), encoding="utf-8") as fh:
                    self.code.text = fh.read()
                self._set_name(name)
                return
            except OSError:
                pass
        self.code.text = STARTER
        self._set_name(None)

    def save(self):
        if self.name:
            self._save_as(self.name)
        else:
            dialogs.ask_text("Fayl adı", "məsələn: salam.py", "", self._save_as)

    def _save_as(self, name):
        name = name.strip().replace("/", "_").replace("\\", "_")
        if not name:
            return
        # Bu redaktor Python mənbə faylı saxlayır: həmişə .py uzantısı.
        base, extension = os.path.splitext(name)
        if extension.lower() != ".py":
            name = (base if extension else name) + ".py"
        if self.storage_manager is None:
            dialogs.info("Saxlama xətası", "Android fayl seçicisi qoşulmayıb.")
            return
        def finished(ok, uri_or_error):
            if ok:
                self._saved_uri = uri_or_error
                self._set_name(name)

                # SAF-dəki əsas nüsxə ilə yanaşı daxili iş nüsxəsini də sinxron saxla.
                # Bu, PyCreator-un Fayllar siyahısının və mövcud iş axınının uyğun qalmasını təmin edir.
                try:
                    os.makedirs(self.code_dir, exist_ok=True)
                    self._write(self._path(name))
                except OSError:
                    pass

                self.persist()
                if hasattr(self, "on_saved") and callable(self.on_saved):
                    self.on_saved()
                self._append_status("Download/pyProject qovluğunda saxlandı: %s" % name)
            else:
                dialogs.info("Saxlama xətası", uri_or_error or "Fayl saxlanmadı.")

        def updated_existing(ok, result):
            if ok:
                finished(True, result)
                return
            error_text = str(result or "").lower()
            # Köhnə build-lərdə .external_uri str(Uri) LocalRef kimi yazılmışdı.
            # Etibarsız/bitmiş URI üçün yeni düzgün SAF sənədi yarat.
            if (not self._saved_uri or
                    not self._saved_uri.startswith("content://") or
                    "no content provider" in error_text or
                    "filenotfoundexception" in error_text or
                    "permission" in error_text):
                self._saved_uri = None
                self.persist()
                self.storage_manager.create_document(self.code.text, name, finished)
            else:
                finished(False, result)

        if self._saved_uri and not self._saved_uri.startswith("content://"):
            # Əvvəlki versiyanın LocalRef mətnini bərpa etməyə çalışma.
            self._saved_uri = None

        if self._saved_uri:
            self.storage_manager.write_document(
                self._saved_uri, self.code.text, updated_existing)
        else:
            self.storage_manager.create_document(self.code.text, name, finished)

    def _append_status(self, text):
        self.title.text = "%s  ✓ %s" % (("Fayl: %s" % self.name) if self.name else "Fayl", text)

    def new_file(self):
        self.persist()
        self._saved_uri = None
        self._set_name(None)
        self.code.text = STARTER
        self.console.text = ""
        self.persist()

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
        self._saved_uri = None
        self._set_name(name)
        self.console.text = ""
        self.persist()
        return True

    def forget(self, name):
        """Fayl silindikdə redaktor həmin faylı göstərirsə adsız rejimə keçir."""
        if self.name == name:
            self._set_name(None)

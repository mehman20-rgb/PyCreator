"""PyCreator: telefonda Python kodu yaz, işlət və kitabxana quraşdır."""
import os

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager

from ui import theme
from ui.theme import ACCENT, BG, PANEL2, Btn

TABS = [("editor", "Redaktor"), ("qr", "QR Code"), ("libs", "Kitabxanalar"), ("files", "Fayllar")]


class PyCreatorApp(App):
    title = "PyCreator"

    def build(self):
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        theme.register_fonts(project_dir)
        Window.clearcolor = BG
        Window.softinput_mode = "resize"

        # Importlar şrift qeydiyyatından sonra edilir ki, bütün vidjetlər DejaVu istifadə etsin.
        from editor.editor_screen import EditorScreen
        from editor.runner_screen import RunnerScreen
        from files.files_screen import FilesScreen
        from packages.libs_screen import LibsScreen
        from tools.qr_screen import QRCodeScreen

        data_dir = self.user_data_dir
        self.code_dir = self._prepare_code_dir(data_dir)
        site_dir = os.path.join(data_dir, "site-packages")
        os.chdir(self.code_dir)
        self._seed_examples(data_dir)

        self.editor = EditorScreen(data_dir, self.code_dir)
        self.runner_page = RunnerScreen(self.editor, lambda: self.switch("editor"))
        self.editor.show_runner = lambda: self.switch("runner")
        self.libs = LibsScreen(site_dir)
        self.qr = QRCodeScreen()
        self.files = FilesScreen(self.code_dir, self._open_from_files, self.editor.forget)

        self.sm = ScreenManager(transition=NoTransition())
        for name, widget in (("editor", self.editor), ("runner", self.runner_page), ("qr", self.qr), ("libs", self.libs), ("files", self.files)):
            screen = Screen(name=name)
            screen.add_widget(widget)
            self.sm.add_widget(screen)

        root = BoxLayout(orientation="vertical")
        root.add_widget(self.sm)
        nav = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(2))
        self.nav = nav
        self.tab_buttons = {}
        for name, label in TABS:
            b = Btn(label, base=PANEL2, height=dp(52))
            b.bind(on_release=lambda _w, n=name: self.switch(n))
            self.tab_buttons[name] = b
            nav.add_widget(b)
        root.add_widget(nav)

        self.switch("editor")
        Window.bind(on_keyboard=self._on_back)
        Clock.schedule_interval(lambda _dt: self.editor.persist(), 20)
        return root

    # ---------- qovluqlar ----------
    def _prepare_code_dir(self, data_dir):
        """Fayl menecerində görünən qovluğu yoxlayır; alınmazsa daxili yaddaşdan istifadə edir."""
        preferred = None
        try:
            from jnius import autoclass  # yalnız Android-də mövcuddur
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            ext = activity.getExternalFilesDir(None)
            if ext is not None:
                preferred = os.path.join(ext.getAbsolutePath(), "kodlar")
        except Exception:
            preferred = None
        for path in (preferred, os.path.join(data_dir, "kodlar")):
            if not path:
                continue
            try:
                os.makedirs(path, exist_ok=True)
                return path
            except OSError:
                continue
        return data_dir

    def _seed_examples(self, data_dir):
        marker = os.path.join(data_dir, ".seeded")
        if os.path.exists(marker):
            return
        from samples.examples import EXAMPLES
        for name, code in EXAMPLES.items():
            path = os.path.join(self.code_dir, name)
            if not os.path.exists(path):
                try:
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write(code)
                except OSError:
                    pass
        try:
            with open(marker, "w") as fh:
                fh.write("1")
        except OSError:
            pass

    # ---------- naviqasiya ----------
    def switch(self, name):
        self.sm.current = name
        self.nav.height = 0 if name == "runner" else dp(52)
        self.nav.opacity = 0 if name == "runner" else 1
        self.nav.disabled = name == "runner"
        for tab, button in self.tab_buttons.items():
            button.base = ACCENT if tab == name else PANEL2
            button.background_color = button.base
        if name == "files":
            self.files.refresh()
            self.editor.persist()

    def _open_from_files(self, name):
        if self.editor.open_file(name):
            self.switch("editor")

    def _on_back(self, _window, key, *_args):
        if key == 27 and self.sm.current != "editor":  # Android "geri" düyməsi
            self.switch("editor")
            return True
        return False

    # ---------- həyat dövrü ----------
    def on_pause(self):
        self.editor.persist()
        return True

    def on_resume(self):
        pass

    def on_stop(self):
        self.editor.persist()


if __name__ == "__main__":
    PyCreatorApp().run()

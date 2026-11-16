"""PyCreator: telefonda Python kodu yaz, işlət və kitabxana quraşdır."""
import os

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager

from ui import theme
from ui.theme import ACCENT, BG, PANEL2, TEXT, Btn

TABS = [("editor", "Redaktor"), ("runner", "Runner"), ("qr", "QR Code"),
        ("libs", "Kitabxanalar"), ("files", "Fayllar"), ("3d", "3D"),
        ("settings", "Settings")]


class PyCreatorApp(App):
    title = "PyCreator"

    def build(self):
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        theme.register_fonts(project_dir)
        Window.clearcolor = BG
        Window.softinput_mode = "resize"

        from editor.editor_screen import EditorScreen
        from editor.runner_screen import RunnerScreen
        from editor.turtle_screen import TurtleScreen
        from files.files_screen import FilesScreen
        from packages.libs_screen import LibsScreen
        from tools.qr_screen import QRCodeScreen
        from tools.three_d_screen import ThreeDScreen
        from screens.settings_screen import SettingsScreen
        from services.storage_manager import StorageManager
        from projects.project_manager import ProjectManager

        data_dir = self.user_data_dir
        # Daxili layihə keşini ictimai Download/pyProject qovluğu ilə qarışdırmırıq.
        # İstifadəçinin real layihə faylları StorageManager-in SAF qovluğunda saxlanır.
        self.projects_dir = os.path.join(data_dir, "ProjectWorkspace")
        self.project_manager = ProjectManager(self.projects_dir)
        old_dir = self._legacy_code_dir(data_dir)
        self.storage_manager = StorageManager(data_dir)
        self.code_dir, self.public_storage = self.storage_manager.prepare(old_dir)
        site_dir = os.path.join(data_dir, "site-packages")
        os.chdir(self.code_dir)
        self._seed_examples(data_dir)

        self.editor = EditorScreen(data_dir, self.code_dir, self.storage_manager)
        self.runner_page = RunnerScreen(self.editor, lambda: self.switch("editor"))
        self.turtle_page = TurtleScreen(lambda: self.switch("editor"))
        self.editor.turtle_canvas = self.turtle_page.canvas_widget
        self.editor.turtle_terminal = self.turtle_page.terminal
        self.editor.show_runner = lambda: self.switch("runner")
        self.editor.show_turtle = lambda: self.switch("turtle")
        self.libs = LibsScreen(site_dir)
        self.qr = QRCodeScreen()
        self.three_d = ThreeDScreen()
        self.editor.show_3d = lambda: self.switch("3d")
        self.files = FilesScreen(self.code_dir, self._open_from_files, self.editor.forget)
        self.editor.on_saved = self.files.refresh
        self.settings_page = SettingsScreen(
            os.path.join(data_dir, "settings.json"), self.storage_manager,
            self._refresh_storage_location)

        self.sm = ScreenManager(transition=NoTransition())
        pages = (("editor", self.editor), ("runner", self.runner_page),
                 ("turtle", self.turtle_page), ("qr", self.qr),
                 ("libs", self.libs), ("files", self.files), ("3d", self.three_d),
                 ("settings", self.settings_page))
        for name, widget in pages:
            screen = Screen(name=name)
            screen.add_widget(widget)
            self.sm.add_widget(screen)

        # Üst panel: üç xətli hamburger düyməsi və açılıb-bağlanan naviqasiya.
        root = BoxLayout(orientation="vertical", spacing=0)
        self.topbar = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=dp(50),
            spacing=dp(8), padding=(dp(6), dp(4)))
        self.menu_btn = Btn(
            "☰", base=PANEL2, size_hint_x=None, width=dp(48),
            height=dp(42), font_size=dp(26))
        self.menu_btn.bind(on_release=lambda *_: self.toggle_navigation())
        self.topbar.add_widget(self.menu_btn)

        self.page_title = Label(
            text="PyCreator", color=TEXT, font_size=dp(16),
            halign="left", valign="middle")
        self.page_title.bind(size=lambda widget, _value:
                             setattr(widget, "text_size", widget.size))
        self.topbar.add_widget(self.page_title)

        body = BoxLayout(orientation="horizontal", spacing=dp(4))
        self.nav = BoxLayout(
            orientation="vertical",
            size_hint_x=None,
            width=0,
            opacity=0,
            disabled=True,
            spacing=dp(7),
            padding=(dp(5), dp(10), dp(5), dp(8)))
        self.drawer_open = False
        self.tab_buttons = {}
        nav_icons = {
            "editor": "‹›",
            "runner": ">_",
            "qr": "▦",
            "libs": "▤",
            "files": "▣",
            "3d": "◇",
            "settings": "⚙",
        }
        body.add_widget(self.nav)
        body.add_widget(self.sm)
        for name, _label in TABS:
            b = Btn(
                nav_icons[name],
                base=PANEL2,
                size_hint_x=1,
                height=dp(52),
                font_size=dp(24))
            if name == "runner":
                b.bind(on_release=lambda *_: self.open_runner())
            else:
                b.bind(on_release=lambda _w, n=name: self.switch(n))
            self.tab_buttons[name] = b
            self.nav.add_widget(b)
        self.nav.add_widget(BoxLayout())
        root.add_widget(self.topbar)
        root.add_widget(body)

        self.switch("editor")
        Window.bind(on_keyboard=self._on_back)
        Clock.schedule_interval(lambda _dt: self.editor.persist(), 20)
        return root

    def _legacy_code_dir(self, data_dir):
        try:
            from jnius import autoclass
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            ext = activity.getExternalFilesDir(None)
            if ext is not None:
                return os.path.join(ext.getAbsolutePath(), "kodlar")
        except Exception:
            pass
        return os.path.join(data_dir, "kodlar")

    def _refresh_storage_location(self):
        old_dir = self.code_dir
        new_dir, is_public = self.storage_manager.prepare(old_dir)
        self.code_dir = new_dir
        self.public_storage = is_public
        os.chdir(new_dir)
        self.editor.code_dir = new_dir
        self.files.code_dir = new_dir
        self.editor.persist()
        self.files.refresh()
        self.settings_page.refresh_storage()

    def _seed_examples(self, data_dir):
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
            with open(os.path.join(data_dir, ".seeded"), "w") as fh:
                fh.write("1")
        except OSError:
            pass

    def toggle_navigation(self):
        """Hamburger düyməsi ilə sol naviqasiya panelini açır və bağlayır."""
        if self.sm.current == "turtle":
            return
        self.drawer_open = not self.drawer_open
        if self.drawer_open:
            self.nav.width = min(max(dp(92), Window.width * 0.23), dp(128))
            self.nav.opacity = 1
            self.nav.disabled = False
            self.menu_btn.text = "×"
        else:
            self.nav.width = 0
            self.nav.opacity = 0
            self.nav.disabled = True
            self.menu_btn.text = "☰"

    def switch(self, name):
        self.sm.current = name
        if name == "editor":
            # Screen aktivləşdikdən sonra klaviaturanı bərpa et; keçid zamanı
            # Kivy-nin fokus/soft-keyboard vəziyyəti dəyişə bilər.
            Clock.schedule_once(
                lambda _dt: self.editor.restore_editor_keyboard(), 0.08)
        immersive = name == "turtle"

        # Səhifə seçildikdə drawer bağlanır; Turtle tam ekran rejimini saxlayır.
        self.drawer_open = False
        self.nav.width = 0
        self.nav.opacity = 0
        self.nav.disabled = True
        self.menu_btn.text = "☰"
        self.topbar.height = 0 if immersive else dp(50)
        self.topbar.opacity = 0 if immersive else 1
        self.topbar.disabled = immersive
        titles = dict(TABS)
        self.page_title.text = titles.get(name, "PyCreator")

        for tab, button in self.tab_buttons.items():
            button.base = ACCENT if tab == name else PANEL2
            button.background_color = button.base
        if name == "files":
            self.files.refresh()
            self.editor.persist()
        if name == "settings":
            self.settings_page.refresh_storage()

    def open_runner(self):
        """Runner ilk dəfə boş açılır; sonrakı keçidlərdə kod yenidən başladılır."""
        if self.editor.runner.running:
            self.switch("runner")
        elif self.editor.has_run_once:
            self.editor.run()
        else:
            self.switch("runner")

    def _open_from_files(self, name):
        if self.editor.open_file(name):
            self.switch("editor")

    def _on_back(self, _window, key, *_args):
        if key == 27 and self.drawer_open:
            self.toggle_navigation()
            return True
        if key == 27 and self.sm.current != "editor":
            self.switch("editor")
            return True
        return False

    def on_pause(self):
        self.editor.persist()
        return True

    def on_resume(self):
        if hasattr(self, "settings_page"):
            self._refresh_storage_location()

    def on_stop(self):
        self.editor.persist()


if __name__ == "__main__":
    PyCreatorApp().run()

"""PyCreator üçün başlanğıc paneli (Home/Dashboard)."""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from ui.theme import ACCENT, MUTED, Btn, make_label


class HomeScreen(BoxLayout):
    def __init__(self, on_editor=None, on_projects=None, on_packages=None,
                 on_settings=None, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(10),
                         padding=dp(16), **kwargs)
        self.add_widget(make_label("PyCreator", size=26, bold=True, height=46))
        self.add_widget(make_label(
            "Python kodlarını yaz, işə sal və layihələrini idarə et.",
            size=14, color=MUTED))
        for title, callback in (
            ("Redaktoru aç", on_editor), ("Layihələr", on_projects),
            ("Kitabxanalar", on_packages), ("Tənzimləmələr", on_settings)
        ):
            button=Btn(title, base=ACCENT if title=="Redaktoru aç" else None)
            if callback:
                button.bind(on_release=lambda _button, fn=callback: fn())
            self.add_widget(button)

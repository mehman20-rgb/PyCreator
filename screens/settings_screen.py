"""PyCreator parametrləri və layihə yaddaşı ekranı."""
import os
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner

from services.settings_manager import SettingsManager
from ui.theme import ACCENT, MUTED, Btn, make_label


class SettingsScreen(BoxLayout):
    def __init__(self, settings_path, storage_manager, on_storage_changed, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(10), padding=dp(14), **kwargs)
        self.settings = SettingsManager(settings_path)
        self.storage_manager = storage_manager
        self.on_storage_changed = on_storage_changed
        values = self.settings.load()
        self.add_widget(make_label("Tənzimləmələr", size=20, bold=True, height=40))
        self.add_widget(make_label("Görünüş", size=14, color=MUTED))
        self.theme_choice = Spinner(text=values.get("theme", "dark"),
            values=("dark", "light"), size_hint_y=None, height=dp(46))
        self.add_widget(self.theme_choice)
        self.add_widget(make_label("Redaktor şrift ölçüsü", size=14, color=MUTED))
        self.font_choice = Spinner(text=str(values.get("font_size", 14)),
            values=("12", "13", "14", "15", "16", "18", "20"),
            size_hint_y=None, height=dp(46))
        self.add_widget(self.font_choice)

        self.add_widget(make_label("Fayl saxlama", size=17, bold=True, height=dp(30)))
        self.storage_status = make_label("", size=12, color=MUTED)
        self.add_widget(self.storage_status)
        self.path_label = make_label("", size=11, color=MUTED)
        self.add_widget(self.path_label)
        access_btn = Btn("Telefon yaddaşına giriş icazəsi", base=ACCENT)
        access_btn.bind(on_release=lambda *_: self.request_storage_access())
        self.add_widget(access_btn)
        refresh_btn = Btn("Yaddaş qovluğunu yenilə")
        refresh_btn.bind(on_release=lambda *_: self.refresh_storage())
        self.add_widget(refresh_btn)

        save = Btn("Yadda saxla", base=ACCENT)
        save.bind(on_release=lambda *_: self.save())
        self.add_widget(save)
        self.refresh_storage()

    def refresh_storage(self):
        allowed = self.storage_manager.has_access()
        public_path = self.storage_manager.public_projects_dir()
        self.storage_status.text = ("İcazə aktivdir — telefon yaddaşında saxlanılır."
            if allowed else "İcazə yoxdur — hazırda tətbiqin daxili yaddaşından istifadə edilir.")
        self.path_label.text = "Hədəf: %s" % (public_path or "Android yaddaşı əlçatan deyil")

    def request_storage_access(self):
        if not self.storage_manager.request_access():
            self.storage_status.text = "İcazə səhifəsi açıla bilmədi. Android ayarlarından PyCreator üçün fayl girişini aktiv et."
        else:
            self.storage_status.text = "Açılan Android səhifəsində PyCreator üçün bütün fayllara giriş icazəsini aktiv et, sonra geri qayıt."
        from kivy.clock import Clock
        Clock.schedule_once(lambda _dt: self.refresh_storage(), 1.0)

    def save(self):
        self.settings.update({"theme": self.theme_choice.text,
                              "font_size": int(self.font_choice.text)})
        self.refresh_storage()

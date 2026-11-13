"""PyCreator parametrlərinin sadə idarəetmə ekranı."""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner

from services.settings_manager import SettingsManager
from ui.theme import ACCENT, MUTED, Btn, make_label


class SettingsScreen(BoxLayout):
    def __init__(self, settings_path, **kwargs):
        super().__init__(orientation="vertical",spacing=dp(10),padding=dp(14),**kwargs)
        self.settings=SettingsManager(settings_path)
        values=self.settings.load()
        self.add_widget(make_label("Tənzimləmələr",size=20,bold=True,height=40))
        self.add_widget(make_label("Görünüş",size=14,color=MUTED))
        self.theme_choice=Spinner(text=values.get("theme","dark"),
            values=("dark","light"),size_hint_y=None,height=dp(46))
        self.add_widget(self.theme_choice)
        self.add_widget(make_label("Redaktor şrift ölçüsü",size=14,color=MUTED))
        self.font_choice=Spinner(text=str(values.get("font_size",14)),
            values=("12","13","14","15","16","18","20"),size_hint_y=None,height=dp(46))
        self.add_widget(self.font_choice)
        save=Btn("Yadda saxla",base=ACCENT)
        save.bind(on_release=lambda *_: self.save())
        self.add_widget(save)

    def save(self):
        self.settings.update({"theme":self.theme_choice.text,
                              "font_size":int(self.font_choice.text)})

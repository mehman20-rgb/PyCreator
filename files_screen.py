"""Fayllar ekranı: saxlanmış proqramların siyahısı, aç və sil."""
import os

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView

import dialogs
from theme import ACCENT, MUTED, RED, Btn, make_label


class FilesScreen(BoxLayout):
    def __init__(self, code_dir, on_open, on_deleted, **kw):
        super().__init__(orientation="vertical", spacing=dp(8), padding=(dp(8), dp(6)), **kw)
        self.code_dir = code_dir
        self.on_open = on_open
        self.on_deleted = on_deleted
        self.add_widget(make_label("Proqramlarım", size=17, bold=True, height=30))
        self.add_widget(make_label("Qovluq: %s" % code_dir, size=11, color=MUTED))
        scroll = ScrollView()
        self.listing = GridLayout(cols=1, spacing=dp(4), size_hint_y=None)
        self.listing.bind(minimum_height=self.listing.setter("height"))
        scroll.add_widget(self.listing)
        self.add_widget(scroll)
        self.refresh()

    def _files(self):
        try:
            names = [n for n in os.listdir(self.code_dir)
                     if not n.startswith(".") and os.path.isfile(os.path.join(self.code_dir, n))]
        except OSError:
            names = []
        return sorted(names, key=str.lower)

    def refresh(self):
        self.listing.clear_widgets()
        names = self._files()
        if not names:
            self.listing.add_widget(make_label(
                "Hələ fayl yoxdur. Redaktorda kod yazıb Saxla düyməsinə bas.",
                size=14, color=MUTED))
            return
        for name in names:
            size = os.path.getsize(os.path.join(self.code_dir, name))
            row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(6))
            row.add_widget(make_label("%s\n%.1f KB" % (name, size / 1024.0), size=14, height=50))
            open_btn = Btn("Aç", base=ACCENT, size_hint_x=None, width=dp(72), height=dp(44))
            del_btn = Btn("Sil", base=RED, size_hint_x=None, width=dp(72), height=dp(44))
            open_btn.bind(on_release=lambda _w, n=name: self.on_open(n))
            del_btn.bind(on_release=lambda _w, n=name: self._ask_delete(n))
            row.add_widget(open_btn)
            row.add_widget(del_btn)
            self.listing.add_widget(row)

    def _ask_delete(self, name):
        dialogs.confirm("Silinsin?", "'%s' faylı həmişəlik silinəcək." % name,
                        lambda: self._delete(name), yes_text="Sil", danger=True)

    def _delete(self, name):
        try:
            os.remove(os.path.join(self.code_dir, name))
        except OSError:
            dialogs.info("Xəta", "Fayl silinə bilmədi.")
            return
        self.on_deleted(name)
        self.refresh()

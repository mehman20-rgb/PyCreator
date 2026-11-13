"""QR Code generator: qrcode kitabxanası ilə kod yaradır və ekranda göstərir."""
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from ui.theme import ACCENT, GREEN, MONO, MUTED, PANEL, PANEL2, TEXT, Btn, make_label

try:
    import qrcode
except Exception:
    qrcode = None


class QRPreview(Widget):
    """QR matrisini Kivy canvas üzərində çəkir; Pillow tələb etmir."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.matrix = None
        self.bind(pos=self.redraw, size=self.redraw)

    def set_matrix(self, matrix):
        self.matrix = matrix
        self.redraw()

    def redraw(self, *_args):
        self.canvas.clear()
        if not self.matrix:
            return
        rows = len(self.matrix)
        cols = len(self.matrix[0]) if rows else 0
        if not rows or not cols:
            return
        side = min(self.width, self.height)
        cell = side / max(rows, cols)
        x0 = self.x + (self.width - cell * cols) / 2
        y0 = self.y + (self.height - cell * rows) / 2
        with self.canvas:
            Color(1, 1, 1, 1)
            Rectangle(pos=(x0, y0), size=(cell * cols, cell * rows))
            Color(0, 0, 0, 1)
            for row, values in enumerate(self.matrix):
                for col, dark in enumerate(values):
                    if dark:
                        Rectangle(
                            pos=(x0 + col * cell, y0 + (rows - row - 1) * cell),
                            size=(cell + 0.02, cell + 0.02),
                        )


class QRCodeScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(8),
                         padding=(dp(12), dp(10)), **kwargs)
        self.add_widget(make_label(
            "Mətn, link və ya Wi-Fi məlumatını QR koda çevir.",
            size=14, color=MUTED))
        self.field = TextInput(
            hint_text="Mətni və ya linki bura yaz...",
            multiline=True, size_hint_y=None, height=dp(104),
            font_size=sp(15), foreground_color=TEXT,
            background_color=PANEL, cursor_color=ACCENT,
        )
        self.add_widget(self.field)
        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        generate = Btn("QR yarat", base=GREEN)
        clear = Btn("Təmizlə", base=PANEL2)
        generate.bind(on_release=lambda *_: self.generate())
        clear.bind(on_release=lambda *_: self.clear())
        actions.add_widget(generate)
        actions.add_widget(clear)
        self.add_widget(actions)
        self.preview = QRPreview(size_hint_y=1)
        self.add_widget(self.preview)
        self.status = make_label("Hazırdır.", size=13, color=MUTED, height=dp(30))
        self.add_widget(self.status)

    def generate(self):
        value = self.field.text.strip()
        if not value:
            self.status.text = "Əvvəlcə mətn və ya link daxil et."
            return
        if qrcode is None:
            self.status.text = "QR modulu tapılmadı. Kitabxanalar bölməsindən qrcode quraşdır."
            return
        try:
            code = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=1,
                border=4,
            )
            code.add_data(value)
            code.make(fit=True)
            self.preview.set_matrix(code.get_matrix())
            self.status.text = "QR kod yaradıldı · %d simvol" % len(value)
        except Exception as err:
            self.status.text = "QR yaratmaq alınmadı: %s" % err

    def clear(self):
        self.field.text = ""
        self.preview.set_matrix(None)
        self.status.text = "Təmizləndi."

"""İlk açılışda qovluğa qoyulan nümunə proqramlar."""

EXAMPLES = {
    "salam.py": '''# Ən sadə proqram
ad = input("Adın nədir? ")
print("Salam,", ad + "!")

for i in range(1, 4):
    print("Sətir", i)
''',
    "hesablama.py": '''# Sadə kalkulyator: input() ilə rəqəm al
a = float(input("Birinci ədəd: "))
b = float(input("İkinci ədəd: "))

print("Cəm:", a + b)
print("Fərq:", a - b)
print("Hasil:", a * b)
if b != 0:
    print("Bölmə:", a / b)
''',
    "opencv_test.py": '''# OpenCV Android APK buildinə daxil edildikdən sonra işləyəcək
import cv2
import numpy as np

# Süni test şəkli yarat
image = np.zeros((240, 320, 3), dtype=np.uint8)
image[50:190, 80:240] = (255, 255, 255)

# Boz rəng və kənar aşkarlanması
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray, 50, 150)

print("OpenCV:", cv2.__version__)
print("Şəkil ölçüsü:", image.shape)
print("Boz şəkil:", gray.shape)
print("Kənar piksel sayı:", cv2.countNonZero(edges))
''',
    "matplotlib_test.py": '''# Matplotlib Android testi: Agg backend PNG faylı yaradır
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

x = [0, 1, 2, 3, 4]
y = [0, 1, 4, 9, 16]
fig, ax = plt.subplots()
ax.plot(x, y, marker="o")
ax.set_title("PyCreator - Matplotlib")
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.grid(True)
fig.savefig("qrafik.png", dpi=120)
plt.close(fig)
print("Matplotlib:", matplotlib.__version__)
print("Qrafik yaradıldı: qrafik.png")
''',
    "pygame_test.py": '''# Pygame Android test: ekran pəncərəsi açır
import pygame

pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("PyCreator - Pygame")
screen.fill((25, 35, 55))
pygame.draw.circle(screen, (0, 200, 255), (320, 240), 70)
pygame.display.flip()
print("Pygame versiyası:", pygame.version.ver)
print("Pəncərə yaradıldı.")
''',
    "beautifulsoup_test.py": '''# HTML mətnindən məlumat çıxarma
from bs4 import BeautifulSoup

html = "<html><body><h1>PyCreator</h1><p>Salam Python</p></body></html>"
soup = BeautifulSoup(html, "html.parser")
print("Başlıq:", soup.h1.text)
print("Mətn:", soup.p.text)
''',
    "sympy_test.py": '''# Simvolik riyaziyyat
import sympy as sp

x = sp.symbols("x")
expression = x**2 - 5*x + 6
print("İfadə:", expression)
print("Vuruqlara ayırma:", sp.factor(expression))
print("Köklər:", sp.solve(expression, x))
''',
    "rich_test.py": '''# Terminalda rəngli və formatlı çıxış
from rich import print
from rich.panel import Panel

print(Panel("[bold cyan]PyCreator[/bold cyan] kitabxana testi"))
print("[green]Rich uğurla işləyir![/green]")
''',
    "colorama_test.py": '''# Terminal rəngləri
from colorama import init, Fore, Style

init(autoreset=True)
print(Fore.GREEN + "Colorama işləyir!")
print(Fore.YELLOW + "Bu sarı mesajdır.")
print(Style.BRIGHT + "PyCreator")
''',
    "tabulate_test.py": '''# Məlumatları cədvəl formasında göstər
from tabulate import tabulate

rows = [["Python", "Proqramlaşdırma"], ["OpenCV", "Kompüter görməsi"], ["SymPy", "Riyaziyyat"]]
print(tabulate(rows, headers=["Modul", "İstifadə sahəsi"], tablefmt="grid"))
''',
    "sorgu_requests.py": '''# Bu nümunə üçün əvvəlcə "Kitabxanalar" bölməsindən requests quraşdır
import requests

cavab = requests.get("https://api.github.com")
print("Status:", cavab.status_code)
print(cavab.headers.get("content-type"))
''',
}

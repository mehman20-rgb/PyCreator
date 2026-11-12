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
    "sorgu_requests.py": '''# Bu nümunə üçün əvvəlcə "Kitabxanalar" bölməsindən requests quraşdır
import requests

cavab = requests.get("https://api.github.com")
print("Status:", cavab.status_code)
print(cavab.headers.get("content-type"))
''',
}

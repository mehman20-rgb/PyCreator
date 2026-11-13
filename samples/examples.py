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
    "sorgu_requests.py": '''# Bu nümunə üçün əvvəlcə "Kitabxanalar" bölməsindən requests quraşdır
import requests

cavab = requests.get("https://api.github.com")
print("Status:", cavab.status_code)
print(cavab.headers.get("content-type"))
''',
}

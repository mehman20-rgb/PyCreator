# PyCreator

PyCreator Android üçün Python IDE layihəsidir. Tətbiq Kivy ilə hazırlanır və Buildozer/GitHub Actions vasitəsilə APK kimi qurulur.

## Mövcud əsas imkanlar

- **Redaktor:** Python kodu yazmaq, sintaksis rənglənməsi, avtomatik indent, simvol sətri və faylı yadda saxlamaq.
- **Python icrası:** `print()`, `input()`, çıxışın tutulması və işləyən kodu dayandırmaq.
- **Kitabxanalar:** PyPI-dən saf Python (`py3-none-any`) wheel-lərinin quraşdırılması və silinməsi.
- **Fayllar:** kod fayllarını açmaq, yadda saxlamaq və silmək.
- **Nümunələr:** ilk açılışda başlanğıc Python faylları.

> Qeyd: `numpy`, `pandas`, `opencv` kimi native/C kitabxanalar runtime paket meneceri ilə quraşdırılmır. Bunlar Android üçün uyğun Buildozer/python-for-Android resepti və APK qurularkən tərtibat tələb edir.

## Repository arxitekturası

```text
PyCreator/
├── main.py
├── buildozer.spec
├── Assets/
├── app/
│   └── application.py
├── core/
│   └── runner.py
├── editor/
│   ├── editor_screen.py
│   ├── autocomplete.py
│   ├── snippets.py
│   └── diagnostics.py
├── files/
│   ├── files_screen.py
│   └── manager.py
├── packages/
│   ├── libs_screen.py
│   └── pkgman.py
├── ui/
│   ├── theme.py
│   ├── dialogs.py
│   ├── components.py
│   └── icons.py
├── samples/
├── screens/
│   ├── home_screen.py
│   ├── terminal_screen.py
│   └── settings_screen.py
├── projects/
│   └── project_manager.py
├── services/
│   └── settings_manager.py
└── .github/workflows/build-apk.yml
```

`main.py` Buildozer üçün kök giriş nöqtəsi olaraq saxlanılır; tətbiqin əsas sinfi `app/application.py` modulundadır. Paket qovluqlarındakı `__init__.py` faylları Python importlarını təmin edir.

## APK qurulması və Release

1. `main` budağına push etdikdə GitHub Actions debug APK yaradır.
2. Actions workflow run daxilində **PyCreator-apk** artifact-ını yükləmək mümkündür.
3. Versiya buraxılışı üçün `v1.0.0`, `v1.0.1`, `v1.1.0` kimi tag yaradılır. Tag push ediləndə GitHub Release açılır və APK faylları ora əlavə olunur.
4. Release APK-larının SHA-256 yoxlama məbləği `SHA256SUMS.txt` faylında saxlanılır.

Versiyalaşdırma:
- `1.0.x`: xəta düzəlişləri;
- `1.x.0`: yeni funksiyalar;
- `2.0.0`: böyük dəyişikliklər.

## Tətbiq ikonu

Sənin seçəcəyin ikon üçün standart yer:

`Assets/app_icon.png`

PNG ikonunu həmin adla əlavə etdikdən sonra GitHub Actions onu APK-ya avtomatik daxil edəcək. İkon hələ əlavə edilməyibsə, build prosesi dayanmır və standart ikonla davam edir. Tövsiyə olunan ölçü 512×512 px-dir.

## Şriftlər

`Assets/` qovluğunda DejaVu şriftləri saxlanılır. Android/Linux mühitində qovluq və fayl adlarının böyük-kiçik hərf registri dəqiq uyğun olmalıdır.

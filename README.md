# PyCreator

Telefonda Python kodu yazıb işlətmək və kitabxana quraşdırmaq üçün sadə tətbiq. Əmr sətri yoxdur, hər şey düymələrlə.

## APK-nı necə əldə etmək olar (pulsuz, kompüter lazım deyil)

1. https://github.com saytında pulsuz hesab aç və **New repository** ilə yeni layihə yarat (məsələn `PyCreator`).
2. Bu qovluqdakı **bütün faylları** (`.github` qovluğu daxil) layihəyə yüklə. Telefonda: **Add file → Upload files**. Qovluq strukturu saxlanmalıdır; ən asan yol zip-i kompüterdə açıb yükləməkdir.
3. **Actions** bölməsinə keç. Qurma `main` budağına yükləmədən sonra özü başlayır. Başlamasa: **APK qur → Run workflow**.
4. İlk qurma 20-40 dəqiqə çəkir (sonrakılar daha tez). Bitəndə qurmanı aç, aşağıda **Artifacts → PyCreator-apk** yüklə, zip-in içindən `.apk` faylını çıxar.
5. Telefonda APK-nı aç və "naməlum mənbələrdən quraşdırma" icazəsini ver.

## İstifadə

- **Redaktor**: kod yaz, **▶ İşlət** bas. `input()` işləyir, **■ Dayan** proqramı saxlayır. Alt sətirdəki düymələr `( ) [ ] { } : =` kimi simvolları və Tab-ı tez yazır.
- **Kitabxanalar**: adı yaz (məsələn `requests rich`) və **Quraşdır** bas. Asılılıqlar avtomatik gəlir.
- **Fayllar**: saxladığın proqramları aç və ya sil. İlk açılışda 3 nümunə hazır gəlir.

## Məhdudiyyət

Kitabxanalar PyPI-dən saf Python (`py3-none-any`) paket kimi yüklənir. Bu o deməkdir ki:

- `requests`, `rich`, `beautifulsoup4`, `tqdm`, `colorama` kimi saf Python kitabxanalar işləyir.
- `numpy`, `pandas`, `pillow` kimi C kodlu kitabxanalar bu üsulla quraşdırılmır (asılılığında C kodu olan paketlər də, məsələn `flask`). Tətbiq bunu səbəbi ilə birlikdə göstərir. Belə kitabxanalar üçün onları APK qurulanda `buildozer.spec` faylındakı `requirements` sətrinə əlavə etmək lazımdır.

## Fayllar

- `main.py`: tətbiq və naviqasiya
- `editor_screen.py`, `libs_screen.py`, `files_screen.py`: üç ekran
- `runner.py`: kodu işlədir, `pkgman.py`: kitabxana meneceri
- `tests/`: kompüterdə işlədilə bilən testlər (`python tests/test_pkgman.py`)

Şriftlər: DejaVu (pulsuz lisenziya), Azərbaycan hərfləri düzgün göstərilsin deyə daxil edilib.

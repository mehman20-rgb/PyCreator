[app]
title = PyCreator
package.name = pycreator
package.domain = org.pycreator
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
source.exclude_dirs = tests,.github,bin,.buildozer
version = 1.0.0
# İkon seçildikdən sonra Assets/app_icon.png adı ilə əlavə et.
# GitHub Actions həmin fayl olduqda icon.filename parametrini avtomatik aktivləşdirir.

# pygments rəngləmə, certifi HTTPS yoxlaması üçün lazımdır
requirements = python3,kivy==2.3.2,pygments,certifi,qrcode,numpy,opencv,charset_normalizer,requests,beautifulsoup4,sympy,rich,colorama,tabulate,pygame,matplotlib
# python-for-android develop: #3360-dan sonrakı pip/venv düzəlişləri daxildir.
# Buildozer bu dəyəri git clone -b üçün istifadə etdiyindən branch adı olmalıdır.
p4a.branch = develop
# Kivy və Pygame eyni SDL2 bootstrap üzərində yığılır.
p4a.bootstrap = sdl2
p4a.local_recipes = ./p4a-recipes
orientation = portrait
fullscreen = 0

# İstifadəçi faylları üçün geniş yaddaş icazəsi deyil, SAF qovluq icazəsi alınır.
android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1

[app]
title = PyCreator
package.name = pycreator
package.domain = org.pycreator
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
source.exclude_dirs = tests,.github,bin,.buildozer
version = 1.0.0

# pygments rəngləmə üçün, certifi HTTPS yoxlaması üçün lazımdır
requirements = python3,kivy==2.3.2,pygments,certifi
p4a.branch = develop
orientation = portrait
fullscreen = 0

android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1

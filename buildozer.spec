[app]
title = Poker House Timer
package.name = pokerhouse
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,mp3,ttf

version = 1.0

# Python 3.12.8 — последняя версия, совместимая с Kivy 2.3.0
# hostpython3 — той же версии, обязательно
requirements = python3==3.12.8,hostpython3==3.12.8,kivy==2.3.0

# Отключаем проблемный модуль grp для Android
android.extra_patches = patches/grp_fix.patch

orientation = landscape
fullscreen = 1

android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1

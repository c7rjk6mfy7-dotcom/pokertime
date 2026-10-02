[app]
title = Poker House Timer
package.name = pokerhouse
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,mp3,ttf

version = 1.0

# Kivy 2.3.0 — стабильная, требует Python 3.11 или 3.12
requirements = python3,kivy==2.3.0

orientation = landscape
fullscreen = 1

android.api = 31
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# Ключевое: NDK 25c — проверенная версия для Kivy
android.ndk = 25c

# Использовать стабильную ветку p4a (релиз, а не develop)
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1

[app]
title = Poker House Timer
package.name = pokerhouse
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,mp3,ttf

version = 1.0

requirements = python3==3.12.8,hostpython3==3.12.8,kivy==2.3.0

orientation = landscape
fullscreen = 1

android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
android.accept_sdk_license = True
android.entrypoint = org.kivy.android.PythonActivity
# Отключаем проблемные модули для сборки на Android (они не нужны для Kivy)
p4a.hostpython3.extra_config_args = --without-grp

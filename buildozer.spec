[app]
title = Poker House Timer
package.name = pokerhouse
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,mp3,ttf

version = 1.0

requirements = python3==3.11.5,kivy==2.3.0

orientation = landscape
fullscreen = 1

android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
# android.p4a_whitelist = ...
# p4a.branch = ...
# p4a.source_dir = ...
[buildozer]
log_level = 2
warn_on_root = 1
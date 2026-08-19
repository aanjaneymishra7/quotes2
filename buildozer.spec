[app]
title = Quote of the Day
package.name = quoteoftheday
package.domain = org.quotesapp

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,txt
source.include_patterns = data/*.json,assets/fonts/*/*.ttf,assets/fonts/*/OFL.txt

version = 1.0.0

requirements = python3,kivy==2.3.1,kivymd==1.2.0,anthropic,certifi,requests,idna,urllib3,charset_normalizer,sniffio,httpx,httpcore,h11,anyio,distro,jiter,typing_extensions

orientation = portrait
fullscreen = 0

# Icon/presplash: drop your own icon.png (512x512) and presplash.png in the
# project root and uncomment these two lines to use them.
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

android.permissions = INTERNET
android.api = 34
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1

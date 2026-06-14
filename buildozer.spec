[app]

# App metadata
title = YouTube Downloader
package.name = youtubedownloader
package.domain = org.kivyapp

# Source
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Version
version = 1.0

# Requirements - Adding openssl, sqlite3, and certifi which are needed by yt-dlp
requirements = python3,kivy==2.3.0,openssl,sqlite3,certifi,yt-dlp

# Android settings
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.arch = arm64-v8a

# App orientation
orientation = portrait

# Fullscreen
fullscreen = 0

# Android features
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1

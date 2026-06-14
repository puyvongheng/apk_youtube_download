"""
YouTube Downloader - Kivy App
Works on Android via yt-dlp
"""

import os
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.widget import Widget

# Android-specific storage path
try:
    from android.storage import primary_external_storage_path
    DOWNLOAD_DIR = os.path.join(primary_external_storage_path(), 'Download', 'YouTubeDownloader')
except ImportError:
    # Desktop fallback
    DOWNLOAD_DIR = os.path.join(os.path.expanduser('~'), 'Downloads', 'YouTubeDownloader')

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class RoundedButton(Button):
    pass


class YouTubeDownloaderLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=20, spacing=15, **kwargs)
        self._status_text = ""
        self._progress_value = 0
        self._is_downloading = False
        self._build_ui()

    def _build_ui(self):
        with self.canvas.before:
            Color(0.07, 0.07, 0.12, 1)
            self._bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        # ── Title ──
        title = Label(
            text='[b][color=ff4444]You[/color][color=ffffff]Tube[/color] [color=aaaaff]Downloader[/color][/b]',
            markup=True,
            font_size='26sp',
            size_hint_y=None,
            height=60,
        )
        self.add_widget(title)

        # ── Subtitle ──
        sub = Label(
            text='Powered by yt-dlp',
            font_size='13sp',
            color=(0.5, 0.5, 0.7, 1),
            size_hint_y=None,
            height=28,
        )
        self.add_widget(sub)

        # ── Divider ──
        self.add_widget(Widget(size_hint_y=None, height=1))

        # ── URL Input ──
        url_label = Label(
            text='YouTube URL',
            font_size='14sp',
            color=(0.7, 0.7, 0.9, 1),
            size_hint_y=None,
            height=30,
            halign='left',
            text_size=(None, None),
        )
        self.add_widget(url_label)

        self.url_input = TextInput(
            hint_text='https://www.youtube.com/watch?v=...',
            multiline=False,
            size_hint_y=None,
            height=48,
            background_color=(0.13, 0.13, 0.22, 1),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.4, 0.4, 0.6, 1),
            cursor_color=(0.6, 0.4, 1, 1),
            padding=[12, 12],
            font_size='14sp',
        )
        self.add_widget(self.url_input)

        # ── Format Selector ──
        fmt_label = Label(
            text='Format',
            font_size='14sp',
            color=(0.7, 0.7, 0.9, 1),
            size_hint_y=None,
            height=30,
            halign='left',
        )
        self.add_widget(fmt_label)

        self.format_spinner = Spinner(
            text='MP4 Video (best quality)',
            values=[
                'MP4 Video (best quality)',
                'MP4 Video (720p)',
                'MP4 Video (480p)',
                'MP4 Video (360p)',
                'MP3 Audio only',
                'M4A Audio only',
            ],
            size_hint_y=None,
            height=46,
            background_color=(0.2, 0.1, 0.4, 1),
            color=(1, 1, 1, 1),
            font_size='14sp',
        )
        self.add_widget(self.format_spinner)

        # ── Download Button ──
        self.download_btn = Button(
            text='⬇  Download',
            size_hint_y=None,
            height=52,
            background_color=(0.5, 0.1, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True,
        )
        self.download_btn.bind(on_press=self.start_download)
        self.add_widget(self.download_btn)

        # ── Progress Bar ──
        self.progress = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=18,
        )
        self.add_widget(self.progress)

        # ── Status Log ──
        status_label = Label(
            text='Status Log',
            font_size='13sp',
            color=(0.6, 0.6, 0.8, 1),
            size_hint_y=None,
            height=26,
            halign='left',
        )
        self.add_widget(status_label)

        scroll = ScrollView(size_hint=(1, 1))
        self.status_box = Label(
            text='Ready. Paste a YouTube URL and press Download.',
            color=(0.7, 0.9, 0.7, 1),
            font_size='13sp',
            size_hint_y=None,
            valign='top',
            halign='left',
            markup=True,
        )
        self.status_box.bind(texture_size=self.status_box.setter('size'))
        scroll.add_widget(self.status_box)
        self.add_widget(scroll)

        # ── Save Path ──
        path_label = Label(
            text=f'Save to: {DOWNLOAD_DIR}',
            font_size='11sp',
            color=(0.4, 0.4, 0.6, 1),
            size_hint_y=None,
            height=30,
            halign='left',
            text_size=(Window.width - 40, None),
        )
        self.add_widget(path_label)

    def _update_bg(self, *args):
        self._bg_rect.size = self.size
        self._bg_rect.pos = self.pos

    def _get_ydl_opts(self):
        fmt = self.format_spinner.text
        if 'MP3' in fmt:
            return {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [self._progress_hook],
                'quiet': True,
                'no_warnings': True,
            }
        elif 'M4A' in fmt:
            return {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                'progress_hooks': [self._progress_hook],
                'quiet': True,
                'no_warnings': True,
            }
        else:
            height_map = {
                'MP4 Video (720p)': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]',
                'MP4 Video (480p)': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]',
                'MP4 Video (360p)': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]',
                'MP4 Video (best quality)': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            }
            return {
                'format': height_map.get(fmt, 'best'),
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'progress_hooks': [self._progress_hook],
                'quiet': True,
                'no_warnings': True,
            }

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0) or 0
            if total > 0:
                pct = downloaded / total * 100
                speed_mb = speed / 1024 / 1024
                msg = f'Downloading... {pct:.1f}%  ({speed_mb:.2f} MB/s)'
                Clock.schedule_once(lambda dt: self._set_status(msg), 0)
                Clock.schedule_once(lambda dt: self._set_progress(pct), 0)
        elif d['status'] == 'finished':
            Clock.schedule_once(lambda dt: self._set_status('✅ Processing file...'), 0)

    def _set_status(self, text):
        self._status_text = self._status_text + '\n' + text if self._status_text else text
        self.status_box.text = self._status_text

    def _set_progress(self, val):
        self.progress.value = val

    def start_download(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self._set_status('[color=ff6666]⚠ Please enter a YouTube URL.[/color]')
            return
        if self._is_downloading:
            self._set_status('[color=ffaa44]⚠ A download is already in progress.[/color]')
            return
        self._is_downloading = True
        self._status_text = ''
        self.progress.value = 0
        self.download_btn.disabled = True
        self.download_btn.text = '⏳ Downloading...'
        self._set_status(f'Starting download...\nURL: {url}')
        t = threading.Thread(target=self._download_thread, args=(url,), daemon=True)
        t.start()

    def _download_thread(self, url):
        try:
            import yt_dlp
            opts = self._get_ydl_opts()
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown')
                Clock.schedule_once(lambda dt: self._on_success(title), 0)
        except Exception as e:
            err = str(e)
            Clock.schedule_once(lambda dt: self._on_error(err), 0)

    def _on_success(self, title):
        self._set_status(f'[color=44ff88]✅ Done! Saved: {title}[/color]')
        self._set_progress(100)
        self.download_btn.disabled = False
        self.download_btn.text = '⬇  Download'
        self._is_downloading = False

    def _on_error(self, err):
        self._set_status(f'[color=ff4444]❌ Error: {err}[/color]')
        self.download_btn.disabled = False
        self.download_btn.text = '⬇  Download'
        self._is_downloading = False


class YouTubeDownloaderApp(App):
    def build(self):
        self.title = 'YouTube Downloader'
        Window.clearcolor = (0.07, 0.07, 0.12, 1)
        return YouTubeDownloaderLayout()


if __name__ == '__main__':
    YouTubeDownloaderApp().run()

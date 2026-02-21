import os
import sys
import threading
import io
import requests
from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import yt_dlp

# ---------------- UI ----------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------------- utils ----------------
def seconds_to_hhmmss(sec):
    try:
        from datetime import timedelta
        return str(timedelta(seconds=int(sec)))
    except:
        return "—"

# ---------------- ffmpeg path ----------------
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

FFMPEG_PATH = os.path.join(BASE_PATH, "FFmpeg", "ffmpeg.exe")

if not os.path.exists(FFMPEG_PATH):
    messagebox.showerror("Ошибка", "FFmpeg не найден в папке FFmpeg")
    sys.exit(1)

# ---------------- app ----------------
class YouTubeDownloaderPro(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader Pro")
        self.geometry("900x580")
        self.minsize(700, 480)
        self.resizable(True, True)

        self.folder_path = os.getcwd()
        self.info = None
        self.thumb_image = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ---------- TOP ----------
        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top, text="Ссылка:").grid(row=0, column=0, padx=6)

        self.url_entry = ctk.CTkEntry(top)
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=6)

        self.bind_all("<Control-v>", self.ctrl_v)
        self.bind_all("<Control-V>", self.ctrl_v)


        self.check_btn = ctk.CTkButton(
            top, text="🔍", width=42, command=self.start_check
        )
        self.check_btn.grid(row=0, column=2, padx=4)

        # ---------- MID ----------
        mid = ctk.CTkFrame(self)
        mid.grid(row=1, column=0, sticky="ew", padx=10)
        mid.grid_columnconfigure(2, weight=1)

        self.thumb_label = ctk.CTkLabel(mid, text="Миниатюра", width=260, height=160)
        self.thumb_label.grid(row=0, column=0, rowspan=4, padx=8)

        ctk.CTkLabel(mid, text="Название:").grid(row=0, column=1, sticky="nw")
        self.title_label = ctk.CTkLabel(mid, text="", wraplength=520, justify="left")
        self.title_label.grid(row=0, column=2, sticky="w")

        ctk.CTkLabel(mid, text="Длительность:").grid(row=1, column=1, sticky="w")
        self.duration_label = ctk.CTkLabel(mid, text="—")
        self.duration_label.grid(row=1, column=2, sticky="w")

        ctk.CTkLabel(mid, text="Качество:").grid(row=2, column=1, sticky="w")
        self.quality_var = ctk.StringVar(value="best")
        self.quality_menu = ctk.CTkOptionMenu(mid, variable=self.quality_var, values=["best"])
        self.quality_menu.grid(row=2, column=2, sticky="w")

        # ---------- BOTTOM ----------
        bot = ctk.CTkFrame(self)
        bot.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        bot.grid_columnconfigure(1, weight=1)

        self.folder_btn = ctk.CTkButton(bot, text="📁 Папка", command=self.select_folder)
        self.folder_btn.grid(row=0, column=0, padx=6)

        self.folder_label = ctk.CTkLabel(bot, text=self.folder_path)
        self.folder_label.grid(row=0, column=1, sticky="w")

        self.save_type_var = ctk.StringVar(value="MP4")
        self.save_menu = ctk.CTkOptionMenu(bot, variable=self.save_type_var, values=["MP4", "MP3"])
        self.save_menu.grid(row=1, column=0, padx=6, pady=6)

        self.download_btn = ctk.CTkButton(bot, text="⬇ Скачать", command=self.start_download)
        self.download_btn.grid(row=1, column=1, sticky="w")

        self.progress = ctk.CTkProgressBar(bot)
        self.progress.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)

        self.status_label = ctk.CTkLabel(bot, text="")
        self.status_label.grid(row=3, column=0, columnspan=2, sticky="w")

    # ---------- events ----------
    def ctrl_v(self, event=None):
        try:
            text = self.clipboard_get()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, text)
        except:
            pass
        return "break"


    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path = folder
            self.folder_label.configure(text=folder)

    # ---------- metadata ----------
    def start_check(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Ошибка", "Введите ссылку")
            return

        self.check_btn.configure(state="disabled")
        self.status_label.configure(text="Получение информации...")

        threading.Thread(target=self.fetch_metadata, args=(url,), daemon=True).start()

    def fetch_metadata(self, url):
        try:
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'ffmpeg_location': FFMPEG_PATH
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
            self.after(0, lambda: self.check_btn.configure(state="normal"))
            return

        self.info = info

        formats = info.get("formats", [])
        qualities = sorted(
        {
            str(f["height"])
            for f in formats
            if isinstance(f.get("height"), int) and f["height"] >= 144
        },
        key=int
    )
        def ui():
            self.title_label.configure(text=info.get("title", ""))
            self.duration_label.configure(text=seconds_to_hhmmss(info.get("duration")))
            self.quality_menu.configure(values=["best"] + qualities + ["audio"])
            self.quality_var.set("best")
            self.status_label.configure(text="Готово")
            self.check_btn.configure(state="normal")

            if info.get("thumbnail"):
                r = requests.get(info["thumbnail"], timeout=10)
                img = Image.open(io.BytesIO(r.content))
                img.thumbnail((260, 160))
                self.thumb_image = ImageTk.PhotoImage(img)
                self.thumb_label.configure(image=self.thumb_image, text="")

        self.after(0, ui)

    # ---------- download ----------
    def start_download(self):
        if not self.info:
            messagebox.showwarning("Ошибка", "Сначала нажмите Проверить")
            return

        threading.Thread(target=self.download_thread, daemon=True).start()

    def download_thread(self):
        url = self.url_entry.get()
        q = self.quality_var.get()
        mode = self.save_type_var.get()

        suffix = f"[{q}p]" if q.isdigit() else "[audio]"
        out = os.path.join(self.folder_path, f"%(title)s {suffix}.%(ext)s")

        ydl_opts = {
            'outtmpl': out,
            'progress_hooks': [self.progress_hook],
            'merge_output_format': 'mp4',
            'ffmpeg_location': FFMPEG_PATH,
            'noplaylist': True
        }

        if mode == "MP3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]
            })
        else:
            if q == "best":
                ydl_opts['format'] = 'bv*+ba/best'
            elif q == "audio":
                ydl_opts['format'] = 'bestaudio/best'
            else:
                ydl_opts['format'] = f'bv*[height<={q}]+ba/best'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Ошибка", str(e)))

        self.after(0, lambda: self.status_label.configure(text="Готово"))
        self.after(0, lambda: self.download_btn.configure(state="normal"))

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            if d.get('total_bytes'):
                self.progress.set(d['downloaded_bytes'] / d['total_bytes'])
        elif d['status'] == 'finished':
            self.progress.set(1)

# ---------- run ----------
if __name__ == "__main__":
    app = YouTubeDownloaderPro()
    app.mainloop()

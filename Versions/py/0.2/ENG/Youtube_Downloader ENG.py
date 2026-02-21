import os
import threading
import io
import requests
from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import yt_dlp
import pyperclip

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def seconds_to_hhmmss(sec):
    try:
        from datetime import timedelta
        return str(timedelta(seconds=int(sec)))
    except:
        return "—"


class YouTubeDownloaderPro(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader Pro")
        self.geometry("820x550")
        self.resizable(False, False)

        self.folder_path = os.getcwd()
        self.info = None
        self.thumb_image = None

        # ---------- TOP ----------
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(top, text="YouTube URL:").grid(row=0, column=0, padx=6)
        self.url_entry = ctk.CTkEntry(top, width=560)
        self.url_entry.grid(row=0, column=1, padx=6)

        paste = ctk.CTkButton(top, text="📋 Paste", command=self.paste_url)
        paste.grid(row=1, column=1, sticky="w", padx=6, pady=4)

        self.check_btn = ctk.CTkButton(top, text="🔍 Check", command=self.start_check)
        self.check_btn.grid(row=0, column=2, padx=6)

        # ---------- MID ----------
        mid = ctk.CTkFrame(self)
        mid.pack(fill="x", padx=12, pady=6)

        self.thumb_label = ctk.CTkLabel(mid, text="Thumbnail", width=260, height=160)
        self.thumb_label.grid(row=0, column=0, rowspan=4, padx=8)

        ctk.CTkLabel(mid, text="Title:").grid(row=0, column=1, sticky="w")
        self.title_label = ctk.CTkLabel(mid, text="", wraplength=480)
        self.title_label.grid(row=0, column=2, sticky="w")

        ctk.CTkLabel(mid, text="Duration:").grid(row=1, column=1, sticky="w")
        self.duration_label = ctk.CTkLabel(mid, text="—")
        self.duration_label.grid(row=1, column=2, sticky="w")

        ctk.CTkLabel(mid, text="Quality:").grid(row=2, column=1, sticky="w")
        self.quality_var = ctk.StringVar(value="best")
        self.quality_menu = ctk.CTkOptionMenu(
            mid,
            variable=self.quality_var,
            values=["best"],
            width=200
        )
        self.quality_menu.grid(row=2, column=2, sticky="w")

        # ---------- BOTTOM ----------
        bot = ctk.CTkFrame(self)
        bot.pack(fill="both", expand=True, padx=12, pady=10)

        self.folder_btn = ctk.CTkButton(bot, text="📁 Select folder", command=self.select_folder)
        self.folder_btn.grid(row=0, column=0, padx=6)

        self.folder_label = ctk.CTkLabel(bot, text=self.folder_path)
        self.folder_label.grid(row=0, column=1, sticky="w")

        self.save_type_var = ctk.StringVar(value="MP4")
        self.save_menu = ctk.CTkOptionMenu(
            bot,
            variable=self.save_type_var,
            values=["MP4", "MP3"]
        )
        self.save_menu.grid(row=1, column=0, padx=6, pady=6)

        self.download_btn = ctk.CTkButton(bot, text="⬇ Download", command=self.start_download)
        self.download_btn.grid(row=1, column=1, sticky="w")

        self.progress = ctk.CTkProgressBar(bot, width=600)
        self.progress.grid(row=2, column=0, columnspan=3, pady=10)

        self.status_label = ctk.CTkLabel(bot, text="")
        self.status_label.grid(row=3, column=0, columnspan=3, sticky="w")

    # ---------- UTILS ----------
    def paste_url(self):
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, pyperclip.paste())

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path = folder
            self.folder_label.configure(text=folder)

    # ---------- CHECK ----------
    def start_check(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Error", "Enter URL")
            return

        self.check_btn.configure(state="disabled")
        self.status_label.configure(text="Loading info...")

        threading.Thread(target=self.fetch_metadata, args=(url,), daemon=True).start()

    def fetch_metadata(self, url):
        try:
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, lambda: self.check_btn.configure(state="normal"))
            return

        self.info = info
        formats = info.get("formats", [])

        qualities = sorted(
            {str(f.get("height")) for f in formats if f.get("height")},
            key=lambda x: int(x)
        )

        def ui():
            self.title_label.configure(text=info.get("title", ""))
            self.duration_label.configure(text=seconds_to_hhmmss(info.get("duration")))
            self.quality_menu.configure(values=["best"] + qualities + ["audio only"])
            self.quality_var.set("best")
            self.status_label.configure(text="Ready")
            self.check_btn.configure(state="normal")

            if info.get("thumbnail"):
                try:
                    r = requests.get(info["thumbnail"], timeout=10)
                    img = Image.open(io.BytesIO(r.content))
                    img.thumbnail((260, 160))
                    self.thumb_image = ImageTk.PhotoImage(img)
                    self.thumb_label.configure(image=self.thumb_image, text="")
                except:
                    pass

        self.after(0, ui)

    # ---------- DOWNLOAD ----------
    def start_download(self):
        if not self.info:
            messagebox.showwarning("Error", "Check video first")
            return

        threading.Thread(target=self.download_thread, daemon=True).start()

    def download_thread(self):
        url = self.url_entry.get().strip()
        q = self.quality_var.get()
        mode = self.save_type_var.get()

        self.progress.set(0)
        self.download_btn.configure(state="disabled")
        self.status_label.configure(text="Downloading...")

        try:
            ydl_opts = {
                'outtmpl': os.path.join(self.folder_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                'noplaylist': True,
                'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None
            }

            if mode == "MP3":
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3'
                    }]
                })
            else:
                if q == "audio only":
                    ydl_opts['format'] = 'bestaudio/best'
                elif q == "best":
                    ydl_opts['format'] = 'bv*+ba/best'
                else:
                    ydl_opts['format'] = f'bv*[height<={q}]+ba/best'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))

        self.after(0, lambda: self.download_btn.configure(state="normal"))
        self.after(0, lambda: self.status_label.configure(text="Done"))

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                p = float(d['_percent_str'].replace('%', '')) / 100
                self.progress.set(p)
            except:
                pass
        elif d['status'] == 'finished':
            self.progress.set(1)


if __name__ == "__main__":
    app = YouTubeDownloaderPro()
    app.mainloop()

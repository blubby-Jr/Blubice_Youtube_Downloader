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

def seconds_to_hhmmss(s):
    try:
        from datetime import timedelta
        return str(timedelta(seconds=int(s)))
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

        # ---------- Top Frame ----------
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=12, pady=(12,6))

        ctk.CTkLabel(top_frame, text="YouTube URL:", font=("Segoe UI", 14)).grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.url_entry = ctk.CTkEntry(top_frame, width=560)
        self.url_entry.grid(row=0, column=1, padx=6, pady=4)

        # --- Вставка URL ---
        self.url_entry.bind("<Control-v>", lambda e: self.url_entry.event_generate('<<Paste>>'))
        self.url_entry.bind("<Control-V>", lambda e: self.url_entry.event_generate('<<Paste>>'))
        self.url_entry.bind("<Button-3>", lambda e: self.url_entry.event_generate('<<Paste>>'))

        paste_btn = ctk.CTkButton(top_frame, text="📋 Вставить ссылку", command=self.paste_url)
        paste_btn.grid(row=1, column=1, padx=6, pady=4, sticky="w")

        self.check_btn = ctk.CTkButton(top_frame, text="🔍 Проверить", command=self.start_check)
        self.check_btn.grid(row=0, column=2, padx=6, pady=4)

        # ---------- Middle Frame ----------
        mid_frame = ctk.CTkFrame(self)
        mid_frame.pack(fill="x", padx=12, pady=6)

        self.thumb_label = ctk.CTkLabel(mid_frame, text="Миниатюра\n(нет)", width=260, height=160, anchor="center", justify="center")
        self.thumb_label.grid(row=0, column=0, rowspan=4, padx=8, pady=8)

        ctk.CTkLabel(mid_frame, text="Название:", anchor="w").grid(row=0, column=1, sticky="w")
        self.title_label = ctk.CTkLabel(mid_frame, text="", anchor="w", wraplength=480)
        self.title_label.grid(row=0, column=2, sticky="w", padx=4)

        ctk.CTkLabel(mid_frame, text="Длительность:", anchor="w").grid(row=1, column=1, sticky="w")
        self.duration_label = ctk.CTkLabel(mid_frame, text="—", anchor="w")
        self.duration_label.grid(row=1, column=2, sticky="w", padx=4)

        ctk.CTkLabel(mid_frame, text="Доступные качества:", anchor="w").grid(row=2, column=1, sticky="nw", pady=(6,0))
        self.quality_var = ctk.StringVar(value="best")
        self.quality_menu = ctk.CTkOptionMenu(mid_frame, variable=self.quality_var, values=["best"], width=260)
        self.quality_menu.grid(row=2, column=2, sticky="w", padx=4, pady=(6,0))

        mid_frame.grid_columnconfigure(2, weight=1)

        # ---------- Bottom Frame ----------
        bot_frame = ctk.CTkFrame(self)
        bot_frame.pack(fill="both", expand=True, padx=12, pady=(6,12))

        self.folder_btn = ctk.CTkButton(bot_frame, text="📁 Выбрать папку", command=self.select_folder)
        self.folder_btn.grid(row=0, column=0, padx=6, pady=8, sticky="w")
        self.folder_label = ctk.CTkLabel(bot_frame, text=f"Папка: {self.folder_path}", anchor="w")
        self.folder_label.grid(row=0, column=1, columnspan=3, sticky="w")

        self.format_label = ctk.CTkLabel(bot_frame, text="Скачать как:", anchor="w")
        self.format_label.grid(row=1, column=0, sticky="w", padx=6)
        self.save_type_var = ctk.StringVar(value="MP4 (видео)")
        self.save_type_menu = ctk.CTkOptionMenu(bot_frame, variable=self.save_type_var, values=["MP4 (видео)","MP3 (аудио)"], width=150)
        self.save_type_menu.grid(row=1, column=1, sticky="w", padx=6)

        self.download_btn = ctk.CTkButton(bot_frame, text="⬇️ Скачать", command=self.start_download, width=160)
        self.download_btn.grid(row=1, column=2, sticky="e", padx=6)

        self.progress = ctk.CTkProgressBar(bot_frame, width=580)
        self.progress.grid(row=2, column=0, columnspan=4, pady=(12,6), padx=6)
        self.status_label = ctk.CTkLabel(bot_frame, text="", anchor="w")
        self.status_label.grid(row=3, column=0, columnspan=4, sticky="w", padx=6)

    # ---------- Paste URL ----------
    def paste_url(self):
        text = pyperclip.paste()
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, text)

    # ---------- Folder ----------
    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_path)
        if folder:
            self.folder_path = folder
            self.folder_label.configure(text=f"Папка: {self.folder_path}")

    # ---------- Metadata ----------
    def start_check(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Ошибка", "Введи ссылку на видео!")
            return
        self.check_btn.configure(state="disabled")
        self.status_label.configure(text="Загружаю метаданные...")
        threading.Thread(target=self.fetch_metadata, args=(url,), daemon=True).start()

    def fetch_metadata(self, url):
        try:
            ydl_opts = {'quiet': True, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            self.after(0, lambda: (messagebox.showerror("Ошибка", f"Не удалось получить метаданные:\n{e}"), self.check_btn.configure(state="normal"), self.status_label.configure(text="")))
            return

        self.info = info
        title = info.get('title', 'Без названия')
        duration = info.get('duration')
        thumbnail = info.get('thumbnail')
        formats = info.get('formats', [])

        heights = set()
        for f in formats:
            h = f.get('height')
            if h: heights.add(int(h))
        sorted_heights = sorted(list(heights))
        quality_values = ["best"] + [str(h) for h in sorted_heights] + ["audio only"]

        def ui_update():
            self.title_label.configure(text=title)
            self.duration_label.configure(text=seconds_to_hhmmss(duration) if duration else "—")
            self.quality_menu.configure(values=quality_values)
            self.quality_var.set("best")
            self.status_label.configure(text="Готово. Выбери качество и нажми Скачать.")
            self.check_btn.configure(state="normal")

            if thumbnail:
                try:
                    resp = requests.get(thumbnail, timeout=10)
                    resp.raise_for_status()
                    img = Image.open(io.BytesIO(resp.content))
                    img.thumbnail((260, 160))
                    self.thumb_image = ImageTk.PhotoImage(img)
                    self.thumb_label.configure(image=self.thumb_image, text="")
                except:
                    self.thumb_label.configure(text="Миниатюра\n(ошибка)")
            else:
                self.thumb_label.configure(text="Миниатюра\n(нет)")

        self.after(0, ui_update)

    # ---------- Download ----------
    def start_download(self):
        if not self.info:
            messagebox.showwarning("Ошибка", "Сначала проверь ссылку (🔍 Проверить).")
            return
        url = self.url_entry.get().strip()
        q = self.quality_var.get()
        save_type = self.save_type_var.get()
        self.download_btn.configure(state="disabled")
        threading.Thread(target=self.download_thread, args=(url,q,save_type), daemon=True).start()

    def download_thread(self,url,q,save_type):
        self.progress.set(0)
        self.status_label.configure(text="Скачивание...")
        try:
            ydl_opts = {
                'outtmpl': os.path.join(self.folder_path, '%(title)s.%(ext)s'),
                'progress_hooks':[self.progress_hook],
                'noplaylist': True
            }
            if save_type == "MP3 (аудио)":
                ydl_opts.update({'format':'bestaudio','postprocessors':[{'key':'FFmpegExtractAudio','preferredcodec':'mp3'}]})
            else:
                if q=="audio only":
                    ydl_opts['format']="bestaudio"
                elif q=="best":
                    ydl_opts['format']="bestvideo+bestaudio/best"
                else:
                    ydl_opts['format']=f"bestvideo[height<={q}]+bestaudio/best"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось скачать:\n{e}"))
        finally:
            self.after(0, lambda: (self.download_btn.configure(state="normal"), self.progress.set(0), self.status_label.configure(text="Готово.")))

    def progress_hook(self,d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str','0.0%').replace('%','').strip()
            try:
                pval = float(p)/100
                self.progress.set(pval)
            except:
                self.progress.set(0)
        elif d['status']=='finished':
            self.progress.set(1.0)

if __name__=="__main__":
    app = YouTubeDownloaderPro()
    app.mainloop()

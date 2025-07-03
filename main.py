import os
import shutil
import json
import subprocess
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox, Listbox, END
from ytmusicapi import YTMusic
from yt_dlp import YoutubeDL
from mutagen.mp4 import MP4

settings_file = "settings.json"

class GTARadioManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GTA Radio Manager")
        self.geometry("800x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.ytmusic = YTMusic()
        self.search_results = []
        self.audio_quality = ctk.StringVar(value="m4a/bestaudio/best")
        self.gta_mode = True
        self.gta_music_folder = None

        self.create_widgets()
        self.load_settings()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Song Title:", font=("Segoe UI", 16)).pack(pady=(20, 5))
        self.song_entry = ctk.CTkEntry(self, width=500)
        self.song_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Artist Name:", font=("Segoe UI", 16)).pack(pady=5)
        self.artist_entry = ctk.CTkEntry(self, width=500)
        self.artist_entry.pack(pady=5)

        ctk.CTkButton(self, text="Search", command=self.search_song).pack(pady=10)

        # Frame to hold styled listbox
        listbox_frame = ctk.CTkFrame(self, fg_color="transparent")
        listbox_frame.pack(pady=10)

        self.result_listbox = Listbox(
            listbox_frame,
            width=100,
            height=10,
            font=("Segoe UI", 12),
            bg="#1e1e1e",
            fg="#ffffff",
            selectbackground="#0078d7",
            border=0,
            highlightthickness=0,
        )
        self.result_listbox.pack()

        ctk.CTkButton(self, text="Download Selected Song", command=self.download_song).pack(pady=10)
        ctk.CTkButton(self, text="Select Music Folder", command=self.select_folder).pack(pady=5)

        self.folder_label = ctk.CTkLabel(self, text="", font=("Segoe UI", 14))
        self.folder_label.pack(pady=5)

        self.output = ctk.CTkTextbox(self, height=100, width=750)
        self.output.pack(pady=10)

    def log(self, message):
        self.output.insert("end", message + "\n")
        self.output.see("end")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.gta_music_folder = folder
            self.folder_label.configure(text=f"Selected folder: {folder}")
            self.save_settings()

    def search_song(self):
        song_name = self.song_entry.get()
        artist_name = self.artist_entry.get()
        if not song_name:
            messagebox.showwarning("Missing Input", "Please enter a song name.")
            return

        self.log("Searching...")
        results = self.ytmusic.search(
            f"{song_name} - {artist_name}" if artist_name else song_name,
            filter="songs",
            limit=10,
        )

        self.search_results = results
        self.result_listbox.delete(0, END)
        for i, result in enumerate(results, 1):
            artists = ", ".join(artist["name"] for artist in result.get("artists", []))
            self.result_listbox.insert(END, f"{i}. {result['title']} - {artists}")

    def download_song(self):
        selection = self.result_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a song from the list.")
            return

        index = selection[0]
        result = self.search_results[index]
        video_id = result.get("videoId")
        artists = ", ".join(artist["name"] for artist in result.get("artists", []))
        song_url = f"https://youtube.com/watch?v={video_id}"
        output_filename = f"{result['title']} - {artists}".replace('"', '_').replace("'", '_')

        ydl_opts = {
            "format": self.audio_quality.get(),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                }
            ],
            "outtmpl": output_filename,
            "quiet": True,
        }

        def download_thread():
            try:
                self.log(f"Downloading: {result['title']} by {artists}")
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([song_url])

                file_path = f"{output_filename}.m4a"
                audio = MP4(file_path)
                audio["\xa9nam"] = result["title"]
                audio["\xa9ART"] = artists.upper() if self.gta_mode else artists
                audio.save()

                if self.gta_music_folder:
                    shutil.move(file_path, os.path.join(self.gta_music_folder, file_path))
                    self.log(f"Downloaded '{output_filename}' to {self.gta_music_folder}")
                else:
                    self.log(f"Saved as {file_path}")

                messagebox.showinfo("Done", "Song downloaded successfully.")

            except Exception as e:
                self.log(f"Error: {e}")
                messagebox.showerror("Error", str(e))

        threading.Thread(target=download_thread).start()

    def load_settings(self):
        if os.path.exists(settings_file):
            with open(settings_file, "r") as f:
                settings = json.load(f)
            self.gta_music_folder = settings.get("gta_music_folder")
            self.audio_quality.set(settings.get("audio_quality", "m4a/bestaudio/best"))
            self.gta_mode = settings.get("gta_mode", True)
            if self.gta_music_folder:
                self.folder_label.configure(text=f"Selected folder: {self.gta_music_folder}")

    def save_settings(self):
        settings = {
            "gta_music_folder": self.gta_music_folder,
            "audio_quality": self.audio_quality.get(),
            "gta_mode": self.gta_mode,
        }
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=4)


if __name__ == "__main__":
    app = GTARadioManager()
    app.mainloop()

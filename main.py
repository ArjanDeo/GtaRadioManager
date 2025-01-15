import os
import shutil
import json
import subprocess
from ytmusicapi import YTMusic
from yt_dlp import YoutubeDL
from mutagen.mp4 import MP4

settings_file = 'settings.json'

def check_settings_file():
    if not os.path.exists(settings_file):
        print("Settings file not found.")
        user_music_folder = input("Please enter the path to your GTA user music folder: ")
        
        if not os.path.isdir(user_music_folder):
            print("The provided path is not valid. Please check the folder path.")
            return None
        
        audio_quality = input('Enter preferred audio quality (1) High (best quality), (2) Medium (lower quality), or press enter for default: ')
        if audio_quality == '1':
            quality = 'bestaudio/best'
        elif audio_quality == '2':
            quality = 'bestaudio'
        else:
            quality = 'm4a/bestaudio/best'

        settings = {"gta_music_folder": user_music_folder, "audio_quality": quality}
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=4)
        
        print(f"Settings file created with GTA music folder: {user_music_folder} and audio quality: {quality}")
        return user_music_folder, quality
    else:
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        return settings.get("gta_music_folder"), settings.get("audio_quality")

def install_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("FFmpeg not found. Please install FFmpeg to continue. (see readme)")
        print("FFmpeg installed successfully.")

def searchForSong(song_name, artist_name):
    ytmusic = YTMusic()
    query = f"{song_name} - {artist_name}"
    results = ytmusic.search(query=query, filter='songs', limit=10)
    return results

def main():
    install_ffmpeg()
    
    music_folder, audio_quality = check_settings_file()
    if not music_folder:
        return
    while True:
        userSongTitle = input('Enter song name: ')
        userArtistName = input('Enter artist name (press enter to skip): ')
        
        results = searchForSong(userSongTitle, userArtistName)
        if not results:
            print("No results found. Try refining your search.")
            return
        
        index = 0
        artists = ''
        for result in results:
            artists = ", ".join(artist['name'] for artist in result.get('artists', []))
            index += 1
            print(f"({index}) {result['title']} - {artists}")
        
        choice = int(input('Select a song to download (e.g. 1, 2, 3 etc): ')) - 1
        artists = ", ".join(artist['name'] for artist in results[choice].get('artists', []))
        
        songUrl = f"https://youtube.com/watch?v={results[choice]['videoId']}"

        ydl_opts = {
            'format': audio_quality,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }],
            'outtmpl': f"{results[choice]['title']} - {artists}",
            'quiet': True
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([songUrl])
        
        sanitized_title = results[choice]['title'].replace('"', '_').replace("'", '_')
        sanitized_artists = artists.replace('"', '_').replace("'", '_')
        file_path = f"{sanitized_title} - {sanitized_artists}.m4a"

        audio = MP4(file_path)
        audio["\xa9nam"] = results[choice]['title']
        audio["\xa9ART"] = artists.upper()
        audio.save()
        print('Successfully changed audio metadata.')

        shutil.move(file_path, f"{music_folder}/{file_path}")
        print(f"Song successfully saved in {music_folder}.")

if __name__ == '__main__':
    main()
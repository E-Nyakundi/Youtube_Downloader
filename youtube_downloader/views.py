import os
import logging
import re
import yt_dlp
import browsercookie
from time import sleep
from pydub import AudioSegment
from datetime import time

logging.basicConfig(level=logging.INFO)

class VideoDownloader:
    def __init__(self, resume=False, audio_only=False, max_retries=5):
        self.resume = resume
        self.audio_only = audio_only
        self.max_retries = max_retries
        self.cookies_path = self.get_browser_cookies()

    def get_browser_cookies(self):
        """Fetch cookies from the browser (Chrome or Firefox)."""
        try:
            # Attempt to get cookies from Chrome
            cookies = browsercookie.chrome()  # If using Chrome, change to .firefox() for Firefox
            return cookies
        except Exception as e:
            logging.error(f"Error fetching cookies: {e}")
            return None  # If cookies can't be fetched, handle the error appropriately

    def sanitize_filename(self, title):
        sanitized_title = re.sub(r'[<>:"/\\|?*]', '', title)
        max_filename_length = 255
        if len(sanitized_title) > max_filename_length:
            sanitized_title = sanitized_title[:max_filename_length]
        return sanitized_title

    def download_video(self, video_url, selected_quality=None):
        """Download video or audio with selected quality."""
        if self.audio_only:
            format_option = 'bestaudio/best'  # Audio only format
        else:
            format_option = selected_quality if selected_quality else 'bestvideo+bestaudio/best'

        ydl_opts = {
            'format': format_option,  # Use selected quality or audio-only
            'cookies': self.cookies_path,  # Pass the cookies to yt-dlp
            'outtmpl': os.path.join(os.path.expanduser('~'), 'Downloads', '%(title)s.%(ext)s'),  # Save to Downloads folder
            'noplaylist': True,  # Avoid downloading playlists
            'quiet': False,  # Show download progress
        }

        retries = 0
        while retries <= self.max_retries:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.extract_info(video_url, download=True)  # Download the video
                    filename = ydl.prepare_filename(result)  # Get the final file name
                    logging.info(f"Downloaded: {filename}")
                    
                    # If audio-only is selected, check if the file is already audio
                    if self.audio_only and filename.endswith('.mp4'):
                        self.convert_mp4_to_mp3(filename)
                    
                    return filename  # Return the path to the downloaded file
            except Exception as e:
                logging.error(f"Error occurred while downloading: {video_url}")
                logging.error(f"Error message: {str(e)}")
                retries += 1
                logging.info(f"Retrying download for video: {video_url} (Retry {retries}/{self.max_retries})")
                sleep(5 * retries)

        if retries > self.max_retries:
            logging.warning(f"Max retries reached for video: {video_url}. Skipping download.")
            return None

    def download_playlist(self, playlist_url, selected_quality=None):
        """Download a playlist with selected quality."""
        ydl_opts = {
            'format': selected_quality or 'best',  # Default to best quality
            'cookies': self.cookies_path,  # Pass the cookies to yt-dlp
            'outtmpl': os.path.join(os.path.expanduser('~'), 'Downloads', '%(playlist)s/%(title)s.%(ext)s'),
            'quiet': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(playlist_url, download=True)
                logging.info(f"Downloaded playlist: {result['title']}")
                return result  # Return playlist details (if needed)
        except Exception as e:
            logging.error(f"Error occurred while downloading playlist: {playlist_url}")
            logging.error(f"Error message: {str(e)}")
            return None

    def convert_mp4_to_mp3(self, mp4_filename):
        """Convert the downloaded MP4 to MP3."""
        mp3_filename = mp4_filename.rsplit('.', 1)[0] + '.mp3'
        try:
            # Using pydub to convert mp4 to mp3
            audio = AudioSegment.from_file(mp4_filename, format="mp4")
            audio.export(mp3_filename, format="mp3")
            os.remove(mp4_filename)  # Delete the original mp4 file
            logging.info(f"Converted {mp4_filename} to {mp3_filename}")
            return mp3_filename
        except Exception as e:
            logging.error(f"Error occurred while converting {mp4_filename} to mp3: {str(e)}")
            return None

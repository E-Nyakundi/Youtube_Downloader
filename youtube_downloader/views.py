import os
import logging
import re
import yt_dlp
from time import sleep
from pydub import AudioSegment

logging.basicConfig(level=logging.INFO)


class VideoDownloader:
    def __init__(self, resume=False, audio_only=False, max_retries=5, cookies_file='cookie.json'):
        self.resume = resume
        self.audio_only = audio_only
        self.max_retries = max_retries
        self.cookies_file = cookies_file  # Path to the cookies file

    def sanitize_filename(self, title):
        sanitized_title = re.sub(r'[<>:"/\\|?*]', '', title)
        max_filename_length = 255
        if len(sanitized_title) > max_filename_length:
            sanitized_title = sanitized_title[:max_filename_length]
        return sanitized_title

    def download_video(self, video_url, selected_quality=None):
        """Download video or audio with selected quality."""
        if self.audio_only:
            format_option = 'bestaudio/best'
        else:
            format_option = selected_quality if selected_quality else 'bestvideo+bestaudio/best'

        ydl_opts = {
            'format': format_option,
            'cookiefile': self.cookies_file,  # Use the provided cookies file
            'outtmpl': os.path.join(os.path.expanduser('~'), 'Downloads', '%(title)s.%(ext)s'),
            'noplaylist': True,
            'quiet': False,
        }

        retries = 0
        while retries <= self.max_retries:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.extract_info(video_url, download=True)
                    filename = ydl.prepare_filename(result)
                    logging.info(f"Downloaded: {filename}")

                    if self.audio_only and filename.endswith('.mp4'):
                        self.convert_mp4_to_mp3(filename)

                    return filename
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
            'format': selected_quality or 'best',
            'cookiefile': self.cookies_file,
            'outtmpl': os.path.join(os.path.expanduser('~'), 'Downloads', '%(playlist)s/%(title)s.%(ext)s'),
            'quiet': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(playlist_url, download=True)
                logging.info(f"Downloaded playlist: {result['title']}")
                return result
        except Exception as e:
            logging.error(f"Error occurred while downloading playlist: {playlist_url}")
            logging.error(f"Error message: {str(e)}")
            return None

    def convert_mp4_to_mp3(self, mp4_filename):
        """Convert the downloaded MP4 to MP3."""
        mp3_filename = mp4_filename.rsplit('.', 1)[0] + '.mp3'
        try:
            audio = AudioSegment.from_file(mp4_filename, format="mp4")
            audio.export(mp3_filename, format="mp3")
            os.remove(mp4_filename)
            logging.info(f"Converted {mp4_filename} to {mp3_filename}")
            return mp3_filename
        except Exception as e:
            logging.error(f"Error occurred while converting {mp4_filename} to mp3: {str(e)}")
            return None

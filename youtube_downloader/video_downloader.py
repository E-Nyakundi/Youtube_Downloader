import os
import logging
import re
import yt_dlp
from time import sleep
from pydub import AudioSegment  # For audio conversion
from datetime import time

logging.basicConfig(level=logging.INFO)
co

class VideoDownloader:
    def __init__(self, resume=False, audio_only=False, max_retries=5, cookies_path=None):
        self.resume = resume
        self.audio_only = audio_only
        self.max_retries = max_retries
        self.cookies_path = cookies_path  # Path to the cookies file

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
            'cookiefile': self.cookies_path,  # Use provided cookies file
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
            'cookiefile': self.cookies_path,  # Use provided cookies file
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


class VideoDetailsFetcher:
    @staticmethod
    def get_video_details(video_url, cookies_path=None):
        ydl_opts = {
            'quiet': True,
            'format': 'best',  # Default to best quality
            'cookiefile': cookies_path,  # Use provided cookies file
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(video_url, download=False)  # Don't download, just fetch details
                formats = result.get('formats', [])
                
                # Explicitly check for audio-only formats
                audio_formats = [f for f in formats if f.get('vcodec') == 'none']  # Audio-only formats
                streams = formats + audio_formats  # Combine video and audio-only streams
                
                return {
                    'title': result.get('title'),
                    'thumbnail_url': result.get('thumbnail'),
                    'description': result.get('description'),
                    'streams': streams,  # Return both audio and video streams
                }
        except Exception as e:
            logging.error(f"Error occurred while fetching video details for {video_url}")
            logging.error(f"Error message: {str(e)}")
            return None

    @staticmethod
    def get_playlist_details(playlist_url, cookies_path=None):
        ydl_opts = {
            'quiet': True,
            'format': 'best',
            'cookiefile': cookies_path,  # Use provided cookies file
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(playlist_url, download=False)
                playlist_details = {
                    'title': result.get('title'),
                    'description': result.get('description'),
                    'thumbnail_url': result['entries'][0]['thumbnail'] if result.get('entries') else None,
                    'videos': [],
                }

                # Extract details for each video in the playlist
                for video in result.get('entries', []):
                    video_details = {
                        'title': video.get('title'),
                        'thumbnail_url': video.get('thumbnail'),
                        'description': video.get('description'),
                        'streams': video.get('formats'),
                    }
                    playlist_details['videos'].append(video_details)

                return playlist_details
        except Exception as e:
            logging.error(f"Error occurred while fetching playlist details for {playlist_url}")
            logging.error(f"Error message: {str(e)}")
            return None

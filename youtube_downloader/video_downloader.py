import os
import logging
import re
import yt_dlp
from datetime import time

logging.basicConfig(level=logging.INFO)

class VideoDownloader:
    def __init__(self, resume=False, audio_only=False, max_retries=5):
        self.resume = resume
        self.audio_only = audio_only
        self.max_retries = max_retries

    def sanitize_filename(self, title):
        sanitized_title = re.sub(r'[<>:"/\\|?*]', '', title)
        max_filename_length = 255
        if len(sanitized_title) > max_filename_length:
            sanitized_title = sanitized_title[:max_filename_length]
        return sanitized_title

    def download_video(self, video_url, selected_quality=None):
        ydl_opts = {
            'format': selected_quality or 'best',  # Choose best format or selected quality
            'outtmpl': os.path.join(os.path.expanduser('~'), 'Downloads', '%(title)s.%(ext)s'),  # Save to Downloads folder
            'noplaylist': True,  # Avoid downloading playlists
            'quiet': False  # Show download progress
        }

        retries = 0
        while retries <= self.max_retries:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.extract_info(video_url, download=True)  # Download the video
                    filename = ydl.prepare_filename(result)  # Get the final file name
                    logging.info(f"Downloaded video: {filename}")
                    return filename  # Return the path to the downloaded video
            except Exception as e:
                logging.error(f"Error occurred while downloading: {video_url}")
                logging.error(f"Error message: {str(e)}")
                retries += 1
                logging.info(f"Retrying download for video: {video_url} (Retry {retries}/{self.max_retries})")
                time.sleep(5 * retries)

        if retries > self.max_retries:
            logging.warning(f"Max retries reached for video: {video_url}. Skipping download.")
            return None

    def download_playlist(self, playlist_url, selected_quality=None):
        ydl_opts = {
            'format': selected_quality or 'best',
            'outtmpl': os.path.join(os.path.expanduser('~'), 'Downloads', '%(playlist)s/%(title)s.%(ext)s'),
            'quiet': False
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

        
class VideoDetailsFetcher:
    @staticmethod
    def get_video_details(video_url):
        try:
            video = YouTube(video_url)
            return {
                'title': video.title,
                'thumbnail_url': video.thumbnail_url,
                'description': video.description,
                'metadata': video.metadata,
                'streams': video.streams,
            }
        except Exception as e:
            logging.error(f"Error occurred while fetching video details for {video_url}: {str(e)}")
            return None


class VideoDetailsFetcher:
    @staticmethod
    def get_video_details(video_url):
        ydl_opts = {
            'quiet': True,
            'format': 'best',
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(video_url, download=False)  # Don't download, just fetch details
                return {
                    'title': result.get('title'),
                    'thumbnail_url': result.get('thumbnail'),
                    'description': result.get('description'),
                    'streams': result.get('formats'),  # 'formats' contains available streams
                }
        except Exception as e:
            logging.error(f"Error occurred while fetching video details for {video_url}")
            logging.error(f"Error message: {str(e)}")
            return None

    @staticmethod
    def get_playlist_details(playlist_url):
        ydl_opts = {
            'quiet': True,
            'format': 'best',
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(playlist_url, download=False)
                playlist_details = {
                    'title': result.get('title'),
                    'description': result.get('description'),
                    'thumbnail_url': result.get('thumbnail'),
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





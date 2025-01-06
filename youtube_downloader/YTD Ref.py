<<<<<<< HEAD
"""
URL configuration for YTD project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("youtube_downloader.urls"))
]


from django.urls import path, include
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('video-download/', views.DownloadView.as_view(), name='download_video'),
    path('', lambda request: redirect('download_video')),  # Redirect root URL to the download view
]


from django.http import HttpResponse, FileResponse
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.shortcuts import render
from .forms import DownloadForm
from .video_downloader import VideoDownloader, VideoDetailsFetcher
import os

class DownloadView(FormView):
    template_name = 'youtube_downloader/index.html'
    form_class = DownloadForm
    success_url = reverse_lazy('download_video')

    def form_valid(self, form):
        url = form.cleaned_data['url']
        selected_quality = form.cleaned_data['selected_quality']

        try:
            if 'playlist' in url:
                details = VideoDetailsFetcher.get_playlist_details(url)
            else:
                details = VideoDetailsFetcher.get_video_details(url)
            
            context = {
                'form': form,
                'details': details,
                'selected_quality': selected_quality,
                'url': url,
            }
            return render(self.request, self.template_name, context)

        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}")

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            if 'download' in request.POST:
                url = request.POST.get('url')
                selected_quality = request.POST.get('selected_quality')
                try:
                    video_downloader = VideoDownloader()
                    if 'playlist' in url:
                        file_paths = video_downloader.download_playlist(url, selected_quality)
                    else:
                        file_path = video_downloader.download_video(url, selected_quality)
                        file_paths = [file_path] if file_path else []

                    # Prepare the response
                    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                    file_size = os.path.getsize(file_path)
                    response['Content-Length'] = file_size
                    return response

                except Exception as e:
                    return HttpResponse(f"An error occurred: {str(e)}")

            return self.form_valid(form)
        else:
            return self.form_invalid(form)


from django import forms

class DownloadForm(forms.Form):
    url = forms.URLField(label='Video/Playlist URL', required=True, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter video or playlist URL'
    }))
    QUALITY_CHOICES = [
        ('128K', '128K'),
        ('256K', '256K'),
        ('360P', '360P'),
        ('480P', '480P'),
        ('720P', '720P'),
        ('1080P', '1080P'),
    ]
    selected_quality = forms.ChoiceField(label='Select Quality', choices=QUALITY_CHOICES, required=False, widget=forms.RadioSelect)



import os
import logging
import re
import requests
from pytube import Playlist, YouTube
from concurrent.futures import ThreadPoolExecutor
from time import sleep

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
        try:
            video = YouTube(video_url)
            if selected_quality:
                video_stream = video.streams.filter(res=selected_quality).first()
            elif self.audio_only:
                video_stream = video.streams.filter(abr=selected_quality).first()
            else:
                video_stream = video.streams.get_highest_resolution()

        except Exception as e:
            logging.error(f"Error occurred while creating YouTube object for URL: {video_url}")
            logging.error(f"Error message: {str(e)}")
            return

        if video_stream is None:
            logging.warning(f"No compatible video stream found for video: {video.title}.")
            return

        logging.info(f"Downloading: {video.title}")

        sanitized_title = self.sanitize_filename(video.title)

        retries = 0
        while retries <= self.max_retries:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.head(video_url, headers=headers)
                if response.status_code == 410:
                    logging.warning(f"Video: {video.title} is no longer available (410 Gone). Skipping download.")
                    return

                # Define download path
                download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
                output_filename = os.path.join(download_path, sanitized_title)

                if self.resume and os.path.isfile(output_filename):
                    logging.info(f"Video '{video.title}' already exists in the output directory. Skipping download.")
                    return

                video_stream.download(output_path=download_path, filename=sanitized_title + ".mp4", skip_existing=self.resume)
                return output_filename

            except Exception as e:
                logging.error(f"Error occurred while downloading: {video.title}")
                logging.error(f"Error message: {str(e)}")

                retries += 1
                logging.info(f"Retrying download for video: {video.title} (Retry {retries}/{self.max_retries})")
                delay = 5 * retries
                sleep(delay)

        if retries > self.max_retries:
            logging.warning(f"Max retries reached for video: {video.title}. Skipping download.")
            return None

    def download_playlist(self, playlist_url, selected_quality=None):
        try:
            playlist = Playlist(playlist_url)
            playlist._video_regex = re.compile(r"\"url\":\"(/watch\?v=[\w-]*)")

            logging.info(f"Number of videos in playlist: {len(playlist.video_urls)}")

            downloaded_files = []

            with ThreadPoolExecutor() as executor:
                futures = []
                for video_url in playlist.video_urls:
                    future = executor.submit(self.download_video, video_url, selected_quality)
                    futures.append(future)

                for future in futures:
                    result = future.result()
                    if result:
                        downloaded_files.append(result)

            logging.info("Playlist download completed.")
            return downloaded_files

        except Exception as e:
            logging.error(f"Error occurred while processing playlist: {playlist_url}")
            logging.error(f"Error message: {str(e)}")
            return None

        
class VideoDetailsFetcher:
    @staticmethod
    def get_video_details(video_url):
        video = YouTube(video_url)
        unique_streams = []
        unique_resolutions = set()
        
        if video.streams is not None:
            for stream in video.streams:
                if stream.type == 'video' and stream.resolution not in unique_resolutions:
                    unique_streams.append(stream)
                    unique_resolutions.add(stream.resolution)
                elif stream.type == 'audio' and stream.abr not in unique_resolutions:
                    unique_streams.append(stream)
                    unique_resolutions.add(stream.abr)

        video_details = {
            'title': video.title,
            'thumbnail_url': video.thumbnail_url,
            'description': video.description,
            'metadata': video.metadata,
            'streams': unique_streams,
        }
        return video_details
    @staticmethod
    def get_playlist_details(playlist_url):
        try:
            playlist = Playlist(playlist_url)
            if not playlist.video_urls:  # Check if there are any videos in the playlist
                logging.warning('No video URLs found in the playlist.')
                return None

            first_video_url = playlist.video_urls[0]
            first_video = YouTube(first_video_url)

            playlist_details = {
                'title': playlist.title,
                'thumbnail_url': first_video.thumbnail_url,
                'description': playlist.description if hasattr(playlist, 'description') else '',
                'metadata': first_video.metadata,
                'videos': [],
                'streams': first_video.streams,
            }

            for video_url in playlist.video_urls:
                video = YouTube(video_url)
                unique_streams = []
                unique_resolutions = set()
                
                if video.streams is not None:
                    for stream in video.streams:
                        if stream.type == 'video' and stream.resolution not in unique_resolutions:
                            unique_streams.append(stream)
                            unique_resolutions.add(stream.resolution)
                        elif stream.type == 'audio' and stream.abr not in unique_resolutions:
                            unique_streams.append(stream)
                            unique_resolutions.add(stream.abr)

                video_details = {
                    'title': video.title,
                    'thumbnail_url': video.thumbnail_url,
                    'description': video.description,
                    'metadata': video.metadata,
                    'streams': unique_streams,
                }
                playlist_details['videos'].append(video_details)

            return playlist_details

        except KeyError as e:
            logging.error(f"KeyError occurred: {str(e)}")
        except AttributeError as e:
            logging.error(f"AttributeError occurred: {str(e)}")
        except Exception as e:
            logging.error(f"Error occurred while getting playlist details for URL '{playlist_url}': {str(e)}")
        return None




=======
"""
URL configuration for YTD project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("youtube_downloader.urls"))
]


from django.urls import path, include
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('video-download/', views.DownloadView.as_view(), name='download_video'),
    path('', lambda request: redirect('download_video')),  # Redirect root URL to the download view
]


from django.http import HttpResponse, FileResponse
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.shortcuts import render
from .forms import DownloadForm
from .video_downloader import VideoDownloader, VideoDetailsFetcher
import os

class DownloadView(FormView):
    template_name = 'youtube_downloader/index.html'
    form_class = DownloadForm
    success_url = reverse_lazy('download_video')

    def form_valid(self, form):
        url = form.cleaned_data['url']
        selected_quality = form.cleaned_data['selected_quality']

        try:
            if 'playlist' in url:
                details = VideoDetailsFetcher.get_playlist_details(url)
            else:
                details = VideoDetailsFetcher.get_video_details(url)
            
            context = {
                'form': form,
                'details': details,
                'selected_quality': selected_quality,
                'url': url,
            }
            return render(self.request, self.template_name, context)

        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}")

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            if 'download' in request.POST:
                url = request.POST.get('url')
                selected_quality = request.POST.get('selected_quality')
                try:
                    video_downloader = VideoDownloader()
                    if 'playlist' in url:
                        file_paths = video_downloader.download_playlist(url, selected_quality)
                    else:
                        file_path = video_downloader.download_video(url, selected_quality)
                        file_paths = [file_path] if file_path else []

                    # Prepare the response
                    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                    file_size = os.path.getsize(file_path)
                    response['Content-Length'] = file_size
                    return response

                except Exception as e:
                    return HttpResponse(f"An error occurred: {str(e)}")

            return self.form_valid(form)
        else:
            return self.form_invalid(form)


from django import forms

class DownloadForm(forms.Form):
    url = forms.URLField(label='Video/Playlist URL', required=True, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter video or playlist URL'
    }))
    QUALITY_CHOICES = [
        ('128K', '128K'),
        ('256K', '256K'),
        ('360P', '360P'),
        ('480P', '480P'),
        ('720P', '720P'),
        ('1080P', '1080P'),
    ]
    selected_quality = forms.ChoiceField(label='Select Quality', choices=QUALITY_CHOICES, required=False, widget=forms.RadioSelect)



import os
import logging
import re
import requests
from pytube import Playlist, YouTube
from concurrent.futures import ThreadPoolExecutor
from time import sleep

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
        try:
            video = YouTube(video_url)
            if selected_quality:
                video_stream = video.streams.filter(res=selected_quality).first()
            elif self.audio_only:
                video_stream = video.streams.filter(abr=selected_quality).first()
            else:
                video_stream = video.streams.get_highest_resolution()

        except Exception as e:
            logging.error(f"Error occurred while creating YouTube object for URL: {video_url}")
            logging.error(f"Error message: {str(e)}")
            return

        if video_stream is None:
            logging.warning(f"No compatible video stream found for video: {video.title}.")
            return

        logging.info(f"Downloading: {video.title}")

        sanitized_title = self.sanitize_filename(video.title)

        retries = 0
        while retries <= self.max_retries:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.head(video_url, headers=headers)
                if response.status_code == 410:
                    logging.warning(f"Video: {video.title} is no longer available (410 Gone). Skipping download.")
                    return

                # Define download path
                download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
                output_filename = os.path.join(download_path, sanitized_title)

                if self.resume and os.path.isfile(output_filename):
                    logging.info(f"Video '{video.title}' already exists in the output directory. Skipping download.")
                    return

                video_stream.download(output_path=download_path, filename=sanitized_title + ".mp4", skip_existing=self.resume)
                return output_filename

            except Exception as e:
                logging.error(f"Error occurred while downloading: {video.title}")
                logging.error(f"Error message: {str(e)}")

                retries += 1
                logging.info(f"Retrying download for video: {video.title} (Retry {retries}/{self.max_retries})")
                delay = 5 * retries
                sleep(delay)

        if retries > self.max_retries:
            logging.warning(f"Max retries reached for video: {video.title}. Skipping download.")
            return None

    def download_playlist(self, playlist_url, selected_quality=None):
        try:
            playlist = Playlist(playlist_url)
            playlist._video_regex = re.compile(r"\"url\":\"(/watch\?v=[\w-]*)")

            logging.info(f"Number of videos in playlist: {len(playlist.video_urls)}")

            downloaded_files = []

            with ThreadPoolExecutor() as executor:
                futures = []
                for video_url in playlist.video_urls:
                    future = executor.submit(self.download_video, video_url, selected_quality)
                    futures.append(future)

                for future in futures:
                    result = future.result()
                    if result:
                        downloaded_files.append(result)

            logging.info("Playlist download completed.")
            return downloaded_files

        except Exception as e:
            logging.error(f"Error occurred while processing playlist: {playlist_url}")
            logging.error(f"Error message: {str(e)}")
            return None

        
class VideoDetailsFetcher:
    @staticmethod
    def get_video_details(video_url):
        video = YouTube(video_url)
        unique_streams = []
        unique_resolutions = set()
        
        if video.streams is not None:
            for stream in video.streams:
                if stream.type == 'video' and stream.resolution not in unique_resolutions:
                    unique_streams.append(stream)
                    unique_resolutions.add(stream.resolution)
                elif stream.type == 'audio' and stream.abr not in unique_resolutions:
                    unique_streams.append(stream)
                    unique_resolutions.add(stream.abr)

        video_details = {
            'title': video.title,
            'thumbnail_url': video.thumbnail_url,
            'description': video.description,
            'metadata': video.metadata,
            'streams': unique_streams,
        }
        return video_details
    @staticmethod
    def get_playlist_details(playlist_url):
        try:
            playlist = Playlist(playlist_url)
            if not playlist.video_urls:  # Check if there are any videos in the playlist
                logging.warning('No video URLs found in the playlist.')
                return None

            first_video_url = playlist.video_urls[0]
            first_video = YouTube(first_video_url)

            playlist_details = {
                'title': playlist.title,
                'thumbnail_url': first_video.thumbnail_url,
                'description': playlist.description if hasattr(playlist, 'description') else '',
                'metadata': first_video.metadata,
                'videos': [],
                'streams': first_video.streams,
            }

            for video_url in playlist.video_urls:
                video = YouTube(video_url)
                unique_streams = []
                unique_resolutions = set()
                
                if video.streams is not None:
                    for stream in video.streams:
                        if stream.type == 'video' and stream.resolution not in unique_resolutions:
                            unique_streams.append(stream)
                            unique_resolutions.add(stream.resolution)
                        elif stream.type == 'audio' and stream.abr not in unique_resolutions:
                            unique_streams.append(stream)
                            unique_resolutions.add(stream.abr)

                video_details = {
                    'title': video.title,
                    'thumbnail_url': video.thumbnail_url,
                    'description': video.description,
                    'metadata': video.metadata,
                    'streams': unique_streams,
                }
                playlist_details['videos'].append(video_details)

            return playlist_details

        except KeyError as e:
            logging.error(f"KeyError occurred: {str(e)}")
        except AttributeError as e:
            logging.error(f"AttributeError occurred: {str(e)}")
        except Exception as e:
            logging.error(f"Error occurred while getting playlist details for URL '{playlist_url}': {str(e)}")
        return None




>>>>>>> bd74355 (Initial commit with virtual environment and requirements)

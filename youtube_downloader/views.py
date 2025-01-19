from django.http import HttpResponse, FileResponse
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.shortcuts import render
from .forms import DownloadForm
from .video_downloader import VideoDownloader, VideoDetailsFetcher
import os
import logging

class DownloadView(FormView):
    template_name = 'youtube_downloader/index.html'
    form_class = DownloadForm
    success_url = reverse_lazy('download_video')

    def get_common_qualities(self, videos):
        # Extract quality options from each video
        all_qualities = [set(video['qualities']) for video in videos]

        # Find common qualities across all videos
        common_qualities = set.intersection(*all_qualities)
        return list(common_qualities)

    def form_valid(self, form):
        url = form.cleaned_data['url']
        try:
            if 'playlist' in url:
                playlist_details = VideoDetailsFetcher.get_playlist_details(url)
                videos = playlist_details['videos']  # List of video details

                # Get common qualities across all videos
                common_qualities = self.get_common_qualities(videos)
                playlist_details['common_qualities'] = common_qualities

                if not common_qualities:
                    return HttpResponse("No common quality found across all videos.")

            else:
                playlist_details = VideoDetailsFetcher.get_video_details(url)

            context = {
                'form': form,
                'details': playlist_details,
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
                    video_downloader = VideoDownloader(audio_only='Audio Only' in selected_quality)
                    if 'playlist' in url:
                        file_paths = video_downloader.download_playlist(url, selected_quality)
                    else:
                        file_path = video_downloader.download_video(url, selected_quality)
                        file_paths = [file_path] if file_path else []

                    # Prepare the response
                    response = FileResponse(open(file_paths[0], 'rb'), as_attachment=True)
                    file_size = os.path.getsize(file_paths[0])
                    response['Content-Length'] = file_size
                    return response

                except Exception as e:
                    return HttpResponse(f"An error occurred: {str(e)}")

            return self.form_valid(form)
        else:
            return self.form_invalid(form)
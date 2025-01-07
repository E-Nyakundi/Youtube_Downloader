from django.urls import path, include
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('video-download/', views.DownloadView.as_view(), name='download_video'),
    path('', lambda request: redirect('download_video')),  # Redirect root URL to the download view
]


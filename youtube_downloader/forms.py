from django import forms

class DownloadForm(forms.Form):
    url = forms.URLField(label='Video/Playlist URL', required=True, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter video or playlist URL'
    }))

    # Placeholder for dynamic quality options (set in the view)
    selected_quality = forms.CharField(label='Select Quality', required=False, widget=forms.RadioSelect)


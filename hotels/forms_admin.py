"""
hotels/forms_admin.py
Form admin Hotel — latitude dùng LeafletMapWidget, longitude ẩn.
"""
from django import forms
from django.utils.safestring import mark_safe
from .models import Hotel
from .widgets import LeafletMapWidget


class HotelAdminForm(forms.ModelForm):

    class Meta:
        model = Hotel
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            # latitude dùng widget bản đồ
            'latitude': LeafletMapWidget(),
            # longitude ẩn — JS sẽ tự điền
            'longitude': forms.TextInput(attrs={
                'style': 'width:120px;font-family:monospace;font-size:13px;',
            }),
        }
        labels = {
            'latitude': '🗺 Bản đồ chọn tọa độ',
            'longitude': 'Kinh độ (tự điền khi click bản đồ)',
        }
        help_texts = {
            'latitude': '',
            'longitude': 'Tự động điền khi bạn click lên bản đồ phía trên.',
        }

    def clean(self):
        cleaned = super().clean()
        lat = cleaned.get('latitude')
        lng = cleaned.get('longitude')

        VN_LAT_MIN, VN_LAT_MAX = 8.18, 23.39
        VN_LNG_MIN, VN_LNG_MAX = 102.14, 109.46

        if lat is None or lng is None:
            raise forms.ValidationError(
                '⚠️ Vui lòng chọn tọa độ trên bản đồ trước khi lưu.'
            )
        if not (VN_LAT_MIN <= float(lat) <= VN_LAT_MAX):
            raise forms.ValidationError(
                f'Vĩ độ {lat} nằm ngoài Việt Nam! '
                f'Hợp lệ: {VN_LAT_MIN}° – {VN_LAT_MAX}°'
            )
        if not (VN_LNG_MIN <= float(lng) <= VN_LNG_MAX):
            raise forms.ValidationError(
                f'Kinh độ {lng} nằm ngoài Việt Nam! '
                f'Hợp lệ: {VN_LNG_MIN}° – {VN_LNG_MAX}°'
            )
        return cleaned
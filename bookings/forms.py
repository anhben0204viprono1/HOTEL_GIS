from django import forms
from .models import Booking
from datetime import date, timedelta


class BookingForm(forms.Form):
    check_in = forms.DateField(
        label='Ngày nhận phòng',
        widget=forms.DateInput(attrs={
            'type': 'date', 'class': 'form-control',
            'min': str(date.today()),
        })
    )
    check_out = forms.DateField(
        label='Ngày trả phòng',
        widget=forms.DateInput(attrs={
            'type': 'date', 'class': 'form-control',
            'min': str(date.today() + timedelta(days=1)),
        })
    )
    num_guests = forms.IntegerField(
        label='Số khách', min_value=1, max_value=10, initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1})
    )
    note = forms.CharField(
        label='Yêu cầu đặc biệt', required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 3,
            'placeholder': 'VD: Phòng tầng cao, view đẹp, giường phụ...',
        })
    )

    def __init__(self, *args, room_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_type = room_type
        if room_type:
            self.fields['num_guests'].max_value = room_type.max_occupancy
            self.fields['num_guests'].widget.attrs['max'] = room_type.max_occupancy

    def clean_check_in(self):
        ci = self.cleaned_data['check_in']
        if ci < date.today():
            raise forms.ValidationError('Ngày nhận phòng không được trong quá khứ.')
        return ci

    def clean(self):
        cleaned = super().clean()
        ci = cleaned.get('check_in')
        co = cleaned.get('check_out')
        ng = cleaned.get('num_guests')

        if ci and co:
            if co <= ci:
                raise forms.ValidationError('Ngày trả phòng phải sau ngày nhận phòng.')
            if (co - ci).days > 30:
                raise forms.ValidationError('Không thể đặt phòng quá 30 đêm liên tiếp.')

        if ng and self.room_type and ng > self.room_type.max_occupancy:
            raise forms.ValidationError(
                f'Loại phòng này chỉ chứa tối đa {self.room_type.max_occupancy} khách.'
            )

        return cleaned


class ReviewForm(forms.Form):
    """Form đánh giá sau khi trả phòng."""
    RATING_CHOICES = [(i, f'{i} sao') for i in range(1, 6)]

    rating = forms.ChoiceField(
        label='Điểm đánh giá',
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'star-radio'}),
    )
    comment = forms.CharField(
        label='Nhận xét',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 4,
            'placeholder': 'Chia sẻ trải nghiệm của bạn tại khách sạn...',
        })
    )

    def clean_rating(self):
        r = int(self.cleaned_data['rating'])
        if r not in range(1, 6):
            raise forms.ValidationError('Điểm đánh giá phải từ 1 đến 5.')
        return r

from django import forms
from .models import Booking
from datetime import date, timedelta


class BookingForm(forms.Form):
    """
    Form đặt phòng — không dùng ModelForm để kiểm soát validation tốt hơn.
    Nhận room_type để validate số khách và tính giá preview.
    """
    check_in  = forms.DateField(
        label='Ngày nhận phòng',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': str(date.today()),
        })
    )
    check_out = forms.DateField(
        label='Ngày trả phòng',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': str(date.today() + timedelta(days=1)),
        })
    )
    num_guests = forms.IntegerField(
        label='Số khách',
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1})
    )
    note = forms.CharField(
        label='Yêu cầu đặc biệt',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
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

        if ng and self.room_type:
            if ng > self.room_type.max_occupancy:
                raise forms.ValidationError(
                    f'Loại phòng này chỉ chứa tối đa {self.room_type.max_occupancy} khách.'
                )

        return cleaned


class HourlyBookingForm(forms.Form):
    """
    Form đặt phòng theo giờ.
    """
    check_in_dt = forms.DateTimeField(
        label="Giờ nhận phòng",
        widget=forms.DateTimeInput(attrs={
            "type": "datetime-local",
            "class": "form-control",
        }),
    )
    check_out_dt = forms.DateTimeField(
        label="Giờ trả phòng",
        widget=forms.DateTimeInput(attrs={
            "type": "datetime-local",
            "class": "form-control",
        }),
    )
    num_guests = forms.IntegerField(
        label="Số khách",
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1}),
    )
    note = forms.CharField(
        label="Yêu cầu đặc biệt",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "VD: Nhận phòng sớm, ưu tiên yên tĩnh...",
        }),
    )

    def __init__(self, *args, room_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_type = room_type
        if room_type:
            self.fields["num_guests"].max_value = room_type.max_occupancy
            self.fields["num_guests"].widget.attrs["max"] = room_type.max_occupancy

    def clean(self):
        cleaned = super().clean()
        ci = cleaned.get("check_in_dt")
        co = cleaned.get("check_out_dt")
        ng = cleaned.get("num_guests")

        if ci and co:
            if co <= ci:
                raise forms.ValidationError("Giờ trả phòng phải sau giờ nhận phòng.")
            if (co - ci).total_seconds() > 48 * 3600:
                raise forms.ValidationError("Không thể đặt theo giờ quá 48 giờ.")

        if ng and self.room_type and ng > self.room_type.max_occupancy:
            raise forms.ValidationError(
                f"Loại phòng này chỉ chứa tối đa {self.room_type.max_occupancy} khách."
            )

        return cleaned

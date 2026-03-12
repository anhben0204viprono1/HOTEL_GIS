from django import forms
from .models import Booking
from datetime import date


class BookingForm(forms.ModelForm):
    class Meta:
        model  = Booking
        fields = ['check_in', 'check_out', 'num_guests', 'note']
        widgets = {
            'check_in':    forms.DateInput(attrs={'type':'date','class':'form-control','min':str(date.today())}),
            'check_out':   forms.DateInput(attrs={'type':'date','class':'form-control','min':str(date.today())}),
            'num_guests':  forms.NumberInput(attrs={'class':'form-control','min':1,'max':10}),
            'note':        forms.Textarea(attrs={'class':'form-control','rows':3}),
        }
        labels = {
            'num_guests': 'Số khách',
            'note':       'Yêu cầu đặc biệt',
        }

    def clean(self):
        cleaned = super().clean()
        ci = cleaned.get('check_in')
        co = cleaned.get('check_out')
        if ci and co:
            if ci < date.today():
                raise forms.ValidationError('Ngày nhận phòng không được trong quá khứ.')
            if co <= ci:
                raise forms.ValidationError('Ngày trả phòng phải sau ngày nhận phòng.')
        return cleaned
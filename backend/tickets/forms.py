from django import forms

class BuyTicketForm(forms.Form):
    start = forms.CharField(max_length=200)
    end = forms.CharField(max_length=200)

class VerifyOTPForm(forms.Form):
    code = forms.CharField(max_length=10, label='Enter OTP')

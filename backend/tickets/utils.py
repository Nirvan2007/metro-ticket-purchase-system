import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail.mail import Mail
from tickets.models import Config
from allauth.socialaccount.models import SocialAccount

APIKEY=os.environ.get("SENDGRID_API_KEY", "APIKEY")

from_email = ('noreplay@metro.teztravels.com', 'Metro Ticketing System')

def get_service_status():
    try:
        config = Config.objects.all().first()
        service_enable = config.enable
    except Exception:
        service_enable = True
    return service_enable

def send_email(user, subject, body):
    to_email = user.email
    if not to_email:
        try:
            sa = SocialAccount.objects.get(user=user)
        except SocialAccount.DoesNotExist:
            return
        to_email = sa.extra_data.get("email", "")
        if not to_email:
            return
    api = SendGridAPIClient(APIKEY)
    to_email = to_email.split(",")
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=body,
    )
    api.send(message)

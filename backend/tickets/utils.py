import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail.mail import Mail
from tickets.models import Config

APIKEY=os.environ.get("SENDGRID_API_KEY", "APIKEY")

from_email = ('noreplay@metro.teztravels.com', 'Metro Ticketing System')

def get_service_status():
    try:
        config = Config.objects.all().first()
        service_enable = config.enable
    except Exception:
        service_enable = True
    return service_enable

def send_email(body):
    api = SendGridAPIClient(APIKEY)
    to_email=body.get("to")
    if not to_email:
        return
    to_email=to_email.split(",")
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=body.get("subject"),
        html_content=body.get("content")
    )
    api.send(message)

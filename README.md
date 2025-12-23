# Metro Ticket Purchasing System

Google OAuth integration stubs via django-allauth (configure client id/secret in .env)
OTP verification (strict): tickets are only created after the user verifies the OTP sent to their email.
Email sending on OTP and on successful ticket purchase (configure SMTP in .env)

## Local dev usage:
1. Open 'backend' in VS Code
2. Create Virtual environment
   ```
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. copy backend/.env.example -> backend/.env and fill EMAIL, OAuth keys and Sendgrid API Key
4. python manage.py migrate
5. python manage.py load_stations (will remove all the lines and load the lines again from pre-defined structure)
6. gunicorn metro.wsgi:application --bind 0.0.0.0:8000

## Email notification:

Email notification is sent for ticket purchase OTP and successful purchase of ticket.
Earlier it was implemented using Django email sending module to send email using external SMTP server.
Production system is deployed using Ubuntu Droplet on Digital Ocean. Digital ocean does not allow outgoing SMTP service.
Therefore **sendgrid** is used for sending email. Configure your sendgrid apikey in .env file using **SENDGRID_API_KEY** key.

## Notes:
- OTP expires in 5 minutes.
- PurchaseRequest model is used to hold pending purchases until OTP verification.
- After OTP verification, a Ticket is created and a confirmation email is sent.

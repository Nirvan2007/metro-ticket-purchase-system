Metro Ticket Purchasing System


Google OAuth integration stubs via django-allauth (configure client id/secret in .env)
OTP verification (strict): tickets are only created after the user verifies the OTP sent to their email.
Email sending on OTP and on successful ticket purchase (configure SMTP in .env)

Local dev usage:
1. Open 'backend' in VS Code
2. Create Virtual environment
   ```
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. copy backend/.env.example -> backend/.env and fill EMAIL and OAuth keys
5. python manage.py migrate
6. python manage.py load_stations
7. python manage.py runserver

Notes:
- OTP expires in 5 minutes.
- PurchaseRequest model is used to hold pending purchases until OTP verification.
- After OTP verification, a Ticket is created and a confirmation email is sent.

# Metro Ticket Purchasing System

**Metro Ticket Purchasing System** is implemented using **Django** framework.
Implements two types of login **Passenger** and **Admin**

## Passenger
Any user can signup for Passenger role. Following options are available for Passenger:
1. Purchase Ticket Online - Validates using OTP sent on email
2. View already purchased ticket with status, price, path and direction
3. Add money to wallet for ticket purchase - no validation
4. Scan purchased ticket to enter and exit metro station
5. Manage user profile
6. View station list for a given metro line

## Admin
Any user which has **is_staff** as **true** in **User** model. Following options are available for Admin:
1. Add new line to metro network
2. Add station in any existing line and update position of already added station in line
3. Purchase offline ticket on behalf of customer and mark it USED
4. Start / Stop Metro Service, also enable / disable particular line for service
5. View current date footfall grouped by each line
6. Scan ticket for any user
7. View station list for a given metro line
8. Manage user profile

Google OAuth integration stubs via django-allauth (configure client id/secret in .env)
OTP verification (strict): tickets are only created after the user verifies the OTP sent to their email.
Email sending on OTP and on successful ticket purchase (configure SMTP in .env)

## Local dev usage:
1. Open 'backend' in VS Code
2. Create Virtual environment
   ```
   python -m venv .venv
   source .venv/bin/activatet
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

## Production Environment
- Deployed using Ubuntu Droplet on Digital ocean
- Uses **docker compose** to run 3 docker containers
- NGINX Web Server to handle incoming HTTPS request
- Only HTTPS is supported and certificate is issued using Lets Encrypt service
- Application Server running python code for the application using Django and gunicorn
- Database Server running PostgreSQL
- sendgrid to send email notification

## Notes:
- OTP expires in 5 minutes.
- PurchaseRequest model is used to hold pending purchases until OTP verification.
- After OTP verification, a Ticket is created and a confirmation email is sent.

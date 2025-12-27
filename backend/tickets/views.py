from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Ticket, Station, Wallet, PurchaseRequest, OTP, Line, StationLine
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
import random
from .forms import VerifyOTPForm
from tickets.metro_graph import (
    shortest_path_by_adj,
    get_direction,
    calc_price_from_path
)
from .utils import send_email, get_service_status

def home(request):
    return render(request, 'tickets/home.html', {})

@login_required
def buy_ticket(request):
    message = ''
    stations = Station.objects.all().order_by('name')

    if request.method == 'POST':
        start_name = request.POST.get('start')
        end_name = request.POST.get('end')

        if start_name == end_name:
            return render(request, 'tickets/buy_ticket.html', {
                'stations': stations,
                'error': "Start and End Station cannot be same."
            })

        try:
            start_obj = Station.objects.get(name=start_name)
            end_obj = Station.objects.get(name=end_name)
        except Station.DoesNotExist:
            message = 'Invalid station names'
            return render(request, 'tickets/buy_ticket.html', {
                'stations': stations,
                'error': message
            })
        path, lines = shortest_path_by_adj(start_obj, end_obj)

        if not path:
            error = f'No path found between {start_name} -> {end_name}.'
            return render(request, 'tickets/buy_ticket.html', {
                'stations': stations,
                'error': error
            })

        price = calc_price_from_path(path)
        direction = get_direction(path, lines)

        try:
            wallet = Wallet.objects.get(user=request.user)
            balance = wallet.balance
        except Exception:
            balance = 0
        if balance < price:
            return render(request, 'tickets/buy_ticket.html', {
                'stations': stations,
                'error': f"Insufficient fund, required {price} available {balance}."
            })
        purchase = PurchaseRequest.objects.create(
            user=request.user,
            start_name=start_name,
            end_name=end_name,
            path=path,
            direction=lines,
            price=price
        )
        code = str(random.randint(100000, 999999))
        expires = timezone.now() + timedelta(minutes=5)
        print("code: ", code)
        OTP.objects.create(
            purchase=purchase,
            code=code,
            expires_at=expires
        )
        subject = 'Your Metro Ticket OTP'
        body = (
            f'Your OTP to confirm metro ticket from <b>{start_name}</b> to <b>{end_name}</b> is: <b>{code}</b>.<br>'
            f'It expires at <b>{expires}</b>.<br>If you did not request this, ignore.'
        )

        try:
            send_email(
                {
                    "to": request.user.email,
                    "subject": subject,
                    "content": body
                }
            )
        except Exception as e:
            print("Unable to send email:", str(e))

        return render(request, 'tickets/otp_sent.html', {
            'purchase': purchase,
            'path': path,
            'directions': direction
        })

    return render(request, 'tickets/buy_ticket.html', {
        'stations': stations,
        'message': message
    })


@login_required
def resend_otp(request, purchase_id):
    purchase = get_object_or_404(PurchaseRequest, id=purchase_id, user=request.user)
    code = str(random.randint(100000, 999999))
    expires = timezone.now() + timedelta(minutes=5)
    print("code: ", code)
    OTP.objects.create(
        purchase=purchase,
        code=code,
        expires_at=expires
    )
    subject = 'Your Metro Ticket OTP'
    body = (
        f'Your OTP to confirm metro ticket from <b>{purchase.start_name}</b> to <b>{purchase.end_name}</b> is: <b>{code}</b>.<br>'
        f'It expires at <b>{expires}</b>.<br>If you did not request this, ignore.'
    )

    try:
        send_email(
            {
                "to": request.user.email,
                "subject": subject,
                "content": body
            }
        )
    except Exception as e:
        print("Unable to send email:", str(e))
    form = VerifyOTPForm()
    #return render(request, 'tickets/verify_otp.html', {'form': form, 'purchase': purchase})
    return redirect('tickets:verify_otp', purchase.id)


@login_required
def verify_otp(request, purchase_id):
    purchase = get_object_or_404(PurchaseRequest, id=purchase_id, user=request.user)
    latest_otp = purchase.otps.order_by('-created_at').first()
    if request.method == 'POST':
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code'].strip()
            if latest_otp and latest_otp.code == code and latest_otp.is_valid():
                start_obj = Station.objects.get(name=purchase.start_name)
                end_obj = Station.objects.get(name=purchase.end_name)
                try:
                    wallet = Wallet.objects.get(user=request.user)
                except Wallet.DoesNotExist:
                    wallet = Wallet.objects.create(user=request.user, balance=0)
                if purchase.price > wallet.balance:
                    return render(request, 'tickets/wallet_view.html', {
                        'balance': wallet.balance, 'message': f"Insufficent fund need {purchase.price}"}) 
                wallet.balance = wallet.balance - purchase.price
                wallet.save()
                ticket = Ticket.objects.create(user=request.user, start=start_obj, end=end_obj, path=purchase.path, direction=purchase.direction, price=purchase.price, expires_at=timezone.now()+timedelta(hours=6), status='ACTIVE')
                path = ", ".join(purchase.path)
                direction = get_direction(purchase.path, purchase.direction)
                direction = " - ".join(direction)
                subject = 'Metro Ticket Purchased'
                body = f'Your ticket (ID: <b>{ticket.id}</b>) from <b>{ticket.start.name}</b> to <b>{ticket.end.name}</b> has been issued. Price: <b>{ticket.price}</b>.<br>Please follow following direction:<br>Path: <b>{path}</b><br>Direction: <b>{direction}</b>'
                try:
                    send_email({
                        'to': request.user.email,
                        'subject': subject,
                        'content': body
                    })
                except Exception as e:
                    print("Unable to send email:", str(e))
                purchase.delete()
                return redirect('tickets:ticket_list')
            else:
                form.add_error('code', 'Invalid or expired OTP.')
    else:
        form = VerifyOTPForm()
    return render(request, 'tickets/verify_otp.html', {'form': form, 'purchase': purchase})

@login_required
def ticket_list(request):
    tickets = Ticket.objects.filter(user=request.user).order_by('-created_at')
    for ticket in tickets:
        ticket.direction = get_direction(ticket.path, ticket.direction)
        ticket.direction = " - ".join(ticket.direction)
        ticket.path = ", ".join(ticket.path)
    return render(request, 'tickets/ticket_list.html', {'tickets': tickets})

@login_required
def wallet_view(request):
    message = ''
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=request.user, balance=0)
    if request.method == 'POST':
        try:
            money = int(request.POST.get("money", 0))
        except Exception:
            return render(request, 'tickets/wallet_view.html', {
                'balance': wallet.balance,
                'error': "Invalid money added"})
        wallet.balance = wallet.balance + money
        wallet.save()
        message = f'{money} added to wallet.'
    return render(request, 'tickets/wallet_view.html', {
        'balance': wallet.balance, 'message': message})

@login_required
def scanner_view(request):
    return render(request, 'tickets/scanner.html', {})

@login_required
def scan_ticket_api(request, ticket_id):
    try:
        ticket = Ticket.objects.get(id=ticket_id)
    except Ticket.DoesNotExist:
        return JsonResponse({'error': 'Invalid Ticket ID'})
    #ticket = get_object_or_404(Ticket, id=ticket_id)
    if not request.user.is_staff and ticket.user.id != request.user.id:
        return JsonResponse({'error': 'Invalid Ticket ID'})
    action = request.GET.get('action','toggle')
    if action == 'enter':
        if ticket.status == 'ACTIVE':

            if not get_service_status():
                return JsonResponse({'error': "Metro service is disabled, so cannot enter metro"})
            # validation if line is open for use
            curr_line = ""
            for l in ticket.direction:
                if l == curr_line:
                    continue
                curr_line = l
                try:
                    ln = Line.objects.get(name=l)
                    if not ln.enable:
                        return JsonResponse({'error': f"Line {l} is not operative, so cannot buy this ticket."})
                except Exception:
                    return JsonResponse({'error': 'Invalid path selected.'})
 
            ticket.status = 'IN_USE'
            ticket.started_at = timezone.now()
        else:
            return JsonResponse({'error': 'Ticket must be in ACTIVE state to enter'})
    elif action == 'exit':
        if ticket.status == 'IN_USE':
            ticket.status = 'USED'
            ticket.ended_at = timezone.now()
        else:
            return JsonResponse({'error': 'Ticket must be in IN_USE state to exit'})
    else:
        ticket.status = 'USED' if ticket.status != 'USED' else 'ACTIVE'
    ticket.save()
    return JsonResponse({'status': ticket.status, 'ticket_id': ticket.id})


@login_required
def station_list(request):
    lines = Line.objects.all().order_by("name")
    stations = []
    line = ''
    if request.method == 'POST':
        line_name = request.POST.get("line")
        if not line_name:
            return render(request, 'tickets/station_list.html',
                {"lines": lines, "stations": stations}
            )
        try:
            ln = Line.objects.get(name=line_name)
        except Line.DoesNotExist:
            return render(request, 'tickets/station_list.html',
                {"lines": lines, "stations": stations}
            )
        stations = StationLine.objects.filter(line=ln).order_by("position")
        line = line_name
    return render(request, 'tickets/station_list.html',
        {"lines": lines, "stations": stations, "ln": line}
    )

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Ticket, Station, Wallet, PurchaseRequest, OTP
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from delhi_metro_lines import load_data, shortest_path, line, get_station_by_name
from django.core.mail import send_mail
from django.conf import settings
import random
from .forms import VerifyOTPForm
from tickets.metro_graph import (
    build_graph,
    shortest_path_by_name,
    generate_directions,
    calc_price_from_path
)
def home(request):
    return render(request, 'tickets/home.html', {})

@login_required
def buy_ticket(request):
    message = ''
    stations = Station.objects.all().order_by('name')

    if request.method == 'POST':
        start_name = request.POST.get('start')
        end_name = request.POST.get('end')

        try:
            start_obj = Station.objects.get(name=start_name)
            end_obj = Station.objects.get(name=end_name)
        except Station.DoesNotExist:
            message = 'Invalid station names'
            return render(request, 'tickets/buy_ticket.html', {
                'stations': stations,
                'message': message
            })
        graph = build_graph()
        path_names = shortest_path_by_name(start_name, end_name, graph)

        if not path_names:
            message = 'No path found'
            return render(request, 'tickets/buy_ticket.html', {
                'stations': stations,
                'message': message
            })

        price = calc_price_from_path(path_names)
        directions = generate_directions(path_names)

        purchase = PurchaseRequest.objects.create(
            user=request.user,
            start_name=start_name,
            end_name=end_name,
            path=path_names,
            price=price
        )
        code = str(random.randint(100000, 999999))
        expires = timezone.now() + timedelta(minutes=5)
        OTP.objects.create(
            purchase=purchase,
            code=code,
            expires_at=expires
        )
        subject = 'Your Metro Ticket OTP'
        body = (
            f'Your OTP to confirm metro ticket from {start_name} to {end_name} is: {code}.\n'
            f'It expires at {expires}.\nIf you did not request this, ignore.'
        )

        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=False
        )

        return render(request, 'tickets/otp_sent.html', {
            'purchase': purchase,
            'directions': directions
        })

    return render(request, 'tickets/buy_ticket.html', {
        'stations': stations,
        'message': message
    })


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
                ticket = Ticket.objects.create(user=request.user, start=start_obj, end=end_obj, path=purchase.path, price=purchase.price, expires_at=timezone.now()+timedelta(hours=6), status='ACTIVE')
                subject = 'Metro Ticket Purchased'
                body = f'Your ticket (ID: {ticket.id}) from {ticket.start.name} to {ticket.end.name} has been issued. Price: {ticket.price}.'
                send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [request.user.email], fail_silently=False)
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
    return render(request, 'tickets/ticket_list.html', {'tickets': tickets})

@login_required
def scanner_view(request):
    return render(request, 'tickets/scanner.html', {})

@login_required
def scan_ticket_api(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if not request.user.is_staff and ticket.user.id != request.user.id:
        return render(request, 'tickets/scanner.html', {})
    action = request.GET.get('action','toggle')
    if action == 'enter':
        ticket.status = 'IN_USE'
    elif action == 'exit':
        ticket.status = 'USED'
    else:
        ticket.status = 'USED' if ticket.status != 'USED' else 'ACTIVE'
    ticket.save()
    return JsonResponse({'status': ticket.status, 'ticket_id': ticket.id})

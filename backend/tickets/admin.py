from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Ticket, Station, Line, StationLine, Config
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta, date, datetime
from delhi_metro_lines import load_data, shortest_path, line, get_station_by_name
from django.core.mail import send_mail
from django.conf import settings
from .forms import VerifyOTPForm
from tickets.metro_graph import (
    shortest_path_by_adj,
    get_direction,
    calc_price_from_path
)
from .utils import get_service_status

def is_admin_staff(user):
    return user.is_staff

@user_passes_test(is_admin_staff)
def add_line(request):
    message = ''

    if request.method == 'POST':
        line_name = request.POST.get('line_name').strip()
        if not line_name:
            error = 'No Line Name Given'
            return render(request, 'tickets/add_line.html', {
                'error': error
            })
        try:
            line = Line.objects.get(name__iexact=line_name)
            error = 'Line Already Exist'
            return render(request, 'tickets/add_line.html', {
                'error': error
            })
        except Line.DoesNotExist:
            pass
        Line.objects.create(name=line_name)
        message = f"{line_name} added successfully."

    return render(request, 'tickets/add_line.html', {
        'message': message
    })


@user_passes_test(is_admin_staff)
def add_station(request):
    message = ''
    lines = Line.objects.all().order_by('name')

    if request.method == 'POST':
        line = request.POST.get('line')
        station = request.POST.get('station').strip()
        if not station:
            return render(request, 'tickets/add_station.html', {
                'lines': lines,
                'error': 'No Station Name Given.'
            })
        try:
            position = request.POST.get('position', 1000)
            if not position:
                position = 1000
            position = int(position)
        except Exception:
            return render(request, 'tickets/add_station.html', {
                'lines': lines,
                'error': 'Invalid station position.'
            })
        try:
            line_obj = Line.objects.get(name__iexact=line)
        except Line.DoesNotExist:
            return render(request, 'tickets/add_station.html', {
                'lines': lines,
                'error': f"Provided Line {line} Does not exist."
            })
        try:
            station_obj = Station.objects.get(name__iexact=station)
        except Station.DoesNotExist:
            station_obj = Station.objects.create(name=station)

        st_lines = StationLine.objects.filter(line=line_obj).order_by('position')
        ins_position = 1
        st = None
        for s in st_lines:
            if s.station_id == station_obj.id:
                st = s
            if s.position == position:
                ins_position = position
                if st:
                    continue
                s.position = s.position + 1
                s.save()
            elif s.position > position:
                if st:
                    continue
                s.position = s.position + 1
                s.save()
            else:
                ins_position = s.position + 1
                if not st:
                    continue
                ins_position = s.position
                s.position = s.position - 1
                s.save()
        if not st:
            StationLine.objects.create(line=line_obj, station=station_obj, position=ins_position)
        else:
            st.position = ins_position
            st.save()
        message = f"{station} inserted / updated at {ins_position} position in {line} line."

    return render(request, 'tickets/add_station.html', {
        'lines': lines,
        'message': message
    })


def create_manage_line_page(request, error='', message=''):
    service_enable = get_service_status()
    enable_lines = Line.objects.filter(enable=True).order_by("name")
    disable_lines = Line.objects.filter(enable=False).order_by("name")
    return render(request, 'tickets/manage_line.html', {
        'message': message,
        'error': error,
        'enable_lines': enable_lines,
        'disable_lines': disable_lines,
        'start': "disabled" if service_enable else "",
        'stop': "" if service_enable else "disabled"
    })

@user_passes_test(is_admin_staff)
def manage_line(request, enable=False, service=False):
    message = ''

    if request.method == 'POST':
        if service:
            try:
                config = Config.objects.all().first()
                if not config:
                    raise Config.DoesNotExist
                config.enable = enable
                config.save()
            except Config.DoesNotExist:
                Config.objects.create(enable=enable)
            service_enable = enable
            message = f'Metro service {"started" if enable else "stoped"}.'
            return create_manage_line_page(request, '', message)
        line = "dis_line" if enable else "en_line"
        line_name = request.POST.get(line)
        if not line_name:
            error = 'No Line Name Given'
            return create_manage_line_page(request, error, message)
        try:
            line = Line.objects.get(name__iexact=line_name)
        except Line.DoesNotExist:
            return create_manage_line_page(request, "Line not found.", message)
        line.enable = enable
        line.save()
        message = f"Line {line_name} {'enabled' if enable else 'disabled'} for service."
    return create_manage_line_page(request, '', message)

@user_passes_test(is_admin_staff)
def enable_line(request):
    return manage_line(request, enable=True)

@user_passes_test(is_admin_staff)
def disable_line(request):
    return manage_line(request, enable=False)

@user_passes_test(is_admin_staff)
def start_service(request):
    return manage_line(request, enable=True, service=True)

@user_passes_test(is_admin_staff)
def stop_service(request):
    return manage_line(request, enable=False, service=True)

@user_passes_test(is_admin_staff)
def buy_ticket_offline(request):
    message = ''
    path = ''
    direction = ''
    service_enable = get_service_status()
    stations = Station.objects.all().order_by('name')

    if request.method == 'POST':
        start_name = request.POST.get('start')
        end_name = request.POST.get('end')
        if start_name == end_name:
            return render(request, 'tickets/buy_ticket_offline.html', {
                'stations': stations,
                'error': "Start and End Station cannot be same."
            })

        if not service_enable:
            return render(request, 'tickets/buy_ticket_offline.html', {
                'stations': stations,
                'error': 'Metro service not running cannot buy offline ticket now.'
            })
        try:
            start_obj = Station.objects.get(name=start_name)
            end_obj = Station.objects.get(name=end_name)
        except Station.DoesNotExist:
            message = 'Invalid station names'
            return render(request, 'tickets/buy_ticket_offline.html', {
                'stations': stations,
                'error': message
            })
        path, lines = shortest_path_by_adj(start_obj, end_obj)
        if not path:
            message = f'No path found between {start_name} -> {end_name}'
            return render(request, 'tickets/buy_ticket_offline.html', {
                'stations': stations,
                'error': message
            })

        # validation if line is open for use
        curr_line = ""
        for l in lines:
            if l == curr_line:
                continue
            curr_line = l
            try:
                ln = Line.objects.get(name=l)
                if not ln.enable:
                    return render(request, 'tickets/buy_ticket_offline.html', {
                        'stations': stations,
                        'error': f"Line {l} is not operative, so cannot buy this ticket."
                    })
            except Exception:
                return render(request, 'tickets/buy_ticket_offline.html', {
                    'stations': stations,
                    'error': "Invalid Path."
                })
        price = calc_price_from_path(path)
        direction = get_direction(path, lines)

        ticket = Ticket.objects.create(
            user=request.user,
            start=start_obj,
            end=end_obj,
            path=path,
            direction=lines,
            price=price,
            status='USED',
            started_at=timezone.now(),
            ended_at=timezone.now()
        )
        path = ", ".join(path)
        direction = " - ".join(direction)
        message = f"A ticket has been purchased from {start_name} -> {end_name} at price {price} and marked as used."

    return render(request, 'tickets/buy_ticket_offline.html', {
        'stations': stations,
        'message': message,
        'path': path,
        'direction': direction
    })


@user_passes_test(is_admin_staff)
def foot_fall(request):
    lines = {}
    stations={}
    today = date.today()
    tickets = Ticket.objects.filter(started_at__gte=today.isoformat())
    for ticket in tickets:
        if ticket.status not in ["IN_USE", "USED"]:
            continue
        if not len(ticket.direction):
            continue
        curr_line = ticket.direction[0]
        i = 0
        stations[ticket.path[0]] = stations[ticket.path[0]] + 1 if ticket.path[0] in stations else 1
        lines[ticket.direction[0]] = lines[ticket.direction[0]] + 1 if ticket.direction[0] in lines else 1
        for st in ticket.path:
            if i < len(ticket.direction) and curr_line != ticket.direction[i]:
                lines[ticket.direction[i]] = lines[ticket.direction[i]] + 1 if ticket.direction[i] in lines else 1
                stations[st] = stations[st] + 1 if st in stations else 1
                curr_line = ticket.direction[i]
            i = i + 1
        stations[st] = stations[st] + 1 if st in stations else 1
    return render(request, 'tickets/line_footfall.html', {
        'today': today,
        'lines': lines,
        'stations': stations
    })

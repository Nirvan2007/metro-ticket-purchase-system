from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Ticket, Station, Line, StationLine
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from delhi_metro_lines import load_data, shortest_path, line, get_station_by_name
from django.core.mail import send_mail
from django.conf import settings
from .forms import VerifyOTPForm
from tickets.metro_graph import (
    shortest_path_by_adj,
    get_direction,
    calc_price_from_path
)

@login_required
def add_line(request):
    message = ''

    if request.method == 'POST':
        line_name = request.POST.get('line_name')
        if not line_name:
            message = 'No Line Name Given'
            return render(request, 'tickets/add_line.html', {
                'message': message
            })
        try:
            line = Line.objects.get(name__iexact=line_name)
            message = 'Line Already Exist'
            return render(request, 'tickets/add_line.html', {
                'message': message
            })
        except Line.DoesNotExist:
            pass
        line = Line.objects.create(name=line_name)

        return render(request, 'tickets/add_line.html', {
            'message': f"{line_name} added successfully."
        })

    return render(request, 'tickets/add_line.html', {
        'message': message
    })


@login_required
def add_station(request):
    message = ''
    lines = Line.objects.all().order_by('name')

    if request.method == 'POST':
        line = request.POST.get('line')
        station = request.POST.get('station')
        try:
            position = int(request.POST.get('position', 1000))
        except Exception:
            return render(request, 'tickets/add_station.html', {
                'lines': lines,
                'message': 'Invalid station position.'
            })
        try:
            line_obj = Line.objects.get(name__iexact=line)
        except Line.DoesNotExist:
            return render(request, 'tickets/add_station.html', {
                'lines': lines,
                'message': 'Provided Line Does not exist.'
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
        return render(request, 'tickets/add_station.html', {
            'lines': lines,
            'message': f"{station} {st} at {ins_position}"
        })

    return render(request, 'tickets/add_station.html', {
        'lines': lines,
        'message': message
    })


@login_required
def manage_line(request, enable=False):
    message = ''

    enable_lines = Line.objects.filter(enable=True)
    disable_lines = Line.objects.filter(enable=False)
    if request.method == 'POST':
        line = "dis_line" if enable else "en_line"
        line_name = request.POST.get(line)
        if not line_name:
            message = 'No Line Name Given'
            return render(request, 'tickets/manage_line.html', {
                'message': message,
                'enable_lines': enable_lines,
                'disable_lines': disable_lines
            })
        try:
            line = Line.objects.get(name__iexact=line_name)
        except Line.DoesNotExist:
            return render(request, 'tickets/manage_line.html', {
                'message': 'Line not found.',
                'enable_lines': enable_lines,
                'disable_lines': disable_lines
            })
        line.enable = enable
        line.save()
        message = f"Line {line_name} {'enabled' if enable else 'disabled'} for service."

    enable_lines = Line.objects.filter(enable=True)
    disable_lines = Line.objects.filter(enable=False)
    return render(request, 'tickets/manage_line.html', {
        'message': message,
        'enable_lines': enable_lines,
        'disable_lines': disable_lines
    })


@login_required
def enable_line(request):
    return manage_line(request, enable=True)

@login_required
def disable_line(request):
    return manage_line(request, enable=False)

@login_required
def buy_ticket_offline(request):
    message = ''
    path = ''
    direction = ''
    stations = Station.objects.all().order_by('name')

    if request.method == 'POST':
        start_name = request.POST.get('start')
        end_name = request.POST.get('end')
        if start_name == end_name:
            return render(request, 'tickets/buy_ticket_offline.html', {
                'stations': stations,
                'message': "Start and End Station cannot be same."
            })

        try:
            start_obj = Station.objects.get(name=start_name)
            end_obj = Station.objects.get(name=end_name)
        except Station.DoesNotExist:
            message = 'Invalid station names'
            return render(request, 'tickets/buy_ticket_offline.html', {
                'stations': stations,
                'message': message
            })
        #graph = build_graph()
        #path_names = shortest_path_by_name(start_name, end_name, graph)
        path, lines = shortest_path_by_adj(start_obj, end_obj)

        if not path:
            message = 'No path found'
            return render(request, 'tickets/buy_ticket_offline.html', {
                'stations': stations,
                'message': message
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
                        'message': f"Line {l} is not operative, so cannot buy this ticket."
                    })
            except Exception:
                return render(request, 'tickets/buy_ticket_offline.html', {
                    'stations': stations,
                    'message': "Invalid Path."
                })
        price = calc_price_from_path(path)
        #directions = generate_directions(path_names)
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
        message = f"A ticket has been purchased from {start_name} -> {end_name} and marked as used."

    return render(request, 'tickets/buy_ticket_offline.html', {
        'stations': stations,
        'message': message,
        'path': path,
        'direction': direction
    })



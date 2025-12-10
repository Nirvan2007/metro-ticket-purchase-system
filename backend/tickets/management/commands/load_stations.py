from django.core.management.base import BaseCommand
from tickets.models import Station, Line, StationLine
from delhi_metro_lines import load_data

class Command(BaseCommand):
    help = 'Load stations from delhi_metro_lines into Station model'

    def handle(self, *args, **options):
        Stations, names = load_data()
        Line.objects.all().delete()
        for st in Stations:
            i = 0
            for line_name in st.line:
                try:
                    line = Line.objects.get(name=line_name)
                except Line.DoesNotExist:
                    line = Line.objects.create(name=line_name)
                try:
                    station = Station.objects.get(name=st.station_name)
                except Station.DoesNotExist:
                    station = Station.objects.create(name=st.station_name)
                StationLine.objects.create(station=station, line=line, position=st.position[i])
                i = i + 1
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(Stations)} stations.'))

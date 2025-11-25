from django.core.management.base import BaseCommand
from tickets.models import Station
from delhi_metro_lines import load_data

class Command(BaseCommand):
    help = 'Load stations from delhi_metro_lines into Station model'

    def handle(self, *args, **options):
        Stations, names = load_data()
        Station.objects.all().delete()
        for st in Stations:
            Station.objects.create(name=st.station_name, lines=st.line, positions=st.position)
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(Stations)} stations.'))

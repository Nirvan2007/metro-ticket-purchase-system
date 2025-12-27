
from tickets.models import StationLine

PRICE_PER_STATION = 10

def get_adj(station):
    adj = {}
    st_lines = StationLine.objects.filter(station=station)
    for line in st_lines:
        try:
            before = StationLine.objects.get(line=line.line, position=line.position-1)
        except StationLine.DoesNotExist:
            before = None
        try:
            after = StationLine.objects.get(line=line.line, position=line.position+1)
        except StationLine.DoesNotExist:
            after = None
        adj[line.line] = []
        if before:
            adj[line.line].append(before.station)
        if after:
            adj[line.line].append(after.station)
    return adj

def shortest_path_by_adj(start, stop):
    visited = [start.name]
    L = [(start, [start.name], [])]
    while L:
        current, path, lines = L.pop(0)
        if current.name == stop.name:
            return path, lines
        adjs = get_adj(current)
        for line, adj in adjs.items():
            for a in adj:
                if a.name not in visited:
                    neighbor = a
                    visited.append(a.name)
                    L.append((a, path + [a.name], lines + [line.name]))
    return None, None

def get_direction(path, lines):
    direction = []
    text = f"Start at {path[0]} on {lines[0]} line"
    direction.append(text)
    curr_line = lines[0]
    i = 0
    for st in path:
        if i < len(lines) and curr_line != lines[i]:
            text = f"Change to {lines[i]} at {st}"
            direction.append(text)
            curr_line = lines[i]
        i = i + 1
    text = f"Leave Metro at {st}"
    direction.append(text)
    return direction


def calc_price_from_path(path):
    if not path or len(path) <= 1:
        return 0
    return (len(path) - 1) * PRICE_PER_STATION

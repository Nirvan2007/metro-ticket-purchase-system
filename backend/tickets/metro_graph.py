
from collections import defaultdict, deque
import delhi_station_lists as dsl
from typing import List, Optional, Dict, Set
from tickets.models import Station, Line, StationLine

PRICE_PER_STATION = 10

_GRAPH_CACHE: Optional[Dict[str, List[str]]] = None

def _datasets():
    return [
        dsl.stations_red_line,
        dsl.stations_blue_line_main,
        dsl.stations_blue_line_branch,
        dsl.stations_green_line_main,
        dsl.stations_yellow_line,
        dsl.stations_violet_line,
        dsl.stations_green_line_branch,
        dsl.stations_pink_line,
        dsl.stations_airport_express_line,
        dsl.stations_magenta_line,
        dsl.stations_grey_line,
    ]

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

def build_graph(force_reload: bool = False) -> Dict[str, List[str]]:
    """
    Build adjacency graph from the line lists in delhi_station_lists.
    Returns mapping: station_name -> [neighbour_station_name, ...]
    """
    global _GRAPH_CACHE
    if _GRAPH_CACHE is not None and not force_reload:
        return _GRAPH_CACHE

    graph: Dict[str, Set[str]] = defaultdict(set)

    for data_list in _datasets():

        names = [t[0] for t in data_list]
        for i, name in enumerate(names):
            if i > 0:
                graph[name].add(names[i - 1])
            if i < len(names) - 1:
                graph[name].add(names[i + 1])

    _GRAPH_CACHE = {k: sorted(list(v)) for k, v in graph.items()}
    return _GRAPH_CACHE

def shortest_path_by_name(start_name: str, end_name: str, graph: Optional[Dict[str, List[str]]] = None) -> Optional[List[str]]:
    if graph is None:
        graph = build_graph()

    if start_name == end_name:
        return [start_name]

    visited = {start_name}
    dq = deque([(start_name, [start_name])])

    while dq:
        current, path = dq.popleft()
        for neigh in graph.get(current, []):
            if neigh not in visited:
                if neigh == end_name:
                    return path + [neigh]
                visited.add(neigh)
                dq.append((neigh, path + [neigh]))
    return None

def find_common_line_between(a: str, b: str) -> Optional[str]:
    for data_list in _datasets():
        names = [t[0] for t in data_list]
        if a in names and b in names:
            return data_list[0][1]
    return None

def generate_directions(path: List[str]) -> List[str]:
    dirn = []
    if not path:
        return dirn

    if len(path) == 1:
        dirn.append(f"You're already at {path[0]}")
        return dirn

    cur_line = find_common_line_between(path[0], path[1]) or "unknown line"
    dirn.append(f"Start at {path[0]} on {cur_line}")

    for i in range(0, len(path) - 1):
        a = path[i]
        b = path[i + 1]
        common = find_common_line_between(a, b)
        if common is None:
            next_line = None
            if i + 2 < len(path):
                next_line = find_common_line_between(path[i + 1], path[i + 2])
            next_line = next_line or "another line"
            dirn.append(f"Change at {a} from {cur_line} to {next_line}")
            cur_line = next_line
        else:
            cur_line = common

    dirn.append(f"Leave metro at {path[-1]}")
    return dirn

def calc_price_from_path(path: List[str]) -> int:
    if not path or len(path) <= 1:
        return 0
    return (len(path) - 1) * PRICE_PER_STATION

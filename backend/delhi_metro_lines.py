# delhi_metro_lines.py - adapted for Django import
#new
import delhi_station_lists as dsl

class Station:
    def __init__(self,station_name,line = None,position = None,adj = None):
        self.station_name = station_name
        self.line = line
        self.position = position
        self.adj = adj
        self.id = [self.line[0] + "_" + str(self.position[0])]
    def add_line(self,line,position):
        if self.line == None:
            self.line = []
            self.line.append(line)
        else:
            self.line.append(line)
        if self.position == None:
            self.position = []
            self.position.append(position)
        else:
            self.position.append(position)
    def update_id(self,line,position):
        self.id.append(line + "_" + str(position))
    def system(self,Lines,Stations):
        for i in range (0,len(self.line)):
            self.adj = []
            cur_line = self.line[i]
            cur_line_list = getattr(Lines, cur_line)
            for j in range(len(Stations)):
                if Stations[j].id == self.id:
                    if self.position[i] == 1:
                        try:
                            self.adj.append(Stations[j+1])
                        except IndexError:
                            pass
                    elif self.position[i] == cur_line_list[-1][2]:
                        self.adj.append(Stations[j-1])
                    else:
                        if j == len(Stations) - 1:
                            self.adj.append(Stations[j-1])
                        else:
                            self.adj.append(Stations[j+1])
                            self.adj.append(Stations[j-1])
                    break
        if len(self.line) > 1:
            for new in Stations:
                if new.station_name == self.station_name and new != self:
                    self.adj.append(new.station_name)
class line:
    def __init__(self):
        
        self.red_line = dsl.stations_red_line
        self.blue_line_main = dsl.stations_blue_line_main
        self.blue_line_branch = dsl.stations_blue_line_branch
        self.green_line_main = dsl.stations_green_line_main
        self.yellow_line = dsl.stations_yellow_line
        self.violet_line = dsl.stations_violet_line
        self.green_line_branch = dsl.stations_green_line_branch
        self.airport_express_line = dsl.stations_airport_express_line
        self.magenta_line = dsl.stations_magenta_line
        self.pink_line = dsl.stations_pink_line
        self.grey_line = dsl.stations_grey_line
def load_data():
    Stations = []
    Stations_name = []
    datasets = [dsl.stations_red_line, dsl.stations_blue_line_main, dsl.stations_blue_line_branch,
                dsl.stations_green_line_main, dsl.stations_yellow_line, dsl.stations_violet_line,
                dsl.stations_green_line_branch, dsl.stations_pink_line, dsl.stations_airport_express_line,
                dsl.stations_magenta_line, dsl.stations_grey_line]
    for data_list in datasets:
        for data in data_list:
            if data[0] not in Stations_name:
                Stations_name.append(data[0])
                cls = Station(data[0],[data[1],],[data[2],])
                Stations.append(cls)
            else:
                for i in Stations:
                    if i.station_name == data[0]:
                        i.add_line(data[1],data[2])
                        i.update_id(data[1],data[2])
    Lines = line()
    for st in Stations:
        st.system(Lines,Stations)
    return Stations, Stations_name

def get_station_by_name(name, Stations):
    for st in Stations:
        if st.station_name == name:
            return st
    return None

def shortest_path(start, stop, Stations):
    L = [(start, [start.station_name])]
    visited = {start.station_name}
    while L:
        current, path = L.pop(0)
        if current.station_name == stop.station_name:
            return path
        for adj in current.adj:
            neighbor = adj if hasattr(adj, 'station_name') else None
            if neighbor is None:
                from .delhi_metro_lines import get_station_by_name as _g
                neighbor = _g(adj, Stations)
            if neighbor and neighbor.station_name not in visited:
                visited.add(neighbor.station_name)
                L.append((neighbor, path + [neighbor.station_name]))
    return None

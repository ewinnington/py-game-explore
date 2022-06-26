from csv import reader 

def import_csv_layout(filename):
    terrain_map = []
    with open(filename) as level_map:
        layout = reader(level_map,delimiter=',')
        for row in layout:
            terrain_map.append(list(row))
    return terrain_map


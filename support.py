import pygame
from csv import reader 
import os 
from data import COLORKEY

def import_csv_layout(filename):
    terrain_map = []
    with open(filename) as level_map:
        layout = reader(level_map,delimiter=',')
        for row in layout:
            terrain_map.append(list(row))
    return terrain_map

def import_folder(path): 
    surface_list = []
    for _,_,img_files in os.walk(path):
        for image in img_files:
            full_path = os.path.join(path,image)
            image_surf = pygame.image.load(full_path).convert_alpha()
            image_surf.set_colorkey(COLORKEY)
            surface_list.append(image_surf)

    return surface_list
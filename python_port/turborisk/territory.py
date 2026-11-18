"""
TurboRisk - Python Port
Territory and Map Handling

Ported from Territ.pas
"""

import os
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import configparser

from .globals import G, MAXTERRITORIES, MAXBORDERS, MAXORIGINS, ContinentID, Territory, ContinentInfo


def setup_territories():
    """Setup static info about territories - the standard Risk map"""
    # Helper function to create territory with proper border list
    def make_territory(name, nbord, bord_list, continent):
        terr = Territory(name=name, nbord=nbord, continent=continent)
        # Create a 1-indexed border list
        terr.bord = [0] * (MAXTERRITORIES + 1)  # Override the default
        for i, border in enumerate(bord_list, 1):
            terr.bord[i] = border
        return terr
    
    # Clear existing territories
    for i in range(1, MAXTERRITORIES + 1):
        G.ar_territory[i] = Territory()
    
    # North America
    G.ar_territory[1] = make_territory('Alaska', 3, [2, 4, 37], ContinentID.NA)
    G.ar_territory[2] = make_territory('Northwest Territory', 4, [1, 3, 4, 5], ContinentID.NA)
    G.ar_territory[3] = make_territory('Greenland', 4, [2, 5, 6, 20], ContinentID.NA)
    G.ar_territory[4] = make_territory('Alberta', 4, [1, 2, 5, 7], ContinentID.NA)
    G.ar_territory[5] = make_territory('Ontario', 6, [2, 3, 4, 6, 7, 8], ContinentID.NA)
    G.ar_territory[6] = make_territory('Quebec', 3, [3, 5, 8], ContinentID.NA)
    G.ar_territory[7] = make_territory('Western US', 4, [4, 5, 8, 9], ContinentID.NA)
    G.ar_territory[8] = make_territory('Eastern US', 4, [5, 6, 7, 9], ContinentID.NA)
    G.ar_territory[9] = make_territory('Central America', 3, [7, 8, 10], ContinentID.NA)
    
    # South America
    G.ar_territory[10] = make_territory('Venezuela', 3, [9, 11, 12], ContinentID.SA)
    G.ar_territory[11] = make_territory('Peru', 3, [10, 12, 13], ContinentID.SA)
    G.ar_territory[12] = make_territory('Brazil', 4, [10, 11, 13, 14], ContinentID.SA)
    G.ar_territory[13] = make_territory('Argentina', 2, [11, 12], ContinentID.SA)
    
    # Africa
    G.ar_territory[14] = make_territory('North Africa', 6, [25, 26, 12, 15, 16, 17], ContinentID.AF)
    G.ar_territory[15] = make_territory('Egypt', 4, [14, 16, 26, 27], ContinentID.AF)
    G.ar_territory[16] = make_territory('East Africa', 6, [14, 15, 17, 18, 19, 27], ContinentID.AF)
    G.ar_territory[17] = make_territory('Congo', 3, [14, 16, 18], ContinentID.AF)
    G.ar_territory[18] = make_territory('South Africa', 3, [16, 17, 19], ContinentID.AF)
    G.ar_territory[19] = make_territory('Madagascar', 2, [16, 18], ContinentID.AF)
    
    # Europe
    G.ar_territory[20] = make_territory('Iceland', 3, [3, 21, 24], ContinentID.EU)
    G.ar_territory[21] = make_territory('Scandinavia', 4, [20, 22, 23, 24], ContinentID.EU)
    G.ar_territory[22] = make_territory('Ukraine', 6, [21, 23, 26, 27, 28, 29], ContinentID.EU)
    G.ar_territory[23] = make_territory('Northern Europe', 5, [21, 22, 24, 25, 26], ContinentID.EU)
    G.ar_territory[24] = make_territory('Great Britain', 4, [20, 21, 23, 25], ContinentID.EU)
    G.ar_territory[25] = make_territory('Western Europe', 4, [23, 24, 26, 14], ContinentID.EU)
    G.ar_territory[26] = make_territory('Southern Europe', 6, [22, 23, 25, 27, 14, 15], ContinentID.EU)
    
    # Middle East and Asia
    G.ar_territory[27] = make_territory('Middle East', 6, [22, 26, 15, 16, 29, 30], ContinentID.AS)
    G.ar_territory[28] = make_territory('Yamal-Nemets', 4, [22, 29, 33, 34], ContinentID.AS)
    G.ar_territory[29] = make_territory('Kazakhstan', 5, [22, 28, 27, 30, 32], ContinentID.AS)
    G.ar_territory[30] = make_territory('India', 4, [27, 29, 31, 32], ContinentID.AS)
    G.ar_territory[31] = make_territory('Siam', 3, [30, 32, 39], ContinentID.AS)
    G.ar_territory[32] = make_territory('China', 4, [29, 30, 31, 33], ContinentID.AS)
    
    # Northern Asia/Russia
    G.ar_territory[33] = make_territory('Mongolia', 6, [28, 32, 34, 36, 37, 38], ContinentID.AS)
    G.ar_territory[34] = make_territory('Taymyr', 4, [28, 33, 35, 36], ContinentID.AS)
    G.ar_territory[35] = make_territory('Yakut', 3, [34, 36, 37], ContinentID.AS)
    G.ar_territory[36] = make_territory('Buryat', 4, [33, 34, 35, 37], ContinentID.AS)
    G.ar_territory[37] = make_territory('Koryak', 5, [1, 33, 35, 36, 38], ContinentID.AS)
    G.ar_territory[38] = make_territory('Japan', 2, [33, 37], ContinentID.AS)
    
    # Australia
    G.ar_territory[39] = make_territory('Indonesia', 3, [31, 40, 42], ContinentID.AU)
    G.ar_territory[40] = make_territory('Western Australia', 3, [39, 41, 42], ContinentID.AU)
    G.ar_territory[41] = make_territory('Eastern Australia', 2, [40, 42], ContinentID.AU)
    G.ar_territory[42] = make_territory('New Guinea', 3, [39, 40, 41], ContinentID.AU)
    
    # Setup continent info
    setup_continents()


def setup_continents():
    """Setup continent information"""
    G.ar_continent[ContinentID.NA] = ContinentInfo(name='North America', bonus=5)
    G.ar_continent[ContinentID.SA] = ContinentInfo(name='South America', bonus=2)
    G.ar_continent[ContinentID.EU] = ContinentInfo(name='Europe', bonus=5)
    G.ar_continent[ContinentID.AF] = ContinentInfo(name='Africa', bonus=3)
    G.ar_continent[ContinentID.AS] = ContinentInfo(name='Asia', bonus=7)
    G.ar_continent[ContinentID.AU] = ContinentInfo(name='Australia', bonus=2)


def load_map(map_file: str):
    """Load a map from file"""
    map_path = os.path.join(G.s_g_app_path, 'maps')
    if not os.path.exists(map_path):
        map_path = os.path.join(os.path.dirname(__file__), '..', '..', 'maps')
    
    full_path = os.path.join(map_path, map_file)
    
    # Parse the .trm file (INI format)
    config = configparser.ConfigParser()
    config.read(full_path)
    
    # Load map metadata
    G.s_map_file = map_file
    G.s_map_desc = config.get('Map', 'Desc', fallback='')
    G.s_map_font_name = config.get('Map', 'FontName', fallback='Courier New')
    G.i_map_font_size = config.getint('Map', 'FontSize', fallback=8)
    G.t_map_text_fg = config.getint('Map', 'TextFG', fallback=0x000000)
    G.t_map_text_bg = config.getint('Map', 'TextBG', fallback=0xFFFFFF)
    
    # Load territory colors and coordinates
    for i in range(1, MAXTERRITORIES + 1):
        section = f'Territory_{i}'
        if config.has_section(section):
            G.ar_territory[i].color = config.getint(section, 'Color', fallback=0x000000)
            G.ar_territory[i].coord_x = config.getint(section, 'Tx', fallback=0)
            G.ar_territory[i].coord_y = config.getint(section, 'Ty', fallback=0)
            G.ar_territory[i].norig = config.getint(section, 'FFCount', fallback=0)
            
            # Load floodfill origins
            G.ar_territory[i].orig = []
            for j in range(1, G.ar_territory[i].norig + 1):
                x = config.getint(section, f'FF{j}x', fallback=0)
                y = config.getint(section, f'FF{j}y', fallback=0)
                G.ar_territory[i].orig.append((x, y))
    
    # Try to load the bitmap
    bitmap_file = os.path.splitext(map_file)[0] + '.bmp'
    bitmap_path = os.path.join(map_path, bitmap_file)
    
    try:
        G.base_map = Image.open(bitmap_path)
    except FileNotFoundError:
        # Try PNG
        png_file = os.path.splitext(map_file)[0] + '.png'
        png_path = os.path.join(map_path, png_file)
        try:
            G.base_map = Image.open(png_path)
        except FileNotFoundError:
            G.base_map = None


def find_territory(x: int, y: int) -> int:
    """Find a territory index from a point's map coordinates"""
    # Simple implementation: check if coordinates match any territory's label position
    for i in range(1, MAXTERRITORIES + 1):
        terr = G.ar_territory[i]
        # Check if (x, y) is close to the territory's coordinate
        if terr.coord_x > 0 and terr.coord_y > 0:
            if abs(x - terr.coord_x) < 20 and abs(y - terr.coord_y) < 20:
                return i
    return 0


def display_territory(territory: int):
    """Display a territory (placeholder for now)"""
    # In the Python version, this would update the GUI
    pass


def assign_territory(t: int, g: int):
    """Assign a territory to a player"""
    G.ar_territory[t].owner = g


def claim_territory(t: int, g: int):
    """Claim a territory for a player (with initial army)"""
    from .globals import ActionKind
    from .action_history import record_game_action
    before = G.ar_territory[t].army
    assign_territory(t, g)
    G.ar_territory[t].army += 1
    G.ar_player[g].new_army -= 1
    G.ar_player[g].territ += 1
    G.ar_player[g].army += 1
    record_game_action(ActionKind.AK_ASSIGNMENT, g, 0, 0, t, 1, before)


def transfer_armies(from_t: int, to_t: int, armies: int, kind: int):
    """Transfer armies from one territory to another"""
    if armies <= 0:
        return
    
    from_before = G.ar_territory[from_t].army
    to_before = G.ar_territory[to_t].army
    
    G.ar_territory[to_t].army += armies
    G.ar_territory[from_t].army -= armies
    
    from .action_history import record_game_action
    record_game_action(ActionKind(kind), G.i_turn, 0, from_t, to_t, armies, from_before, to_before)


def place_armies(t: int, g: int, armies: int):
    """Place n armies on a territory"""
    G.ar_territory[t].army += armies
    G.ar_player[g].new_army -= armies
    G.ar_player[g].army += armies


def is_adjacent(from_t: int, to_t: int) -> bool:
    """Check whether two territories are adjacent"""
    terr = G.ar_territory[from_t]
    for i in range(1, terr.nbord + 1):
        if terr.bord[i] == to_t:
            return True
    return False


def is_frontier(t: int) -> bool:
    """Check whether a territory is owned and borders enemy territories"""
    terr = G.ar_territory[t]
    if terr.owner == 0:
        return False
    
    for i in range(1, terr.nbord + 1):
        border = terr.bord[i]
        if border > 0 and G.ar_territory[border].owner != terr.owner:
            return True
    return False


def resize_main_window():
    """Resize main window according to map and toolbar"""
    # Placeholder - in GUI version this would resize the window
    pass


def flood_fill(bitmap: Image.Image, init_x: int, init_y: int, fill_color: int):
    """Flood fill implementation"""
    # Get the color at the initial point
    try:
        target_color = bitmap.getpixel((init_x, init_y))
    except IndexError:
        return
    
    if target_color == fill_color:
        return
    
    # Convert to RGB tuples
    if isinstance(target_color, int):
        target_color = (target_color >> 16, (target_color >> 8) & 0xFF, target_color & 0xFF)
    if isinstance(fill_color, int):
        fill_color = (fill_color >> 16, (fill_color >> 8) & 0xFF, fill_color & 0xFF)
    
    width, height = bitmap.size
    pixels = bitmap.load()
    
    stack = [(init_x, init_y)]
    visited = set()
    
    while stack:
        x, y = stack.pop()
        
        if x < 0 or x >= width or y < 0 or y >= height:
            continue
        
        if (x, y) in visited:
            continue
        
        current_color = pixels[x, y]
        if isinstance(current_color, int):
            current_color = (current_color >> 16, (current_color >> 8) & 0xFF, current_color & 0xFF)
        
        if current_color != target_color:
            continue
        
        pixels[x, y] = fill_color
        visited.add((x, y))
        
        # Add neighbors
        stack.append((x + 1, y))
        stack.append((x - 1, y))
        stack.append((x, y + 1))
        stack.append((x, y - 1))


# Initialize territories on import
setup_territories()

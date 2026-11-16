"""
TurboRisk - Python Port
Core Global Definitions and Data Structures

This module contains the main data types, constants, and global state for the TurboRisk game.
Ported from Globals.pas
"""

import enum
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
import random
from datetime import datetime


# ============================================================================
# VERSION INFORMATION
# ============================================================================

VERSION = '2.1.2'  # TurboRisk
VERSION_TRSIM = '1.0A'  # TRSim


# ============================================================================
# CONSTANTS
# ============================================================================

MAXTERRITORIES = 42  # Number of countries in the map
MAXBORDERS = 6  # Max number of borders per Territory
MAXORIGINS = 20  # Max number of floodfill points per Territory (for coloring)
MAXPLAYERS = 10  # Max number of players
MAXPLSETS = 50  # Max number of players sets
STDPLSETS = 5  # Number of standard players sets
MAXBUFFER = 500  # Number of buffers for the computer players

# Default trade values for AI
AI_DEF_TRADE_VAL = [4, 6, 8, 10, 12, 15, 20, 25]

# Default initial armies for AI
AI_DEF_INI_ARMY = [0, 0, 40, 35, 30, 25, 20, 20, 20, 20, 20]  # Index 2..MAXPLAYERS

# Default player colors
DEFAULT_COLORS = [
    0x0000FF,  # clBlue
    0x00FF00,  # clRed
    0x00FF00,  # clGreen (note: duplicate in original)
    0xFFFF00,  # clYellow
    0x00FFFF,  # clAqua
    0xFF00FF,  # clFuchsia
    0x00FF00,  # clLime (note: duplicate)
    0xFFF8DC,  # clCream
    0x800000,  # clMaroon
    0x800080,  # clPurple
]


# ============================================================================
# ENUMS AND TYPES
# ============================================================================

class GameState(enum.Enum):
    STOPPED = 0
    ASSIGNING = 1
    DISTRIBUTING = 2
    PLAYING = 3


class HumanPhase(enum.Enum):
    PLACEMENT = 0
    ATTACK = 1


class CardType(enum.Enum):
    INFANTRY = 0
    ARTILLERY = 1
    CAVALRY = 2
    JOKER = 3


class CardsSet(enum.Enum):
    INF = 0
    ART = 1
    CAV = 2
    DIF = 3  # Different


class CardsHandling(enum.Enum):
    MANUAL = 0
    SMART = 1
    AUTO = 2


class ContinentID(enum.Enum):
    NA = 0  # North America
    SA = 1  # South America
    EU = 2  # Europe
    AF = 3  # Africa
    AS = 4  # Asia
    AU = 5  # Australia


class CardValueType(enum.Enum):
    CONSTANT = 0
    PROGRESSIVE = 1


class SimStatus(enum.Enum):
    RUNNING = 0
    COMPLETE = 1
    ERROR = 2
    TURN_LIMIT = 3
    TIME_LIMIT = 4
    ABORT = 5


class RoutineType(enum.Enum):
    ASSIGNMENT = 0
    PLACEMENT = 1
    ATTACK = 2
    OCCUPATION = 3
    FORTIFICATION = 4


class AssignmentType(enum.Enum):
    RANDOM = 0
    TURNS = 1


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Territory:
    """Information about a territory"""
    # Dynamic - change during the game
    owner: int = 0  # Player who owns the territory (1-indexed, 0 = unowned)
    army: int = 0  # Number of occupying armies
    
    # Static - specific of each territory
    name: str = ""
    nbord: int = 0  # Number of borders
    bord: List[int] = field(default_factory=lambda: [0] * (MAXBORDERS + 1))  # Border territories (1-indexed)
    continent: ContinentID = ContinentID.NA  # Continent which the territory belongs to
    
    # Semi-dynamic - depending on the actual map
    color: int = 0  # Color in the base map (RGB)
    coord_x: int = 0  # X coordinate for the label
    coord_y: int = 0  # Y coordinate for the label
    norig: int = 0  # Number of floodfill areas for coloring
    orig: List[Tuple[int, int]] = field(default_factory=list)  # Coordinates of floodfill areas


@dataclass
class ContinentInfo:
    """Information about a continent"""
    # Dynamic - change during the game
    owner: int = 0  # Owner of the continent (if any)
    
    # Static - specific of each continent
    name: str = ""
    bonus: int = 0  # Bonus armies for the owner


@dataclass
class CPUUsage:
    """Information about CPU usage by TRPs (for TRSim)"""
    time: int = 0  # Length of calls (in high resolution timer ticks)
    phases: int = 0  # Number of phases (e.g. attack, occupation...)
    calls: int = 0  # Number of calls


# Type aliases for arrays
CardCounts = List[int]  # Indexed by CardType
PlayerBuffer = List[float]  # Indexed 1..MAXBUFFER


@dataclass
class Player:
    """Information about a player"""
    # Parameters selected by the player
    name: str = ""
    active: bool = False
    color: int = 0
    computer: bool = False  # True if player is a TRP
    cards_handling: CardsHandling = CardsHandling.SMART
    keep_log: bool = False
    prg_file: str = ""  # Source file name for computer players (TRP)
    code: str = ""  # Tokenized script for computer players (compiled TRP)
    
    # Status variables
    army: int = 0  # Total armies (not updated in real-time)
    new_army: int = 0  # Armies to be placed
    territ: int = 0  # Number of owned territories
    cards: CardCounts = field(default_factory=lambda: [0] * 4)  # Count of owned cards per kind
    nscambi: int = 0  # Number of card trades completed
    fl_conq: bool = False  # True if player conquered at least one territory during the turn
    fl_move: bool = False  # True if player performed at least one troops move during the turn
    last_turn: int = 0  # Last turn played by the player
    rank: int = 0  # Rank at the end of the game
    
    # Runtime variables
    buffer: PlayerBuffer = field(default_factory=lambda: [0.0] * (MAXBUFFER + 1))
    usnapshot_enabled: bool = False
    ulog_enabled: bool = False
    umessage_enabled: bool = False
    udialog_enabled: bool = False
    
    # TRSim statistics
    cpu: Dict[RoutineType, CPUUsage] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.cpu:
            for rt in RoutineType:
                self.cpu[rt] = CPUUsage()


@dataclass
class TRCompContext:
    """Context for TRComp (TRP compiler/testing)"""
    current_player: int = 0
    conquest: bool = False
    card_trade_by_combination: bool = False
    territory_owner: List[int] = field(default_factory=lambda: [0] * (MAXTERRITORIES + 1))
    territory_armies: List[int] = field(default_factory=lambda: [0] * (MAXTERRITORIES + 1))
    player_active: List[bool] = field(default_factory=lambda: [False] * (MAXPLAYERS + 1))
    player_name: List[str] = field(default_factory=lambda: [""] * (MAXPLAYERS + 1))
    player_program: List[str] = field(default_factory=lambda: [""] * (MAXPLAYERS + 1))
    player_cards: List[CardCounts] = field(default_factory=list)
    player_new_armies: List[int] = field(default_factory=lambda: [0] * (MAXPLAYERS + 1))
    buffers: PlayerBuffer = field(default_factory=lambda: [0.0] * (MAXBUFFER + 1))
    message: str = ""
    
    def __post_init__(self):
        if len(self.player_cards) == 0:
            self.player_cards = [field(default_factory=lambda: [0] * 4) for _ in range(MAXPLAYERS + 1)]


@dataclass
class PlayersSet:
    """Information about a set of players"""
    name: str = ""
    players: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ActionEvent:
    """Action event for history tracking"""
    kind: int = 0
    turn: int = 0
    player: int = 0
    opponent: int = 0
    from_territory: int = 0
    to_territory: int = 0
    armies: int = 0
    from_before: int = 0
    to_before: int = 0
    from_after: int = 0
    to_after: int = 0
    attacker_loss: int = 0
    defender_loss: int = 0
    captured: int = 0


# ============================================================================
# GLOBAL VARIABLES
# ============================================================================

class GlobalState:
    """Singleton class to hold all global state"""
    
    def __init__(self):
        # Generic global variables
        self.b_g_trsim = False  # True if the main program is TRSim
        self.b_trsim_cli = False  # True when TRSim is running without the GUI
        self.b_trcomp_running = False  # True while TRComp executes a test routine
        self.s_trcomp_runtime_log = ""
        self.s_g_app_name = "TurboRisk"
        self.s_g_app_vers = VERSION
        self.s_g_app_path = ""
        self.s_g_last_news = datetime.now()
        self.i_performance_frequency = 1
        
        # Global variables about the state of the game
        self.game_state = GameState.STOPPED
        self.i_turn_counter = 0
        self.i_turn = 0  # Current player
        self.i_first_turn = 0
        self.i_n_players = 0
        self.i_to_assign = 0
        self.b_human_turn = False
        self.human_phase = HumanPhase.PLACEMENT
        self.b_eliminated_player = False
        self.b_stop_asap = False
        self.b_close_asap = False
        self.i_rank = 0
        
        # Global variables about the map
        self.base_map = None  # Will be a PIL Image or similar
        self.ar_territory = [Territory() for _ in range(MAXTERRITORIES + 1)]
        self.ar_continent = {cid: ContinentInfo() for cid in ContinentID}
        self.s_map_file = ""
        self.s_map_desc = ""
        self.s_map_font_name = ""
        self.i_map_font_size = 0
        self.t_map_text_fg = 0
        self.t_map_text_bg = 0
        
        # Global variables about players and sets of players
        self.ar_player = [Player() for _ in range(MAXPLAYERS + 1)]
        self.ar_players_set = [PlayersSet() for _ in range(MAXPLSETS + 1)]
        self.ai_turn_list = [0] * (MAXPLAYERS + 1)
        self.i_pl_set = 0
        self.i_pl_set_count = 0
        
        # Global variables about the rules
        self.r_assignment_type = AssignmentType.RANDOM
        self.r_initial_armies = [0] * (MAXPLAYERS + 1)
        self.r_cards_value_type = CardValueType.CONSTANT
        self.r_set_value = [0] * 4  # Indexed by CardsSet
        self.r_trade_value = [0] * 9  # Indexed 1..8
        self.r_value_inc = 0
        self.r_max_held_cards = 5
        self.r_final_move = True
        self.r_immediate_trade = True
        
        # Global variable about stats
        self.b_st_op_ter = True
        self.b_st_op_arm = True
        self.b_st_op_con = True
        self.b_st_op_car = True
        self.b_st_op_ctiv = True
        
        # TRSim simulation environment
        self.i_sim_curr = 0
        self.i_sim_compl = 0
        self.i_sim_games = 0
        self.i_sim_winner = 0
        self.i_sim_game_time = 0
        self.i_sim_time_limit = 0
        self.i_sim_turn_limit = 0
        self.i_sim_players = 0
        self.i_sim_min_pl = 2
        self.i_sim_max_pl = 10
        self.u_sim_status = SimStatus.RUNNING
        self.b_sim_abort = False
        self.dt_sim_game_time = None
        self.dt_sim_start_time = None
        self.s_sim_game_log_file = ""
        self.s_sim_cpu_log_file = ""
        
        # Interface preferences
        self.s_pref_tlb_buttons = ""
        self.b_pref_confirm_abort = True
        self.b_pref_show_toolbar = True
        self.b_pref_check_update = False
        self.b_pref_expert_attack = False
        self.b_pref_map_hover = True
        self.b_pref_map_selected = True
        self.i_pref_map_hover = -20
        self.i_pref_map_selected = -20
        
        # Territory selection state
        self.hoover_territ = 0
        self.to_territ = 0
        self.from_territ = 0
        
        # Script execution
        self.script_exec = None  # Will be set up later
        
        # Action history
        self.action_history: List[ActionEvent] = []
        
        # Random state
        self.random = random.Random()
        
        # Flags for required TRP procedures
        self.b_assignment_found = False
        self.b_placement_found = False
        self.b_attack_found = False
        self.b_occupation_found = False
        self.b_fortification_found = False


# Create global state singleton
G = GlobalState()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def best_text_color(bkg_color: int) -> int:
    """Find best contrast text color for a background color"""
    # Simple implementation: use black or white based on brightness
    r = (bkg_color >> 16) & 0xFF
    g = (bkg_color >> 8) & 0xFF
    b = bkg_color & 0xFF
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return 0xFFFFFF if brightness < 128 else 0x000000


def change_color(color: int, percent: int) -> int:
    """Make a color lighter or darker by a percentage"""
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    
    factor = 1.0 + (percent / 100.0)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    
    return (r << 16) | (g << 8) | b


# ============================================================================
# TERRITORY AND PLAYER ACCESSORS
# ============================================================================

def get_from_territory() -> int:
    return G.from_territ


def get_to_territory() -> int:
    return G.to_territ


def get_hoover_territory() -> int:
    return G.hoover_territ


def set_from_territory(i_t: int):
    G.from_territ = i_t


def set_to_territory(i_t: int):
    G.to_territ = i_t


def set_hoover_territory(i_t: int):
    G.hoover_territ = i_t


# ============================================================================
# ACTION HISTORY
# ============================================================================

class ActionKind(enum.Enum):
    AK_ASSIGNMENT = 1
    AK_PLACEMENT = 2
    AK_ATTACK = 3
    AK_OCCUPATION = 4
    AK_FORTIFICATION = 5
    AK_ELIMINATION = 6
    AK_CARD_TRADE = 7


class ActionField(enum.Enum):
    AF_KIND = 1
    AF_TURN = 2
    AF_PLAYER = 3
    AF_OPPONENT = 4
    AF_FROM = 5
    AF_TO = 6
    AF_ARMIES = 7
    AF_FROM_BEFORE = 8
    AF_TO_BEFORE = 9
    AF_FROM_AFTER = 10
    AF_TO_AFTER = 11
    AF_ATTACKER_LOSS = 12
    AF_DEFENDER_LOSS = 13
    AF_CAPTURED = 14


ACTION_KIND_COUNT = 7
ACTION_FIELD_COUNT = 14


def record_game_action(kind: int, player: int, opponent: int, from_t: int, to_t: int, 
                       armies: int, from_before: int = 0, to_before: int = 0,
                       attacker_loss: int = 0, defender_loss: int = 0, captured: int = 0):
    """Record a game action in the history"""
    event = ActionEvent()
    event.kind = kind
    event.turn = G.i_turn_counter
    event.player = player
    event.opponent = opponent
    event.from_territory = from_t
    event.to_territory = to_t
    event.armies = armies
    event.from_before = from_before
    event.to_before = to_before
    
    if from_t > 0 and from_t <= MAXTERRITORIES:
        event.from_after = G.ar_territory[from_t].army
    if to_t > 0 and to_t <= MAXTERRITORIES:
        event.to_after = G.ar_territory[to_t].army
    
    event.attacker_loss = attacker_loss
    event.defender_loss = defender_loss
    event.captured = captured
    
    G.action_history.append(event)


def action_count() -> int:
    return len(G.action_history)


def action_value(index: int, field: int) -> int:
    """Get a specific field value from an action in the history"""
    if index < 1 or index > len(G.action_history):
        return 0
    event = G.action_history[index - 1]
    
    field_map = {
        1: 'kind',
        2: 'turn',
        3: 'player',
        4: 'opponent',
        5: 'from_territory',
        6: 'to_territory',
        7: 'armies',
        8: 'from_before',
        9: 'to_before',
        10: 'from_after',
        11: 'to_after',
        12: 'attacker_loss',
        13: 'defender_loss',
        14: 'captured',
    }
    
    attr = field_map.get(field, None)
    if attr:
        return getattr(event, attr, 0)
    return 0


# ============================================================================
# DEFAULT PLAYERS SETS
# ============================================================================

def default_players_sets():
    """Initialize default player sets"""
    G.i_pl_set_count = STDPLSETS
    
    sets_config = [
        {
            'name': '* Very easy *',
            'players': ['human', 'napoleon.trp', 'rambo.trp', 'simple.trp']
        },
        {
            'name': '* Easy *',
            'players': ['human', 'alexander.trp', 'borg.trp', 'napoleon.trp', 'rambo.trp', 'struggler.trp']
        },
        {
            'name': '* Medium *',
            'players': ['human', 'digger.trp', 'era$or-bot.trp', 'raptorbot.trp', 'shy.trp', 'struggler.trp']
        },
        {
            'name': '* Hard *',
            'players': ['human', 'australian+.trp', 'digger.trp', 'era$or-bot.trp', 
                       'raptorbot.trp', 'shy2.trp', 'wyrm.trp', 'zotob.trp']
        },
        {
            'name': '* Very hard *',
            'players': ['human', 'australian09.trp', 'descartes09.trp', 'frank+.trp',
                       'raptorbot.trp', 'shy.trp', 'vexer.trp', 'wyrm.trp', 'struggler+.trp']
        }
    ]
    
    for i, config in enumerate(sets_config, 1):
        if i <= STDPLSETS:
            G.ar_players_set[i].name = config['name']
            G.ar_players_set[i].players = []
            
            # Add human player
            G.ar_players_set[i].players.append({
                'name': 'human',
                'active': True,
                'color': DEFAULT_COLORS[0],
                'computer': False,
                'cards_handling': CardsHandling.SMART,
                'keep_log': False,
                'prg_file': ''
            })
            
            # Add computer players
            for prg in config['players']:
                if prg != 'human':
                    G.ar_players_set[i].players.append({
                        'name': prg.replace('.trp', ''),
                        'active': True,
                        'color': DEFAULT_COLORS[len(G.ar_players_set[i].players) % len(DEFAULT_COLORS)],
                        'computer': True,
                        'cards_handling': CardsHandling.SMART,
                        'keep_log': False,
                        'prg_file': prg
                    })


# Initialize default player sets
default_players_sets()

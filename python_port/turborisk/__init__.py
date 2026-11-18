"""
TurboRisk Game Engine

Core modules for the TurboRisk game.
"""

from .globals import G, VERSION, MAXTERRITORIES, MAXPLAYERS
from .territory import setup_territories, load_map, is_adjacent, is_frontier
from .action_history import (
    begin_action_history, end_action_history, record_action, action_count,
    action_value, start_action_log, stop_action_log, save_action_history,
    load_action_history, ActionEvent, ActionKind, ActionField
)
from .exp_subr import (
    t_name, t_owner, t_armies, t_continent, t_borders_count, t_border,
    t_is_bordering, t_is_front, t_is_mine, t_is_entry, t_fronts_count,
    t_front, t_strongest_front, t_weakest_front, t_pressure, t_distance,
    t_shortest_path, t_weakest_path, t_path_to_front,
    p_me, p_name, p_program, p_active, p_alive, p_human, p_armies_count,
    p_new_armies, p_territories_count, p_card_count, p_card_turn_in_value,
    c_owner, c_bonus, c_territories_count, c_territory, c_borders_count,
    c_border, c_entries_count, c_entry, c_analysis, c_leader,
    s_conquest, s_players_count, s_alive_players_count, s_cards_based_on_combo,
    u_message, u_log, u_buffer_set, u_buffer_get, u_random, u_take_snapshot,
    u_dialog, u_abort_game, u_log_off, u_log_on, u_message_off, u_message_on,
    u_dialog_off, u_dialog_on, u_snapshot_off, u_snapshot_on,
    set_urandom_seed, TRP_FUNCTIONS
)
from .computer import ComputerPlayer, execute_computer_turn
from .game_logic import setup, new_game_setup, supervisor, game_cleanup
from .cards import draw_card, trade_cards
from .network import (
    NetworkMessage, NetworkMessageType, NetworkPlayer, NetworkServer,
    NetworkClient, NetworkGameManager, start_network_game
)

# Import advanced GUI features (may fail if Tkinter is not available)
try:
    from .gui_advanced import (
        ColorManager, StatisticsVisualizer, MapVisualizer, Tooltip,
        GameReplay, show_advanced_statistics, show_game_replay, create_map_visualizer
    )
except ImportError:
    # Tkinter not available, create dummy functions
    ColorManager = None
    StatisticsVisualizer = None
    MapVisualizer = None
    Tooltip = None
    GameReplay = None
    def show_advanced_statistics(root): pass
    def show_game_replay(root): pass
    def create_map_visualizer(parent_frame): return None

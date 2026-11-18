"""
TurboRisk - Python Port
Game Logic Module

This module contains the core game logic functions.
Ported from various .pas files (Globals.pas, NewGame.pas, Attack.pas, Move.pas, etc.)
"""

import os
import random
from typing import Optional, List, Tuple

from .globals import (
    G, MAXPLAYERS, MAXTERRITORIES, MAXBUFFER, GameState, HumanPhase, RoutineType,
    AssignmentType, CardsHandling, ContinentID, CardType, SimStatus
)
from .territory import setup_territories, claim_territory, place_armies, transfer_armies
from .exp_subr import t_owner, t_name, t_armies, t_continent
from .trp_runtime import TRPRuntimeInstance


# =============================================================================
# Game Setup Functions
# =============================================================================

def setup():
    """
    Initialize the game.
    Ported from Setup procedure in Globals.pas
    """
    # Initialize territories
    setup_territories()
    
    # Set default values
    G.bG_TRSim = False
    G.game_state = GameState.STOPPED
    G.i_turn = 0
    G.i_turn_counter = 0
    G.bHumanTurn = False
    G.bStopASAP = False
    G.bCloseASAP = False
    
    # Initialize players
    for i in range(1, MAXPLAYERS + 1):
        G.ar_player[i].active = False
        G.ar_player[i].computer = False
        G.ar_player[i].name = f"Player {i}"
        G.ar_player[i].color = get_default_color(i)
        G.ar_player[i].prg_file = ""
        G.ar_player[i].keep_log = False
        G.ar_player[i].cards_handling = CardsHandling.CONSTANT
    
    # Set player 1 as human by default
    G.ar_player[1].active = True
    G.ar_player[1].computer = False
    G.ar_player[1].name = "Player 1"
    
    # Initialize other state
    G.hoover_territory = 0
    G.from_territory = 0
    G.to_territory = 0
    G.i_rank = 0
    
    # Clear territories
    for i in range(1, MAXTERRITORIES + 1):
        G.ar_territory[i].owner = 0
        G.ar_territory[i].army = 0


def get_default_color(player_id: int) -> int:
    """Get default color for a player"""
    colors = [0x0000FF, 0xFF0000, 0x00FF00, 0xFFFF00, 0xFF00FF, 0x00FFFF, 0x800000, 0x008000]
    return colors[(player_id - 1) % len(colors)]


def new_game_setup():
    """
    Set up a new game.
    Ported from NewGameSetup procedure in Globals.pas
    """
    from .computer import computer
    
    # Reset action history
    # BeginActionHistory(ActionMetadata) - TODO
    
    # Reset territories
    G.hoover_territory = 0
    G.from_territory = 0
    G.to_territory = 0
    
    for i in range(1, MAXTERRITORIES + 1):
        G.ar_territory[i].army = 0
        G.ar_territory[i].owner = 0
    
    # Reset continents
    for cont in range(1, 7):  # coNA to coAU
        G.ar_continent[cont].owner = 0
    
    # Count active players
    active_count = sum(1 for i in range(1, MAXPLAYERS + 1) if G.ar_player[i].active)
    
    if active_count < 2:
        raise ValueError("At least two players required")
    
    # Reset players
    for i in range(1, MAXPLAYERS + 1):
        if G.ar_player[i].active:
            # Reset buffers
            for b in range(1, MAXBUFFER + 1):
                G.ar_player[i].buffer[b] = 0.0
            
            # Reset runtime flags
            G.ar_player[i].u_snapshot_enabled = False
            G.ar_player[i].u_log_enabled = False
            G.ar_player[i].u_message_enabled = False
            G.ar_player[i].u_dialog_enabled = False
            
            # Set initial armies based on player count
            G.ar_player[i].new_army = get_initial_armies(active_count)
            G.ar_player[i].territ = 0
            G.ar_player[i].army = 0
            
            # Reset cards
            for card_type in range(1, 5):  # caInf, caArt, caCav, caJok
                G.ar_player[i].cards[card_type] = 0
            
            G.ar_player[i].n_scambi = 0
            G.ar_player[i].rank = 0
            
            # Load and compile TRP scripts for computer players
            if G.ar_player[i].computer and G.ar_player[i].prg_file:
                try:
                    TRPRuntimeInstance.create_context()
                    TRPRuntimeInstance.set_player(i)
                    script_path = os.path.join(G.sG_AppPath, 'players', G.ar_player[i].prg_file)
                    if os.path.exists(script_path):
                        if not TRPRuntimeInstance.load_from_file(script_path):
                            print(f"Error loading script for player {i}: {TRPRuntimeInstance.exception_message}")
                    else:
                        print(f"Script file not found: {script_path}")
                except Exception as e:
                    print(f"Error compiling TRP for player {i}: {e}")
    
    # Set game state
    G.game_state = GameState.ASSIGNING
    G.i_turn = 1
    G.i_turn_counter = 0
    
    # Find first active player
    for i in range(1, MAXPLAYERS + 1):
        if G.ar_player[i].active:
            G.i_turn = i
            break
    
    # Set human turn
    G.bHumanTurn = not G.ar_player[G.i_turn].computer
    
    # If first player is computer, start supervisor
    if not G.bHumanTurn:
        supervisor()


def get_initial_armies(player_count: int) -> int:
    """Get initial armies based on player count"""
    # From Globals.pas: RInitialArmies array
    initial_armies = {
        2: 40,
        3: 35,
        4: 30,
        5: 25,
        6: 20
    }
    return initial_armies.get(player_count, 20)


# =============================================================================
# Game Supervisor (Main Game Loop)
# =============================================================================

def supervisor():
    """
    Main game supervisor/loop.
    Ported from Supervisor procedure in Globals.pas
    """
    from .computer import computer
    from .human import human
    
    while True:
        if G.bStopASAP:
            G.bStopASAP = False
            game_cleanup()
            return
        
        if G.bCloseASAP:
            G.bCloseASAP = False
            game_cleanup()
            return
        
        # Check game state
        if G.game_state == GameState.STOPPED:
            return
        
        # Determine whose turn it is
        current_player = G.ar_player[G.i_turn]
        
        if current_player.computer:
            # Computer player turn
            G.bHumanTurn = False
            computer.execute_computer_turn()
        else:
            # Human player turn
            G.bHumanTurn = True
            # Human turn is handled by GUI events
            return
        
        # After computer turn, check for game over
        if check_game_over():
            game_cleanup()
            return
        
        # Move to next player
        next_player()
        
        # Update turn counter
        G.i_turn_counter += 1


def next_player():
    """Move to the next active player"""
    start_player = G.i_turn
    while True:
        G.i_turn += 1
        if G.i_turn > MAXPLAYERS:
            G.i_turn = 1
        
        if G.ar_player[G.i_turn].active:
            break
        
        if G.i_turn == start_player:
            # No active players found
            G.game_state = GameState.STOPPED
            break


def check_game_over() -> bool:
    """Check if the game is over"""
    active_count = sum(1 for i in range(1, MAXPLAYERS + 1) if G.ar_player[i].active)
    return active_count < 2


# =============================================================================
# Game Cleanup
# =============================================================================

def game_cleanup():
    """
    Clean up game state.
    Ported from GameCleanup procedure in Globals.pas
    """
    G.game_state = GameState.STOPPED
    G.bHumanTurn = False
    G.bStopASAP = False
    G.bCloseASAP = False
    
    # Reset territories
    for i in range(1, MAXTERRITORIES + 1):
        G.ar_territory[i].owner = 0
        G.ar_territory[i].army = 0
    
    # Reset players
    for i in range(1, MAXPLAYERS + 1):
        G.ar_player[i].new_army = 0
        G.ar_player[i].territ = 0
        G.ar_player[i].army = 0
        
        # Reset cards
        for card_type in range(1, 5):
            G.ar_player[i].cards[card_type] = 0
        
        G.ar_player[i].n_scambi = 0
    
    # Reset global state
    G.hoover_territory = 0
    G.from_territory = 0
    G.to_territory = 0
    G.i_rank = 0
    G.i_turn = 0
    G.i_turn_counter = 0


# =============================================================================
# Assignment Phase
# =============================================================================

def assignment_phase():
    """
    Handle the territory assignment phase.
    Ported from various procedures in Globals.pas and Computer.pas
    """
    if G.game_state != GameState.ASSIGNING:
        return
    
    # Find first free territory
    for terr in range(1, MAXTERRITORIES + 1):
        if G.ar_territory[terr].owner == 0:
            # Assign to current player
            claim_territory(terr, G.i_turn)
            G.ar_player[G.i_turn].territ += 1
            
            # Check if all territories are assigned
            all_assigned = all(G.ar_territory[i].owner != 0 for i in range(1, MAXTERRITORIES + 1))
            if all_assigned:
                # Move to distribution phase
                G.game_state = GameState.DISTRIBUTING
                # Add initial armies
                for i in range(1, MAXPLAYERS + 1):
                    if G.ar_player[i].active:
                        G.ar_player[i].army = G.ar_player[i].new_army
                break
            else:
                # Next player
                next_player()
            break


# =============================================================================
# Placement Phase
# =============================================================================

def placement_phase():
    """
    Handle the army placement phase.
    """
    if G.game_state != GameState.DISTRIBUTING:
        return
    
    current_player = G.ar_player[G.i_turn]
    
    if current_player.new_army <= 0:
        # No more armies to place, move to playing phase
        G.game_state = GameState.PLAYING
        G.human_phase = HumanPhase.PLACEMENT
        return
    
    # Place one army
    # This would be triggered by GUI click on a territory


# =============================================================================
# Attack Phase
# =============================================================================

def attack_phase(from_terr: int, to_terr: int) -> bool:
    """
    Handle an attack from one territory to another.
    Ported from UomoAttacca in Human.pas
    
    Returns: True if attack was successful
    """
    # Validate attack
    if from_terr < 1 or from_terr > MAXTERRITORIES:
        return False
    
    if to_terr < 1 or to_terr > MAXTERRITORIES:
        return False
    
    # Check if from territory belongs to current player
    if G.ar_territory[from_terr].owner != G.i_turn:
        return False
    
    # Check if to territory belongs to enemy
    if G.ar_territory[to_terr].owner == G.i_turn:
        return False
    
    # Check if territories are adjacent
    from .territory import is_adjacent
    if not is_adjacent(from_terr, to_terr):
        return False
    
    # Check if from territory has enough armies (at least 2)
    if G.ar_territory[from_terr].army < 2:
        return False
    
    # TODO: Implement actual attack logic (dice rolling, etc.)
    # For now, just simulate a successful attack
    
    # Attacker wins
    # Transfer armies
    attacking_armies = G.ar_territory[from_terr].army - 1  # Leave at least 1 behind
    G.ar_territory[from_terr].army = 1
    G.ar_territory[to_terr].owner = G.i_turn
    G.ar_territory[to_terr].army = attacking_armies
    
    G.ar_player[G.i_turn].territ += 1
    
    # Update human phase
    G.human_phase = HumanPhase.OCCUPATION
    
    return True


def occupation_phase(from_terr: int, to_terr: int, armies: int) -> bool:
    """
    Handle the occupation phase after a successful attack.
    Ported from UomoSposta in Human.pas
    
    Returns: True if occupation was successful
    """
    # Validate occupation
    if from_terr < 1 or from_terr > MAXTERRITORIES:
        return False
    
    if to_terr < 1 or to_terr > MAXTERRITORIES:
        return False
    
    # Check if both territories belong to current player
    if G.ar_territory[from_terr].owner != G.i_turn or G.ar_territory[to_terr].owner != G.i_turn:
        return False
    
    # Check if territories are adjacent
    from .territory import is_adjacent
    if not is_adjacent(from_terr, to_terr):
        return False
    
    # Check if from territory has enough armies
    if G.ar_territory[from_terr].army <= armies:
        return False
    
    # Transfer armies
    transfer_armies(from_terr, to_terr, armies, 0)  # 0 = occupation
    
    # Check if this is the final move
    G.ar_player[G.i_turn].fl_move = True
    
    # Move to next phase
    G.human_phase = HumanPhase.FORTIFICATION
    
    return True


def fortification_phase(from_terr: int, to_terr: int, armies: int) -> bool:
    """
    Handle the fortification phase.
    
    Returns: True if fortification was successful
    """
    # Validate fortification
    if from_terr < 1 or from_terr > MAXTERRITORIES:
        return False
    
    if to_terr < 1 or to_terr > MAXTERRITORIES:
        return False
    
    # Check if both territories belong to current player
    if G.ar_territory[from_terr].owner != G.i_turn or G.ar_territory[to_terr].owner != G.i_turn:
        return False
    
    # Check if territories are adjacent
    from .territory import is_adjacent
    if not is_adjacent(from_terr, to_terr):
        return False
    
    # Check if from territory has enough armies (at least 2)
    if G.ar_territory[from_terr].army <= 1:
        return False
    
    # Check if armies to move is valid
    if armies < 1 or armies >= G.ar_territory[from_terr].army:
        return False
    
    # Transfer armies
    transfer_armies(from_terr, to_terr, armies, 1)  # 1 = fortification
    
    # End turn
    G.human_phase = HumanPhase.PLACEMENT
    
    return True


# =============================================================================
# Card Functions
# =============================================================================

def draw_card() -> Optional[int]:
    """
    Draw a card for the current player.
    Returns: Card type or None if no card available
    """
    # TODO: Implement card drawing logic
    return None


def turn_in_cards(card_set: List[int]) -> int:
    """
    Turn in a set of cards.
    Returns: Number of armies awarded
    """
    # TODO: Implement card turn-in logic
    return 0


# =============================================================================
# Save/Restore Game
# =============================================================================

def save_game(filename: str, description: str = "") -> bool:
    """
    Save game state to a file.
    """
    # TODO: Implement game saving
    return False


def restore_game(filename: str) -> bool:
    """
    Restore game state from a file.
    """
    # TODO: Implement game restoring
    return False


# =============================================================================
# Utility Functions
# =============================================================================

def set_hover_territory(terr: int):
    """Set the hover territory"""
    G.hoover_territory = terr


def set_from_territory(terr: int):
    """Set the from territory"""
    G.from_territory = terr


def set_to_territory(terr: int):
    """Set the to territory"""
    G.to_territory = terr


def get_hover_territory() -> int:
    """Get the hover territory"""
    return G.hoover_territory


def get_from_territory() -> int:
    """Get the from territory"""
    return G.from_territory


def get_to_territory() -> int:
    """Get the to territory"""
    return G.to_territory


# =============================================================================
# Export all functions
# =============================================================================

__all__ = [
    'setup',
    'new_game_setup',
    'supervisor',
    'next_player',
    'check_game_over',
    'game_cleanup',
    'assignment_phase',
    'placement_phase',
    'attack_phase',
    'occupation_phase',
    'fortification_phase',
    'draw_card',
    'turn_in_cards',
    'save_game',
    'restore_game',
    'set_hover_territory',
    'set_from_territory',
    'set_to_territory',
    'get_hover_territory',
    'get_from_territory',
    'get_to_territory',
]

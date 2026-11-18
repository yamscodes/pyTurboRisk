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
    G.b_g_trsim = False
    G.game_state = GameState.STOPPED
    G.i_turn = 0
    G.i_turn_counter = 1
    G.b_human_turn = False
    G.b_stop_asap = False
    G.b_close_asap = False
    
    # Initialize players
    for i in range(1, MAXPLAYERS + 1):
        G.ar_player[i].active = False
        G.ar_player[i].computer = False
        G.ar_player[i].name = f"Player {i}"
        G.ar_player[i].color = get_default_color(i)
        G.ar_player[i].prg_file = ""
        G.ar_player[i].keep_log = False
        G.ar_player[i].cards_handling = CardsHandling.MANUAL
    
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
    for cont_id in ContinentID:
        G.ar_continent[cont_id].owner = 0
    
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
            for card_type in range(4):  # caInf, caArt, caCav, caJok (0-3)
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
    G.i_turn_counter = 1
    
    # Find first active player
    for i in range(1, MAXPLAYERS + 1):
        if G.ar_player[i].active:
            G.i_turn = i
            break
    
    # Set human turn
    G.b_human_turn = not G.ar_player[G.i_turn].computer
    
    # If first player is computer, start supervisor
    if not G.b_human_turn:
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
    from .computer import computer, execute_computer_turn
    from .cards import draw_card as cards_draw_card
    
    while True:
        if G.b_stop_asap:
            G.b_stop_asap = False
            game_cleanup()
            return
        
        if G.b_close_asap:
            G.b_close_asap = False
            game_cleanup()
            return
        
        # Check game state
        if G.game_state == GameState.STOPPED:
            return
        
        # Handle the case where we enter here after having waited for a Human Player to move
        if G.b_human_turn:
            G.b_human_turn = False
            # Assign a card if necessary
            if G.game_state == GameState.PLAYING and G.ar_player[G.i_turn].fl_conq:
                cards_draw_card()
            # Pass the turn to the next player
            next_player()
            return
        
        # Check game state and execute appropriate phase
        if G.game_state == GameState.ASSIGNING:
            # Assignment phase
            # This is handled by computer.execute_assignment() or human interaction
            if G.ar_player[G.i_turn].computer:
                execute_computer_turn()
            else:
                G.b_human_turn = True
                return
        
        elif G.game_state == GameState.DISTRIBUTING:
            # Distribution phase
            if G.ar_player[G.i_turn].computer:
                execute_computer_turn()
            else:
                G.b_human_turn = True
                return
        
        elif G.game_state == GameState.PLAYING:
            # Check if game has been won
            if G.i_n_players < 2:
                # Game over - someone has conquered the world
                game_cleanup()
                return
            
            # Prepare and execute a move
            if G.ar_player[G.i_turn].active and G.ar_player[G.i_turn].territ > 0:
                # Initialize turn
                G.ar_player[G.i_turn].fl_conq = False
                G.ar_player[G.i_turn].fl_move = False
                
                # Assign new armies
                assign_new_armies(False)
                
                # Execute a move
                if G.ar_player[G.i_turn].computer:
                    # Computer player
                    execute_computer_turn()
                    # Pick a new card if at least one territory has been conquered
                    if G.ar_player[G.i_turn].fl_conq:
                        cards_draw_card()
                    next_player()
                else:
                    # Human player
                    if G.ar_player[G.i_turn].new_army > 0:
                        G.human_phase = HumanPhase.PLACEMENT
                    else:
                        G.human_phase = HumanPhase.ATTACK
                    
                    G.from_territory = 0
                    G.to_territory = 0
                    
                    # Human player: wait for a move
                    G.b_human_turn = True
                    return
            else:
                # Skip inactive player
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
    G.b_human_turn = False
    G.b_stop_asap = False
    G.b_close_asap = False
    
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
        for card_type in range(4):
            G.ar_player[i].cards[card_type] = 0
        
        G.ar_player[i].n_scambi = 0
    
    # Reset global state
    G.hoover_territory = 0
    G.from_territory = 0
    G.to_territory = 0
    G.i_rank = 0
    G.i_turn = 0
    G.i_turn_counter = 1


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

def perform_attack(attacker_terr: int, defender_terr: int) -> Tuple[bool, str]:
    """
    Perform a single attack between two territories.
    Ported from PerformAttack in Globals.pas
    
    Args:
        attacker_terr: Territory attacking from
        defender_terr: Territory being attacked
    
    Returns:
        Tuple of (conquest_successful, message)
    """
    import random
    
    # Get defender
    defender = G.ar_territory[defender_terr].owner
    moved_armies = 0
    
    # Reset elimination flag
    G.b_eliminated_player = False
    
    # Save initial armies
    initial_attacker = G.ar_territory[attacker_terr].army
    initial_defender = G.ar_territory[defender_terr].army
    
    # Determine number of dice
    # Attacker can use up to 3 dice (army - 1)
    attacker_dice_count = min(G.ar_territory[attacker_terr].army - 1, 3)
    # Defender can use up to 2 dice
    defender_dice_count = min(G.ar_territory[defender_terr].army, 2)
    
    # Roll dice
    attacker_dice = throw_dice(attacker_dice_count)
    defender_dice = throw_dice(defender_dice_count)
    
    # Compare dice and count losses
    min_dice = min(attacker_dice_count, defender_dice_count)
    attacker_losses = 0
    defender_losses = 0
    
    for i in range(min_dice):
        if attacker_dice[i] > defender_dice[i]:
            defender_losses += 1
        else:
            attacker_losses += 1
    
    # Build message
    msg = f"A:[{'-'.join(map(str, attacker_dice[:attacker_dice_count]))}] "
    msg += f"D:[{'-'.join(map(str, defender_dice[:defender_dice_count]))}] "
    
    if attacker_losses == 2:
        msg += "Attacker loses 2 armies."
    elif defender_losses == 2:
        msg += "Defender loses 2 armies."
    elif attacker_losses == 1 and defender_losses == 1:
        msg += "Both sides lose 1 army."
    elif attacker_losses == 1:
        msg += "Attacker loses 1 army."
    elif defender_losses == 1:
        msg += "Defender loses 1 army."
    
    # Update territories
    opponent = 0
    G.ar_territory[attacker_terr].army -= attacker_losses
    G.ar_territory[defender_terr].army -= defender_losses
    
    # Check if territory was conquered
    if G.ar_territory[defender_terr].army == 0:
        # Conquered territory
        msg += f" {t_name(defender_terr)} conquered."
        
        # Assign territory to attacker
        from .territory import claim_territory
        claim_territory(defender_terr, G.i_turn)
        
        # Move armies (attacker_dice_count or remaining armies - 1)
        if attacker_dice_count >= G.ar_territory[attacker_terr].army:
            attacker_dice_count -= 1
        
        G.ar_territory[attacker_terr].army -= attacker_dice_count
        G.ar_territory[defender_terr].army += attacker_dice_count
        moved_armies = attacker_dice_count
        
        G.ar_player[G.i_turn].fl_conq = True
        opponent = defender
        
        # Check if opponent has been eliminated
        if G.ar_player[opponent].territ == 0:
            G.b_eliminated_player = True
            G.i_rank += 1
            G.ar_player[opponent].rank = G.i_rank
            msg += f" {G.ar_player[opponent].name} destroyed."
            
            # Capture opponent's cards
            for card_type in range(4):
                G.ar_player[G.i_turn].cards[card_type] += G.ar_player[opponent].cards[card_type]
                G.ar_player[opponent].cards[card_type] = 0
            
            # Decrease number of active players
            G.i_n_players -= 1
            
            # Stop human turn if game won
            if G.b_human_turn and G.i_n_players < 2:
                G.b_human_turn = False
        
        return (True, msg)
    else:
        return (False, msg)


def attack_phase(from_terr: int, to_terr: int, attack_type: str = "once") -> Tuple[bool, str]:
    """
    Handle an attack from one territory to another.
    Ported from UomoAttacca in Human.pas and Attack.pas
    
    Args:
        from_terr: Territory attacking from
        to_terr: Territory being attacked
        attack_type: "once", "do_or_die", "until1", or "until2"
    
    Returns:
        Tuple of (conquest_successful, message)
    """
    # Validate attack
    if from_terr < 1 or from_terr > MAXTERRITORIES:
        return (False, "Invalid from territory")
    
    if to_terr < 1 or to_terr > MAXTERRITORIES:
        return (False, "Invalid to territory")
    
    # Check if from territory belongs to current player
    if G.ar_territory[from_terr].owner != G.i_turn:
        return (False, "From territory not owned by you")
    
    # Check if to territory belongs to enemy
    if G.ar_territory[to_terr].owner == G.i_turn:
        return (False, "Cannot attack your own territory")
    
    # Check if territories are adjacent
    from .territory import is_adjacent
    if not is_adjacent(from_terr, to_terr):
        return (False, "Territories are not adjacent")
    
    # Check if from territory has enough armies (at least 2)
    if G.ar_territory[from_terr].army < 2:
        return (False, "Not enough armies to attack")
    
    # Perform attack based on type
    if attack_type == "once":
        conquest, msg = perform_attack(from_terr, to_terr)
        return (conquest, msg)
    
    elif attack_type == "do_or_die":
        # Keep attacking until conquest or only 1 army left
        while True:
            conquest, msg = perform_attack(from_terr, to_terr)
            if conquest or G.ar_territory[from_terr].army < 2:
                return (conquest, msg)
    
    elif attack_type == "until1":
        # Attack until conquest or attacker has <= target armies
        # For now, default to 1
        target = 1
        while True:
            if G.ar_territory[from_terr].army <= target:
                return (False, "Attacker has too few armies")
            conquest, msg = perform_attack(from_terr, to_terr)
            if conquest or G.ar_territory[from_terr].army < 2:
                return (conquest, msg)
    
    elif attack_type == "until2":
        # Attack until conquest or defender has <= target armies
        # For now, default to 1
        target = 1
        while True:
            if G.ar_territory[to_terr].army <= target:
                return (False, "Defender has too few armies")
            conquest, msg = perform_attack(from_terr, to_terr)
            if conquest or G.ar_territory[from_terr].army < 2:
                return (conquest, msg)
    
    return (False, "Invalid attack type")


def throw_dice(num_dice: int) -> List[int]:
    """
    Roll dice and return sorted results (descending).
    Ported from ThrowDice in Globals.pas
    
    Args:
        num_dice: Number of dice to roll (1-3)
    
    Returns:
        List of dice values sorted in descending order
    """
    import random
    
    # Roll dice
    dice = [random.randint(1, 6) for _ in range(num_dice)]
    
    # Sort in descending order
    dice.sort(reverse=True)
    
    return dice


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
    G.human_phase = HumanPhase.PLACEMENT
    
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
    from .cards import draw_card as cards_draw_card
    cards_draw_card()
    # Return the last card type drawn (stored in G)
    # For now, just return None as the card was already added to the player
    return None


def turn_in_cards(card_set: List[int]) -> int:
    """
    Turn in a set of cards for armies.
    Args:
        card_set: List of 4 integers [inf, cav, art, jok] representing cards to turn in
    Returns: Number of armies awarded
    """
    from .cards import trade_cards
    if len(card_set) >= 4:
        return trade_cards(card_set[0], card_set[1], card_set[2], card_set[3])
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

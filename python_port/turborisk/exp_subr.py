"""
TurboRisk - Python Port
External Subroutines for TRP Scripts

This module provides the functions that are available to TRP (TurboRisk Program) scripts.
Ported from ExpSubr.pas
"""

import random
from typing import List, Tuple, Optional
from .globals import G, MAXTERRITORIES, MAXPLAYERS, ContinentID, Territory, Player
from .territory import is_adjacent, is_frontier


# ============================================================================
# TERRITORY FUNCTIONS
# ============================================================================

def t_name(t: int) -> str:
    """Returns the name of territory T, '?' if T is out of range"""
    if 1 <= t <= MAXTERRITORIES:
        return G.ar_territory[t].name
    return '?'


def t_owner(t: int) -> int:
    """Returns the owner of territory T, 0 if T is unassigned, -1 if T is out of range"""
    if 1 <= t <= MAXTERRITORIES:
        return G.ar_territory[t].owner
    return -1


def t_armies(t: int) -> int:
    """Returns the number of armies on territory T, 0 if T is unassigned, -1 if T is out of range"""
    if 1 <= t <= MAXTERRITORIES:
        return G.ar_territory[t].army
    return -1


def t_continent(t: int) -> int:
    """Returns the ID of the continent which territory T belongs to, -1 if T is out of range"""
    if 1 <= t <= MAXTERRITORIES:
        return G.ar_territory[t].continent.value + 1  # +1 to match Pascal ordinal
    return -1


def t_borders_count(t: int) -> int:
    """Returns the number of borders of territory T (max 6), -1 if T is out of range"""
    if 1 <= t <= MAXTERRITORIES:
        return G.ar_territory[t].nbord
    return -1


def t_border(t: int, b: int) -> int:
    """Returns bordering territory #B of territory T, -1 if T or B are out of range"""
    if 1 <= t <= MAXTERRITORIES and 1 <= b <= G.ar_territory[t].nbord:
        return G.ar_territory[t].bord[b]
    return -1


def t_is_bordering(t1: int, t2: int) -> bool:
    """Returns true if territory T1 is bordering on territory T2"""
    if 1 <= t1 <= MAXTERRITORIES and 1 <= t2 <= MAXTERRITORIES:
        return is_adjacent(t1, t2)
    return False


def t_is_front(t: int) -> bool:
    """Returns true if territory T is owned by current player and has at least one bordering
    territory occupied by opponents"""
    if 1 <= t <= MAXTERRITORIES:
        return is_frontier(t) and G.ar_territory[t].owner == G.i_turn
    return False


def t_is_mine(t: int) -> bool:
    """Returns true if territory T is owned by current player"""
    if 1 <= t <= MAXTERRITORIES:
        return G.ar_territory[t].owner == G.i_turn
    return False


def t_is_entry(t: int) -> bool:
    """Returns true if territory T is an Entry Territory
    Entry territories are territories which are part of a continent but
    may be accessed from another continent"""
    # List from the original Pascal code
    entry_territories = {1, 3, 9, 10, 12, 14, 15, 16, 20, 22, 25, 26, 27, 28, 29, 31, 37, 39}
    return t in entry_territories


def t_fronts_count(t: int) -> int:
    """Returns the number of territories bordering on territory T which are occupied
    by opponents, -1 if T is out of range"""
    if 1 <= t <= MAXTERRITORIES:
        count = 0
        terr = G.ar_territory[t]
        for i in range(1, terr.nbord + 1):
            border = terr.bord[i]
            if border > 0 and G.ar_territory[border].owner != terr.owner:
                count += 1
        return count
    return -1


def t_front(t: int, f: int) -> int:
    """Returns the F-th territory bordering on territory T which is occupied
    by opponents, -1 if T or F are out of range"""
    if 1 <= t <= MAXTERRITORIES:
        count = 0
        terr = G.ar_territory[t]
        for i in range(1, terr.nbord + 1):
            border = terr.bord[i]
            if border > 0 and G.ar_territory[border].owner != terr.owner:
                count += 1
                if count == f:
                    return border
        return -1
    return -1


def t_strongest_front(t: int) -> Tuple[int, int, bool]:
    """Returns the strongest front territory and its armies
    Returns (enemy_territory, enemy_armies, success)"""
    if 1 <= t <= MAXTERRITORIES:
        max_armies = -1
        strongest = -1
        terr = G.ar_territory[t]
        
        for i in range(1, terr.nbord + 1):
            border = terr.bord[i]
            if border > 0 and G.ar_territory[border].owner != terr.owner:
                armies = G.ar_territory[border].army
                if armies > max_armies:
                    max_armies = armies
                    strongest = border
        
        if strongest > 0:
            return (strongest, max_armies, True)
    return (-1, -1, False)


def t_weakest_front(t: int) -> Tuple[int, int, bool]:
    """Returns the weakest front territory and its armies
    Returns (enemy_territory, enemy_armies, success)"""
    if 1 <= t <= MAXTERRITORIES:
        min_armies = float('inf')
        weakest = -1
        terr = G.ar_territory[t]
        
        for i in range(1, terr.nbord + 1):
            border = terr.bord[i]
            if border > 0 and G.ar_territory[border].owner != terr.owner:
                armies = G.ar_territory[border].army
                if armies < min_armies:
                    min_armies = armies
                    weakest = border
        
        if weakest > 0:
            return (weakest, min_armies, True)
    return (-1, -1, False)


def t_pressure(t: int) -> int:
    """Returns the pressure on territory T (total enemy armies on bordering territories)"""
    if 1 <= t <= MAXTERRITORIES:
        total = 0
        terr = G.ar_territory[t]
        for i in range(1, terr.nbord + 1):
            border = terr.bord[i]
            if border > 0 and G.ar_territory[border].owner != terr.owner:
                total += G.ar_territory[border].army
        return total
    return -1


def t_distance(st: int, dt: int) -> int:
    """Returns the distance (number of territories) from ST to DT"""
    # Simple BFS implementation
    if st < 1 or st > MAXTERRITORIES or dt < 1 or dt > MAXTERRITORIES:
        return -1
    
    if st == dt:
        return 0
    
    visited = [False] * (MAXTERRITORIES + 1)
    queue = [(st, 0)]
    visited[st] = True
    
    while queue:
        current, dist = queue.pop(0)
        terr = G.ar_territory[current]
        
        for i in range(1, terr.nbord + 1):
            neighbor = terr.bord[i]
            if neighbor > 0 and not visited[neighbor]:
                if neighbor == dt:
                    return dist + 1
                visited[neighbor] = True
                queue.append((neighbor, dist + 1))
    
    return -1


def t_shortest_path(st: int, dt: int) -> Tuple[int, int, bool]:
    """Returns the shortest path from ST to DT
    Returns (through_territory, path_length, success)
    This is a simplified version - returns first step and total length"""
    if st < 1 or st > MAXTERRITORIES or dt < 1 or dt > MAXTERRITORIES:
        return (-1, -1, False)
    
    if st == dt:
        return (-1, 0, True)
    
    # BFS to find path
    visited = [False] * (MAXTERRITORIES + 1)
    parent = [0] * (MAXTERRITORIES + 1)
    queue = [st]
    visited[st] = True
    found = False
    
    while queue:
        current = queue.pop(0)
        terr = G.ar_territory[current]
        
        for i in range(1, terr.nbord + 1):
            neighbor = terr.bord[i]
            if neighbor > 0 and not visited[neighbor]:
                parent[neighbor] = current
                if neighbor == dt:
                    found = True
                    break
                visited[neighbor] = True
                queue.append(neighbor)
        
        if found:
            break
    
    if found:
        # Reconstruct path
        path = []
        node = dt
        while node != st:
            path.append(node)
            node = parent[node]
        path.append(st)
        path.reverse()
        
        if len(path) > 1:
            return (path[1], len(path) - 1, True)
        return (-1, 0, True)
    
    return (-1, -1, False)


def t_weakest_path(st: int, dt: int) -> Tuple[int, int, int, bool]:
    """Returns the weakest path from ST to DT
    Returns (through_territory, path_length, enemy_armies, success)"""
    # This is a simplified version
    result = t_shortest_path(st, dt)
    if result[2]:  # If success
        tt, pl, _ = result
        if tt > 0:
            ea = G.ar_territory[tt].army
            return (tt, pl, ea, True)
    return (-1, -1, -1, False)


def t_path_to_front(t: int) -> int:
    """Returns the distance to the nearest front from territory T"""
    if 1 <= t <= MAXTERRITORIES:
        # Find the nearest territory that is a front
        visited = [False] * (MAXTERRITORIES + 1)
        queue = [(t, 0)]
        visited[t] = True
        
        while queue:
            current, dist = queue.pop(0)
            if is_frontier(current) and G.ar_territory[current].owner == G.ar_territory[t].owner:
                return dist
            
            terr = G.ar_territory[current]
            for i in range(1, terr.nbord + 1):
                neighbor = terr.bord[i]
                if neighbor > 0 and not visited[neighbor]:
                    visited[neighbor] = True
                    queue.append((neighbor, dist + 1))
        
        return -1
    return -1


# ============================================================================
# PLAYER FUNCTIONS
# ============================================================================

def p_me() -> int:
    """Returns the current player's ID"""
    return G.i_turn


def p_name(p: int) -> str:
    """Returns the name of player P"""
    if 1 <= p <= MAXPLAYERS:
        return G.ar_player[p].name
    return '?'


def p_program(p: int) -> str:
    """Returns the program file of player P"""
    if 1 <= p <= MAXPLAYERS:
        return G.ar_player[p].prg_file
    return ''


def p_active(p: int) -> bool:
    """Returns true if player P is active"""
    if 1 <= p <= MAXPLAYERS:
        return G.ar_player[p].active
    return False


def p_alive(p: int) -> bool:
    """Returns true if player P is alive (has territories)"""
    if 1 <= p <= MAXPLAYERS:
        return G.ar_player[p].active and G.ar_player[p].territ > 0
    return False


def p_human(p: int) -> bool:
    """Returns true if player P is human"""
    if 1 <= p <= MAXPLAYERS:
        return not G.ar_player[p].computer
    return False


def p_armies_count(p: int) -> int:
    """Returns the total number of armies owned by player P"""
    if 1 <= p <= MAXPLAYERS:
        return G.ar_player[p].army
    return 0


def p_new_armies(p: int) -> int:
    """Returns the number of new armies to place for player P"""
    if 1 <= p <= MAXPLAYERS:
        return G.ar_player[p].new_army
    return 0


def p_territories_count(p: int) -> int:
    """Returns the number of territories owned by player P"""
    if 1 <= p <= MAXPLAYERS:
        return G.ar_player[p].territ
    return 0


def p_card_count(p: int) -> int:
    """Returns the total number of cards held by player P"""
    if 1 <= p <= MAXPLAYERS:
        return sum(G.ar_player[p].cards)
    return 0


def p_card_turn_in_value(p: int) -> int:
    """Returns the card turn-in value for player P"""
    # This depends on the card value type and number of trades
    if 1 <= p <= MAXPLAYERS:
        n_trades = G.ar_player[p].nscambi
        if G.r_cards_value_type == G.r_cards_value_type.PROGRESSIVE:
            # Progressive value
            if n_trades < 8:
                return G.r_trade_value[n_trades]
            else:
                return G.r_trade_value[7] + (n_trades - 7) * G.r_value_inc
        else:
            # Constant value - return the average or max
            return max(G.r_set_value)
    return 0


# ============================================================================
# CONTINENT FUNCTIONS
# ============================================================================

def c_owner(c: int) -> int:
    """Returns the owner of continent C"""
    if 1 <= c <= 6:  # 6 continents
        cid = ContinentID(c - 1)  # Convert to enum
        return G.ar_continent[cid].owner
    return 0


def c_bonus(c: int) -> int:
    """Returns the bonus armies for continent C"""
    if 1 <= c <= 6:
        cid = ContinentID(c - 1)
        return G.ar_continent[cid].bonus
    return 0


def c_territories_count(c: int) -> int:
    """Returns the number of territories in continent C"""
    if 1 <= c <= 6:
        count = 0
        for t in range(1, MAXTERRITORIES + 1):
            if G.ar_territory[t].continent.value + 1 == c:
                count += 1
        return count
    return 0


def c_territory(c: int, t_index: int) -> int:
    """Returns the T-index-th territory in continent C"""
    if 1 <= c <= 6 and t_index >= 1:
        count = 0
        for t in range(1, MAXTERRITORIES + 1):
            if G.ar_territory[t].continent.value + 1 == c:
                count += 1
                if count == t_index:
                    return t
    return 0


def c_borders_count(c: int) -> int:
    """Returns the number of bordering territories for continent C"""
    # This is a simplified version
    if 1 <= c <= 6:
        # Count territories in this continent that border territories outside it
        count = 0
        for t in range(1, MAXTERRITORIES + 1):
            if G.ar_territory[t].continent.value + 1 == c:
                terr = G.ar_territory[t]
                for i in range(1, terr.nbord + 1):
                    border = terr.bord[i]
                    if border > 0 and G.ar_territory[border].continent.value + 1 != c:
                        count += 1
                        break
        return count
    return 0


def c_border(c: int, b: int) -> int:
    """Returns the B-th bordering territory of continent C"""
    if 1 <= c <= 6 and b >= 1:
        borders = []
        for t in range(1, MAXTERRITORIES + 1):
            if G.ar_territory[t].continent.value + 1 == c:
                terr = G.ar_territory[t]
                for i in range(1, terr.nbord + 1):
                    border = terr.bord[i]
                    if border > 0 and G.ar_territory[border].continent.value + 1 != c:
                        if border not in borders:
                            borders.append(border)
        
        if b <= len(borders):
            return borders[b - 1]
    return 0


def c_entries_count(c: int) -> int:
    """Returns the number of entry territories for continent C"""
    if 1 <= c <= 6:
        count = 0
        for t in range(1, MAXTERRITORIES + 1):
            if G.ar_territory[t].continent.value + 1 == c and t_is_entry(t):
                count += 1
        return count
    return 0


def c_entry(c: int, e: int) -> int:
    """Returns the E-th entry territory of continent C"""
    if 1 <= c <= 6 and e >= 1:
        entries = []
        for t in range(1, MAXTERRITORIES + 1):
            if G.ar_territory[t].continent.value + 1 == c and t_is_entry(t):
                entries.append(t)
        
        if e <= len(entries):
            return entries[e - 1]
    return 0


def c_analysis(c: int) -> Tuple[int, int, int, int, bool]:
    """Returns analysis of continent C
    Returns (player_territories, player_armies, enemy_territories, enemy_armies, success)"""
    if 1 <= c <= 6:
        pt = pa = et = ea = 0
        current_player = G.i_turn
        
        for t in range(1, MAXTERRITORIES + 1):
            if G.ar_territory[t].continent.value + 1 == c:
                owner = G.ar_territory[t].owner
                armies = G.ar_territory[t].army
                
                if owner == current_player:
                    pt += 1
                    pa += armies
                elif owner > 0:
                    et += 1
                    ea += armies
        
        return (pt, pa, et, ea, True)
    return (0, 0, 0, 0, False)


def c_leader(c: int) -> Tuple[int, int, int, bool]:
    """Returns the leader (player with most territories) of continent C
    Returns (player, territories, armies, success)"""
    if 1 <= c <= 6:
        player_territories = {}
        player_armies = {}
        
        for t in range(1, MAXTERRITORIES + 1):
            if G.ar_territory[t].continent.value + 1 == c:
                owner = G.ar_territory[t].owner
                if owner > 0:
                    player_territories[owner] = player_territories.get(owner, 0) + 1
                    player_armies[owner] = player_armies.get(owner, 0) + G.ar_territory[t].army
        
        if player_territories:
            leader = max(player_territories, key=player_territories.get)
            return (leader, player_territories[leader], player_armies.get(leader, 0), True)
    return (0, 0, 0, False)


# ============================================================================
# STATE FUNCTIONS
# ============================================================================

def s_conquest() -> bool:
    """Returns true if the current player conquered a territory in this turn"""
    return G.ar_player[G.i_turn].fl_conq


def s_players_count() -> int:
    """Returns the total number of players in the game"""
    return G.i_n_players


def s_alive_players_count() -> int:
    """Returns the number of alive players in the game"""
    count = 0
    for p in range(1, MAXPLAYERS + 1):
        if G.ar_player[p].active and G.ar_player[p].territ > 0:
            count += 1
    return count


def s_cards_based_on_combo() -> bool:
    """Returns true if card values are based on combinations"""
    return G.r_cards_value_type == G.r_cards_value_type.COMBINATION


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

# Random number generator state
class URandomState:
    def __init__(self):
        self.rand_seed = 0
        self.initialized = False


# Global random state
_b_urandom_initialized = False
_urandom = random.Random()


def set_urandom_seed(seed: int):
    """Set the seed for URandom"""
    global _b_urandom_initialized, _urandom
    _urandom.seed(seed)
    _b_urandom_initialized = True


def u_random(r: int) -> float:
    """Returns a random number between 0 and R-1"""
    global _b_urandom_initialized, _urandom
    
    if not _b_urandom_initialized:
        # Initialize with a seed based on game state
        set_urandom_seed(G.random.randint(0, 2**31 - 1))
    
    return _urandom.random() * r


def capture_urandom_state() -> URandomState:
    """Capture the current state of the random number generator"""
    state = URandomState()
    state.rand_seed = _urandom.getstate()[1][0]  # Simplified
    state.initialized = _b_urandom_initialized
    return state


def restore_urandom_state(state: URandomState):
    """Restore the state of the random number generator"""
    global _b_urandom_initialized, _urandom
    _urandom.seed(state.rand_seed)
    _b_urandom_initialized = state.initialized


def u_buffer_set(b: int, v: float):
    """Set buffer B to value V"""
    if 1 <= b <= G.MAXBUFFER:
        G.ar_player[G.i_turn].buffer[b] = v


def u_buffer_get(b: int) -> float:
    """Get the value of buffer B"""
    if 1 <= b <= G.MAXBUFFER:
        return G.ar_player[G.i_turn].buffer[b]
    return 0.0


def u_message(m: str):
    """Display a message (in GUI version, this would show a dialog)"""
    if G.ar_player[G.i_turn].umessage_enabled:
        print(f"Player {G.i_turn} ({G.ar_player[G.i_turn].name}): {m}")


def u_log(m: str):
    """Log a message"""
    if G.ar_player[G.i_turn].ulog_enabled:
        print(f"[LOG] Player {G.i_turn}: {m}")


def u_take_snapshot(m: str):
    """Take a snapshot"""
    if G.ar_player[G.i_turn].usnapshot_enabled:
        print(f"[SNAPSHOT] {m}")


def u_dialog(m: str, b: str) -> int:
    """Show a dialog with message M and buttons B (comma-separated)"""
    if not G.ar_player[G.i_turn].udialog_enabled:
        return 0
    
    # Simple implementation - just return first button
    buttons = b.split(',')
    print(f"[DIALOG] {m}")
    print(f"Buttons: {buttons}")
    return 1  # Default to first button


def u_abort_game():
    """Abort the current game"""
    G.b_stop_asap = True


def u_log_off():
    """Disable logging for current player"""
    G.ar_player[G.i_turn].ulog_enabled = False


def u_log_on():
    """Enable logging for current player"""
    G.ar_player[G.i_turn].ulog_enabled = True


def u_message_off():
    """Disable messages for current player"""
    G.ar_player[G.i_turn].umessage_enabled = False


def u_message_on():
    """Enable messages for current player"""
    G.ar_player[G.i_turn].umessage_enabled = True


def u_dialog_off():
    """Disable dialogs for current player"""
    G.ar_player[G.i_turn].udialog_enabled = False


def u_dialog_on():
    """Enable dialogs for current player"""
    G.ar_player[G.i_turn].udialog_enabled = True


def u_snapshot_off():
    """Disable snapshots for current player"""
    G.ar_player[G.i_turn].usnapshot_enabled = False


def u_snapshot_on():
    """Enable snapshots for current player"""
    G.ar_player[G.i_turn].usnapshot_enabled = True


# Create a dictionary of all available functions for the TRP scripting engine
TRP_FUNCTIONS = {
    # Territory functions
    'TName': t_name,
    'TOwner': t_owner,
    'TArmies': t_armies,
    'TContinent': t_continent,
    'TBordersCount': t_borders_count,
    'TBorder': t_border,
    'TIsBordering': t_is_bordering,
    'TIsFront': t_is_front,
    'TIsMine': t_is_mine,
    'TIsEntry': t_is_entry,
    'TFrontsCount': t_fronts_count,
    'TFront': t_front,
    'TStrongestFront': lambda t: t_strongest_front(t)[2],  # Return success
    'TWeakestFront': lambda t: t_weakest_front(t)[2],  # Return success
    'TPressure': t_pressure,
    'TDistance': t_distance,
    'TShortestPath': lambda st, dt: t_shortest_path(st, dt)[2],  # Return success
    'TWeakestPath': lambda st, dt: t_weakest_path(st, dt)[3],  # Return success
    'TPathToFront': t_path_to_front,
    
    # Player functions
    'PMe': p_me,
    'PName': p_name,
    'PProgram': p_program,
    'PActive': p_active,
    'PAlive': p_alive,
    'PHuman': p_human,
    'PArmiesCount': p_armies_count,
    'PNewArmies': p_new_armies,
    'PTerritoriesCount': p_territories_count,
    'PCardCount': p_card_count,
    'PCardTurnInValue': p_card_turn_in_value,
    
    # Continent functions
    'COwner': c_owner,
    'CBonus': c_bonus,
    'CTerritoriesCount': c_territories_count,
    'CTerritory': c_territory,
    'CBordersCount': c_borders_count,
    'CBorder': c_border,
    'CEntriesCount': c_entries_count,
    'CEntry': c_entry,
    'CAnalysis': lambda c: c_analysis(c)[4],  # Return success
    'CLeader': lambda c: c_leader(c)[3],  # Return success
    
    # State functions
    'SConquest': s_conquest,
    'SPlayersCount': s_players_count,
    'SAlivePlayersCount': s_alive_players_count,
    'SCardsBasedOnCombo': s_cards_based_on_combo,
    
    # Utility functions
    'UMessage': u_message,
    'ULog': u_log,
    'UBufferSet': u_buffer_set,
    'UBufferGet': u_buffer_get,
    'URandom': u_random,
    'UTakeSnapshot': u_take_snapshot,
    'UDialog': u_dialog,
    'UAbortGame': u_abort_game,
    'ULogOff': u_log_off,
    'ULogOn': u_log_on,
    'UMessageOff': u_message_off,
    'UMessageOn': u_message_on,
    'UDialogOff': u_dialog_off,
    'UDialogOn': u_dialog_on,
    'USnapShotOff': u_snapshot_off,
    'USnapShotOn': u_snapshot_on,
    
    # History functions (from globals)
    'HCount': lambda: G.action_count(),
    'HGet': lambda index, field: G.action_value(index, field),
}

"""
TurboRisk Web Application - Routes
Main game routes and logic for the Flask web interface.
"""

import random
import json
from flask import render_template, request, redirect, url_for, session, jsonify
from . import app

# Import from the core game modules
import sys
import os

# Add the parent directory to the path to import turborisk modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from turborisk.globals import (
    G, MAXTERRITORIES, MAXPLAYERS, GameState, HumanPhase, 
    ContinentID, Territory, ContinentInfo, Player
)
from turborisk.territory import setup_territories, setup_continents, is_adjacent
from turborisk.game_logic import (
    get_initial_armies, next_player as game_next_player,
    check_game_over, assignment_phase, placement_phase,
    perform_attack, game_cleanup
)
from turborisk.exp_subr import t_owner, t_name, t_armies, t_continent, t_border
from turborisk.cards import draw_card as cards_draw_card


# =============================================================================
# Web Game State Management
# =============================================================================

class WebGameState:
    """Manages game state specific to the web interface"""
    
    def __init__(self):
        self.session_id = None
        self.selected_territory = None
        self.attack_from = None
        self.attack_to = None
        self.move_from = None
        self.move_to = None
        self.placement_armies = 1  # Default: place 1 army
        self.game_message = ""
        self.last_action = ""
    
    def reset(self):
        """Reset web-specific state"""
        self.selected_territory = None
        self.attack_from = None
        self.attack_to = None
        self.move_from = None
        self.move_to = None
        self.placement_armies = 1
        self.game_message = ""
        self.last_action = ""


# Create a web game state instance
web_state = WebGameState()


def init_web_game():
    """Initialize a new game for the web interface"""
    # Initialize the global state
    G.b_g_trsim = False
    G.s_g_app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Setup territories
    setup_territories()
    setup_continents()
    
    # Initialize players
    num_players = int(session.get('num_players', 2))
    
    for i in range(1, MAXPLAYERS + 1):
        G.ar_player[i] = Player()
        G.ar_player[i].active = (i <= num_players)
        G.ar_player[i].computer = False  # For now, all human in web version
        G.ar_player[i].name = f"Player {i}"
        G.ar_player[i].color = get_default_color(i)
        G.ar_player[i].cards_handling = 1  # SMART
    
    # Set game state
    G.game_state = GameState.ASSIGNING
    G.i_turn = 1
    G.i_turn_counter = 1
    G.b_human_turn = True
    G.i_n_players = num_players
    G.i_to_assign = MAXTERRITORIES
    
    # Reset territories
    for i in range(1, MAXTERRITORIES + 1):
        G.ar_territory[i].owner = 0
        G.ar_territory[i].army = 0
    
    # Reset continents
    for cont_id in ContinentID:
        G.ar_continent[cont_id].owner = 0
    
    # Set initial armies for each player
    for i in range(1, num_players + 1):
        G.ar_player[i].new_army = get_initial_armies(num_players)
    
    # Reset web state
    web_state.reset()
    web_state.game_message = f"New game started with {num_players} players!"
    
    # Perform initial territory assignment
    assign_all_territories()
    
    # Move to distribution phase
    G.game_state = GameState.DISTRIBUTING
    for i in range(1, num_players + 1):
        if G.ar_player[i].active:
            G.ar_player[i].army = G.ar_player[i].new_army
    
    web_state.game_message = f"Player {G.i_turn}, place your armies!"


def get_default_color(player_id: int) -> int:
    """Get default color for a player"""
    colors = [0x0000FF, 0xFF0000, 0x00FF00, 0xFFFF00, 0xFF00FF, 0x00FFFF, 0x800000, 0x008000]
    return colors[(player_id - 1) % len(colors)]


def assign_all_territories():
    """Assign all territories randomly to players"""
    # Collect all territories
    territories = list(range(1, MAXTERRITORIES + 1))
    random.shuffle(territories)
    
    # Assign to players in round-robin fashion
    current_player = 1
    for terr in territories:
        # Find next active player
        while current_player <= MAXPLAYERS and not G.ar_player[current_player].active:
            current_player += 1
        if current_player > MAXPLAYERS:
            current_player = 1
            while current_player <= MAXPLAYERS and not G.ar_player[current_player].active:
                current_player += 1
        
        if current_player <= MAXPLAYERS:
            G.ar_territory[terr].owner = current_player
            G.ar_territory[terr].army = 1
            G.ar_player[current_player].territ += 1
            G.ar_player[current_player].army += 1
            current_player += 1
    
    # Update continent owners
    update_continent_owners()


def update_continent_owners():
    """Update continent ownership based on territory ownership"""
    for cont_id in ContinentID:
        # Check if all territories in continent are owned by one player
        territories_in_continent = [
            i for i in range(1, MAXTERRITORIES + 1)
            if G.ar_territory[i].continent == cont_id and G.ar_territory[i].owner > 0
        ]
        
        if territories_in_continent:
            first_owner = G.ar_territory[territories_in_continent[0]].owner
            all_same_owner = all(
                G.ar_territory[t].owner == first_owner
                for t in territories_in_continent
            )
            
            if all_same_owner:
                G.ar_continent[cont_id].owner = first_owner
            else:
                G.ar_continent[cont_id].owner = 0
        else:
            G.ar_continent[cont_id].owner = 0


def get_territory_info(terr_id: int) -> dict:
    """Get information about a territory for display"""
    terr = G.ar_territory[terr_id]
    return {
        'id': terr_id,
        'name': terr.name,
        'owner': terr.owner,
        'army': terr.army,
        'continent': terr.continent.name,
        'color': f"#{terr.color:06X}" if terr.color else None,
        'x': terr.coord_x,
        'y': terr.coord_y
    }


def get_player_info(player_id: int) -> dict:
    """Get information about a player for display"""
    player = G.ar_player[player_id]
    return {
        'id': player_id,
        'name': player.name,
        'active': player.active,
        'computer': player.computer,
        'color': f"#{player.color:06X}" if player.color else None,
        'armies': player.army,
        'territories': player.territ,
        'new_army': player.new_army,
        'cards': player.cards,
        'conquered': player.fl_conq
    }


def can_attack(from_terr: int, to_terr: int) -> bool:
    """Check if an attack is valid"""
    if from_terr == to_terr:
        return False
    
    if G.ar_territory[from_terr].owner != G.i_turn:
        return False
    
    if G.ar_territory[to_terr].owner == G.i_turn:
        return False
    
    if G.ar_territory[from_terr].army <= 1:
        return False
    
    # Check if territories are adjacent
    if not is_adjacent(from_terr, to_terr):
        return False
    
    return True


def can_move(from_terr: int, to_terr: int) -> bool:
    """Check if a movement is valid"""
    if from_terr == to_terr:
        return False
    
    if G.ar_territory[from_terr].owner != G.i_turn:
        return False
    
    if G.ar_territory[to_terr].owner != G.i_turn:
        return False
    
    if G.ar_territory[from_terr].army <= 1:
        return False
    
    # Check if territories are adjacent
    if not is_adjacent(from_terr, to_terr):
        return False
    
    return True


def can_place_army(terr_id: int) -> bool:
    """Check if armies can be placed on a territory"""
    if G.game_state != GameState.DISTRIBUTING:
        return False
    
    if G.ar_territory[terr_id].owner != G.i_turn:
        return False
    
    if G.ar_player[G.i_turn].new_army <= 0:
        return False
    
    return True


# =============================================================================
# Flask Routes
# =============================================================================

@app.route('/')
def index():
    """Main game page"""
    # Check if game is initialized
    if 'game_initialized' not in session:
        return redirect(url_for('setup'))
    
    # Get game state
    territories = [get_territory_info(i) for i in range(1, MAXTERRITORIES + 1)]
    players = [get_player_info(i) for i in range(1, MAXPLAYERS + 1) if G.ar_player[i].active]
    current_player = G.ar_player[G.i_turn]
    
    # Get continent info
    continents = []
    for cont_id in ContinentID:
        cont = G.ar_continent[cont_id]
        continents.append({
            'id': cont_id.name,
            'name': cont.name,
            'bonus': cont.bonus,
            'owner': cont.owner
        })
    
    # Determine current phase
    phase = ""
    if G.game_state == GameState.ASSIGNING:
        phase = "assigning"
    elif G.game_state == GameState.DISTRIBUTING:
        phase = "distributing"
    elif G.game_state == GameState.PLAYING:
        if current_player.new_army > 0:
            phase = "placement"
        else:
            phase = "attack"
    
    return render_template('game.html',
                         territories=territories,
                         players=players,
                         current_player_id=G.i_turn,
                         current_player=current_player,
                         game_state=G.game_state.name,
                         phase=phase,
                         message=web_state.game_message,
                         selected_territory=web_state.selected_territory,
                         attack_from=web_state.attack_from,
                         attack_to=web_state.attack_to,
                         continents=continents)


@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Game setup page"""
    if request.method == 'POST':
        num_players = int(request.form.get('num_players', 2))
        session['num_players'] = num_players
        session['game_initialized'] = True
        
        # Initialize the game
        init_web_game()
        
        return redirect(url_for('index'))
    
    return render_template('setup.html')


@app.route('/new_game')
def new_game():
    """Start a new game"""
    session.pop('game_initialized', None)
    return redirect(url_for('setup'))


@app.route('/select_territory/<int:terr_id>')
def select_territory(terr_id):
    """Select a territory"""
    if G.game_state == GameState.DISTRIBUTING:
        # Placement phase
        if can_place_army(terr_id):
            # Place an army
            armies_to_place = min(web_state.placement_armies, G.ar_player[G.i_turn].new_army)
            G.ar_territory[terr_id].army += armies_to_place
            G.ar_player[G.i_turn].new_army -= armies_to_place
            G.ar_player[G.i_turn].army += armies_to_place
            
            web_state.game_message = f"Placed {armies_to_place} army(ies) on {t_name(terr_id)}"
            web_state.last_action = "place"
            
            # Check if player has no more armies to place
            if G.ar_player[G.i_turn].new_army <= 0:
                # Move to next player or phase
                G.game_state = GameState.PLAYING
                G.ar_player[G.i_turn].new_army = calculate_new_armies(G.i_turn)
                web_state.game_message = f"Player {G.i_turn}, start your turn!"
        
        return jsonify({
            'success': True,
            'message': web_state.game_message,
            'new_army': G.ar_player[G.i_turn].new_army,
            'territory_army': G.ar_territory[terr_id].army
        })
    
    elif G.game_state == GameState.PLAYING:
        current_player_id = G.i_turn
        
        # If we're in placement phase (have new armies)
        if G.ar_player[current_player_id].new_army > 0:
            if G.ar_territory[terr_id].owner == current_player_id:
                # Place armies
                armies_to_place = min(web_state.placement_armies, G.ar_player[current_player_id].new_army)
                G.ar_territory[terr_id].army += armies_to_place
                G.ar_player[current_player_id].new_army -= armies_to_place
                G.ar_player[current_player_id].army += armies_to_place
                
                web_state.game_message = f"Placed {armies_to_place} army(ies) on {t_name(terr_id)}"
                web_state.last_action = "place"
                
                # Check if done with placement
                if G.ar_player[current_player_id].new_army <= 0:
                    web_state.game_message = "Placement complete. Ready to attack!"
                
                return jsonify({
                    'success': True,
                    'message': web_state.game_message,
                    'new_army': G.ar_player[current_player_id].new_army,
                    'territory_army': G.ar_territory[terr_id].army,
                    'action': 'place'
                })
        
        # Attack phase
        if web_state.attack_from is None:
            # Selecting source for attack
            if G.ar_territory[terr_id].owner == current_player_id and G.ar_territory[terr_id].army > 1:
                web_state.attack_from = terr_id
                web_state.game_message = f"Selected {t_name(terr_id)} as attack source. Select target."
                return jsonify({
                    'success': True,
                    'message': web_state.game_message,
                    'attack_from': terr_id,
                    'action': 'select_attack_source'
                })
            else:
                web_state.game_message = "You can only attack from your own territories with more than 1 army."
                return jsonify({'success': False, 'message': web_state.game_message})
        
        elif web_state.attack_from is not None and web_state.attack_to is None:
            # Selecting target for attack
            if can_attack(web_state.attack_from, terr_id):
                web_state.attack_to = terr_id
                web_state.game_message = f"Ready to attack {t_name(terr_id)} from {t_name(web_state.attack_from)}. Click to confirm."
                return jsonify({
                    'success': True,
                    'message': web_state.game_message,
                    'attack_from': web_state.attack_from,
                    'attack_to': terr_id,
                    'action': 'select_attack_target'
                })
            else:
                web_state.game_message = "Invalid attack target."
                return jsonify({'success': False, 'message': web_state.game_message})
        
        elif web_state.attack_from is not None and web_state.attack_to is not None:
            # Perform the attack
            if terr_id == web_state.attack_to:
                result = perform_attack(web_state.attack_from, web_state.attack_to)
                
                # Update game state
                if result[0]:  # Conquest successful
                    update_continent_owners()
                    G.ar_player[current_player_id].fl_conq = True
                    
                    # Check if player conquered a territory and can draw a card
                    if G.ar_player[current_player_id].fl_conq:
                        # For now, just note it - card drawing happens at end of turn
                        pass
                
                web_state.game_message = result[1]
                web_state.last_action = "attack"
                
                # Reset attack selection
                web_state.attack_from = None
                web_state.attack_to = None
                
                # Check if attacker still has armies to attack with
                if G.ar_territory[web_state.attack_from].army > 1:
                    # Can continue attacking
                    web_state.attack_from = web_state.attack_from
                    web_state.game_message += " You can attack again."
                
                return jsonify({
                    'success': True,
                    'message': web_state.game_message,
                    'attack_from': web_state.attack_from,
                    'attack_to': web_state.attack_to,
                    'action': 'attack_performed',
                    'conquest': result[0]
                })
            else:
                # Cancel attack selection
                web_state.attack_from = None
                web_state.attack_to = None
                web_state.game_message = "Attack cancelled."
                return jsonify({
                    'success': True,
                    'message': web_state.game_message,
                    'attack_from': None,
                    'attack_to': None,
                    'action': 'attack_cancelled'
                })
    
    return jsonify({'success': False, 'message': 'Invalid action'})


@app.route('/place_armies/<int:terr_id>', methods=['POST'])
def place_armies(terr_id):
    """Place armies on a territory"""
    data = request.get_json()
    armies = data.get('armies', 1)
    
    if G.game_state != GameState.PLAYING:
        return jsonify({'success': False, 'message': 'Not in playing phase'})
    
    current_player_id = G.i_turn
    
    if G.ar_player[current_player_id].new_army <= 0:
        return jsonify({'success': False, 'message': 'No armies to place'})
    
    if G.ar_territory[terr_id].owner != current_player_id:
        return jsonify({'success': False, 'message': 'Not your territory'})
    
    armies_to_place = min(armies, G.ar_player[current_player_id].new_army)
    G.ar_territory[terr_id].army += armies_to_place
    G.ar_player[current_player_id].new_army -= armies_to_place
    G.ar_player[current_player_id].army += armies_to_place
    
    web_state.game_message = f"Placed {armies_to_place} army(ies) on {t_name(terr_id)}"
    web_state.last_action = "place"
    
    return jsonify({
        'success': True,
        'message': web_state.game_message,
        'new_army': G.ar_player[current_player_id].new_army,
        'territory_army': G.ar_territory[terr_id].army
    })


@app.route('/set_placement_armies', methods=['POST'])
def set_placement_armies():
    """Set the number of armies to place"""
    data = request.get_json()
    armies = data.get('armies', 1)
    web_state.placement_armies = armies
    return jsonify({'success': True, 'armies': web_state.placement_armies})


@app.route('/attack/<int:from_terr>/<int:to_terr>')
def attack(from_terr, to_terr):
    """Perform an attack"""
    if G.game_state != GameState.PLAYING:
        return jsonify({'success': False, 'message': 'Not in playing phase'})
    
    if not can_attack(from_terr, to_terr):
        return jsonify({'success': False, 'message': 'Invalid attack'})
    
    result = perform_attack(from_terr, to_terr)
    
    # Update game state
    current_player_id = G.i_turn
    if result[0]:  # Conquest successful
        update_continent_owners()
        G.ar_player[current_player_id].fl_conq = True
    
    web_state.game_message = result[1]
    web_state.last_action = "attack"
    web_state.attack_from = None
    web_state.attack_to = None
    
    # Check game over
    if check_game_over():
        # Find the winner
        for i in range(1, MAXPLAYERS + 1):
            if G.ar_player[i].active and G.ar_player[i].territ > 0:
                web_state.game_message = f"Game over! {G.ar_player[i].name} has won!"
                G.game_state = GameState.STOPPED
                break
    
    return jsonify({
        'success': True,
        'message': web_state.game_message,
        'conquest': result[0],
        'from_army': G.ar_territory[from_terr].army,
        'to_army': G.ar_territory[to_terr].army,
        'to_owner': G.ar_territory[to_terr].owner
    })


@app.route('/move/<int:from_terr>/<int:to_terr>')
def move(from_terr, to_terr):
    """Move armies between territories"""
    data = request.get_json()
    armies = data.get('armies', 1)
    
    if G.game_state != GameState.PLAYING:
        return jsonify({'success': False, 'message': 'Not in playing phase'})
    
    if not can_move(from_terr, to_terr):
        return jsonify({'success': False, 'message': 'Invalid move'})
    
    current_player_id = G.i_turn
    
    # Check if player has moved already
    if G.ar_player[current_player_id].fl_move:
        return jsonify({'success': False, 'message': 'Already moved this turn'})
    
    # Limit armies to move
    armies_to_move = min(armies, G.ar_territory[from_terr].army - 1)
    
    if armies_to_move <= 0:
        return jsonify({'success': False, 'message': 'Not enough armies'})
    
    # Perform the move
    G.ar_territory[from_terr].army -= armies_to_move
    G.ar_territory[to_terr].army += armies_to_move
    G.ar_player[current_player_id].fl_move = True
    
    web_state.game_message = f"Moved {armies_to_move} armies from {t_name(from_terr)} to {t_name(to_terr)}"
    web_state.last_action = "move"
    
    return jsonify({
        'success': True,
        'message': web_state.game_message,
        'from_army': G.ar_territory[from_terr].army,
        'to_army': G.ar_territory[to_terr].army
    })


@app.route('/end_turn')
def end_turn():
    """End the current player's turn"""
    if G.game_state != GameState.PLAYING:
        return jsonify({'success': False, 'message': 'Not in playing phase'})
    
    current_player_id = G.i_turn
    
    # Draw a card if player conquered at least one territory
    if G.ar_player[current_player_id].fl_conq:
        cards_draw_card()
        G.ar_player[current_player_id].fl_conq = False
        web_state.game_message = f"{G.ar_player[current_player_id].name} drew a card!"
    
    # Reset movement flag
    G.ar_player[current_player_id].fl_move = False
    
    # Move to next player
    old_player = G.i_turn
    game_next_player()
    
    # Check if game over
    if check_game_over():
        for i in range(1, MAXPLAYERS + 1):
            if G.ar_player[i].active and G.ar_player[i].territ > 0:
                web_state.game_message = f"Game over! {G.ar_player[i].name} has won!"
                G.game_state = GameState.STOPPED
                break
    else:
        # Calculate new armies for next player
        if G.game_state == GameState.PLAYING:
            G.ar_player[G.i_turn].new_army = calculate_new_armies(G.i_turn)
            web_state.game_message = f"Player {G.i_turn}'s turn. {G.ar_player[G.i_turn].new_army} new armies to place."
    
    web_state.attack_from = None
    web_state.attack_to = None
    web_state.selected_territory = None
    
    return jsonify({
        'success': True,
        'message': web_state.game_message,
        'next_player': G.i_turn,
        'new_army': G.ar_player[G.i_turn].new_army if G.game_state == GameState.PLAYING else 0
    })


def calculate_new_armies(player_id: int) -> int:
    """Calculate the number of new armies a player gets"""
    player = G.ar_player[player_id]
    
    # Base: number of territories / 3 (minimum 3)
    base_armies = max(3, player.territ // 3)
    
    # Add continent bonuses
    continent_bonus = 0
    for cont_id in ContinentID:
        if G.ar_continent[cont_id].owner == player_id:
            continent_bonus += G.ar_continent[cont_id].bonus
    
    # Add card trade bonus (simplified - would need to implement card trading)
    card_bonus = 0
    
    return base_armies + continent_bonus + card_bonus


@app.route('/cancel_action')
def cancel_action():
    """Cancel the current action"""
    web_state.attack_from = None
    web_state.attack_to = None
    web_state.move_from = None
    web_state.move_to = None
    web_state.selected_territory = None
    web_state.game_message = "Action cancelled."
    
    return jsonify({
        'success': True,
        'message': web_state.game_message,
        'attack_from': None,
        'attack_to': None
    })


@app.route('/get_game_state')
def get_game_state():
    """Get the current game state as JSON"""
    territories = {i: get_territory_info(i) for i in range(1, MAXTERRITORIES + 1)}
    players = {i: get_player_info(i) for i in range(1, MAXPLAYERS + 1) if G.ar_player[i].active}
    
    return jsonify({
        'game_state': G.game_state.name,
        'current_player': G.i_turn,
        'territories': territories,
        'players': players,
        'message': web_state.game_message,
        'attack_from': web_state.attack_from,
        'attack_to': web_state.attack_to
    })


@app.route('/territory_info/<int:terr_id>')
def territory_info(terr_id):
    """Get detailed information about a territory"""
    terr = G.ar_territory[terr_id]
    
    # Get adjacent territories
    borders = []
    for i in range(1, terr.nbord + 1):
        border_id = terr.bord[i]
        if border_id > 0:
            borders.append({
                'id': border_id,
                'name': G.ar_territory[border_id].name,
                'owner': G.ar_territory[border_id].owner,
                'army': G.ar_territory[border_id].army
            })
    
    return jsonify({
        'id': terr_id,
        'name': terr.name,
        'owner': terr.owner,
        'owner_name': G.ar_player[terr.owner].name if terr.owner > 0 else '',
        'army': terr.army,
        'continent': terr.continent.name,
        'borders': borders
    })


# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

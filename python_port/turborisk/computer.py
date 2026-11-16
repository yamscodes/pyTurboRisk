"""
TurboRisk - Python Port
Computer Player Logic

This module handles the execution of computer player turns using TRP scripts.
Ported from Computer.pas
"""

import time
from typing import Optional, List, Dict, Any

from .globals import G, MAXTERRITORIES, MAXPLAYERS, GameState, RoutineType, SimStatus
from .territory import claim_territory, place_armies, transfer_armies, is_adjacent
from .exp_subr import set_urandom_seed


class TRPError(Exception):
    """Exception for TRP script errors"""
    pass


class ComputerPlayer:
    """Handles computer player logic"""
    
    def __init__(self):
        self.start_time = 0
        self.end_time = 0
        self.error_message = ""
    
    def cpu_phase(self, routine: RoutineType):
        """Increment CPU phase counter for a routine"""
        if 1 <= G.i_turn <= MAXPLAYERS:
            G.ar_player[G.i_turn].cpu[routine].phases += 1
    
    def cpu_call(self, routine: RoutineType, ticks: int):
        """Record CPU call for a routine"""
        if 1 <= G.i_turn <= MAXPLAYERS:
            G.ar_player[G.i_turn].cpu[routine].time += ticks
            G.ar_player[G.i_turn].cpu[routine].calls += 1
    
    def log_trp_decision(self, message: str):
        """Log a TRP decision"""
        if G.b_trsim_cli and G.verbose:
            print(f"[verbose] turn {G.i_turn_counter} player {G.ar_player[G.i_turn].name}: {message}")
    
    def show_error(self, msg: str):
        """Show an error message"""
        self.error_message = msg
        
        if not G.b_g_trsim:  # TurboRisk
            # In GUI version, show error dialog
            print(f"TRP Error: {msg}")
            
            if G.b_stop_asap:
                G.b_close_asap = True
        else:  # TRSim
            print(f"TRP error: {msg}")
            
            if G.error_dump:
                # Dump game state
                self.dump_game_state(msg)
            
            if G.chk_error_abort:
                G.u_sim_status = SimStatus.ERROR
                G.b_stop_asap = True
    
    def dump_game_state(self, msg: str):
        """Dump game state for debugging"""
        import os
        from datetime import datetime
        
        dump_dir = os.path.join(G.s_g_app_path, 'Dump')
        os.makedirs(dump_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dump_file = os.path.join(dump_dir, f'trdump_{timestamp}.trd')
        
        with open(dump_file, 'w') as f:
            f.write(f"TRP Error: {msg}\n\n")
            f.write(f"Game State:\n")
            f.write(f"  Turn: {G.i_turn_counter}\n")
            f.write(f"  Current Player: {G.i_turn}\n")
            f.write(f"  Game State: {G.game_state}\n\n")
            
            f.write(f"Territories:\n")
            for i in range(1, MAXTERRITORIES + 1):
                terr = G.ar_territory[i]
                f.write(f"  {i}: {terr.name} (Owner: {terr.owner}, Armies: {terr.army})\n")
            
            f.write(f"\nPlayers:\n")
            for i in range(1, MAXPLAYERS + 1):
                player = G.ar_player[i]
                if player.active:
                    f.write(f"  {i}: {player.name} (Armies: {player.army}, Territories: {player.territ})\n")
        
        print(f"Game state dumped to: {dump_file}")
    
    def execute_assignment(self):
        """Execute the assignment routine for the computer player"""
        to_territory = 0
        
        try:
            self.cpu_phase(RoutineType.ASSIGNMENT)
            start_time = time.time()
            
            # Execute the TRP ASSIGNMENT procedure
            # This would call the script's ASSIGNMENT function
            # For now, we'll use a simple AI
            to_territory = self.simple_assignment_ai()
            
            self.end_time = time.time()
            self.cpu_call(RoutineType.ASSIGNMENT, int((self.end_time - start_time) * 1000))
            
        except Exception as e:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Assignment\nError: {str(e)}"
            self.show_error(msg)
            return
        
        # Validate the request
        if to_territory < 1 or to_territory > MAXTERRITORIES:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Assignment\nTo territory: {to_territory}\nError: Invalid territory"
            self.show_error(msg)
            return
        
        if G.ar_territory[to_territory].owner != 0:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Assignment\nTo territory: {to_territory}\nError: Territory already owned"
            self.show_error(msg)
            return
        
        # Assign the territory
        self.log_trp_decision(f"Assignment: {G.ar_territory[to_territory].name}")
        claim_territory(to_territory, G.i_turn)
        
        # Log
        if G.ar_player[G.i_turn].keep_log:
            self.write_log(f"{G.ar_territory[to_territory].name} assigned.")
    
    def simple_assignment_ai(self) -> int:
        """Simple AI for territory assignment - pick the first available territory"""
        # In a real implementation, this would call the TRP script
        # For now, just pick territories in order
        for i in range(1, MAXTERRITORIES + 1):
            if G.ar_territory[i].owner == 0:
                return i
        return 1
    
    def execute_placement(self, armies_to_place: int):
        """Execute the placement routine for the computer player"""
        to_territory = 0
        
        while armies_to_place > 0:
            to_territory = 0
            
            try:
                self.cpu_phase(RoutineType.PLACEMENT)
                start_time = time.time()
                
                # Execute the TRP PLACEMENT procedure
                to_territory = self.simple_placement_ai()
                
                self.end_time = time.time()
                self.cpu_call(RoutineType.PLACEMENT, int((self.end_time - start_time) * 1000))
                
            except Exception as e:
                msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Placement\nError: {str(e)}"
                self.show_error(msg)
                return
            
            # Validate the request
            if to_territory < 1 or to_territory > MAXTERRITORIES:
                msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Placement\nTo territory: {to_territory}\nError: Invalid territory"
                self.show_error(msg)
                return
            
            if G.ar_territory[to_territory].owner != G.i_turn:
                msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Placement\nTo territory: {to_territory}\nError: Territory not owned by player"
                self.show_error(msg)
                return
            
            # Place the army
            self.log_trp_decision(f"Placement: add 1 army to {G.ar_territory[to_territory].name}")
            place_armies(to_territory, G.i_turn, 1)
            armies_to_place -= 1
    
    def simple_placement_ai(self) -> int:
        """Simple AI for army placement - reinforce the strongest territory"""
        # In a real implementation, this would call the TRP script
        # For now, just pick the first owned territory
        for i in range(1, MAXTERRITORIES + 1):
            if G.ar_territory[i].owner == G.i_turn:
                return i
        return 1
    
    def execute_attack(self):
        """Execute the attack routine for the computer player"""
        from_territory = 0
        to_territory = 0
        
        try:
            self.cpu_phase(RoutineType.ATTACK)
            start_time = time.time()
            
            # Execute the TRP ATTACK procedure
            from_territory, to_territory = self.simple_attack_ai()
            
            self.end_time = time.time()
            self.cpu_call(RoutineType.ATTACK, int((self.end_time - start_time) * 1000))
            
        except Exception as e:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Attack\nError: {str(e)}"
            self.show_error(msg)
            return
        
        # Validate the request
        if from_territory < 1 or from_territory > MAXTERRITORIES:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Attack\nFrom territory: {from_territory}\nError: Invalid from territory"
            self.show_error(msg)
            return
        
        if to_territory < 1 or to_territory > MAXTERRITORIES:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Attack\nTo territory: {to_territory}\nError: Invalid to territory"
            self.show_error(msg)
            return
        
        if not is_adjacent(from_territory, to_territory):
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Attack\nFrom: {from_territory}, To: {to_territory}\nError: Territories are not adjacent"
            self.show_error(msg)
            return
        
        if G.ar_territory[from_territory].owner != G.i_turn:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Attack\nFrom territory: {from_territory}\nError: From territory not owned by player"
            self.show_error(msg)
            return
        
        if G.ar_territory[to_territory].owner == G.i_turn:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Attack\nTo territory: {to_territory}\nError: To territory already owned by player"
            self.show_error(msg)
            return
        
        # Perform the attack
        self.log_trp_decision(f"Attack: {G.ar_territory[from_territory].name} -> {G.ar_territory[to_territory].name}")
        # TODO: Implement actual attack logic
        print(f"Attack from {from_territory} to {to_territory}")
    
    def simple_attack_ai(self) -> Tuple[int, int]:
        """Simple AI for attacks - find the first valid attack"""
        # In a real implementation, this would call the TRP script
        # For now, just find the first owned territory that can attack
        for from_t in range(1, MAXTERRITORIES + 1):
            if G.ar_territory[from_t].owner == G.i_turn:
                for i in range(1, G.ar_territory[from_t].nbord + 1):
                    to_t = G.ar_territory[from_t].bord[i]
                    if to_t > 0 and G.ar_territory[to_t].owner != G.i_turn:
                        return (from_t, to_t)
        return (0, 0)
    
    def execute_occupation(self, from_territory: int, to_territory: int):
        """Execute the occupation routine for the computer player"""
        armies = 0
        
        try:
            self.cpu_phase(RoutineType.OCCUPATION)
            start_time = time.time()
            
            # Execute the TRP OCCUPATION procedure
            armies = self.simple_occupation_ai(from_territory, to_territory)
            
            self.end_time = time.time()
            self.cpu_call(RoutineType.OCCUPATION, int((self.end_time - start_time) * 1000))
            
        except Exception as e:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Occupation\nError: {str(e)}"
            self.show_error(msg)
            return
        
        # Validate the request
        if armies < 0:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Occupation\nArmies: {armies}\nError: Invalid army count"
            self.show_error(msg)
            return
        
        # Check if from_territory has enough armies
        if G.ar_territory[from_territory].army <= armies:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Occupation\nFrom: {from_territory}, Armies: {armies}\nError: Not enough armies"
            self.show_error(msg)
            return
        
        # Transfer armies
        self.log_trp_decision(f"Occupation: move {armies} armies from {G.ar_territory[from_territory].name} to {G.ar_territory[to_territory].name}")
        transfer_armies(from_territory, to_territory, armies, 0)  # 0 = occupation
    
    def simple_occupation_ai(self, from_territory: int, to_territory: int) -> int:
        """Simple AI for occupation - move all but 1 army"""
        # In a real implementation, this would call the TRP script
        # For now, move all but 1 army
        armies = G.ar_territory[from_territory].army - 1
        return max(1, armies)
    
    def execute_fortification(self):
        """Execute the fortification routine for the computer player"""
        from_territory = 0
        to_territory = 0
        armies = 0
        
        try:
            self.cpu_phase(RoutineType.FORTIFICATION)
            start_time = time.time()
            
            # Execute the TRP FORTIFICATION procedure
            from_territory, to_territory, armies = self.simple_fortification_ai()
            
            self.end_time = time.time()
            self.cpu_call(RoutineType.FORTIFICATION, int((self.end_time - start_time) * 1000))
            
        except Exception as e:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Fortification\nError: {str(e)}"
            self.show_error(msg)
            return
        
        # Validate the request
        if from_territory < 1 or from_territory > MAXTERRITORIES:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Fortification\nFrom territory: {from_territory}\nError: Invalid from territory"
            self.show_error(msg)
            return
        
        if to_territory < 1 or to_territory > MAXTERRITORIES:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Fortification\nTo territory: {to_territory}\nError: Invalid to territory"
            self.show_error(msg)
            return
        
        if armies < 1:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Fortification\nArmies: {armies}\nError: Invalid army count"
            self.show_error(msg)
            return
        
        # Check if territories are adjacent and owned by the player
        if G.ar_territory[from_territory].owner != G.i_turn or G.ar_territory[to_territory].owner != G.i_turn:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Fortification\nError: Territories not owned by player"
            self.show_error(msg)
            return
        
        if not is_adjacent(from_territory, to_territory):
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Fortification\nError: Territories are not adjacent"
            self.show_error(msg)
            return
        
        # Check if from_territory has enough armies
        if G.ar_territory[from_territory].army <= armies:
            msg = f"Player: {G.ar_player[G.i_turn].name}\nRoutine: Fortification\nFrom: {from_territory}, Armies: {armies}\nError: Not enough armies"
            self.show_error(msg)
            return
        
        # Transfer armies
        self.log_trp_decision(f"Fortification: move {armies} armies from {G.ar_territory[from_territory].name} to {G.ar_territory[to_territory].name}")
        transfer_armies(from_territory, to_territory, armies, 0)  # 0 = fortification
    
    def simple_fortification_ai(self) -> Tuple[int, int, int]:
        """Simple AI for fortification - find the first valid fortification"""
        # In a real implementation, this would call the TRP script
        # For now, just find the first owned territory that can fortify another
        for from_t in range(1, MAXTERRITORIES + 1):
            if G.ar_territory[from_t].owner == G.i_turn and G.ar_territory[from_t].army > 1:
                for i in range(1, G.ar_territory[from_t].nbord + 1):
                    to_t = G.ar_territory[from_t].bord[i]
                    if to_t > 0 and G.ar_territory[to_t].owner == G.i_turn:
                        armies = G.ar_territory[from_t].army - 1
                        return (from_t, to_t, armies)
        return (0, 0, 0)
    
    def execute_computer_turn(self):
        """Execute a complete turn for the computer player"""
        # Assignment phase
        if G.game_state == GameState.ASSIGNING:
            self.execute_assignment()
        
        # Placement phase
        elif G.game_state == GameState.DISTRIBUTING:
            armies_to_place = G.ar_player[G.i_turn].new_army
            if armies_to_place > 0:
                self.execute_placement(armies_to_place)
        
        # Playing phase
        elif G.game_state == GameState.PLAYING:
            # Attack phase
            self.execute_attack()
            
            # Occupation phase (after conquest)
            # This would be called after a successful attack
            
            # Fortification phase
            self.execute_fortification()
    
    def write_log(self, message: str):
        """Write to the player's log"""
        if G.ar_player[G.i_turn].keep_log:
            print(f"[LOG] {G.ar_player[G.i_turn].name}: {message}")


# Create a global instance
computer = ComputerPlayer()


def execute_computer_turn():
    """Execute the computer player's turn"""
    computer.execute_computer_turn()

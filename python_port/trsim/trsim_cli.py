#!/usr/bin/env python3
"""
TRSimCLI - Python Port
Command-line interface for running TurboRisk simulations

This module provides a command-line interface for running scheduled TRP games
without showing the simulator GUI.

Usage:
    python trsim_cli.py --schedule <file> [options]

Ported from TRSimCLI.lpr and Sim.pas
"""

import argparse
import os
import sys
import time
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from turborisk.globals import G, MAXPLAYERS, MAXTERRITORIES, GameState, SimStatus, Player, DEFAULT_COLORS, CardsHandling, ContinentID, AssignmentType, CardValueType
from turborisk.territory import setup_territories, load_map
from turborisk.exp_subr import set_urandom_seed, u_message


class TRSimCLI:
    """Main TRSimCLI class"""
    
    def __init__(self):
        self.schedule_file = ""
        self.map_name = "std_map_small.trm"
        self.game_log_file = "TRSimCLI.sgl"
        self.cpu_log_file = "TRSimCLI.scl"
        self.action_log_file = ""
        self.turn_limit = 0
        self.time_limit = 0
        self.seed = None
        self.verbose = False
        self.error_dump = False
        self.statistically_significant_sample = False
        self.allow_duplicate_players = False
        
        # Runtime state
        self.normalized_schedule: List[str] = []
        self.unique_players: List[str] = []
        self.exit_code = 2  # Default to error
        self.games_completed = 0
        self.games_with_errors = 0
        self.start_time = None
        
    def parse_args(self):
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(
            description='TRSimCLI - Run scheduled TRP games without showing the simulator GUI',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Each non-empty, non-comment schedule line is one comma-separated roster.
Player names may include or omit .trp; each roster needs 2-10 players.
Blank lines and lines beginning with # are ignored.
Paths for schedules and logs are relative to the current directory.
Map files are loaded from the maps directory beside TRSimCLI.

Example: python trsim_cli.py --schedule pairings.csv --map std_map_small.trm --turn-limit 20

Exit codes:
  0 - Success
  1 - One or more TRP errors
  2 - Input or setup error

Turn- and time-limited games are logged separately from TRP errors.
Concurrent runs must use different game-log and CPU-log paths.
            """
        )
        
        parser.add_argument('--schedule', required=True, help='Required roster schedule (one game per line)')
        parser.add_argument('--map', default='std_map_small.trm', help='Map in maps (default: std_map_small.trm)')
        parser.add_argument('--game-log', default='TRSimCLI.sgl', help='Game log (default: TRSimCLI.sgl)')
        parser.add_argument('--cpu-log', default='TRSimCLI.scl', help='CPU usage log (default: TRSimCLI.scl)')
        parser.add_argument('--action-log', default='', help='Optional public action history (JSONL, appended)')
        parser.add_argument('--turn-limit', type=int, default=0, help='Maximum turns per game (0: unlimited)')
        parser.add_argument('--time-limit', type=int, default=0, help='Maximum seconds per game (0: unlimited)')
        parser.add_argument('--seed', type=int, default=None, help='Random-number-generator seed')
        parser.add_argument('--statistically-significant-sample', action='store_true', 
                           help='Repeat schedule up to 10x until statistical significance')
        parser.add_argument('--verbose', action='store_true', help='Log TRP decisions and action outcomes')
        parser.add_argument('--error-dump', action='store_true', help='Write a game dump when a TRP errors')
        parser.add_argument('--allow-duplicate-players', action='store_true', 
                           help='Permit repeated instances of the same bot')
        
        args = parser.parse_args()
        
        self.schedule_file = args.schedule
        self.map_name = args.map
        self.game_log_file = args.game_log
        self.cpu_log_file = args.cpu_log
        self.action_log_file = args.action_log
        self.turn_limit = args.turn_limit
        self.time_limit = args.time_limit
        self.seed = args.seed
        self.verbose = args.verbose
        self.error_dump = args.error_dump
        self.statistically_significant_sample = args.statistically_significant_sample
        self.allow_duplicate_players = args.allow_duplicate_players
        
        return args
    
    def validate_inputs(self):
        """Validate command line inputs"""
        # Check schedule file exists
        if not os.path.exists(self.schedule_file):
            print(f"Error: Schedule file not found: {self.schedule_file}")
            return False
        
        # Check map file exists
        maps_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'maps')
        if not os.path.exists(maps_dir):
            maps_dir = os.path.join(os.path.dirname(__file__), 'maps')
        
        map_path = os.path.join(maps_dir, self.map_name)
        if not os.path.exists(map_path):
            print(f"Error: Map file not found: {map_path}")
            return False
        
        # Check map extension
        if not self.map_name.lower().endswith('.trm'):
            print(f"Error: Map file must have .trm extension: {self.map_name}")
            return False
        
        return True
    
    def load_schedule(self):
        """Load and validate the schedule file"""
        with open(self.schedule_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        schedule = []
        unique_players = set()
        min_players = MAXPLAYERS + 1
        max_players = 0
        
        for line_num, line in enumerate(lines, 1):
            # Remove BOM if present
            line = line.lstrip('\ufeff')
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Split by comma
            players = [p.strip() for p in line.split(',')]
            
            # Validate player count
            if len(players) < 2 or len(players) > MAXPLAYERS:
                print(f"Error: Schedule line {line_num} has an invalid player count ({len(players)} players)")
                return False, [], []
            
            # Normalize player names
            normalized_players = []
            for player in players:
                if not player.lower().endswith('.trp'):
                    player = player + '.trp'
                
                # Check if it's a valid filename
                if not player.lower().endswith('.trp') or os.path.dirname(player) != '':
                    print(f"Error: Invalid player filename on schedule line {line_num}: {player}")
                    return False, [], []
                
                # Check if file exists
                players_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'players')
                if not os.path.exists(players_dir):
                    players_dir = os.path.join(os.path.dirname(__file__), 'players')
                
                player_path = os.path.join(players_dir, player)
                if not os.path.exists(player_path):
                    print(f"Error: Player file not found: {player_path}")
                    return False, [], []
                
                # Check for duplicates
                if not self.allow_duplicate_players:
                    if player in normalized_players:
                        print(f"Error: Duplicate player on schedule line {line_num}: {player}")
                        return False, [], []
                
                normalized_players.append(player)
                unique_players.add(player.lower())
            
            schedule.append(','.join(normalized_players))
            min_players = min(min_players, len(normalized_players))
            max_players = max(max_players, len(normalized_players))
        
        if not schedule:
            print("Error: Schedule contains no game rosters")
            return False, [], []
        
        self.normalized_schedule = schedule
        self.unique_players = sorted(unique_players)
        
        return True, schedule, unique_players
    
    def initialize_game(self):
        """Initialize the game state"""
        # Set global flags
        G.b_g_trsim = True
        G.b_trsim_cli = True
        G.b_trcomp_running = False
        
        # Set application path
        G.s_g_app_path = os.path.dirname(os.path.abspath(__file__))
        
        # Load map
        G.s_map_file = self.map_name
        load_map(self.map_name)
        
        # Set simulation parameters
        G.i_sim_turn_limit = self.turn_limit
        G.i_sim_time_limit = self.time_limit
        
        # Set seed if specified
        if self.seed is not None:
            set_urandom_seed(self.seed)
            G.random.seed(self.seed)
        
        # Initialize territories
        setup_territories()
    
    def setup_game(self, roster: str):
        """Setup a game with the given roster"""
        players = roster.split(',')
        num_players = len(players)
        
        # Reset game state
        G.game_state = GameState.STOPPED
        G.i_turn_counter = 0
        G.i_turn = 0
        G.i_first_turn = 0
        G.i_n_players = num_players
        G.i_to_assign = MAXTERRITORIES
        G.b_human_turn = False
        G.b_eliminated_player = False
        G.b_stop_asap = False
        G.b_close_asap = False
        G.i_rank = num_players
        
        # Reset players
        for i in range(1, MAXPLAYERS + 1):
            G.ar_player[i] = Player()
        
        # Setup players
        for i, player_file in enumerate(players, 1):
            G.ar_player[i] = Player()
            G.ar_player[i].name = os.path.splitext(player_file)[0]
            G.ar_player[i].active = True
            G.ar_player[i].computer = True
            
            # Set the program file path
            players_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'players')
            if not os.path.exists(players_dir):
                players_dir = os.path.join(os.path.dirname(__file__), 'players')
            full_path = os.path.join(players_dir, player_file)
            G.ar_player[i].prg_file = full_path
            
            G.ar_player[i].color = DEFAULT_COLORS[(i - 1) % len(DEFAULT_COLORS)]
            G.ar_player[i].cards_handling = CardsHandling.SMART
            G.ar_player[i].keep_log = True
            
            # Enable logging based on verbose flag
            G.ar_player[i].ulog_enabled = self.verbose
            G.ar_player[i].umessage_enabled = self.verbose
        
        # Reset territories
        for i in range(1, MAXTERRITORIES + 1):
            G.ar_territory[i].owner = 0
            G.ar_territory[i].army = 0
        
        # Reset continents
        for cid in ContinentID:
            G.ar_continent[cid].owner = 0
        
        # Clear action history
        G.action_history = []
    
    def run_game(self, roster: str) -> Tuple[bool, int, Optional[str]]:
        """Run a single game with the given roster
        
        Returns: (success, winner, error_message)
        """
        game_start = time.time()
        G.dt_sim_game_time = datetime.now()
        
        # Setup game
        self.setup_game(roster)
        
        # TODO: Implement the full game loop
        # For now, just do a simple assignment and return
        
        # Simulate territory assignment
        players = roster.split(',')
        num_players = len(players)
        
        # Simple round-robin assignment
        for i in range(1, MAXTERRITORIES + 1):
            player_idx = ((i - 1) % num_players) + 1
            G.ar_territory[i].owner = player_idx
            G.ar_territory[i].army = 1
            G.ar_player[player_idx].territ += 1
            G.ar_player[player_idx].army += 1
        
        # Determine winner (for now, just pick the first player)
        winner = 1
        
        game_time = time.time() - game_start
        G.i_sim_game_time = int(game_time)
        G.u_sim_status = SimStatus.COMPLETE
        
        # Log the game
        self.log_message(f"Game completed in {game_time:.2f}s, winner: {players[winner - 1]}")
        
        return True, winner, None
    
    def check_statistical_significance(self) -> bool:
        """Check if we have statistical significance
        
        For now, just return True if we've run enough games
        """
        if not self.statistically_significant_sample:
            return True
        
        # TODO: Implement Wilson confidence interval calculation
        # For now, just run a minimum number of games
        min_games = len(self.normalized_schedule)
        if self.games_completed >= min_games * 10:
            return True
        
        return False
    
    def log_message(self, message: str):
        """Log a message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"{timestamp} {message}"
        print(log_entry)
        
        # Write to game log file
        with open(self.game_log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    
    def log_action(self, action: Dict):
        """Log an action to the action log file"""
        if not self.action_log_file:
            return
        
        with open(self.action_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(action) + '\n')
    
    def run(self):
        """Run the simulation"""
        # Parse arguments
        self.parse_args()
        
        # Validate inputs
        if not self.validate_inputs():
            return 2
        
        # Load schedule
        success, schedule, unique_players = self.load_schedule()
        if not success:
            return 2
        
        # Initialize game
        self.initialize_game()
        
        # Start simulation
        self.start_time = datetime.now()
        G.dt_sim_start_time = self.start_time
        
        num_games = len(schedule)
        G.i_sim_games = num_games
        
        if self.statistically_significant_sample:
            # Repeat schedule cyclically
            max_games = num_games * 10
            G.i_sim_games = max_games
        
        self.log_message(f"Starting simulation with {num_games} games")
        
        # Run games
        game_num = 0
        while game_num < G.i_sim_games:
            # Check for statistical significance
            if self.statistically_significant_sample and self.check_statistical_significance():
                break
            
            roster_idx = game_num % num_games
            roster = schedule[roster_idx]
            
            G.i_sim_curr = game_num + 1
            
            self.log_message(f"Game {game_num + 1}/{G.i_sim_games}: {roster}")
            
            try:
                success, winner, error = self.run_game(roster)
                
                if success:
                    G.i_sim_compl += 1
                    self.games_completed += 1
                    G.u_sim_status = SimStatus.COMPLETE
                    G.i_sim_winner = winner
                else:
                    G.i_sim_compl += 1
                    self.games_completed += 1
                    G.u_sim_status = SimStatus.ERROR
                    self.games_with_errors += 1
                    self.log_message(f"Error in game {game_num + 1}: {error}")
                    
                    if self.error_dump:
                        # TODO: Dump game state
                        pass
                
                game_num += 1
                
            except Exception as e:
                G.i_sim_compl += 1
                self.games_completed += 1
                G.u_sim_status = SimStatus.ERROR
                self.games_with_errors += 1
                self.log_message(f"Exception in game {game_num + 1}: {str(e)}")
                
                if self.error_dump:
                    # TODO: Dump game state
                    pass
                
                game_num += 1
        
        # Finalize
        self.log_message(f"Simulation complete: {self.games_completed} games, {self.games_with_errors} errors")
        
        # Set exit code
        if self.games_with_errors > 0:
            self.exit_code = 1
        else:
            self.exit_code = 0
        
        return self.exit_code


def main():
    """Main entry point"""
    cli = TRSimCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

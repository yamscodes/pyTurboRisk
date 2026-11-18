"""
TRSim - Simulation Tool GUI
Python port of Sim.pas (GUI version)
"""

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog, scrolledtext
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("Warning: Tkinter not available. TRSim GUI will not work.")

import os
import sys
import json
import time
from datetime import datetime
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from turborisk import G, MAXPLAYERS, MAXTERRITORIES
from turborisk.globals import GameState, SimStatus, ContinentID
from turborisk.territory import setup_territories, load_map, save_map
from turborisk.game_logic import setup, new_game_setup, supervisor, game_cleanup
from turborisk.computer import execute_computer_turn
from turborisk.trp_transpiler_v3 import TRPTranspiler
from turborisk.action_history import begin_action_history, end_action_history, start_action_log, stop_action_log


class TRSimGUI:
    """TRSim - Simulation Tool GUI"""
    
    def __init__(self, root):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run TRSim GUI.")
        
        self.root = root
        self.root.title("TRSim - TurboRisk Simulation Tool")
        self.root.geometry("1024x768")
        
        self.simulation_running = False
        self.simulation_thread = None
        self.stop_simulation = False
        
        # Initialize
        setup_territories()
        setup()
        
        self.create_menu_bar()
        self.create_main_layout()
        self.create_simulation_panel()
        self.create_players_panel()
        self.create_logging_panel()
        self.create_status_bar()
        
        # Load preferences
        self.load_preferences()
    
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Simulation", command=self.new_simulation)
        file_menu.add_command(label="Open Schedule...", command=self.open_schedule)
        file_menu.add_command(label="Save Schedule...", command=self.save_schedule)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.file_exit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Simulation menu
        sim_menu = tk.Menu(menubar, tearoff=0)
        sim_menu.add_command(label="Start", command=self.start_simulation, accelerator="F5")
        sim_menu.add_command(label="Stop", command=self.stop_simulation, accelerator="F4")
        sim_menu.add_command(label="Pause", command=self.pause_simulation)
        sim_menu.add_separator()
        sim_menu.add_command(label="Run Single Game", command=self.run_single_game)
        menubar.add_cascade(label="Simulation", menu=sim_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Show Map", command=self.toggle_show_map)
        view_menu.add_command(label="Show Stats", command=self.toggle_show_stats)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Preferences...", command=self.show_preferences)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_main_layout(self):
        """Create the main layout"""
        # Main paned window
        self.main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Simulation controls
        self.left_panel = tk.Frame(self.main_paned)
        self.main_paned.add(self.left_panel)
        
        # Right panel - Results and logs
        self.right_panel = tk.Frame(self.main_paned)
        self.main_paned.add(self.right_panel)
        
        # Notebook for right panel
        self.right_notebook = ttk.Notebook(self.right_panel)
        self.right_notebook.pack(fill=tk.BOTH, expand=True)
    
    def create_simulation_panel(self):
        """Create the simulation control panel"""
        # Simulation settings frame
        settings_frame = ttk.LabelFrame(self.left_panel, text="Simulation Settings")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Games to run
        ttk.Label(settings_frame, text="Games to Run:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.games_entry = ttk.Entry(settings_frame, width=10)
        self.games_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        self.games_entry.insert(0, "100")
        
        # Min Players
        ttk.Label(settings_frame, text="Min Players:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.min_players_entry = ttk.Entry(settings_frame, width=10)
        self.min_players_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        self.min_players_entry.insert(0, "2")
        
        # Max Players
        ttk.Label(settings_frame, text="Max Players:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.max_players_entry = ttk.Entry(settings_frame, width=10)
        self.max_players_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        self.max_players_entry.insert(0, "6")
        
        # Turn Limit
        ttk.Label(settings_frame, text="Turn Limit:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.turn_limit_entry = ttk.Entry(settings_frame, width=10)
        self.turn_limit_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
        self.turn_limit_entry.insert(0, "200")
        
        # Time Limit (seconds)
        ttk.Label(settings_frame, text="Time Limit (s):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        self.time_limit_entry = ttk.Entry(settings_frame, width=10)
        self.time_limit_entry.grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)
        self.time_limit_entry.insert(0, "60")
        
        # Map selection
        ttk.Label(settings_frame, text="Map:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=2)
        self.map_combo = ttk.Combobox(settings_frame, width=15)
        self.map_combo.grid(row=5, column=1, sticky=tk.W, padx=5, pady=2)
        self.map_combo['values'] = ['std_map_small.trm', 'std_map.trm']
        self.map_combo.set('std_map_small.trm')
        
        # Control buttons
        control_frame = ttk.Frame(self.left_panel)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_btn = ttk.Button(control_frame, text="Start (F5)", command=self.start_simulation)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop (F4)", command=self.stop_simulation, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_btn = ttk.Button(control_frame, text="Pause", command=self.pause_simulation, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress
        progress_frame = ttk.LabelFrame(self.left_panel, text="Progress")
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(progress_frame, text="Current Game:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.current_game_label = ttk.Label(progress_frame, text="0")
        self.current_game_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(progress_frame, text="Completed:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.completed_label = ttk.Label(progress_frame, text="0")
        self.completed_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(progress_frame, text="Status:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress_bar.grid(row=3, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=5)
    
    def create_players_panel(self):
        """Create the players configuration panel"""
        players_frame = ttk.LabelFrame(self.left_panel, text="Players")
        players_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Player list
        ttk.Label(players_frame, text="Available Players:").pack(anchor=tk.W, padx=5, pady=2)
        
        # List of TRP files
        self.players_listbox = tk.Listbox(players_frame, height=10, selectmode=tk.MULTIPLE)
        self.players_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Scan for TRP files
        self.scan_trp_files()
        
        # Selected players
        ttk.Label(players_frame, text="Selected Players:").pack(anchor=tk.W, padx=5, pady=(10, 2))
        self.selected_players_listbox = tk.Listbox(players_frame, height=5)
        self.selected_players_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Buttons
        btn_frame = ttk.Frame(players_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Add ->", command=self.add_player).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="<- Remove", command=self.remove_player).pack(side=tk.LEFT, padx=5)
    
    def create_logging_panel(self):
        """Create the logging panel"""
        # Game log tab
        self.log_frame = tk.Frame(self.right_notebook)
        self.right_notebook.add(self.log_frame, text="Game Log")
        
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            wrap=tk.WORD,
            font=('Courier', 10),
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Statistics tab
        self.stats_frame = tk.Frame(self.right_notebook)
        self.right_notebook.add(self.stats_frame, text="Statistics")
        
        self.stats_text = scrolledtext.ScrolledText(
            self.stats_frame,
            wrap=tk.WORD,
            font=('Courier', 10),
            state=tk.DISABLED
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        # CPU Log tab
        self.cpu_frame = tk.Frame(self.right_notebook)
        self.right_notebook.add(self.cpu_frame, text="CPU Log")
        
        self.cpu_text = scrolledtext.ScrolledText(
            self.cpu_frame,
            wrap=tk.WORD,
            font=('Courier', 10),
            state=tk.DISABLED
        )
        self.cpu_text.pack(fill=tk.BOTH, expand=True)
    
    def create_status_bar(self):
        """Create the status bar"""
        self.status_bar = tk.Frame(self.root, relief=tk.SUNKEN, bd=1)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_message = tk.Label(self.status_bar, text="Ready", anchor=tk.W)
        self.status_message.pack(fill=tk.X, expand=True, padx=5)
    
    def scan_trp_files(self):
        """Scan for TRP files in the players directory"""
        self.players_listbox.delete(0, tk.END)
        
        # Check default players directory
        players_dir = os.path.join(G.sG_AppPath, 'players')
        if os.path.exists(players_dir):
            for filename in sorted(os.listdir(players_dir)):
                if filename.lower().endswith('.trp'):
                    self.players_listbox.insert(tk.END, filename)
        
        # Also check in python_port/players if it exists
        python_players_dir = os.path.join(os.path.dirname(G.sG_AppPath), 'python_port', 'players')
        if os.path.exists(python_players_dir):
            for filename in sorted(os.listdir(python_players_dir)):
                if filename.lower().endswith('.trp') and filename not in self.players_listbox.get(0, tk.END):
                    self.players_listbox.insert(tk.END, filename)
    
    def add_player(self):
        """Add selected players to the simulation"""
        selections = self.players_listbox.curselection()
        for index in selections:
            player_file = self.players_listbox.get(index)
            if player_file not in self.selected_players_listbox.get(0, tk.END):
                self.selected_players_listbox.insert(tk.END, player_file)
    
    def remove_player(self):
        """Remove selected players from the simulation"""
        selections = self.selected_players_listbox.curselection()
        for index in reversed(selections):
            self.selected_players_listbox.delete(index)
    
    def new_simulation(self):
        """Create a new simulation"""
        if self.simulation_running:
            if not messagebox.askyesno("Warning", "Simulation is running. Stop it first?"):
                return
            self.stop_simulation()
        
        # Reset all
        self.games_entry.delete(0, tk.END)
        self.games_entry.insert(0, "100")
        self.min_players_entry.delete(0, tk.END)
        self.min_players_entry.insert(0, "2")
        self.max_players_entry.delete(0, tk.END)
        self.max_players_entry.insert(0, "6")
        self.turn_limit_entry.delete(0, tk.END)
        self.turn_limit_entry.insert(0, "200")
        self.time_limit_entry.delete(0, tk.END)
        self.time_limit_entry.insert(0, "60")
        
        self.current_game_label.config(text="0")
        self.completed_label.config(text="0")
        self.status_label.config(text="Ready")
        self.progress_bar['value'] = 0
        
        self.log_message("New simulation created")
    
    def open_schedule(self):
        """Open a schedule file"""
        filename = filedialog.askopenfilename(
            title="Open Schedule File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    # Parse CSV file
                    lines = f.readlines()
                    for line in lines[1:]:  # Skip header
                        line = line.strip()
                        if line:
                            parts = line.split(',')
                            if len(parts) >= 2:
                                player_file = parts[0].strip()
                                if player_file not in self.selected_players_listbox.get(0, tk.END):
                                    self.selected_players_listbox.insert(tk.END, player_file)
                
                self.log_message(f"Schedule loaded from: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load schedule: {str(e)}")
    
    def save_schedule(self):
        """Save the schedule to a file"""
        filename = filedialog.asksaveasfilename(
            title="Save Schedule File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            defaultextension=".csv"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    # Write header
                    f.write("Player File,Player Name,Type\n")
                    
                    # Write players
                    for i, player_file in enumerate(self.selected_players_listbox.get(0, tk.END)):
                        f.write(f"{player_file},Player {i+1},Computer\n")
                
                self.log_message(f"Schedule saved to: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save schedule: {str(e)}")
    
    def start_simulation(self):
        """Start the simulation"""
        if self.simulation_running:
            messagebox.showwarning("Warning", "Simulation is already running")
            return
        
        # Get settings
        try:
            num_games = int(self.games_entry.get())
            min_players = int(self.min_players_entry.get())
            max_players = int(self.max_players_entry.get())
            turn_limit = int(self.turn_limit_entry.get())
            time_limit = int(self.time_limit_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid settings. Please enter valid numbers.")
            return
        
        # Get selected players
        players = self.selected_players_listbox.get(0, tk.END)
        if not players:
            messagebox.showerror("Error", "Please select at least one player")
            return
        
        if len(players) < min_players:
            messagebox.showerror("Error", f"Need at least {min_players} players, but only {len(players)} selected")
            return
        
        # Disable UI
        self.simulation_running = True
        self.stop_simulation = False
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.NORMAL)
        
        # Reset counters
        self.current_game = 0
        self.completed_games = 0
        self.current_game_label.config(text="0")
        self.completed_label.config(text="0")
        self.status_label.config(text="Running")
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = num_games
        
        # Clear logs
        self.clear_logs()
        
        # Start simulation in a thread
        self.simulation_thread = threading.Thread(
            target=self.run_simulation_thread,
            args=(num_games, min_players, max_players, turn_limit, time_limit, players),
            daemon=True
        )
        self.simulation_thread.start()
        
        self.log_message(f"Simulation started: {num_games} games with {len(players)} players")
    
    def run_simulation_thread(self, num_games, min_players, max_players, turn_limit, time_limit, players):
        """Run the simulation in a background thread"""
        try:
            # Initialize statistics
            stats = {
                'total_games': 0,
                'wins': {},
                'average_turns': 0,
                'total_turns': 0,
                'start_time': datetime.now()
            }
            
            # Initialize players
            for i, player_file in enumerate(players):
                stats['wins'][player_file] = 0
            
            # Run games
            for game_num in range(num_games):
                if self.stop_simulation:
                    break
                
                # Update current game
                self.current_game = game_num + 1
                self.root.after(0, lambda: self.current_game_label.config(text=str(self.current_game)))
                self.root.after(0, lambda: self.progress_bar['value'], self.current_game)
                
                # Set up the game
                try:
                    # Reset game state
                    setup()
                    setup_territories()
                    
                    # Load map if specified
                    map_file = self.map_combo.get()
                    if map_file:
                        try:
                            load_map(map_file)
                        except:
                            pass
                    
                    # Set up players for this game
                    num_game_players = min_players + (game_num % (max_players - min_players + 1))
                    num_game_players = min(num_game_players, len(players))
                    
                    for i in range(1, MAXPLAYERS + 1):
                        G.ar_player[i].active = (i <= num_game_players)
                        if i <= num_game_players:
                            G.ar_player[i].computer = True
                            G.ar_player[i].name = f"Player {i}"
                            G.ar_player[i].prg_file = players[(i-1) % len(players)]
                    
                    # Start action history
                    begin_action_history()
                    start_action_log(f"sim_game_{game_num}.jsonl")
                    
                    # Run the game
                    new_game_setup()
                    
                    # Run until completion
                    turn_count = 0
                    while G.game_state != GameState.STOPPED and turn_count < turn_limit:
                        if self.stop_simulation:
                            break
                        
                        supervisor()
                        turn_count += 1
                        
                        # Check for winner
                        active_players = sum(1 for i in range(1, MAXPLAYERS + 1) if G.ar_player[i].active and G.ar_player[i].territ > 0)
                        if active_players <= 1:
                            # Find the winner
                            for i in range(1, MAXPLAYERS + 1):
                                if G.ar_player[i].active and G.ar_player[i].territ > 0:
                                    winner_file = G.ar_player[i].prg_file
                                    stats['wins'][winner_file] = stats['wins'].get(winner_file, 0) + 1
                                    break
                            break
                    
                    # Clean up
                    end_action_history()
                    stop_action_log()
                    game_cleanup()
                    
                    stats['total_turns'] += turn_count
                    stats['total_games'] += 1
                    
                    # Update completed count
                    self.completed_games += 1
                    self.root.after(0, lambda: self.completed_label.config(text=str(self.completed_games)))
                    
                    # Update logs
                    self.root.after(0, lambda: self.log_message(f"Game {game_num + 1} completed in {turn_count} turns"))
                    
                except Exception as e:
                    self.root.after(0, lambda: self.log_message(f"Game {game_num + 1} error: {str(e)}", error=True))
            
            # Calculate statistics
            if stats['total_games'] > 0:
                stats['average_turns'] = stats['total_turns'] / stats['total_games']
            stats['end_time'] = datetime.now()
            stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
            
            # Update UI
            self.root.after(0, lambda: self.update_statistics(stats))
            self.root.after(0, lambda: self.log_message(f"Simulation completed: {stats['total_games']} games in {stats['duration']:.2f} seconds"))
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Simulation error: {str(e)}", error=True))
        finally:
            # Clean up
            self.simulation_running = False
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.pause_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.status_label.config(text="Completed"))
    
    def update_statistics(self, stats):
        """Update the statistics display"""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        
        self.stats_text.insert(tk.END, f"Simulation Statistics\n")
        self.stats_text.insert(tk.END, f"===================\n\n")
        self.stats_text.insert(tk.END, f"Total Games: {stats['total_games']}\n")
        self.stats_text.insert(tk.END, f"Total Turns: {stats['total_turns']}\n")
        self.stats_text.insert(tk.END, f"Average Turns: {stats['average_turns']:.2f}\n")
        self.stats_text.insert(tk.END, f"Duration: {stats['duration']:.2f} seconds\n\n")
        
        self.stats_text.insert(tk.END, f"Wins by Player:\n")
        self.stats_text.insert(tk.END, f"----------------\n")
        for player_file, wins in sorted(stats['wins'].items()):
            if wins > 0:
                percentage = (wins / stats['total_games']) * 100 if stats['total_games'] > 0 else 0
                self.stats_text.insert(tk.END, f"{player_file}: {wins} ({percentage:.1f}%)\n")
        
        self.stats_text.config(state=tk.DISABLED)
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.stop_simulation = True
        self.log_message("Stopping simulation...")
    
    def pause_simulation(self):
        """Pause the simulation"""
        # Note: Pausing is not fully implemented yet
        self.log_message("Pause: Not yet implemented")
    
    def run_single_game(self):
        """Run a single game"""
        if self.simulation_running:
            messagebox.showwarning("Warning", "Simulation is running. Stop it first?")
            return
        
        # Get settings
        try:
            turn_limit = int(self.turn_limit_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid turn limit")
            return
        
        # Get selected players
        players = self.selected_players_listbox.get(0, tk.END)
        if not players:
            messagebox.showerror("Error", "Please select at least one player")
            return
        
        # Run a single game
        self.simulation_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        self.current_game = 1
        self.completed_games = 0
        self.current_game_label.config(text="1")
        self.completed_label.config(text="0")
        self.status_label.config(text="Running")
        
        self.clear_logs()
        self.log_message("Running single game...")
        
        # Run in thread
        self.simulation_thread = threading.Thread(
            target=self.run_simulation_thread,
            args=(1, 2, 2, turn_limit, 60, players),
            daemon=True
        )
        self.simulation_thread.start()
    
    def toggle_show_map(self):
        """Toggle map display"""
        self.log_message("Show Map: Not yet implemented")
    
    def toggle_show_stats(self):
        """Toggle stats display"""
        self.log_message("Show Stats: Not yet implemented")
    
    def show_preferences(self):
        """Show preferences dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Preferences")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="TRSim Preferences").pack(pady=10)
        
        # Add preference options here
        ttk.Checkbutton(dialog, text="Show detailed logging").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Checkbutton(dialog, text="Save game logs").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Checkbutton(dialog, text="Save CPU logs").pack(anchor=tk.W, padx=10, pady=5)
        
        ttk.Button(dialog, text="OK", command=dialog.destroy).pack(pady=10)
        
        self.root.wait_window(dialog)
    
    def load_preferences(self):
        """Load preferences from config file"""
        # Not yet implemented
        pass
    
    def save_preferences(self):
        """Save preferences to config file"""
        # Not yet implemented
        pass
    
    def file_exit(self):
        """Exit the application"""
        if self.simulation_running:
            if not messagebox.askyesno("Warning", "Simulation is running. Stop it and exit?"):
                return
            self.stop_simulation()
        
        self.root.quit()
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About TRSim", 
                           f"TRSim - TurboRisk Simulation Tool\n\n"
                           f"Version: {G.sG_AppVers}\n"
                           f"Python Port")
    
    def clear_logs(self):
        """Clear all log displays"""
        for text_widget in [self.log_text, self.stats_text, self.cpu_text]:
            text_widget.config(state=tk.NORMAL)
            text_widget.delete(1.0, tk.END)
            text_widget.config(state=tk.DISABLED)
    
    def log_message(self, message, error=False):
        """Log a message"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        if error:
            self.log_text.insert(tk.END, f"[{timestamp}] ERROR: {message}\n", 'error')
        else:
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Update status message
        self.status_message.config(text=message)


def main():
    """Main entry point for TRSim GUI"""
    if not TKINTER_AVAILABLE:
        print("Error: Tkinter is required to run TRSim GUI.")
        print("Install it with: pip install tk")
        sys.exit(1)
    
    root = tk.Tk()
    app = TRSimGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()

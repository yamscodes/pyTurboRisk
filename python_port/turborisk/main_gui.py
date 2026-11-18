"""
TurboRisk - Python Port
Main GUI Application

This module provides the main GUI window for TurboRisk using Tkinter.
Ported from Main.pas and Main.lfm

Note: This module requires Tkinter and PIL to be installed.
To run the GUI, you need a proper display environment.
"""

import os
import sys

# Try to import GUI dependencies
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    from PIL import Image, ImageTk
    TKINTER_AVAILABLE = True
except ImportError as e:
    TKINTER_AVAILABLE = False
    print(f"Warning: Tkinter/PIL not available: {e}")
    print("GUI functionality will be limited.")

from .globals import G, MAXTERRITORIES, GameState
from .territory import setup_territories, find_territory
from .exp_subr import t_owner, t_name


class MainGUI:
    """Main GUI window for TurboRisk"""
    
    def __init__(self, root):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI. Please install tkinter and PIL.")
        
        self.root = root
        self.root.title(f"TurboRisk {G.sG_AppVers}")
        
        # Set window size
        self.root.geometry("1024x768")
        self.root.minsize(800, 600)
        
        # Configure styles
        self.configure_styles()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create main map panel
        self.create_map_panel()
        
        # Create status bar
        self.create_status_bar()
        
        # Initialize game state
        self.initialize_game()
        
        # Bind events
        self.bind_events()
        
        # Load map image if available
        self.load_map_image()
    
    def configure_styles(self):
        """Configure Tkinter styles"""
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TButton', padding=2)
        style.configure('TMenubutton', padding=2)
    
    def create_menu_bar(self):
        """Create the menu bar"""
        self.menu_bar = tk.Menu(self.root)
        
        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="New Game", command=self.mnu_fil_new_click, accelerator="Ctrl+N")
        self.file_menu.add_command(label="Save Game", command=self.mnu_fil_save_click, accelerator="Ctrl+S")
        self.file_menu.add_command(label="Restore Game", command=self.mnu_fil_restore_click, accelerator="Ctrl+O")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="End Game", command=self.mnu_fil_end_click)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.mnu_fil_exit_click)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        
        # Options menu
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.options_menu.add_command(label="Players", command=self.mnu_opt_players_click)
        self.options_menu.add_command(label="Map", command=self.mnu_opt_map_click)
        self.options_menu.add_command(label="Rules", command=self.mnu_opt_rules_click)
        self.options_menu.add_command(label="Preferences", command=self.mnu_opt_pref_click)
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        
        # View menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.view_menu.add_command(label="Statistics", command=self.mnu_vie_stats_click)
        self.view_menu.add_command(label="History", command=self.mnu_vie_hist_click)
        self.view_menu.add_command(label="Log", command=self.mnu_vie_log_click)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        
        # Help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Readme", command=self.mnu_hel_readme_click)
        self.help_menu.add_command(label="About", command=self.mnu_hel_about_click)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="Homepage", command=self.mnu_hel_homepage_click)
        self.help_menu.add_command(label="Check for Updates", command=self.mnu_hel_check_updates_click)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        
        self.root.config(menu=self.menu_bar)
    
    def create_toolbar(self):
        """Create the toolbar"""
        self.toolbar = tk.Frame(self.root, relief=tk.RAISED, bd=1, height=40)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Toolbar buttons
        button_configs = [
            ("New", self.cmd_new_game_click, "New Game"),
            ("End", self.cmd_end_game_click, "End Game"),
            ("Save", self.cmd_save_game_click, "Save Game"),
            ("Restore", self.cmd_restore_game_click, "Restore Game"),
            ("Stats", self.cmd_statistics_click, "Statistics"),
            ("EndTurn", self.cmd_end_turn_click, "End Turn"),
            ("Log", self.cmd_log_click, "Log"),
            ("History", self.cmd_history_click, "History"),
            ("Rules", self.cmd_rules_click, "Rules"),
            ("Map", self.cmd_map_click, "Map"),
            ("Preferences", self.cmd_preferences_click, "Preferences"),
            ("About", self.cmd_about_click, "About"),
        ]
        
        self.toolbar_buttons = {}
        for name, command, tooltip in button_configs:
            btn = tk.Button(self.toolbar, text=name, command=command, width=8)
            btn.pack(side=tk.LEFT, padx=2, pady=2)
            self.toolbar_buttons[name] = btn
            # Add tooltip
            btn.bind("<Enter>", lambda e, t=tooltip: self.show_tooltip(t))
            btn.bind("<Leave>", lambda e: self.hide_tooltip())
        
        # Disable some buttons initially
        self.toolbar_buttons["Save"].config(state=tk.DISABLED)
        self.toolbar_buttons["Restore"].config(state=tk.DISABLED)
        self.toolbar_buttons["EndTurn"].config(state=tk.DISABLED)
    
    def create_map_panel(self):
        """Create the main map display panel"""
        self.map_frame = tk.Frame(self.root, relief=tk.SUNKEN, bd=2)
        self.map_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Canvas for map display
        self.map_canvas = tk.Canvas(self.map_frame, bg='white', highlightthickness=0)
        self.map_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Map image reference
        self.map_image = None
        self.map_image_tk = None
        
        # Territory hover information
        self.hover_territory = 0
        self.from_territory = 0
        self.to_territory = 0
        
        # Bind mouse events
        self.map_canvas.bind("<Motion>", self.img_map_mouse_move)
        self.map_canvas.bind("<Button-1>", self.img_map_mouse_up)
    
    def create_status_bar(self):
        """Create the status bar"""
        self.status_frame = tk.Frame(self.root, relief=tk.SUNKEN, bd=1)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status panels
        self.status_panels = []
        for i in range(3):
            panel = tk.Label(self.status_frame, text="", relief=tk.FLAT, anchor=tk.W, bd=1)
            panel.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.status_panels.append(panel)
        
        # Set initial status
        self.status_panels[0].config(text="TurboRisk", width=20)
        self.status_panels[1].config(text="Ready", width=40)
        self.status_panels[2].config(text="", width=60)
    
    def initialize_game(self):
        """Initialize game state"""
        # Set up territories
        setup_territories()
        
        # Initialize global state
        G.bG_TRSim = False
        G.game_state = GameState.STOPPED
        G.bHumanTurn = False
        
        # Set application path
        G.sG_AppPath = os.path.dirname(os.path.abspath(__file__)) + os.sep
    
    def load_map_image(self):
        """Load the map image"""
        # Try to find a map image
        map_files = ['std_map.png', 'std_map_small.png', 'world_map.png']
        for map_file in map_files:
            map_path = os.path.join(G.sG_AppPath, 'maps', map_file)
            if os.path.exists(map_path):
                try:
                    self.map_image = Image.open(map_path)
                    self.map_image_tk = ImageTk.PhotoImage(self.map_image)
                    self.map_canvas.create_image(0, 0, anchor=tk.NW, image=self.map_image_tk)
                    self.map_canvas.config(scrollregion=(0, 0, self.map_image.width, self.map_image.height))
                    return
                except Exception as e:
                    print(f"Error loading map image: {e}")
        
        # If no map image found, create a placeholder
        self.map_canvas.create_rectangle(0, 0, 800, 600, fill='lightblue')
        self.map_canvas.create_text(400, 300, text="Map not found", fill='black')
    
    def bind_events(self):
        """Bind keyboard and other events"""
        self.root.bind("<KeyPress>", self.form_key_down)
        self.root.protocol("WM_DELETE_WINDOW", self.form_close)
    
    def show_tooltip(self, text):
        """Show a tooltip"""
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{self.root.winfo_pointerx()+10}+{self.root.winfo_pointery()+10}")
        label = tk.Label(self.tooltip, text=text, bg='yellow', relief=tk.SOLID, bd=1)
        label.pack()
    
    def hide_tooltip(self):
        """Hide the tooltip"""
        if hasattr(self, 'tooltip'):
            self.tooltip.destroy()
    
    # Menu event handlers
    def mnu_fil_new_click(self):
        """Handle New Game menu click"""
        if G.game_state != GameState.STOPPED:
            return
        
        # Show New Game dialog
        try:
            from .dialogs import PlayersDialog
            dlg = PlayersDialog(self.root)
            if dlg.show_modal():
                self.status_panels[2].config(text="Preparing new game, please wait...")
                self.root.update()
                
                # TODO: Call NewGameSetup
                self.status_panels[2].config(text="")
                
                if G.game_state != GameState.STOPPED:
                    self.supervisor()
                else:
                    self.game_cleanup()
        except ImportError:
            # Tkinter not available, show message
            self.status_panels[2].config(text="GUI not available - Tkinter required")
    
    def mnu_fil_save_click(self):
        """Handle Save Game menu click"""
        if not G.bHumanTurn:
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".trg",
            filetypes=[("TurboRisk Game", "*.trg")],
            initialdir=G.sG_AppPath,
            initialfile="my_game.trg"
        )
        if filename:
            # TODO: Call SaveGame
            self.status_panels[2].config(text="Game saved.")
    
    def mnu_fil_restore_click(self):
        """Handle Restore Game menu click"""
        filename = filedialog.askopenfilename(
            filetypes=[("TurboRisk Game", "*.trg")],
            initialdir=G.sG_AppPath
        )
        if filename:
            self.status_panels[2].config(text="Restoring game, please wait...")
            self.root.update()
            
            # TODO: Call GameCleanup and RestoreGame
            self.status_panels[2].config(text="")
            
            if G.game_state == GameState.STOPPED:
                self.game_cleanup()
                return
            
            # TODO: Call MostraIstruzioni and UpdateGridPos
            self.toolbar_buttons["Save"].config(state=tk.NORMAL)
            self.toolbar_buttons["Restore"].config(state=tk.NORMAL)
    
    def mnu_fil_end_click(self):
        """Handle End Game menu click"""
        if G.game_state == GameState.STOPPED:
            return
        
        if G.bPrefConfirmAbort:
            if messagebox.askyesno("Confirm", "Are you sure you want to quit this game?"):
                pass
            else:
                return
        
        if G.bHumanTurn:
            self.game_cleanup()
            return
        else:
            G.bStopASAP = True
    
    def mnu_fil_exit_click(self):
        """Handle Exit menu click"""
        self.root.quit()
    
    def mnu_vie_stats_click(self):
        """Handle Statistics menu click"""
        try:
            from .dialogs import StatsDialog
            if not hasattr(self, 'stats_dialog'):
                self.stats_dialog = StatsDialog(self.root)
            self.stats_dialog.show()
        except ImportError:
            self.status_panels[2].config(text="GUI not available - Tkinter required")
    
    def mnu_vie_hist_click(self):
        """Handle History menu click"""
        try:
            from .dialogs import HistoryDialog
            dlg = HistoryDialog(self.root)
            dlg.show_modal()
        except ImportError:
            self.status_panels[2].config(text="GUI not available - Tkinter required")
    
    def mnu_vie_log_click(self):
        """Handle Log menu click"""
        try:
            from .dialogs import LogDialog
            if not hasattr(self, 'log_dialog'):
                self.log_dialog = LogDialog(self.root)
            self.log_dialog.show()
        except ImportError:
            self.status_panels[2].config(text="GUI not available - Tkinter required")
    
    def mnu_opt_players_click(self):
        """Handle Players menu click"""
        try:
            from .dialogs import PlayersDialog
            dlg = PlayersDialog(self.root)
            dlg.show_modal()
        except ImportError:
            self.status_panels[2].config(text="GUI not available - Tkinter required")
    
    def mnu_opt_map_click(self):
        """Handle Map menu click"""
        try:
            from .dialogs import MapDialog
            dlg = MapDialog(self.root)
            if dlg.show_modal():
                # Map changed, reload
                self.load_map_image()
        except ImportError:
            self.status_panels[2].config(text="GUI not available - Tkinter required")
    
    def mnu_opt_rules_click(self):
        """Handle Rules menu click"""
        try:
            from .dialogs import RulesDialog
            dlg = RulesDialog(self.root)
            dlg.show_modal()
        except ImportError:
            self.status_panels[2].config(text="GUI not available - Tkinter required")
    
    def mnu_opt_pref_click(self):
        """Handle Preferences menu click"""
        try:
            from .dialogs import PrefDialog
            dlg = PrefDialog(self.root)
            dlg.show_modal()
        except ImportError:
            self.status_panels[2].config(text="GUI not available - Tkinter required")
    
    def mnu_hel_readme_click(self):
        """Handle Readme menu click"""
        try:
            import webbrowser
            webbrowser.open(os.path.join(G.sG_AppPath, 'Doc', 'TurboRisk.chm'))
        except Exception as e:
            self.status_panels[2].config(text=f"Error opening readme: {e}")
    
    def mnu_hel_about_click(self):
        """Handle About menu click"""
        try:
            from .dialogs import AboutDialog
            dlg = AboutDialog(self.root)
            dlg.show_modal()
        except ImportError:
            self.status_panels[2].config(text="GUI not available - Tkinter required")
    
    def mnu_hel_homepage_click(self):
        """Handle Homepage menu click"""
        import webbrowser
        webbrowser.open("http://www.marioferrari.org/freeware/turborisk/turborisk.html")
    
    def mnu_hel_check_updates_click(self):
        """Handle Check for Updates menu click"""
        import webbrowser
        webbrowser.open("http://groups.google.com/group/turborisk")
    
    # Toolbar button handlers
    def cmd_new_game_click(self):
        """Handle New Game button click"""
        self.mnu_fil_new_click()
    
    def cmd_end_game_click(self):
        """Handle End Game button click"""
        self.mnu_fil_end_click()
    
    def cmd_save_game_click(self):
        """Handle Save Game button click"""
        self.mnu_fil_save_click()
    
    def cmd_restore_game_click(self):
        """Handle Restore Game button click"""
        self.mnu_fil_restore_click()
    
    def cmd_statistics_click(self):
        """Handle Statistics button click"""
        self.mnu_vie_stats_click()
    
    def cmd_end_turn_click(self):
        """Handle End Turn button click"""
        if G.bHumanTurn and G.game_state == GameState.PLAYING:
            self.set_from_territory(0)
            self.set_to_territory(0)
            self.supervisor()
    
    def cmd_log_click(self):
        """Handle Log button click"""
        self.mnu_vie_log_click()
    
    def cmd_history_click(self):
        """Handle History button click"""
        self.mnu_vie_hist_click()
    
    def cmd_rules_click(self):
        """Handle Rules button click"""
        self.mnu_opt_rules_click()
    
    def cmd_map_click(self):
        """Handle Map button click"""
        self.mnu_opt_map_click()
    
    def cmd_preferences_click(self):
        """Handle Preferences button click"""
        self.mnu_opt_pref_click()
    
    def cmd_about_click(self):
        """Handle About button click"""
        self.mnu_hel_about_click()
    
    # Map event handlers
    def img_map_mouse_move(self, event):
        """Handle mouse move on map"""
        if G.game_state == GameState.STOPPED:
            return
        
        # Find territory at mouse position
        terr = find_territory(event.x, event.y)
        
        # If changed, update hover territory
        if terr != self.hover_territory:
            self.set_hover_territory(terr)
    
    def img_map_mouse_up(self, event):
        """Handle mouse click on map"""
        if not G.bHumanTurn:
            return
        
        # Find territory at mouse position
        terr = find_territory(event.x, event.y)
        
        self.toolbar_buttons["EndTurn"].config(state=tk.DISABLED)
        
        if terr > 0:
            # TODO: Handle territory click based on game state
            # This is a complex logic that needs to be ported from Main.pas
            pass
        else:
            self.set_from_territory(0)
            self.set_to_territory(0)
            self.show_instructions()
            
            if G.bHumanTurn and G.game_state == GameState.PLAYING:
                self.toolbar_buttons["EndTurn"].config(state=tk.NORMAL)
    
    def form_key_down(self, event):
        """Handle keyboard events"""
        if event.keysym == "Escape":
            self.root.iconify()
        elif event.keysym == "space":
            if G.bHumanTurn and G.game_state == GameState.PLAYING:
                self.set_from_territory(0)
                self.set_to_territory(0)
                self.supervisor()
    
    def form_close(self):
        """Handle window close"""
        self.cleanup()
        self.root.quit()
    
    # Game state helpers
    def set_hover_territory(self, terr):
        """Set the hover territory"""
        self.hover_territory = terr
        # TODO: Highlight territory on map
    
    def set_from_territory(self, terr):
        """Set the from territory"""
        self.from_territory = terr
        # TODO: Update UI
    
    def set_to_territory(self, terr):
        """Set the to territory"""
        self.to_territory = terr
        # TODO: Update UI
    
    def show_instructions(self):
        """Show game instructions in status bar"""
        # TODO: Implement based on game state
        pass
    
    def supervisor(self):
        """Run the game supervisor (main game loop)"""
        # TODO: Implement game supervisor logic
        pass
    
    def game_cleanup(self):
        """Clean up game state"""
        # TODO: Implement game cleanup
        G.game_state = GameState.STOPPED
        G.bHumanTurn = False
        self.toolbar_buttons["Save"].config(state=tk.DISABLED)
        self.toolbar_buttons["Restore"].config(state=tk.DISABLED)
        self.toolbar_buttons["EndTurn"].config(state=tk.DISABLED)
    
    def cleanup(self):
        """Clean up resources"""
        self.game_cleanup()
        if self.map_image:
            del self.map_image
        if self.map_image_tk:
            del self.map_image_tk


def run_gui():
    """Run the TurboRisk GUI application"""
    root = tk.Tk()
    app = MainGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()

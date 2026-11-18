"""
TurboRisk - Python Port
Dialog Classes

This module provides all the dialog classes for TurboRisk.
Ported from the various .pas form files.
"""

# Try to import GUI dependencies
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("Warning: Tkinter not available. GUI functionality will be limited.")

from .globals import G, MAXPLAYERS, MAXTERRITORIES
from .territory import load_map


# =============================================================================
# About Dialog
# =============================================================================

class AboutDialog:
    """About dialog showing version and credits"""
    
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
        self.dialog = None
    
    def show_modal(self):
        """Show the dialog modally"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("About TurboRisk")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="TurboRisk", font=('Arial', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Version
        self.lbl_version = ttk.Label(main_frame, text=f"Version {G.sG_AppVers}", font=('Arial', 12))
        self.lbl_version.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Credits text
        credits_text = """
Many thanks to Steve Stancliff for his WinRisk program, which I liked 
and used so much, and which inspired TurboRisk.

I want to thank all the many people who gave a contribution to make 
TurboRisk a better program.

A very special thanks to the following people for their invaluable help:

Paul R. Brown
Julio Couce
"""
        
        txt_credits = tk.Text(main_frame, wrap=tk.WORD, width=50, height=15, bd=0)
        txt_credits.insert(tk.END, credits_text)
        txt_credits.config(state=tk.DISABLED)
        txt_credits.grid(row=2, column=0, columnspan=2, pady=10)
        
        # OK button
        ttk.Button(main_frame, text="OK", command=self.on_ok).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Wait for dialog to close
        self.parent.wait_window(self.dialog)
    
    def on_ok(self):
        """Handle OK button click"""
        self.dialog.destroy()


# =============================================================================
# Log Dialog
# =============================================================================

class LogDialog:
    """Log dialog for displaying game messages"""
    
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
        self.dialog = None
        self.txt_log = None
    
    def show(self):
        """Show the dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Game Log")
        self.dialog.transient(self.parent)
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log text area
        self.txt_log = tk.Text(main_frame, wrap=tk.WORD, width=80, height=30)
        self.txt_log.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, command=self.txt_log.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_log.config(yscrollcommand=scrollbar.set)
        
        # Action log button
        self.cmd_action_log = ttk.Button(main_frame, text="Log actions...", command=self.cmd_action_log_click)
        self.cmd_action_log.pack(side=tk.BOTTOM, pady=5)
        
        # Update menu state
        if hasattr(self.parent, 'menu_bar') and hasattr(self.parent, 'toolbar_buttons'):
            # Update menu check state
            pass
    
    def hide(self):
        """Hide the dialog"""
        if self.dialog:
            self.dialog.withdraw()
    
    def is_visible(self):
        """Check if dialog is visible"""
        return self.dialog and self.dialog.winfo_viewable()
    
    def cmd_action_log_click(self):
        """Handle action log button click"""
        # TODO: Implement action logging
        messagebox.showinfo("Info", "Action logging not yet implemented")
    
    def write_log(self, message):
        """Write a message to the log"""
        if self.txt_log:
            self.txt_log.insert(tk.END, message + "\n")
            self.txt_log.see(tk.END)


# =============================================================================
# Stats Dialog
# =============================================================================

class StatsDialog:
    """Statistics dialog showing player stats"""
    
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
        self.dialog = None
        self.grid = None
        self.ready = False
    
    def show(self):
        """Show the dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Statistics")
        self.dialog.transient(self.parent)
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create grid
        self.create_grid(main_frame)
        
        # Update stats
        self.update_stats()
        
        self.ready = True
        
        # Update menu state
        if hasattr(self.parent, 'menu_bar'):
            # Update menu check state
            pass
    
    def hide(self):
        """Hide the dialog"""
        if self.dialog:
            self.dialog.withdraw()
    
    def is_visible(self):
        """Check if dialog is visible"""
        return self.dialog and self.dialog.winfo_viewable()
    
    def create_grid(self, parent):
        """Create the statistics grid"""
        # Column headers
        headers = ["Player", "Territ.", "Armies", "Continents", "Cards", "CTIV"]
        
        for col, header in enumerate(headers):
            label = ttk.Label(parent, text=header, relief=tk.RAISED, padding=5)
            label.grid(row=0, column=col, sticky=tk.NSEW)
        
        # Player rows
        for row in range(1, MAXPLAYERS + 1):
            for col in range(len(headers)):
                cell = ttk.Label(parent, text="-", relief=tk.SUNKEN, padding=5, width=10, anchor=tk.CENTER)
                cell.grid(row=row, column=col, sticky=tk.NSEW)
        
        # Configure grid weights
        for col in range(len(headers)):
            parent.columnconfigure(col, weight=1)
        for row in range(MAXPLAYERS + 1):
            parent.rowconfigure(row, weight=1)
    
    def update_stats(self):
        """Update statistics display"""
        if not self.ready or not self.dialog:
            return
        
        # TODO: Implement actual stats update
        # This would iterate through players and update the grid
        pass


# =============================================================================
# History Dialog
# =============================================================================

class HistoryDialog:
    """History dialog showing game history and ranking"""
    
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
        self.dialog = None
    
    def show_modal(self):
        """Show the dialog modally"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Game History")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook (tabs)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # History tab
        history_tab = ttk.Frame(notebook)
        notebook.add(history_tab, text="History")
        
        # Create list view for history
        self.lst_history = tk.Frame(history_tab)
        self.lst_history.pack(fill=tk.BOTH, expand=True)
        
        # Add columns
        columns = ["Date", "Players", "Winner", "Duration"]
        for col, header in enumerate(columns):
            label = ttk.Label(self.lst_history, text=header, relief=tk.RAISED, padding=5)
            label.grid(row=0, column=col, sticky=tk.NSEW)
        
        # Ranking tab
        ranking_tab = ttk.Frame(notebook)
        notebook.add(ranking_tab, text="Ranking")
        
        # Create ranking grid
        self.grd_ranking = tk.Frame(ranking_tab)
        self.grd_ranking.pack(fill=tk.BOTH, expand=True)
        
        ranking_headers = ["Rank", "Player", "Games", "Won", "Points"]
        for col, header in enumerate(ranking_headers):
            label = ttk.Label(self.grd_ranking, text=header, relief=tk.RAISED, padding=5)
            label.grid(row=0, column=col, sticky=tk.NSEW)
        
        # OK button
        ttk.Button(main_frame, text="OK", command=self.on_ok).pack(pady=10)
        
        # Wait for dialog to close
        self.parent.wait_window(self.dialog)
    
    def on_ok(self):
        """Handle OK button click"""
        self.dialog.destroy()
    
    def load_history_file(self, filename):
        """Load history from a file"""
        # TODO: Implement history file loading
        pass


# =============================================================================
# Players Dialog
# =============================================================================

class PlayersDialog:
    """Players setup dialog"""
    
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
        self.dialog = None
        self.result = False
    
    def show_modal(self):
        """Show the dialog modally and return True if OK was clicked"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Players Setup")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Player type
        ttk.Label(main_frame, text="Player Type:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.player_type = tk.StringVar(value="Human")
        human_rb = ttk.Radiobutton(main_frame, text="Human", variable=self.player_type, value="Human", command=self.on_type_click)
        computer_rb = ttk.Radiobutton(main_frame, text="Computer", variable=self.player_type, value="Computer", command=self.on_type_click)
        human_rb.grid(row=1, column=0, sticky=tk.W)
        computer_rb.grid(row=2, column=0, sticky=tk.W)
        
        # Name or Program
        ttk.Label(main_frame, text="Name:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.txt_name = ttk.Entry(main_frame, width=30)
        self.txt_name.grid(row=4, column=0, sticky=tk.W)
        
        # Program file (hidden by default)
        self.cbo_prg_file = ttk.Entry(main_frame, width=30)
        self.cbo_prg_file.grid(row=4, column=0, sticky=tk.W)
        self.cbo_prg_file.grid_remove()  # Hide initially
        
        # Color
        ttk.Label(main_frame, text="Color:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.cbo_color = ttk.Combobox(main_frame, width=20)
        self.cbo_color['values'] = ['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Orange', 'Black', 'White']
        self.cbo_color.grid(row=6, column=0, sticky=tk.W)
        self.cbo_color.set('Red')
        
        # Cards option
        self.chk_log = tk.BooleanVar()
        self.chk_log_check = ttk.Checkbutton(main_frame, text="Keep Log", variable=self.chk_log)
        self.chk_log_check.grid(row=7, column=0, sticky=tk.W, pady=5)
        
        # OK/Cancel buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=10, column=0, pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Wait for dialog to close
        self.parent.wait_window(self.dialog)
        
        return self.result
    
    def on_type_click(self):
        """Handle player type selection change"""
        if self.player_type.get() == "Human":
            self.txt_name.grid()
            self.cbo_prg_file.grid_remove()
        else:
            self.txt_name.grid_remove()
            self.cbo_prg_file.grid()
    
    def on_ok(self):
        """Handle OK button click"""
        if self.player_type.get() == "Computer" and not self.cbo_prg_file.get():
            messagebox.showerror("Error", "Specify a program.")
            return
        
        self.result = True
        self.dialog.destroy()
    
    def on_cancel(self):
        """Handle Cancel button click"""
        self.result = False
        self.dialog.destroy()


# =============================================================================
# Preferences Dialog
# =============================================================================

class PrefDialog:
    """Preferences dialog"""
    
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
        self.dialog = None
        self.result = False
    
    def show_modal(self):
        """Show the dialog modally and return True if OK was clicked"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Preferences")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook (tabs)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar tab
        toolbar_tab = ttk.Frame(notebook)
        notebook.add(toolbar_tab, text="Toolbar")
        
        # Map tab
        map_tab = ttk.Frame(notebook)
        notebook.add(map_tab, text="Map")
        
        # Game tab
        game_tab = ttk.Frame(notebook)
        notebook.add(game_tab, text="Game")
        
        # Toolbar settings
        self.chk_show_toolbar = tk.BooleanVar(value=True)
        ttk.Checkbutton(toolbar_tab, text="Show Toolbar", variable=self.chk_show_toolbar).pack(anchor=tk.W, pady=5)
        
        # Map settings
        self.chk_map_hover = tk.BooleanVar(value=True)
        ttk.Checkbutton(map_tab, text="Show Territory on Hover", variable=self.chk_map_hover).pack(anchor=tk.W, pady=5)
        
        self.chk_map_selected = tk.BooleanVar(value=True)
        ttk.Checkbutton(map_tab, text="Highlight Selected Territory", variable=self.chk_map_selected).pack(anchor=tk.W, pady=5)
        
        # Game settings
        self.chk_confirm_abort = tk.BooleanVar(value=True)
        ttk.Checkbutton(game_tab, text="Confirm Game Abort", variable=self.chk_confirm_abort).pack(anchor=tk.W, pady=5)
        
        self.chk_expert_attack = tk.BooleanVar(value=False)
        ttk.Checkbutton(game_tab, text="Expert Attack Mode", variable=self.chk_expert_attack).pack(anchor=tk.W, pady=5)
        
        # OK/Cancel buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset Rules", command=self.on_reset_rules).pack(side=tk.LEFT, padx=5)
        
        # Wait for dialog to close
        self.parent.wait_window(self.dialog)
        
        return self.result
    
    def on_ok(self):
        """Handle OK button click"""
        # Save preferences
        G.bPrefShowToolbar = self.chk_show_toolbar.get()
        G.bPrefMapHoover = self.chk_map_hover.get()
        G.bPrefMapSelected = self.chk_map_selected.get()
        G.bPrefConfirmAbort = self.chk_confirm_abort.get()
        G.bPrefExpertAttack = self.chk_expert_attack.get()
        
        self.result = True
        self.dialog.destroy()
    
    def on_cancel(self):
        """Handle Cancel button click"""
        self.result = False
        self.dialog.destroy()
    
    def on_reset_rules(self):
        """Handle Reset Rules button click"""
        # TODO: Implement rules reset
        messagebox.showinfo("Info", "Rules reset not yet implemented")


# =============================================================================
# Rules Dialog
# =============================================================================

class RulesDialog:
    """Rules setup dialog"""
    
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
        self.dialog = None
        self.result = False
    
    def show_modal(self):
        """Show the dialog modally and return True if OK was clicked"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Game Rules")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook (tabs)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Rules tab
        rules_tab = ttk.Frame(notebook)
        notebook.add(rules_tab, text="Rules")
        
        # Assignment type
        ttk.Label(rules_tab, text="Assignment Type:").pack(anchor=tk.W, pady=5)
        self.opt_assignment = tk.StringVar(value="Random")
        ttk.Radiobutton(rules_tab, text="Random", variable=self.opt_assignment, value="Random").pack(anchor=tk.W)
        ttk.Radiobutton(rules_tab, text="Manual", variable=self.opt_assignment, value="Manual").pack(anchor=tk.W)
        
        # Cards tab
        cards_tab = ttk.Frame(notebook)
        notebook.add(cards_tab, text="Cards")
        
        ttk.Label(cards_tab, text="Card Usage:").pack(anchor=tk.W, pady=5)
        self.opt_cards = tk.StringVar(value="Constant")
        ttk.Radiobutton(cards_tab, text="Constant", variable=self.opt_cards, value="Constant").pack(anchor=tk.W)
        ttk.Radiobutton(cards_tab, text="Progressive", variable=self.opt_cards, value="Progressive").pack(anchor=tk.W)
        
        # Move tab
        move_tab = ttk.Frame(notebook)
        notebook.add(move_tab, text="Move")
        
        self.chk_final_move = tk.BooleanVar(value=True)
        ttk.Checkbutton(move_tab, text="Final Move", variable=self.chk_final_move).pack(anchor=tk.W, pady=5)
        
        # OK/Cancel buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset Rules", command=self.on_reset_rules).pack(side=tk.LEFT, padx=5)
        
        # Wait for dialog to close
        self.parent.wait_window(self.dialog)
        
        return self.result
    
    def on_ok(self):
        """Handle OK button click"""
        # Save rules
        # TODO: Update global rules variables
        self.result = True
        self.dialog.destroy()
    
    def on_cancel(self):
        """Handle Cancel button click"""
        self.result = False
        self.dialog.destroy()
    
    def on_reset_rules(self):
        """Handle Reset Rules button click"""
        # TODO: Implement rules reset
        messagebox.showinfo("Info", "Rules reset not yet implemented")


# =============================================================================
# Map Dialog
# =============================================================================

class MapDialog:
    """Map selection dialog"""
    
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
        self.dialog = None
        self.result = False
        self.loading = False
    
    def show_modal(self):
        """Show the dialog modally and return True if OK was clicked"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Select Map")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Map list
        ttk.Label(main_frame, text="Available Maps:").pack(anchor=tk.W, pady=5)
        
        self.lst_map = tk.Frame(main_frame)
        self.lst_map.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Map preview
        self.map_preview = ttk.LabelFrame(main_frame, text="Map Preview")
        self.map_preview.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.img_preview = ttk.Label(self.map_preview, text="Preview not available")
        self.img_preview.pack(fill=tk.BOTH, expand=True)
        
        # Map info
        ttk.Label(main_frame, text="Map Size:").pack(anchor=tk.W, pady=5)
        self.txt_map_size = ttk.Entry(main_frame, width=20)
        self.txt_map_size.pack(anchor=tk.W)
        
        ttk.Label(main_frame, text="Author:").pack(anchor=tk.W, pady=5)
        self.txt_map_author = ttk.Entry(main_frame, width=20)
        self.txt_map_author.pack(anchor=tk.W)
        
        ttk.Label(main_frame, text="Revision:").pack(anchor=tk.W, pady=5)
        self.txt_map_revision = ttk.Entry(main_frame, width=20)
        self.txt_map_revision.pack(anchor=tk.W)
        
        # OK/Cancel buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Load map list
        self.form_show()
        
        # Wait for dialog to close
        self.parent.wait_window(self.dialog)
        
        return self.result
    
    def form_show(self):
        """Load the list of available maps"""
        self.loading = True
        
        # Clear list
        for widget in self.lst_map.winfo_children():
            widget.destroy()
        
        # Try to find .trm files in maps directory
        maps_dir = os.path.join(G.sG_AppPath, 'maps')
        if os.path.exists(maps_dir):
            try:
                import glob
                map_files = glob.glob(os.path.join(maps_dir, '*.trm'))
                
                for i, map_file in enumerate(map_files):
                    map_name = os.path.basename(map_file)
                    btn = ttk.Radiobutton(self.lst_map, text=map_name, value=map_file)
                    btn.pack(anchor=tk.W)
                    if map_name == G.sMapFile:
                        btn.select()
            except Exception as e:
                print(f"Error loading maps: {e}")
        
        self.loading = False
    
    def on_ok(self):
        """Handle OK button click"""
        # Get selected map
        for widget in self.lst_map.winfo_children():
            if isinstance(widget, ttk.Radiobutton) and widget.instate(['selected']):
                map_file = widget.cget('value')
                G.sMapFile = os.path.basename(map_file)
                load_map()
                break
        
        self.result = True
        self.dialog.destroy()
    
    def on_cancel(self):
        """Handle Cancel button click"""
        self.result = False
        self.dialog.destroy()


# =============================================================================
# Utility function to write to log
# =============================================================================

def scrivi_log(message):
    """Write a message to the log (compatibility function)"""
    # This would be called from the game logic
    # In the GUI, we need to update the log dialog if it's visible
    pass


# =============================================================================
# Export all dialog classes
# =============================================================================

__all__ = [
    'AboutDialog',
    'LogDialog',
    'StatsDialog',
    'HistoryDialog',
    'PlayersDialog',
    'PrefDialog',
    'RulesDialog',
    'MapDialog',
    'scrivi_log',
]

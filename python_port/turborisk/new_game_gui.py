"""
TurboRisk - Python Port
New Game Dialog

This module provides the New Game dialog for TurboRisk.
Ported from NewGame.pas and NewGame.lfm
"""

# Try to import GUI dependencies
try:
    import tkinter as tk
    from tkinter import ttk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("Warning: Tkinter not available. GUI functionality will be limited.")

from .globals import G


class NewGameDialog:
    """Dialog for starting a new game"""
    
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        
        self.parent = parent
        self.result = False
        self.dialog = None
    
    def show(self):
        """Show the dialog and return True if OK was clicked"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("New Game")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Create main frame
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Game settings
        ttk.Label(main_frame, text="Game Settings").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Number of players
        ttk.Label(main_frame, text="Number of Players:").grid(row=1, column=0, sticky=tk.W)
        self.num_players = ttk.Spinbox(main_frame, from_=2, to=6, width=5)
        self.num_players.grid(row=1, column=1, sticky=tk.W)
        self.num_players.set(4)
        
        # OK/Cancel buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=10, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Wait for dialog to close
        self.parent.wait_window(self.dialog)
        
        return self.result
    
    def on_ok(self):
        """Handle OK button click"""
        # Save settings
        num_players = int(self.num_players.get())
        G.n_players = num_players
        
        # Activate the selected number of players
        for i in range(1, 11):
            G.ar_player[i].active = (i <= num_players)
        
        self.result = True
        self.dialog.destroy()
    
    def on_cancel(self):
        """Handle Cancel button click"""
        self.result = False
        self.dialog.destroy()


# Stub functions for forms that haven't been ported yet
class StatsDialog:
    """Statistics dialog"""
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
    
    def show(self):
        """Show the dialog"""
        pass


class HistoryDialog:
    """History dialog"""
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
    
    def show_modal(self):
        """Show the dialog modally"""
        pass


class LogDialog:
    """Log dialog"""
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
    
    def show(self):
        """Show the dialog"""
        pass


class PlayersDialog:
    """Players dialog"""
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
    
    def show_modal(self):
        """Show the dialog modally"""
        pass


class MapDialog:
    """Map dialog"""
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
    
    def show_modal(self):
        """Show the dialog modally"""
        pass


class RulesDialog:
    """Rules dialog"""
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
    
    def show_modal(self):
        """Show the dialog modally"""
        pass


class PrefDialog:
    """Preferences dialog"""
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
    
    def show_modal(self):
        """Show the dialog modally"""
        pass


class AboutDialog:
    """About dialog"""
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
    
    def show_modal(self):
        """Show the dialog modally"""
        pass

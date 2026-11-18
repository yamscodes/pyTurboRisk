"""
TurboRisk - Python Port
Human Player Logic

This module handles human player logic and related dialogs.
Ported from Human.pas, Attack.pas, and Move.pas
"""

# Try to import GUI dependencies
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("Warning: Tkinter not available. GUI functionality will be limited.")

from typing import Optional, Tuple

try:
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("Warning: Tkinter not available. GUI functionality will be limited.")

from .globals import (
    G, MAXPLAYERS, MAXTERRITORIES, GameState, HumanPhase, AssignmentType,
    CardsHandling, ContinentID, CardType
)
from .territory import is_adjacent, transfer_armies
from .exp_subr import t_name, t_owner, t_armies, t_continent
from .game_logic import set_from_territory, set_to_territory, get_from_territory, get_to_territory, attack_phase
from .cards import draw_card


# =============================================================================
# Human Player Logic
# =============================================================================

def show_instructions():
    """
    Show instructions to the human player.
    Ported from MostraIstruzioni in Human.pas
    """
    msg = ""
    
    if G.game_state == GameState.ASSIGNING:
        msg = "Please claim a territory."
    elif G.game_state == GameState.DISTRIBUTING:
        if G.ar_player[G.i_turn].new_army > 1:
            msg = f"You have {G.ar_player[G.i_turn].new_army} armies left to place. Please place an army."
        else:
            msg = "You have 1 army left to place. Please place it."
    elif G.game_state == GameState.PLAYING and G.human_phase == HumanPhase.PLACEMENT:
        if G.ar_player[G.i_turn].new_army > 1:
            msg = (f"You have {G.ar_player[G.i_turn].new_army} armies left to place "
                   "(click=1, +shift=5, +ctrl+shift=10, +alt+ctrl+shift=25)")
        else:
            msg = "You have 1 army left to place."
    else:
        if get_from_territory() == 0:
            msg = "Please choose a territory to attack or move from (click) or pass (spacebar)"
        else:
            from_terr = get_from_territory()
            msg = f"From {t_name(from_terr)}. Please choose a territory to attack or move to."
    
    # Update status bar if GUI is available
    if hasattr(G, 'main_gui') and G.main_gui:
        G.main_gui.status_panels[2].config(text=msg)
    
    return msg


def human_attack(from_terr: int, to_terr: int, attack_type: str = "once") -> bool:
    """
    Handle human attack.
    Ported from UomoAttacca in Human.pas
    
    Args:
        from_terr: Territory attacking from
        to_terr: Territory being attacked
        attack_type: Type of attack ("once", "do_or_die", "until1", "until2")
    
    Returns: True if attack was successful (territory conquered)
    """
    # Show attack dialog
    attack_dlg = AttackDialog(G.main_gui.root if hasattr(G, 'main_gui') and G.main_gui else None)
    attack_dlg.iTf = from_terr
    attack_dlg.iTt = to_terr
    attack_dlg.attack_type = attack_type
    
    if attack_dlg.show_modal():
        # Perform the attack
        conquest, msg = attack_phase(from_terr, to_terr, attack_dlg.attack_type)
        
        # Update status
        if hasattr(G, 'main_gui') and G.main_gui:
            G.main_gui.status_panels[2].config(text=msg)
        
        # Check if territory was conquered
        if conquest:
            # Move troops into the conquered territory if auto-move is enabled
            if attack_dlg.chk_auto_move.get() and G.ar_territory[from_terr].army > 1:
                human_move(from_terr, to_terr, False)
            
            # Check if all opponents have been eliminated
            if G.b_eliminated_player:
                # Draw a card if in playing state
                if G.game_state == GameState.PLAYING and G.ar_player[G.i_turn].fl_conq:
                    draw_card()
                
                # Check if game is over
                if G.i_n_players < 2:
                    G.b_human_turn = False
            
            return True
        
        return False
    
    return False


def human_move(from_terr: int, to_terr: int, b_move: bool) -> bool:
    """
    Handle human troop movement.
    Ported from UomoSposta in Human.pas
    
    Args:
        from_terr: Territory to move from
        to_terr: Territory to move to
        b_move: True if this is a fortification move, False if occupation
    
    Returns: True if move was successful
    """
    # Show move dialog
    move_dlg = MoveDialog(G.main_gui.root if hasattr(G, 'main_gui') and G.main_gui else None)
    move_dlg.iTf = from_terr
    move_dlg.iTt = to_terr
    move_dlg.iProv = G.ar_territory[from_terr].army
    move_dlg.iDest = G.ar_territory[to_terr].army
    move_dlg.iMinDest = move_dlg.iDest
    
    if move_dlg.show_modal():
        # Move was successful
        armies_to_move = move_dlg.iProv - G.ar_territory[from_terr].army
        
        if b_move:
            # Fortification move
            G.ar_player[G.i_turn].fl_move = True
            # Record action: AK_FORTIFICATION
        else:
            # Occupation move
            # Record action: AK_OCCUPATION
            pass
        
        return True
    else:
        # Move was cancelled
        set_from_territory(0)
        set_to_territory(0)
        show_instructions()
        return False


# =============================================================================
# Attack Dialog
# =============================================================================

class AttackDialog:
    """Dialog for handling attacks"""
    
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
        self.dialog = None
        self.result = False
        self.iTf = 0  # From territory
        self.iTt = 0  # To territory
        self.attack_type = "once"  # Default attack type
    
    def show_modal(self) -> bool:
        """Show the dialog modally and return True if attack was successful"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Attack")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # From territory info
        ttk.Label(main_frame, text="From:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.pan_from_terr = ttk.Label(main_frame, text=t_name(self.iTf), font=('Arial', 10, 'bold'))
        self.pan_from_terr.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Armies:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.pan_from_armies = ttk.Label(main_frame, text=str(G.ar_territory[self.iTf].army))
        self.pan_from_armies.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # To territory info
        ttk.Label(main_frame, text="To:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.pan_to_terr = ttk.Label(main_frame, text=t_name(self.iTt), font=('Arial', 10, 'bold'))
        self.pan_to_terr.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Armies:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.pan_to_armies = ttk.Label(main_frame, text=str(G.ar_territory[self.iTt].army))
        self.pan_to_armies.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Attack options
        ttk.Label(main_frame, text="Attack Options:").grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # Attack buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=5)
        
        ttk.Button(button_frame, text="Attack Once", command=lambda: self.set_attack_type("once")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Attack Until Win or 1", command=lambda: self.set_attack_type("until1")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Do or Die", command=lambda: self.set_attack_type("do_or_die")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Retreat", command=self.cmd_retreat_click).pack(side=tk.LEFT, padx=5)
        
        # Auto move all checkbox
        self.chk_auto_move = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Auto move all troops after conquest", variable=self.chk_auto_move).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # OK/Cancel buttons
        button_frame2 = ttk.Frame(main_frame)
        button_frame2.grid(row=7, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame2, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame2, text="Cancel", command=self.on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Wait for dialog to close
        self.parent.wait_window(self.dialog)
        
        return self.result
    
    def set_attack_type(self, attack_type: str):
        """Set the attack type and close dialog with success"""
        self.attack_type = attack_type
        self.result = True
        self.dialog.destroy()
    
    def cmd_retreat_click(self):
        """Handle Retreat button"""
        self.result = False
        self.dialog.destroy()
    
    def on_ok(self):
        """Handle OK button"""
        self.result = True
        self.dialog.destroy()
    
    def on_cancel(self):
        """Handle Cancel button"""
        self.result = False
        self.dialog.destroy()


# =============================================================================
# Move Dialog
# =============================================================================

class MoveDialog:
    """Dialog for moving armies between territories"""
    
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
        self.dialog = None
        self.result = False
        self.iTf = 0  # From territory
        self.iTt = 0  # To territory
        self.iProv = 0  # Armies available
        self.iDest = 0  # Armies at destination
        self.iMinDest = 0  # Minimum armies at destination
    
    def show_modal(self) -> bool:
        """Show the dialog modally and return True if move was successful"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Move Armies")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # From territory info
        ttk.Label(main_frame, text="From:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.pan_from_terr = ttk.Label(main_frame, text=t_name(self.iTf), font=('Arial', 10, 'bold'))
        self.pan_from_terr.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Armies:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.pan_from_armies = ttk.Label(main_frame, text=str(self.iProv))
        self.pan_from_armies.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # To territory info
        ttk.Label(main_frame, text="To:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.pan_to_terr = ttk.Label(main_frame, text=t_name(self.iTt), font=('Arial', 10, 'bold'))
        self.pan_to_terr.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Armies:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.pan_to_armies = ttk.Label(main_frame, text=str(self.iDest))
        self.pan_to_armies.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Move buttons
        ttk.Label(main_frame, text="Move:").grid(row=4, column=0, sticky=tk.W, pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=5)
        
        move_counts = [1, 5, 10, 25, -1, -5, -10, -25]
        for count in move_counts:
            btn = ttk.Button(button_frame, text=str(abs(count)), 
                           command=lambda c=count: self.move_armies(c))
            btn.pack(side=tk.LEFT, padx=2)
        
        # All and Balance buttons
        ttk.Button(button_frame, text="All", command=self.cmd_all_click).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Balance", command=self.cmd_balance_click).pack(side=tk.LEFT, padx=5)
        
        # OK/Cancel buttons
        button_frame2 = ttk.Frame(main_frame)
        button_frame2.grid(row=6, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame2, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame2, text="Cancel", command=self.on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Update display
        self.update_display()
        
        # Wait for dialog to close
        self.parent.wait_window(self.dialog)
        
        return self.result
    
    def move_armies(self, count: int):
        """Move armies by the specified count"""
        if count > 0:
            # Move from iProv to iDest
            move_count = min(count, self.iProv - 1)  # Leave at least 1
            move_count = min(move_count, self.iDest - self.iMinDest + count if count < 0 else count)
            self.iProv -= move_count
            self.iDest += move_count
        else:
            # Move from iDest to iProv (negative count)
            move_count = min(abs(count), self.iDest - self.iMinDest)
            self.iProv += move_count
            self.iDest -= move_count
        
        self.update_display()
    
    def cmd_all_click(self):
        """Move all possible armies"""
        move_count = self.iProv - 1  # Leave at least 1
        move_count = min(move_count, self.iDest - self.iMinDest + move_count)
        self.iProv -= move_count
        self.iDest += move_count
        self.update_display()
    
    def cmd_balance_click(self):
        """Balance armies between territories"""
        total = self.iProv + self.iDest
        self.iProv = total // 2
        self.iDest = total - self.iProv
        # Ensure at least 1 in source
        if self.iProv < 1:
            self.iProv = 1
            self.iDest = total - 1
        # Ensure at least min in destination
        if self.iDest < self.iMinDest:
            self.iDest = self.iMinDest
            self.iProv = total - self.iMinDest
        self.update_display()
    
    def update_display(self):
        """Update the display"""
        self.pan_from_armies.config(text=str(self.iProv))
        self.pan_to_armies.config(text=str(self.iDest))
    
    def on_ok(self):
        """Handle OK button"""
        # Update actual territory armies
        G.ar_territory[self.iTf].army = self.iProv
        G.ar_territory[self.iTt].army = self.iDest
        
        self.result = True
        self.dialog.destroy()
    
    def on_cancel(self):
        """Handle Cancel button"""
        self.result = False
        self.dialog.destroy()


# =============================================================================
# Export all functions and classes
# =============================================================================

__all__ = [
    'show_instructions',
    'human_attack',
    'human_move',
    'AttackDialog',
    'MoveDialog',
]

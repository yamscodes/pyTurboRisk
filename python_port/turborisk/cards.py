"""
TurboRisk - Python Port
Card Logic Module

This module handles card drawing, trading, and management.
Ported from Cards.pas
"""

import random
from typing import Optional, List, Tuple

try:
    import tkinter as tk
    from tkinter import ttk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("Warning: Tkinter not available. GUI functionality will be limited.")

from .globals import (
    G, MAXPLAYERS, CardType, CardsHandling, CardsSet, CardValueType
)
from .exp_subr import t_name


# =============================================================================
# Card Constants
# =============================================================================

# Card types
CA_INF = 1  # Infantry
CA_CAV = 2  # Cavalry
CA_ART = 3  # Artillery
CA_JOK = 4  # Joker

# Cards set types
CS_DIF = 1  # Different (one of each)
CS_INF = 2  # All Infantry
CS_CAV = 3  # All Cavalry
CS_ART = 4  # All Artillery


# =============================================================================
# Card Functions
# =============================================================================

def draw_card():
    """
    Assign a new card to the current player.
    Ported from PescaCarta in Cards.pas
    """
    # Randomly select a card type
    # Distribution: 14 Infantry, 14 Artillery, 14 Cavalry, 2 Joker = 44 total
    rand_val = random.randint(1, 44)
    
    if 1 <= rand_val <= 14:
        card_type = CA_INF  # Infantry
    elif 15 <= rand_val <= 28:
        card_type = CA_ART  # Artillery
    elif 29 <= rand_val <= 42:
        card_type = CA_CAV  # Cavalry
    else:  # 43-44
        card_type = CA_JOK  # Joker
    
    # Add card to current player
    G.ar_player[G.i_turn].cards[card_type] += 1
    
    # Log the card draw
    card_names = {
        CA_INF: "Infantry",
        CA_CAV: "Cavalry", 
        CA_ART: "Artillery",
        CA_JOK: "Joker"
    }
    print(f"Player {G.i_turn} drew a {card_names.get(card_type, 'Unknown')} card")


def test_combination(inf: int, cav: int, art: int, jok: int) -> int:
    """
    Check the validity and value of a card combination.
    Ported from TestCombinazione in Cards.pas
    
    Args:
        inf: Number of Infantry cards
        cav: Number of Cavalry cards
        art: Number of Artillery cards
        jok: Number of Joker cards
    
    Returns:
        Number of armies awarded, or -1 if invalid, or 0 if not a valid combination
    """
    # Check if exactly 3 cards
    if inf + cav + art + jok != 3:
        return -1
    
    current_player = G.ar_player[G.i_turn]
    
    # Check if the combination is possible (player has enough cards)
    if (inf > current_player.cards[CA_INF] or
        cav > current_player.cards[CA_CAV] or
        art > current_player.cards[CA_ART] or
        jok > current_player.cards[CA_JOK]):
        return -1
    
    # Check combination types
    # Different cards (one of each type, with joker substituting)
    if ((inf == 1 and cav == 1 and art == 1) or
        (inf == 1 and cav == 1 and jok == 1) or
        (inf == 1 and jok == 1 and art == 1) or
        (jok == 1 and cav == 1 and art == 1) or
        (inf == 1 and jok == 2) or
        (cav == 1 and jok == 2) or
        (art == 1 and jok == 2) or
        (jok == 3)):
        result = G.r_set_value[CS_DIF]
    elif inf == 3 or (inf == 2 and jok == 1):
        result = G.r_set_value[CS_INF]
    elif cav == 3 or (cav == 2 and jok == 1):
        result = G.r_set_value[CS_CAV]
    elif art == 3 or (art == 2 and jok == 1):
        result = G.r_set_value[CS_ART]
    else:
        result = 0
    
    # Apply progressive value if enabled
    if result > 0 and G.r_cards_value_type == CardValueType.PROGRESSIVE:
        if current_player.n_scambi < 8:
            result = G.r_trade_value[current_player.n_scambi + 1]
        else:
            result = G.r_trade_value[8] + (current_player.n_scambi - 7) * G.r_value_inc
    
    return result


def find_best_combination() -> Optional[Tuple[int, int, int, int]]:
    """
    Evaluate the best combination for the current player.
    Ported from CercaCombinazioneMigliore in Cards.pas
    
    Returns:
        Tuple of (inf, cav, art, jok) for the best combination, or None if no valid combination
    """
    max_benefit = 0
    best_combo = (0, 0, 0, 0)
    
    # Try all possible combinations
    combinations = [
        (1, 1, 1, 0), (1, 1, 0, 1), (1, 0, 1, 1), (0, 1, 1, 1),
        (1, 0, 0, 2), (0, 1, 0, 2), (0, 0, 1, 2), (0, 0, 0, 3),
        (3, 0, 0, 0), (0, 3, 0, 0), (0, 0, 3, 0),
        (2, 0, 0, 1), (0, 2, 0, 1), (0, 0, 2, 1)
    ]
    
    for combo in combinations:
        benefit = test_combination(*combo)
        if benefit > max_benefit:
            max_benefit = benefit
            best_combo = combo
    
    if max_benefit > 0:
        return best_combo
    else:
        return None


def trade_cards(inf: int, cav: int, art: int, jok: int) -> int:
    """
    Trade in a set of cards for armies.
    
    Args:
        inf: Number of Infantry cards to trade
        cav: Number of Cavalry cards to trade
        art: Number of Artillery cards to trade
        jok: Number of Joker cards to trade
    
    Returns:
        Number of armies awarded
    """
    # Check if combination is valid
    benefit = test_combination(inf, cav, art, jok)
    
    if benefit <= 0:
        return 0
    
    # Deduct cards from player
    current_player = G.ar_player[G.i_turn]
    current_player.cards[CA_INF] -= inf
    current_player.cards[CA_CAV] -= cav
    current_player.cards[CA_ART] -= art
    current_player.cards[CA_JOK] -= jok
    
    # Add armies
    current_player.new_army += benefit
    current_player.n_scambi += 1
    
    return benefit


def can_trade_cards() -> bool:
    """
    Check if the current player can trade cards.
    """
    return find_best_combination() is not None


def get_card_count(card_type: int) -> int:
    """
    Get the number of cards of a specific type for the current player.
    """
    return G.ar_player[G.i_turn].cards.get(card_type, 0)


def get_total_cards() -> int:
    """
    Get the total number of cards for the current player.
    """
    current_player = G.ar_player[G.i_turn]
    return sum(current_player.cards.values())


# =============================================================================
# Cards Dialog
# =============================================================================

class CardsDialog:
    """Dialog for trading cards"""
    
    def __init__(self, parent):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run the GUI.")
        self.parent = parent
        self.dialog = None
        self.result = False
        self.ready = False
        self.i_p_benefit = 0
        self.i_p_inf = 0
        self.i_p_cav = 0
        self.i_p_art = 0
        self.i_p_jok = 0
    
    def show_modal(self) -> bool:
        """Show the dialog modally and return True if trade was successful"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Trade Cards")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Card list (checklist)
        ttk.Label(main_frame, text="Select cards to trade:").pack(anchor=tk.W, pady=5)
        
        self.card_vars = []
        self.card_checks = []
        
        # Create checkboxes for each card
        card_types = [
            (CA_INF, "Infantry"),
            (CA_CAV, "Cavalry"),
            (CA_ART, "Artillery"),
            (CA_JOK, "Joker")
        ]
        
        current_player = G.ar_player[G.i_turn]
        
        for card_type, card_name in card_types:
            count = current_player.cards.get(card_type, 0)
            for i in range(count):
                var = tk.BooleanVar()
                cb = ttk.Checkbutton(main_frame, text=card_name, variable=var)
                cb.pack(anchor=tk.W)
                self.card_vars.append(var)
                self.card_checks.append((card_type, cb, var))
        
        # Armies to receive
        self.pan_armies = ttk.Label(main_frame, text="")
        self.pan_armies.pack(pady=10)
        
        # Trade/Hold buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        self.cmd_trade = ttk.Button(button_frame, text="Trade", command=self.cmd_trade_click, state=tk.DISABLED)
        self.cmd_trade.pack(side=tk.LEFT, padx=5)
        
        self.cmd_hold = ttk.Button(button_frame, text="Hold", command=self.cmd_hold_click)
        self.cmd_hold.pack(side=tk.LEFT, padx=5)
        
        self.cmd_cancel = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        self.cmd_cancel.pack(side=tk.LEFT, padx=5)
        
        # Prepare form
        self.prepare_form()
        self.ready = True
        
        # Wait for dialog to close
        self.parent.wait_window(self.dialog)
        
        return self.result
    
    def prepare_form(self):
        """Prepare the form with player's cards"""
        self.ready = False
        
        # Clear existing checkboxes
        for cb in self.card_checks:
            cb[1].pack_forget()
        self.card_checks = []
        self.card_vars = []
        
        # Create checkboxes for each card
        card_types = [
            (CA_INF, "Infantry"),
            (CA_CAV, "Cavalry"),
            (CA_ART, "Artillery"),
            (CA_JOK, "Joker")
        ]
        
        current_player = G.ar_player[G.i_turn]
        
        for card_type, card_name in card_types:
            count = current_player.cards.get(card_type, 0)
            for i in range(count):
                var = tk.BooleanVar()
                cb = ttk.Checkbutton(self.pan_armies.master, text=card_name, variable=var,
                                    command=self.lst_cards_click_check)
                cb.pack(anchor=tk.W)
                self.card_checks.append((card_type, cb, var))
                self.card_vars.append(var)
        
        # Check if can hold (not too many cards)
        total_cards = get_total_cards()
        self.cmd_hold.config(state=tk.NORMAL if total_cards <= G.r_max_held_cards else tk.DISABLED)
        
        self.ready = True
        self.lst_cards_click_check()
    
    def lst_cards_click_check(self):
        """Handle card selection change"""
        if not self.ready:
            return
        
        # Count selected cards
        self.i_p_inf = 0
        self.i_p_cav = 0
        self.i_p_art = 0
        self.i_p_jok = 0
        
        for card_type, cb, var in self.card_checks:
            if var.get():
                if card_type == CA_INF:
                    self.i_p_inf += 1
                elif card_type == CA_CAV:
                    self.i_p_cav += 1
                elif card_type == CA_ART:
                    self.i_p_art += 1
                elif card_type == CA_JOK:
                    self.i_p_jok += 1
        
        # Test combination
        self.i_p_benefit = test_combination(self.i_p_inf, self.i_p_cav, self.i_p_art, self.i_p_jok)
        
        if self.i_p_benefit <= 0:
            self.cmd_trade.config(state=tk.DISABLED)
            self.pan_armies.config(text="")
        else:
            self.cmd_trade.config(state=tk.NORMAL)
            self.pan_armies.config(text=f"{self.i_p_benefit} armies")
    
    def cmd_trade_click(self):
        """Handle Trade button click"""
        if self.i_p_benefit > 0:
            # Trade the cards
            trade_cards(self.i_p_inf, self.i_p_cav, self.i_p_art, self.i_p_jok)
            self.result = True
            self.dialog.destroy()
    
    def cmd_hold_click(self):
        """Handle Hold button click"""
        self.result = False
        self.dialog.destroy()
    
    def on_cancel(self):
        """Handle Cancel button"""
        self.result = False
        self.dialog.destroy()


# =============================================================================
# Export all functions and classes
# =============================================================================

__all__ = [
    'CA_INF', 'CA_CAV', 'CA_ART', 'CA_JOK',
    'CS_DIF', 'CS_INF', 'CS_CAV', 'CS_ART',
    'draw_card', 'test_combination', 'find_best_combination',
    'trade_cards', 'can_trade_cards', 'get_card_count', 'get_total_cards',
    'CardsDialog',
]

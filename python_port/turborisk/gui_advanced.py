"""
TurboRisk - Advanced GUI Features
Python port - Advanced GUI components and features

This module provides advanced GUI features for TurboRisk that go beyond
the basic functionality. These features enhance the user experience and
provide additional visualization and interaction capabilities.
"""

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

import os
import sys
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .globals import G, MAXPLAYERS, MAXTERRITORIES
from .territory import setup_territories
from .action_history import action_count, action_value, ActionKind, ActionField


# =============================================================================
# Color Management
# =============================================================================

class ColorManager:
    """Manages player colors and provides color-related utilities"""
    
    # Standard player colors
    PLAYER_COLORS = [
        '#FF0000',  # Red
        '#00FF00',  # Green
        '#0000FF',  # Blue
        '#FFFF00',  # Yellow
        '#FF00FF',  # Magenta
        '#00FFFF',  # Cyan
        '#FF8000',  # Orange
        '#8000FF',  # Purple
        '#00FF80',  # Spring Green
        '#FF8080',  # Light Red
    ]
    
    # Continent colors
    CONTINENT_COLORS = {
        'CO_NA': '#FFCCCC',  # North America - light red
        'CO_SA': '#CCFFCC',  # South America - light green
        'CO_EU': '#CCCCFF',  # Europe - light blue
        'CO_AF': '#FFFFCC',  # Africa - light yellow
        'CO_AS': '#FFCCFF',  # Asia - light purple
        'CO_AU': '#CCFFFF',  # Australia - light cyan
    }
    
    @classmethod
    def get_player_color(cls, player_id: int) -> str:
        """Get the color for a player"""
        if 1 <= player_id <= len(cls.PLAYER_COLORS):
            return cls.PLAYER_COLORS[player_id - 1]
        return '#808080'  # Gray for extra players
    
    @classmethod
    def get_continent_color(cls, continent_name: str) -> str:
        """Get the color for a continent"""
        return cls.CONTINENT_COLORS.get(continent_name, '#FFFFFF')
    
    @classmethod
    def get_territory_color(cls, territory_id: int) -> str:
        """Get the color for a territory based on its owner"""
        from .globals import G
        owner = G.ar_territory[territory_id].owner
        if owner > 0:
            return cls.get_player_color(owner)
        return '#FFFFFF'  # White for unowned
    
    @classmethod
    def best_text_color(cls, bg_color: str) -> str:
        """Get the best text color (black or white) for a background color"""
        # Simple brightness calculation
        if bg_color.startswith('#'):
            r = int(bg_color[1:3], 16)
            g = int(bg_color[3:5], 16)
            b = int(bg_color[5:7], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            return '#000000' if brightness > 128 else '#FFFFFF'
        return '#000000'


# =============================================================================
# Statistics Visualization
# =============================================================================

@dataclass
class PlayerStats:
    """Statistics for a player"""
    name: str
    territories: int
    armies: int
    cards: int
    wins: int
    losses: int
    color: str


class StatisticsVisualizer:
    """Visualizes game statistics"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.dialog = None
        self.canvas = None
        self.bar_height = 30
        self.bar_spacing = 5
    
    def show(self):
        """Show the statistics dialog"""
        if not TKINTER_AVAILABLE:
            return
        
        self.dialog = tk.Toplevel(self.root)
        self.dialog.title("Game Statistics")
        self.dialog.geometry("600x400")
        self.dialog.transient(self.root)
        self.dialog.grab_set()
        
        # Create notebook
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Territories tab
        self._create_territories_tab(notebook)
        
        # Armies tab
        self._create_armies_tab(notebook)
        
        # History tab
        self._create_history_tab(notebook)
        
        # Wait for dialog to close
        self.root.wait_window(self.dialog)
    
    def _create_territories_tab(self, notebook):
        """Create the territories statistics tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Territories")
        
        # Collect data
        stats = []
        for i in range(1, MAXPLAYERS + 1):
            if G.ar_player[i].active:
                territories = G.ar_player[i].territ
                color = ColorManager.get_player_color(i)
                stats.append({
                    'player_id': i,
                    'name': G.ar_player[i].name,
                    'territories': territories,
                    'color': color
                })
        
        # Sort by territories
        stats.sort(key=lambda x: x['territories'], reverse=True)
        
        # Find max for scaling
        max_territories = max([s['territories'] for s in stats]) if stats else 1
        
        # Draw bars
        canvas = tk.Canvas(frame, width=500, height=len(stats) * (self.bar_height + self.bar_spacing) + 20)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        for i, stat in enumerate(stats):
            y = i * (self.bar_height + self.bar_spacing) + 10
            width = 400 * stat['territories'] / max_territories if max_territories > 0 else 0
            
            # Draw bar
            canvas.create_rectangle(50, y, 50 + width, y + self.bar_height, 
                                   fill=stat['color'], outline='#000000')
            
            # Draw text
            text_color = ColorManager.best_text_color(stat['color'])
            canvas.create_text(40, y + self.bar_height // 2, 
                              text=f"P{stat['player_id']}", anchor=tk.E, fill=text_color)
            canvas.create_text(50 + width + 10, y + self.bar_height // 2,
                              text=f"{stat['territories']}", anchor=tk.W, fill=text_color)
            canvas.create_text(300, y + self.bar_height // 2,
                              text=stat['name'], anchor=tk.W)
    
    def _create_armies_tab(self, notebook):
        """Create the armies statistics tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Armies")
        
        # Collect data
        stats = []
        for i in range(1, MAXPLAYERS + 1):
            if G.ar_player[i].active:
                armies = G.ar_player[i].army
                color = ColorManager.get_player_color(i)
                stats.append({
                    'player_id': i,
                    'name': G.ar_player[i].name,
                    'armies': armies,
                    'color': color
                })
        
        # Sort by armies
        stats.sort(key=lambda x: x['armies'], reverse=True)
        
        # Find max for scaling
        max_armies = max([s['armies'] for s in stats]) if stats else 1
        
        # Draw bars
        canvas = tk.Canvas(frame, width=500, height=len(stats) * (self.bar_height + self.bar_spacing) + 20)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        for i, stat in enumerate(stats):
            y = i * (self.bar_height + self.bar_spacing) + 10
            width = 400 * stat['armies'] / max_armies if max_armies > 0 else 0
            
            # Draw bar
            canvas.create_rectangle(50, y, 50 + width, y + self.bar_height, 
                                   fill=stat['color'], outline='#000000')
            
            # Draw text
            text_color = ColorManager.best_text_color(stat['color'])
            canvas.create_text(40, y + self.bar_height // 2, 
                              text=f"P{stat['player_id']}", anchor=tk.E, fill=text_color)
            canvas.create_text(50 + width + 10, y + self.bar_height // 2,
                              text=f"{stat['armies']}", anchor=tk.W, fill=text_color)
            canvas.create_text(300, y + self.bar_height // 2,
                              text=stat['name'], anchor=tk.W)
    
    def _create_history_tab(self, notebook):
        """Create the game history tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="History")
        
        # Create a listbox for action history
        listbox = tk.Listbox(frame, font=('Courier', 10))
        listbox.pack(fill=tk.BOTH, expand=True)
        
        # Populate with action history
        count = action_count()
        for i in range(1, min(count + 1, 100)):  # Show last 100 actions
            action_type = action_value(i, ActionField.AF_KIND)
            player = action_value(i, ActionField.AF_PLAYER)
            territory = action_value(i, ActionField.AF_TERRITORY)
            
            action_name = ActionKind(action_type).name if action_type else "UNKNOWN"
            listbox.insert(tk.END, f"Turn {i}: {action_name} - Player {player}, Territory {territory}")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)


# =============================================================================
# Map Visualization with Zoom and Pan
# =============================================================================

class MapVisualizer:
    """Advanced map visualization with zoom and pan"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.canvas = None
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.dragging = False
        self.last_x = 0
        self.last_y = 0
    
    def create(self, parent_frame):
        """Create the map visualization canvas"""
        if not TKINTER_AVAILABLE:
            return
        
        # Create canvas
        self.canvas = tk.Canvas(parent_frame, bg='white', 
                                scrollregion=(0, 0, 2000, 2000))
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        h_scroll = ttk.Scrollbar(parent_frame, orient=tk.HORIZONTAL, 
                                command=self.canvas.xview)
        h_scroll.pack(fill=tk.X, side=tk.BOTTOM)
        v_scroll = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, 
                                command=self.canvas.yview)
        v_scroll.pack(fill=tk.Y, side=tk.RIGHT)
        
        self.canvas.configure(xscrollcommand=h_scroll.set, 
                              yscrollcommand=v_scroll.set)
        
        # Bind events
        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)
        self.canvas.bind('<Configure>', self.on_configure)
        
        # Draw initial map
        self.draw_map()
    
    def on_mouse_down(self, event):
        """Handle mouse down for panning"""
        self.dragging = True
        self.last_x = event.x
        self.last_y = event.y
    
    def on_mouse_drag(self, event):
        """Handle mouse drag for panning"""
        if self.dragging:
            dx = event.x - self.last_x
            dy = event.y - self.last_y
            self.pan_x += dx
            self.pan_y += dy
            self.canvas.xview_scroll(-dx, tk.UNITS)
            self.canvas.yview_scroll(-dy, tk.UNITS)
            self.last_x = event.x
            self.last_y = event.y
    
    def on_mouse_up(self, event):
        """Handle mouse up"""
        self.dragging = False
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel for zooming"""
        # Get mouse position in canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Zoom in/out
        if event.delta > 0:
            self.zoom_level *= 1.1
        else:
            self.zoom_level *= 0.9
        
        # Clamp zoom level
        self.zoom_level = max(0.1, min(self.zoom_level, 10.0))
        
        # Redraw map
        self.draw_map()
        
        # Adjust view to keep mouse position centered
        self.canvas.xview_scroll(int(x * (1 - 1/self.zoom_level)), tk.UNITS)
        self.canvas.yview_scroll(int(y * (1 - 1/self.zoom_level)), tk.UNITS)
    
    def on_configure(self, event):
        """Handle canvas resize"""
        self.draw_map()
    
    def draw_map(self):
        """Draw the map on the canvas"""
        if not self.canvas:
            return
        
        self.canvas.delete("all")
        
        # Get canvas dimensions
        width = self.canvas.winfo_width() or 800
        height = self.canvas.winfo_height() or 600
        
        # Draw territories
        for i in range(1, MAXTERRITORIES + 1):
            terr = G.ar_territory[i]
            if terr.name:
                # Calculate position (simplified layout)
                x = 50 + (i % 10) * 100 * self.zoom_level
                y = 100 + (i // 10) * 60 * self.zoom_level
                
                # Draw territory circle
                radius = 20 * self.zoom_level
                color = ColorManager.get_territory_color(i)
                self.canvas.create_oval(x - radius, y - radius, 
                                        x + radius, y + radius,
                                        outline='blue', fill=color, 
                                        tags=f"territory_{i}")
                
                # Draw territory name (only at higher zoom levels)
                if self.zoom_level > 0.5:
                    self.canvas.create_text(x, y, text=str(i), 
                                           tags=f"territory_{i}")
                
                # Draw army count
                if terr.army > 0:
                    self.canvas.create_text(x, y - radius - 10, 
                                           text=str(terr.army), 
                                           tags=f"territory_{i}")
        
        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def zoom_in(self):
        """Zoom in"""
        self.zoom_level *= 1.2
        self.zoom_level = min(self.zoom_level, 10.0)
        self.draw_map()
    
    def zoom_out(self):
        """Zoom out"""
        self.zoom_level *= 0.8
        self.zoom_level = max(self.zoom_level, 0.1)
        self.draw_map()
    
    def reset_zoom(self):
        """Reset zoom to default"""
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.draw_map()


# =============================================================================
# Tooltip System
# =============================================================================

class Tooltip:
    """Creates a tooltip for widgets"""
    
    def __init__(self, widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip = None
        self.id = None
        
        self.widget.bind('<Enter>', self.on_enter)
        self.widget.bind('<Leave>', self.on_leave)
    
    def on_enter(self, event=None):
        """Show tooltip after delay"""
        if self.tooltip:
            self.tooltip.destroy()
        self.id = self.widget.after(self.delay, self.show_tooltip)
    
    def on_leave(self, event=None):
        """Hide tooltip"""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
    
    def show_tooltip(self):
        """Show the tooltip"""
        if not self.tooltip:
            self.tooltip = tk.Toplevel(self.widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{self.widget.winfo_rootx() + 10}+{self.widget.winfo_rooty() + 10}")
            
            label = ttk.Label(self.tooltip, text=self.text, 
                            background='#FFFFE0', relief=tk.SOLID, 
                            borderwidth=1, padding=5)
            label.pack()
            
            self.tooltip.lift()


# =============================================================================
# Game Replay System
# =============================================================================

class GameReplay:
    """Allows replaying a game from action history"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.dialog = None
        self.current_action = 0
        self.total_actions = 0
    
    def show(self):
        """Show the replay dialog"""
        if not TKINTER_AVAILABLE:
            return
        
        self.dialog = tk.Toplevel(self.root)
        self.dialog.title("Game Replay")
        self.dialog.geometry("500x400")
        self.dialog.transient(self.root)
        self.dialog.grab_set()
        
        # Get total actions
        self.total_actions = action_count()
        self.current_action = 0
        
        # Create controls
        control_frame = ttk.Frame(self.dialog)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_label = ttk.Label(control_frame, 
                                     text=f"Action 0 of {self.total_actions}")
        self.status_label.pack(side=tk.LEFT)
        
        ttk.Button(control_frame, text="<< First", command=self.first).pack(side=tk.RIGHT, padx=5)
        ttk.Button(control_frame, text="< Prev", command=self.previous).pack(side=tk.RIGHT, padx=5)
        ttk.Button(control_frame, text="Next >", command=self.next).pack(side=tk.RIGHT, padx=5)
        ttk.Button(control_frame, text="Last >>", command=self.last).pack(side=tk.RIGHT, padx=5)
        
        # Create action display
        action_frame = ttk.LabelFrame(self.dialog, text="Action Details")
        action_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.action_text = tk.Text(action_frame, wrap=tk.WORD, font=('Courier', 10))
        self.action_text.pack(fill=tk.BOTH, expand=True)
        
        # Show first action
        self.show_action(self.current_action)
        
        # Wait for dialog to close
        self.root.wait_window(self.dialog)
    
    def show_action(self, action_num: int):
        """Show the details of a specific action"""
        if action_num < 1 or action_num > self.total_actions:
            return
        
        self.current_action = action_num
        self.status_label.config(text=f"Action {action_num} of {self.total_actions}")
        
        # Get action details
        self.action_text.delete(1.0, tk.END)
        
        action_type = action_value(action_num, ActionField.AF_KIND)
        player = action_value(action_num, ActionField.AF_PLAYER)
        territory = action_value(action_num, ActionField.AF_TERRITORY)
        from_terr = action_value(action_num, ActionField.AF_FROM_TERRITORY)
        to_terr = action_value(action_num, ActionField.AF_TO_TERRITORY)
        armies = action_value(action_num, ActionField.AF_ARMIES)
        
        action_name = ActionKind(action_type).name if action_type else "UNKNOWN"
        
        self.action_text.insert(tk.END, f"Action: {action_name}\n")
        self.action_text.insert(tk.END, f"Player: {player}\n")
        self.action_text.insert(tk.END, f"Territory: {territory}\n")
        if from_terr:
            self.action_text.insert(tk.END, f"From: {from_terr}\n")
        if to_terr:
            self.action_text.insert(tk.END, f"To: {to_terr}\n")
        if armies:
            self.action_text.insert(tk.END, f"Armies: {armies}\n")
    
    def first(self):
        """Show first action"""
        self.show_action(1)
    
    def previous(self):
        """Show previous action"""
        self.show_action(self.current_action - 1)
    
    def next(self):
        """Show next action"""
        self.show_action(self.current_action + 1)
    
    def last(self):
        """Show last action"""
        self.show_action(self.total_actions)


# =============================================================================
# Utility Functions
# =============================================================================

def show_advanced_statistics(root: tk.Tk):
    """Show advanced game statistics"""
    if not TKINTER_AVAILABLE:
        print("Tkinter not available. Cannot show statistics.")
        return
    
    visualizer = StatisticsVisualizer(root)
    visualizer.show()


def show_game_replay(root: tk.Tk):
    """Show game replay dialog"""
    if not TKINTER_AVAILABLE:
        print("Tkinter not available. Cannot show replay.")
        return
    
    replay = GameReplay(root)
    replay.show()


def create_map_visualizer(parent_frame):
    """Create a map visualizer with zoom and pan"""
    visualizer = MapVisualizer(parent_frame)
    visualizer.create(parent_frame)
    return visualizer

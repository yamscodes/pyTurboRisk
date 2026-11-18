"""
TRMap - Map Editor GUI
Python port of TRMapForm.pas
"""

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    from PIL import Image, ImageTk, ImageDraw
    TKINTER_AVAILABLE = True
    PIL_AVAILABLE = True
except ImportError as e:
    if 'tkinter' in str(e).lower():
        TKINTER_AVAILABLE = False
        print("Warning: Tkinter not available. TRMap GUI will not work.")
    else:
        PIL_AVAILABLE = False
        print("Warning: PIL not available. Image editing will be limited.")
        TKINTER_AVAILABLE = True

import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from turborisk import G, MAXTERRITORIES
from turborisk.globals import ContinentID, Territory
from turborisk.territory import setup_territories, load_map, save_map


class TRMapGUI:
    """Map Editor GUI"""
    
    def __init__(self, root):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run TRMap.")
        
        self.root = root
        self.root.title("TRMap - Map Editor")
        self.root.geometry("1200x800")
        
        self.current_file = None
        self.modified = False
        self.selected_territory = None
        self.selected_continent = None
        self.drawing = False
        self.last_x = None
        self.last_y = None
        
        # Initialize territories
        setup_territories()
        
        self.create_menu_bar()
        self.create_toolbar()
        self.create_main_layout()
        self.create_territory_panel()
        self.create_continent_panel()
        self.create_status_bar()
        
        # Load default map
        self.load_default_map()
    
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.file_new)
        file_menu.add_command(label="Open...", command=self.file_open)
        file_menu.add_command(label="Save", command=self.file_save)
        file_menu.add_command(label="Save As...", command=self.file_save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.file_exit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.edit_undo)
        edit_menu.add_command(label="Redo", command=self.edit_redo)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Zoom In", command=self.zoom_in)
        view_menu.add_command(label="Zoom Out", command=self.zoom_out)
        view_menu.add_command(label="Reset Zoom", command=self.reset_zoom)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Map menu
        map_menu = tk.Menu(menubar, tearoff=0)
        map_menu.add_command(label="Add Territory", command=self.add_territory)
        map_menu.add_command(label="Remove Territory", command=self.remove_territory)
        map_menu.add_command(label="Add Continent", command=self.add_continent)
        map_menu.add_separator()
        map_menu.add_command(label="Set Borders", command=self.set_borders)
        menubar.add_cascade(label="Map", menu=map_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_toolbar(self):
        """Create the toolbar"""
        toolbar = tk.Frame(self.root, relief=tk.RAISED, bd=2)
        toolbar.pack(fill=tk.X, side=tk.TOP)
        
        # Toolbar buttons
        buttons = [
            ("New", self.file_new),
            ("Open", self.file_open),
            ("Save", self.file_save),
            ("|", None),
            ("Add Territory", self.add_territory),
            ("Remove Territory", self.remove_territory),
            ("|", None),
            ("Zoom In", self.zoom_in),
            ("Zoom Out", self.zoom_out),
        ]
        
        for text, command in buttons:
            if text == "|":
                ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=2)
            else:
                btn = ttk.Button(toolbar, text=text, command=command)
                btn.pack(side=tk.LEFT, padx=2, pady=2)
    
    def create_main_layout(self):
        """Create the main layout"""
        # Main paned window
        self.main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Map canvas
        self.left_panel = tk.Frame(self.main_paned)
        self.main_paned.add(self.left_panel)
        
        # Canvas for map
        self.canvas = tk.Canvas(self.left_panel, bg='white', scrollregion=(0, 0, 2000, 2000))
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        h_scroll = ttk.Scrollbar(self.left_panel, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scroll.pack(fill=tk.X, side=tk.BOTTOM)
        v_scroll = ttk.Scrollbar(self.left_panel, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scroll.pack(fill=tk.Y, side=tk.RIGHT)
        
        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
        # Bind events
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        # Right panel - Properties
        self.right_panel = tk.Frame(self.main_paned)
        self.main_paned.add(self.right_panel)
        
        # Notebook for right panel
        self.right_notebook = ttk.Notebook(self.right_panel)
        self.right_notebook.pack(fill=tk.BOTH, expand=True)
    
    def create_territory_panel(self):
        """Create the territory properties panel"""
        self.territory_frame = tk.Frame(self.right_notebook)
        self.right_notebook.add(self.territory_frame, text="Territory")
        
        # Territory list
        ttk.Label(self.territory_frame, text="Territories:").pack(anchor=tk.W, pady=5)
        self.territory_listbox = tk.Listbox(self.territory_frame, height=10)
        self.territory_listbox.pack(fill=tk.BOTH, expand=True)
        self.territory_listbox.bind('<<ListboxSelect>>', self.on_territory_selected)
        
        # Territory properties
        ttk.Label(self.territory_frame, text="Properties:").pack(anchor=tk.W, pady=(10, 5))
        
        form_frame = tk.Frame(self.territory_frame)
        form_frame.pack(fill=tk.X, pady=5)
        
        # Name
        ttk.Label(form_frame, text="Name:", width=10).grid(row=0, column=0, sticky=tk.W)
        self.territory_name_entry = ttk.Entry(form_frame)
        self.territory_name_entry.grid(row=0, column=1, sticky=tk.EW)
        
        # X position
        ttk.Label(form_frame, text="X:", width=10).grid(row=1, column=0, sticky=tk.W)
        self.territory_x_entry = ttk.Entry(form_frame)
        self.territory_x_entry.grid(row=1, column=1, sticky=tk.EW)
        
        # Y position
        ttk.Label(form_frame, text="Y:", width=10).grid(row=2, column=0, sticky=tk.W)
        self.territory_y_entry = ttk.Entry(form_frame)
        self.territory_y_entry.grid(row=2, column=1, sticky=tk.EW)
        
        # Continent
        ttk.Label(form_frame, text="Continent:", width=10).grid(row=3, column=0, sticky=tk.W)
        self.territory_continent_combo = ttk.Combobox(form_frame, values=[c.name for c in ContinentID])
        self.territory_continent_combo.grid(row=3, column=1, sticky=tk.EW)
        
        # Borders
        ttk.Label(form_frame, text="Borders:", width=10).grid(row=4, column=0, sticky=tk.W)
        self.territory_borders_entry = ttk.Entry(form_frame)
        self.territory_borders_entry.grid(row=4, column=1, sticky=tk.EW)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Update button
        ttk.Button(self.territory_frame, text="Update", command=self.update_territory).pack(pady=5)
        
        # Populate territory list
        self.populate_territory_list()
    
    def create_continent_panel(self):
        """Create the continent properties panel"""
        self.continent_frame = tk.Frame(self.right_notebook)
        self.right_notebook.add(self.continent_frame, text="Continents")
        
        # Continent list
        ttk.Label(self.continent_frame, text="Continents:").pack(anchor=tk.W, pady=5)
        self.continent_listbox = tk.Listbox(self.continent_frame, height=10)
        self.continent_listbox.pack(fill=tk.BOTH, expand=True)
        self.continent_listbox.bind('<<ListboxSelect>>', self.on_continent_selected)
        
        # Continent properties
        ttk.Label(self.continent_frame, text="Properties:").pack(anchor=tk.W, pady=(10, 5))
        
        form_frame = tk.Frame(self.continent_frame)
        form_frame.pack(fill=tk.X, pady=5)
        
        # Name
        ttk.Label(form_frame, text="Name:", width=10).grid(row=0, column=0, sticky=tk.W)
        self.continent_name_entry = ttk.Entry(form_frame)
        self.continent_name_entry.grid(row=0, column=1, sticky=tk.EW)
        
        # Bonus
        ttk.Label(form_frame, text="Bonus:", width=10).grid(row=1, column=0, sticky=tk.W)
        self.continent_bonus_entry = ttk.Entry(form_frame)
        self.continent_bonus_entry.grid(row=1, column=1, sticky=tk.EW)
        
        # Color
        ttk.Label(form_frame, text="Color:", width=10).grid(row=2, column=0, sticky=tk.W)
        self.continent_color_entry = ttk.Entry(form_frame)
        self.continent_color_entry.grid(row=2, column=1, sticky=tk.EW)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Update button
        ttk.Button(self.continent_frame, text="Update", command=self.update_continent).pack(pady=5)
        
        # Populate continent list
        self.populate_continent_list()
    
    def create_status_bar(self):
        """Create the status bar"""
        self.status_bar = tk.Frame(self.root, relief=tk.SUNKEN, bd=1)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(self.status_bar, text="Ready", anchor=tk.W)
        self.status_label.pack(fill=tk.X, expand=True, padx=5)
    
    def load_default_map(self):
        """Load the default map"""
        # Set up territories from the global state
        self.populate_territory_list()
        self.populate_continent_list()
        self.draw_map()
        self.log_message("Default map loaded")
    
    def draw_map(self):
        """Draw the map on the canvas"""
        self.canvas.delete("all")
        
        # Draw continents
        for continent_id in ContinentID:
            color = self.get_continent_color(continent_id)
            # Draw a rectangle for each continent (simplified)
            x = (continent_id.value - 1) * 200 + 50
            y = 50
            self.canvas.create_rectangle(x, y, x + 150, y + 100, fill=color, outline='black', tags=f"continent_{continent_id.name}")
            self.canvas.create_text(x + 75, y + 50, text=continent_id.name, tags=f"continent_{continent_id.name}")
        
        # Draw territories
        for i in range(1, MAXTERRITORIES + 1):
            terr = G.ar_territory[i]
            if terr.name:
                x = 50 + (i % 10) * 100
                y = 200 + (i // 10) * 60
                
                # Draw territory circle
                self.canvas.create_oval(x, y, x + 40, y + 40, outline='blue', tags=f"territory_{i}")
                
                # Draw territory name
                self.canvas.create_text(x + 20, y + 20, text=terr.name, tags=f"territory_{i}")
                
                # Draw territory number
                self.canvas.create_text(x + 20, y + 35, text=str(i), tags=f"territory_{i}")
        
        self.log_message(f"Drew {MAXTERRITORIES} territories")
    
    def get_continent_color(self, continent_id):
        """Get color for a continent"""
        colors = {
            ContinentID.CO_NA: '#FFCCCC',  # North America - light red
            ContinentID.CO_SA: '#CCFFCC',  # South America - light green
            ContinentID.CO_EU: '#CCCCFF',  # Europe - light blue
            ContinentID.CO_AF: '#FFFFCC',  # Africa - light yellow
            ContinentID.CO_AS: '#FFCCFF',  # Asia - light purple
            ContinentID.CO_AU: '#CCFFFF',  # Australia - light cyan
        }
        return colors.get(continent_id, '#FFFFFF')
    
    def populate_territory_list(self):
        """Populate the territory list"""
        self.territory_listbox.delete(0, tk.END)
        for i in range(1, MAXTERRITORIES + 1):
            terr = G.ar_territory[i]
            if terr.name:
                self.territory_listbox.insert(tk.END, f"{i}: {terr.name}")
    
    def populate_continent_list(self):
        """Populate the continent list"""
        self.continent_listbox.delete(0, tk.END)
        for continent_id in ContinentID:
            self.continent_listbox.insert(tk.END, continent_id.name)
    
    def on_canvas_click(self, event):
        """Handle canvas click"""
        self.last_x = event.x
        self.last_y = event.y
        self.drawing = True
        
        # Find clicked territory
        items = self.canvas.find_withtag(f"territory_*")
        for item in items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("territory_"):
                    terr_id = int(tag.replace("territory_", ""))
                    self.selected_territory = terr_id
                    self.log_message(f"Selected territory: {terr_id} - {G.ar_territory[terr_id].name}")
                    self.highlight_territory(terr_id)
                    self.show_territory_properties(terr_id)
                    break
    
    def on_canvas_drag(self, event):
        """Handle canvas drag"""
        if self.drawing and self.last_x and self.last_y:
            # Draw a line or selection box
            pass
        self.last_x = event.x
        self.last_y = event.y
    
    def on_canvas_release(self, event):
        """Handle canvas release"""
        self.drawing = False
    
    def on_canvas_configure(self, event):
        """Handle canvas configure"""
        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_territory_selected(self, event=None):
        """Handle territory selection from list"""
        selection = self.territory_listbox.curselection()
        if selection:
            index = selection[0]
            terr_id = index + 1
            self.selected_territory = terr_id
            self.highlight_territory(terr_id)
            self.show_territory_properties(terr_id)
    
    def on_continent_selected(self, event=None):
        """Handle continent selection from list"""
        selection = self.continent_listbox.curselection()
        if selection:
            index = selection[0]
            continent_id = list(ContinentID)[index]
            self.selected_continent = continent_id
            self.show_continent_properties(continent_id)
    
    def highlight_territory(self, terr_id):
        """Highlight a territory on the canvas"""
        # Remove previous highlights
        self.canvas.delete("highlight")
        
        # Highlight the territory
        items = self.canvas.find_withtag(f"territory_{terr_id}")
        for item in items:
            self.canvas.addtag_withtag("highlight", item)
        
        self.canvas.itemconfig("highlight", outline='red', width=3)
    
    def show_territory_properties(self, terr_id):
        """Show territory properties in the form"""
        terr = G.ar_territory[terr_id]
        self.territory_name_entry.delete(0, tk.END)
        self.territory_name_entry.insert(0, terr.name)
        
        # Get territory position (not stored in original, so use defaults)
        x = 50 + (terr_id % 10) * 100
        y = 200 + (terr_id // 10) * 60
        self.territory_x_entry.delete(0, tk.END)
        self.territory_x_entry.insert(0, str(x))
        self.territory_y_entry.delete(0, tk.END)
        self.territory_y_entry.insert(0, str(y))
        
        # Set continent
        self.territory_continent_combo.set(terr.continent.name)
        
        # Set borders
        borders = ', '.join(str(b) for b in terr.borders[1:13] if b > 0)
        self.territory_borders_entry.delete(0, tk.END)
        self.territory_borders_entry.insert(0, borders)
    
    def show_continent_properties(self, continent_id):
        """Show continent properties in the form"""
        continent = G.ar_continent[continent_id]
        self.continent_name_entry.delete(0, tk.END)
        self.continent_name_entry.insert(0, continent_id.name)
        
        self.continent_bonus_entry.delete(0, tk.END)
        self.continent_bonus_entry.insert(0, str(continent.bonus))
        
        # Color (not stored in original)
        self.continent_color_entry.delete(0, tk.END)
        self.continent_color_entry.insert(0, self.get_continent_color(continent_id))
    
    def update_territory(self):
        """Update territory properties"""
        if self.selected_territory is None:
            messagebox.showwarning("Warning", "No territory selected")
            return
        
        terr = G.ar_territory[self.selected_territory]
        terr.name = self.territory_name_entry.get()
        
        # Update continent
        continent_name = self.territory_continent_combo.get()
        for c_id in ContinentID:
            if c_id.name == continent_name:
                terr.continent = c_id
                break
        
        # Update borders (parse comma-separated list)
        borders_str = self.territory_borders_entry.get()
        borders = [int(b.strip()) if b.strip().isdigit() else 0 for b in borders_str.split(',')]
        for i, border in enumerate(borders[:12]):  # Max 12 borders
            terr.borders[i + 1] = border
        
        self.modified = True
        self.log_message(f"Updated territory: {self.selected_territory}")
        self.draw_map()
    
    def update_continent(self):
        """Update continent properties"""
        if self.selected_continent is None:
            messagebox.showwarning("Warning", "No continent selected")
            return
        
        continent = G.ar_continent[self.selected_continent]
        # Note: continent name is read-only in the original
        
        try:
            continent.bonus = int(self.continent_bonus_entry.get())
        except ValueError:
            messagebox.showwarning("Warning", "Bonus must be a number")
            return
        
        self.modified = True
        self.log_message(f"Updated continent: {self.selected_continent.name}")
        self.draw_map()
    
    def add_territory(self):
        """Add a new territory"""
        # Find first available territory slot
        for i in range(1, MAXTERRITORIES + 1):
            if G.ar_territory[i].name == "":
                G.ar_territory[i].name = f"New Territory {i}"
                G.ar_territory[i].continent = ContinentID.CO_NA  # Default to North America
                self.selected_territory = i
                self.modified = True
                self.log_message(f"Added territory: {i}")
                self.populate_territory_list()
                self.draw_map()
                self.show_territory_properties(i)
                return
        
        messagebox.showwarning("Warning", "Maximum number of territories reached")
    
    def remove_territory(self):
        """Remove a territory"""
        if self.selected_territory is None:
            messagebox.showwarning("Warning", "No territory selected")
            return
        
        if messagebox.askyesno("Confirm", f"Remove territory {self.selected_territory}?"):
            G.ar_territory[self.selected_territory].name = ""
            G.ar_territory[self.selected_territory].owner = 0
            G.ar_territory[self.selected_territory].army = 0
            for i in range(1, 13):
                G.ar_territory[self.selected_territory].borders[i] = 0
            
            self.selected_territory = None
            self.modified = True
            self.log_message(f"Removed territory: {self.selected_territory}")
            self.populate_territory_list()
            self.draw_map()
    
    def add_continent(self):
        """Add a new continent"""
        messagebox.showwarning("Not Implemented", "Adding new continents is not yet implemented")
    
    def set_borders(self):
        """Set borders for a territory"""
        if self.selected_territory is None:
            messagebox.showwarning("Warning", "No territory selected")
            return
        
        # Show border editor dialog
        self.show_border_editor()
    
    def show_border_editor(self):
        """Show the border editor dialog"""
        if self.selected_territory is None:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Borders for Territory {self.selected_territory}")
        dialog.transient(self.root)
        dialog.grab_set()
        
        terr = G.ar_territory[self.selected_territory]
        
        # List of all territories
        ttk.Label(dialog, text="Available Territories:").pack(anchor=tk.W, pady=5)
        territory_vars = []
        
        for i in range(1, MAXTERRITORIES + 1):
            if i != self.selected_territory and G.ar_territory[i].name:
                var = tk.IntVar(value=1 if i in terr.borders[1:13] else 0)
                territory_vars.append((i, var))
                cb = ttk.Checkbutton(dialog, text=f"{i}: {G.ar_territory[i].name}", variable=var)
                cb.pack(anchor=tk.W)
        
        # OK button
        def on_ok():
            # Update borders
            borders = [0] * 13
            for i, var in territory_vars:
                if var.get():
                    for j in range(1, 13):
                        if borders[j] == 0:
                            borders[j] = i
                            break
            
            for j in range(1, 13):
                terr.borders[j] = borders[j]
            
            self.modified = True
            self.log_message(f"Updated borders for territory {self.selected_territory}")
            dialog.destroy()
        
        ttk.Button(dialog, text="OK", command=on_ok).pack(pady=10)
        
        # Wait for dialog to close
        self.root.wait_window(dialog)
    
    def zoom_in(self):
        """Zoom in"""
        self.canvas.scale("all", 0, 0, 1.2, 1.2)
        self.log_message("Zoomed in")
    
    def zoom_out(self):
        """Zoom out"""
        self.canvas.scale("all", 0, 0, 0.8, 0.8)
        self.log_message("Zoomed out")
    
    def reset_zoom(self):
        """Reset zoom"""
        self.draw_map()
        self.log_message("Zoom reset")
    
    def file_new(self):
        """Create a new map"""
        if not self.confirm_discard_changes():
            return
        
        setup_territories()
        self.current_file = None
        self.modified = False
        self.draw_map()
        self.log_message("New map created")
    
    def file_open(self):
        """Open a map file"""
        if not self.confirm_discard_changes():
            return
        
        filename = filedialog.askopenfilename(
            title="Open Map File",
            filetypes=[("TRM Files", "*.trm"), ("All Files", "*.*")],
            defaultextension=".trm"
        )
        
        if filename:
            try:
                load_map(filename)
                self.current_file = filename
                self.modified = False
                self.draw_map()
                self.log_message(f"Opened: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {str(e)}")
    
    def file_save(self):
        """Save the map"""
        if not self.current_file:
            self.file_save_as()
            return
        
        try:
            save_map(self.current_file)
            self.modified = False
            self.log_message(f"Saved: {self.current_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def file_save_as(self):
        """Save as a new file"""
        filename = filedialog.asksaveasfilename(
            title="Save Map File",
            filetypes=[("TRM Files", "*.trm"), ("All Files", "*.*")],
            defaultextension=".trm"
        )
        
        if filename:
            self.current_file = filename
            self.file_save()
    
    def file_exit(self):
        """Exit the application"""
        if self.confirm_discard_changes():
            self.root.quit()
    
    def edit_undo(self):
        """Undo"""
        messagebox.showwarning("Not Implemented", "Undo is not yet implemented")
    
    def edit_redo(self):
        """Redo"""
        messagebox.showwarning("Not Implemented", "Redo is not yet implemented")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About TRMap", 
                           f"TRMap - Map Editor\n\n"
                           f"Version: {G.sG_AppVers}\n"
                           f"Python Port")
    
    def confirm_discard_changes(self):
        """Confirm discarding changes"""
        if self.modified:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them?"
            )
            if result is None:
                return False
            elif result:
                self.file_save()
        return True
    
    def log_message(self, message):
        """Log a message to the status bar"""
        self.status_label.config(text=message)


def main():
    """Main entry point for TRMap"""
    if not TKINTER_AVAILABLE:
        print("Error: Tkinter is required to run TRMap.")
        print("Install it with: pip install tk")
        sys.exit(1)
    
    root = tk.Tk()
    app = TRMapGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()

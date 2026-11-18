"""
TRComp - TRP Compiler/Editor GUI
Python port of TRCompForm.pas
"""

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog, scrolledtext
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("Warning: Tkinter not available. TRComp GUI will not work.")

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from turborisk import G
from turborisk.trp_transpiler_v3 import TRPTranspiler
from turborisk.trp_runtime import TRPRuntimeInstance


class TRCompGUI:
    """TRP Compiler/Editor GUI"""
    
    def __init__(self, root):
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required to run TRComp.")
        
        self.root = root
        self.root.title("TRComp - TRP Compiler/Editor")
        self.root.geometry("1024x768")
        
        self.current_file = None
        self.modified = False
        
        self.create_menu_bar()
        self.create_main_layout()
        self.create_api_panel()
        self.create_status_bar()
        
        # Initialize TRP transpiler
        self.transpiler = TRPTranspiler()
        
        # Load TRP API functions
        self.load_api_functions()
    
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.file_new, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.file_open, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.file_save, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.file_save_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.file_exit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.edit_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.edit_redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.edit_cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self.edit_copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.edit_paste, accelerator="Ctrl+V")
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # Compile menu
        compile_menu = tk.Menu(menubar, tearoff=0)
        compile_menu.add_command(label="Compile", command=self.compile_script, accelerator="F9")
        compile_menu.add_command(label="Run", command=self.run_script, accelerator="F5")
        menubar.add_cascade(label="Compile", menu=compile_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="API Help", command=self.show_api_help)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_main_layout(self):
        """Create the main layout with source editor and diagnostics"""
        # Main paned window
        self.main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Source editor
        self.left_panel = tk.Frame(self.main_paned)
        self.main_paned.add(self.left_panel)
        
        # Source editor
        self.source_editor = scrolledtext.ScrolledText(
            self.left_panel, 
            wrap=tk.WORD,
            font=('Consolas', 12) if 'Consolas' in tk.font.families() else ('Courier', 12),
            tabs=4
        )
        self.source_editor.pack(fill=tk.BOTH, expand=True)
        self.source_editor.bind('<<Modified>>', self.on_source_modified)
        
        # Right panel - API and diagnostics
        self.right_panel = tk.Frame(self.main_paned)
        self.main_paned.add(self.right_panel)
        
        # Notebook for right panel
        self.right_notebook = ttk.Notebook(self.right_panel)
        self.right_notebook.pack(fill=tk.BOTH, expand=True)
        
        # API Tree tab
        self.api_frame = tk.Frame(self.right_notebook)
        self.right_notebook.add(self.api_frame, text="API")
        
        # Diagnostics tab
        self.diagnostics_frame = tk.Frame(self.right_notebook)
        self.right_notebook.add(self.diagnostics_frame, text="Diagnostics")
        
        self.diagnostics_text = scrolledtext.ScrolledText(
            self.diagnostics_frame,
            wrap=tk.WORD,
            font=('Courier', 10),
            state=tk.DISABLED
        )
        self.diagnostics_text.pack(fill=tk.BOTH, expand=True)
        
        # Routines tab
        self.routines_frame = tk.Frame(self.right_notebook)
        self.right_notebook.add(self.routines_frame, text="Routines")
        
        self.routines_listbox = tk.Listbox(self.routines_frame, font=('Courier', 10))
        self.routines_listbox.pack(fill=tk.BOTH, expand=True)
        self.routines_listbox.bind('<<ListboxSelect>>', self.on_routine_selected)
    
    def create_api_panel(self):
        """Create the API panel with function categories"""
        # Tree view for API
        self.api_tree = ttk.Treeview(self.api_frame)
        self.api_tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.api_frame, orient=tk.VERTICAL, command=self.api_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.api_tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind double click
        self.api_tree.bind('<Double-1>', self.on_api_double_click)
    
    def create_status_bar(self):
        """Create the status bar"""
        self.status_bar = tk.Frame(self.root, relief=tk.SUNKEN, bd=1)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(self.status_bar, text="Ready", anchor=tk.W)
        self.status_label.pack(fill=tk.X, expand=True, padx=5)
    
    def load_api_functions(self):
        """Load TRP API functions into the tree view"""
        # Clear existing items
        for item in self.api_tree.get_children():
            self.api_tree.delete(item)
        
        # Add categories
        categories = {
            "Territory Functions": [
                "TName", "TOwner", "TArmies", "TContinent", "TBordersCount", "TBorder",
                "TIsBordering", "TIsFront", "TIsMine", "TIsEntry", "TFrontsCount", "TFront",
                "TStrongestFront", "TWeakestFront", "TPressure", "TDistance",
                "TShortestPath", "TWeakestPath", "TPathToFront"
            ],
            "Player Functions": [
                "PMe", "PName", "PProgram", "PActive", "PAlive", "PHuman",
                "PArmiesCount", "PNewArmies", "PTerritoriesCount", "PCardCount",
                "PCardTurnInValue"
            ],
            "Continent Functions": [
                "COwner", "CBonus", "CTerritoriesCount", "CTerritory",
                "CBordersCount", "CBorder", "CEntriesCount", "CEntry",
                "CAnalysis", "CLeader"
            ],
            "State Functions": [
                "SConquest", "SPlayersCount", "SAlivePlayersCount", "SCardsBasedOnCombo"
            ],
            "Utility Functions": [
                "UMessage", "ULog", "UBufferSet", "UBufferGet", "URandom",
                "UTakeSnapshot", "UDialog", "UAbortGame", "ULogOff", "ULogOn",
                "UMessageOff", "UMessageOn", "UDialogOff", "UDialogOn",
                "USnapShotOff", "USnapShotOn"
            ]
        }
        
        for category, functions in categories.items():
            category_node = self.api_tree.insert('', 'end', text=category, values=[])
            for func in functions:
                self.api_tree.insert(category_node, 'end', text=func, values=[func])
        
        # Expand all categories
        for category in self.api_tree.get_children():
            self.api_tree.item(category, open=True)
    
    def on_source_modified(self, event=None):
        """Handle source modification"""
        if self.source_editor.edit_modified():
            self.modified = True
            self.update_caption()
            self.source_editor.edit_modified(False)
    
    def update_caption(self):
        """Update the window caption"""
        filename = os.path.basename(self.current_file) if self.current_file else "Untitled"
        modified = "* " if self.modified else ""
        self.root.title(f"TRComp - {modified}{filename}")
    
    def file_new(self):
        """Create a new file"""
        if not self.confirm_discard_changes():
            return
        
        self.current_file = None
        self.source_editor.delete(1.0, tk.END)
        self.modified = False
        self.update_caption()
        self.log_message("New file created")
    
    def file_open(self):
        """Open a file"""
        if not self.confirm_discard_changes():
            return
        
        filename = filedialog.askopenfilename(
            title="Open TRP File",
            filetypes=[("TRP Files", "*.trp"), ("All Files", "*.*")],
            defaultextension=".trp"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    content = f.read()
                self.current_file = filename
                self.source_editor.delete(1.0, tk.END)
                self.source_editor.insert(1.0, content)
                self.modified = False
                self.update_caption()
                self.log_message(f"Opened: {filename}")
                self.refresh_routine_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {str(e)}")
    
    def file_save(self):
        """Save the current file"""
        if not self.current_file:
            self.file_save_as()
            return
        
        try:
            content = self.source_editor.get(1.0, tk.END)
            with open(self.current_file, 'w') as f:
                f.write(content)
            self.modified = False
            self.update_caption()
            self.log_message(f"Saved: {self.current_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def file_save_as(self):
        """Save as a new file"""
        filename = filedialog.asksaveasfilename(
            title="Save TRP File",
            filetypes=[("TRP Files", "*.trp"), ("All Files", "*.*")],
            defaultextension=".trp"
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
        try:
            self.source_editor.edit_undo()
        except tk.TclError:
            pass
    
    def edit_redo(self):
        """Redo"""
        try:
            self.source_editor.edit_redo()
        except tk.TclError:
            pass
    
    def edit_cut(self):
        """Cut"""
        self.source_editor.event_generate('<<Cut>>')
    
    def edit_copy(self):
        """Copy"""
        self.source_editor.event_generate('<<Copy>>')
    
    def edit_paste(self):
        """Paste"""
        self.source_editor.event_generate('<<Paste>>')
    
    def compile_script(self):
        """Compile the current script"""
        if not self.current_file:
            messagebox.showwarning("Warning", "Please save the file first")
            return
        
        try:
            source = self.source_editor.get(1.0, tk.END)
            
            # Use the TRP transpiler
            self.log_message(f"Compiling: {self.current_file}")
            
            # Transpile to Python
            python_code = self.transpiler.transpile(source)
            
            # Check for errors
            if self.transpiler.has_errors():
                for error in self.transpiler.get_errors():
                    self.log_message(f"Error: {error}", error=True)
                return
            
            self.log_message("Compilation successful!")
            self.log_message(f"Generated {len(python_code)} lines of Python code")
            
            # Show the generated Python code
            self.diagnostics_text.config(state=tk.NORMAL)
            self.diagnostics_text.delete(1.0, tk.END)
            self.diagnostics_text.insert(1.0, python_code)
            self.diagnostics_text.config(state=tk.DISABLED)
            
            # Refresh routine list
            self.refresh_routine_list()
            
        except Exception as e:
            self.log_message(f"Compilation error: {str(e)}", error=True)
            messagebox.showerror("Error", f"Compilation failed: {str(e)}")
    
    def run_script(self):
        """Run the current script"""
        if not self.current_file:
            messagebox.showwarning("Warning", "Please save the file first")
            return
        
        try:
            # Compile first
            self.compile_script()
            
            # If there were errors, don't run
            if self.transpiler.has_errors():
                return
            
            # Initialize runtime
            TRPRuntimeInstance.create_context()
            TRPRuntimeInstance.set_player(1)
            
            # Load the script
            if not TRPRuntimeInstance.load_from_file(self.current_file):
                self.log_message(f"Error loading script: {TRPRuntimeInstance.exception_message}", error=True)
                return
            
            self.log_message("Script loaded successfully")
            
            # Try to run the main procedure
            if TRPRuntimeInstance.procedure_exists('MAIN'):
                result = TRPRuntimeInstance.run_procedure('MAIN', [])
                self.log_message(f"MAIN procedure executed: {result}")
            else:
                self.log_message("No MAIN procedure found")
            
        except Exception as e:
            self.log_message(f"Runtime error: {str(e)}", error=True)
            messagebox.showerror("Error", f"Runtime error: {str(e)}")
    
    def refresh_routine_list(self):
        """Refresh the list of routines in the script"""
        try:
            source = self.source_editor.get(1.0, tk.END)
            routines = self.transpiler.extract_routines(source)
            
            self.routines_listbox.delete(0, tk.END)
            for routine in routines:
                self.routines_listbox.insert(tk.END, routine)
        except Exception as e:
            self.log_message(f"Error refreshing routine list: {str(e)}", error=True)
    
    def on_routine_selected(self, event=None):
        """Handle routine selection"""
        selection = self.routines_listbox.curselection()
        if selection:
            routine_name = self.routines_listbox.get(selection[0])
            self.log_message(f"Selected routine: {routine_name}")
            
            # Find and highlight the routine in the source
            self.highlight_routine(routine_name)
    
    def highlight_routine(self, routine_name):
        """Highlight a routine in the source editor"""
        source = self.source_editor.get(1.0, tk.END)
        lines = source.split('\n')
        
        for i, line in enumerate(lines):
            if routine_name in line and ('procedure' in line.lower() or 'function' in line.lower()):
                # Found the routine definition
                self.source_editor.tag_remove('highlight', 1.0, tk.END)
                self.source_editor.tag_add('highlight', f"{i+1}.0", f"{i+1}.end")
                self.source_editor.tag_config('highlight', background='yellow')
                self.source_editor.see(f"{i+1}.0")
                break
    
    def on_api_double_click(self, event=None):
        """Handle API tree double click"""
        item = self.api_tree.selection()
        if item:
            item_text = self.api_tree.item(item, 'text')
            # Insert the function name at the cursor position
            self.source_editor.insert(tk.INSERT, item_text)
            self.log_message(f"Inserted: {item_text}")
    
    def show_api_help(self):
        """Show API help"""
        messagebox.showinfo("API Help", "TRP API Functions:\n\n" +
                           "Territory: TName, TOwner, TArmies, ...\n"
                           "Player: PMe, PName, PProgram, ...\n"
                           "Continent: COwner, CBonus, ...\n"
                           "State: SConquest, SPlayersCount, ...\n"
                           "Utility: UMessage, ULog, ...")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About TRComp", 
                           f"TRComp - TRP Compiler/Editor\n\n"
                           f"Version: {G.s_g_app_vers}\n"
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
    
    def log_message(self, message, error=False):
        """Log a message to the diagnostics"""
        self.diagnostics_text.config(state=tk.NORMAL)
        if error:
            self.diagnostics_text.insert(tk.END, f"ERROR: {message}\n", 'error')
        else:
            self.diagnostics_text.insert(tk.END, f"{message}\n")
        self.diagnostics_text.see(tk.END)
        self.diagnostics_text.config(state=tk.DISABLED)
        
        # Update status bar
        self.status_label.config(text=message)


def main():
    """Main entry point for TRComp"""
    if not TKINTER_AVAILABLE:
        print("Error: Tkinter is required to run TRComp.")
        print("Install it with: pip install tk")
        sys.exit(1)
    
    root = tk.Tk()
    app = TRCompGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()

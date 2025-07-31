import customtkinter as ctk
from tkinter import simpledialog, messagebox
import os
import time
import threading
from pynput.keyboard import Controller, Key, Listener
from pynput.mouse import Button, Controller as MouseController
import platform
import sys

from finviz_scraper import main as run_scraper

class TickerNode:
    """Node for the circular doubly-linked list."""
    def __init__(self, symbol):
        self.symbol = symbol
        self.next = None
        self.prev = None

class TickerLinkedList:
    """Circular doubly-linked list to manage ticker symbols."""
    def __init__(self):
        self.head = None

    def add(self, symbol):
        """Add a ticker symbol to the circular list."""
        new_node = TickerNode(symbol)
        if not self.head:
            self.head = new_node
            self.head.next = self.head
            self.head.prev = self.head
        else:
            tail = self.head.prev
            tail.next = new_node
            new_node.prev = tail
            new_node.next = self.head
            self.head.prev = new_node

    def remove(self, symbol):
        """Remove a ticker symbol from the circular list."""
        if not self.head:
            return False  # Empty list
        current = self.head
        while True:
            if current.symbol == symbol:
                if current == self.head and current.next == self.head:
                    # Only one node in the list
                    self.head = None
                else:
                    current.prev.next = current.next
                    current.next.prev = current.prev
                    if current == self.head:
                        self.head = current.next
                return True
            current = current.next
            if current == self.head:
                break
        return False

    def __iter__(self):
        """Iterate through the list."""
        current = self.head
        if not current:
            return
        while True:
            yield current.symbol
            current = current.next
            if current == self.head:
                break

class TypingProgram:
    def __init__(self):
        """Initialize the program, load ticker symbols, and set up the GUI."""
        self.symbol_widgets = {}
        scraped_tickers = run_scraper()

        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))

        # Load backup tickers from original.txt
        backup_path = os.path.join(base_path, "original.txt")
        backup_tickers = []
        if os.path.exists(backup_path):
            with open(backup_path, "r") as backup_file:
                backup_tickers = [line.strip().upper() for line in backup_file if line.strip()]

        # Load excluded tickers from excluded.txt (new!)
        excluded_path = os.path.join(base_path, "excluded.txt")
        excluded_tickers = []
        if os.path.exists(excluded_path):
            with open(excluded_path, "r") as excl_file:
                excluded_tickers = [line.strip().upper() for line in excl_file if line.strip()]

        # Combine scraped + backup tickers
        combined_tickers = sorted(set(ticker.upper() for ticker in scraped_tickers + backup_tickers))

        # Filter out excluded tickers
        filtered_tickers = [t for t in combined_tickers if t not in excluded_tickers]

        # Write filtered tickers to original_and_fetched.txt
        data_path = os.path.join(base_path, "original_and_fetched.txt")
        with open(data_path, "w") as f:
            for ticker in filtered_tickers:
                f.write(ticker + "\n")


        self.load_ticker_symbols()
        self.controller = Controller()
        self.mouse = MouseController()
        self.current_node = self.ticker_symbols.head if self.ticker_symbols.head else None
        self.last_direction = None  # Tracks the last key press direction ("up" or "down")

        # Determine the appropriate modifier key for shortcuts
        if platform.system() == "Darwin":  # macOS
            self.shortcut_key = Key.cmd
        else:  # Windows/Linux
            self.shortcut_key = Key.ctrl_l
        
        self.create_gui()

    def load_ticker_symbols(self):
        """Load ticker symbols into a circular doubly-linked list."""
        self.ticker_symbols = TickerLinkedList()

        # Get the directory of the running script or executable
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        data_path = os.path.join(base_path, "original_and_fetched.txt")

        # Check if the file exists; if not, create it
        if not os.path.exists(data_path):
            with open(data_path, "w") as file:
                pass  # Create an empty file

        # Load existing ticker symbols
        with open(data_path, "r") as file:
            for line in file:
                self.ticker_symbols.add(line.strip().upper())

    def save_ticker_symbols(self):
        """Save the ticker symbols from the linked list back to the file."""
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        data_path = os.path.join(base_path, "original_and_fetched.txt")

        with open(data_path, "w") as file:
            for symbol in self.ticker_symbols:
                file.write(symbol + "\n")

    def add_ticker_symbol(self):
        """Prompt the user to input a new ticker symbol using a custom dialog."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add Ticker Symbol")
        dialog.geometry("300x150")

        label = ctk.CTkLabel(dialog, text="Enter the new ticker symbol:", font=("Arial", 14))
        label.pack(pady=10)

        entry = ctk.CTkEntry(dialog, width=200)
        entry.pack(pady=10)

        def on_submit():
            new_ticker = entry.get().strip().upper()
            if not new_ticker:
                dialog.destroy()
                return

            def do_add():
                self.ticker_symbols.add(new_ticker)
                self.save_ticker_symbols()

                # Save to original.txt
                base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
                original_path = os.path.join(base_path, "original.txt")
                with open(original_path, "a") as orig_file:
                    orig_file.write(new_ticker + "\n")

                # Back to main thread
                self.root.after(0, lambda: finalize_add(new_ticker))

            def finalize_add(ticker):
                self._create_symbol_row(ticker)
                messagebox.showinfo("Success", f"Added '{ticker}' to the list.")
                dialog.destroy()

            threading.Thread(target=do_add).start()

        submit_button = ctk.CTkButton(dialog, text="Submit", command=on_submit)
        submit_button.pack(pady=10)

        dialog.grab_set()  # Make the dialog modal

    def remove_ticker_symbol(self, ticker_to_remove=None):
        """Remove a ticker symbol directly from the list."""
        if not ticker_to_remove:
            return

        def do_removal():
            removed = self.ticker_symbols.remove(ticker_to_remove.upper())
            if removed:
                base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
                excluded_path = os.path.join(base_path, "excluded.txt")

                # Load current excluded tickers
                excluded_tickers = []
                if os.path.exists(excluded_path):
                    with open(excluded_path, "r") as excl_file:
                        excluded_tickers = [line.strip().upper() for line in excl_file if line.strip()]

                ticker_upper = ticker_to_remove.upper()

                # Add to excluded if not already present
                if ticker_upper not in excluded_tickers:
                    with open(excluded_path, "a") as excl_file:
                        excl_file.write(ticker_upper + "\n")

                # Now save the filtered ticker list (excluding excluded tickers)
                # Reload combined tickers from original.txt + scraper
                # (You can reuse your init logic or just save current in-memory list)
                self.save_ticker_symbols()  # This saves current linked list to original_and_fetched.txt

                # UI update on main thread
                self.root.after(0, lambda: self._finalize_removal(ticker_upper))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Ticker symbol not found."))


        threading.Thread(target=do_removal).start()

    def _finalize_removal(self, symbol):
        """Update UI after background removal completes."""
        frame = self.symbol_widgets.pop(symbol, None)
        if frame:
            frame.destroy()
        messagebox.showinfo("Success", f"Removed '{symbol}' from the list.")
        self.root.focus_force()

    def remove_all_ticker_symbols(self):
        """Remove all ticker symbols from the list."""
        if messagebox.askyesno("Confirm", "Are you sure you want to remove all ticker symbols?"):
            self.ticker_symbols = TickerLinkedList()  # Reset the linked list
            self.save_ticker_symbols()

            # Also clear original.txt
            base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
            original_path = os.path.join(base_path, "original.txt")

            if os.path.exists(original_path):
                with open(original_path, "w") as f:
                    pass  # Empty the file

            self.update_ticker_list()
            messagebox.showinfo("Success", "All ticker symbols have been removed.")
            self.root.focus_force()

    def bulk_add_ticker_symbols(self):
        """Prompt the user to input multiple ticker symbols and add them."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Bulk Add Ticker Symbols")
        dialog.geometry("400x300")

        label = ctk.CTkLabel(dialog, text="Enter ticker symbols (comma-separated):", font=("Arial", 14))
        label.pack(pady=10)

        text_area = ctk.CTkTextbox(dialog, height=150, width=350)
        text_area.pack(pady=10)

        def on_submit():
            symbols = text_area.get("1.0", "end").strip().upper()
            if not symbols:
                dialog.destroy()
                return

            symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]

            def do_bulk_add():
                for symbol in symbol_list:
                    self.ticker_symbols.add(symbol)
                self.save_ticker_symbols()

                # Save to original.txt
                base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
                original_path = os.path.join(base_path, "original.txt")
                with open(original_path, "a") as orig_file:
                    for symbol in symbol_list:
                        orig_file.write(symbol + "\n")

                # Back to main thread
                self.root.after(0, lambda: finalize_bulk_add(symbol_list))

            def finalize_bulk_add(symbols_added):
                for symbol in symbols_added:
                    self._create_symbol_row(symbol)
                messagebox.showinfo("Success", "Added all valid symbols to the list.")
                dialog.destroy()

            threading.Thread(target=do_bulk_add).start()

        submit_button = ctk.CTkButton(dialog, text="Submit", command=on_submit)
        submit_button.pack(pady=10)

        dialog.grab_set()

    def create_gui(self):
        """Create the main GUI window."""
        self.root = ctk.CTk()
        self.root.title("Ticker Symbol Manager")
        self.root.geometry("900x800")

        ctk.set_appearance_mode("light")

        title_label = ctk.CTkLabel(self.root, text="Stock Ticker Manager", font=("Arial", 28, "bold"))
        title_label.pack(pady=20)

        self.scrollable_frame = ctk.CTkScrollableFrame(self.root, height=600, width=850)
        self.scrollable_frame.pack(pady=10)

        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(pady=10)

        add_button = ctk.CTkButton(button_frame, text="Add Ticker Symbol", command=self.add_ticker_symbol, width=200)
        add_button.grid(row=0, column=0, padx=10)

        bulk_add_button = ctk.CTkButton(button_frame, text="Bulk Add Ticker Symbols", command=self.bulk_add_ticker_symbols, width=200)
        bulk_add_button.grid(row=0, column=1, padx=10)

        remove_all_button = ctk.CTkButton(button_frame, text="Remove All", command=self.remove_all_ticker_symbols, width=200)
        remove_all_button.grid(row=0, column=2, padx=10)

        self.update_ticker_list()

    def update_ticker_list(self, full_refresh=True):
        """Update the ticker list display. Supports partial updates."""
        if full_refresh:
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self.symbol_widgets.clear()

            for symbol in self.ticker_symbols:
                self._create_symbol_row(symbol)

    def _create_symbol_row(self, symbol):
        """Create a row in the GUI for a single ticker symbol."""
        if symbol in self.symbol_widgets:
            return  # already added

        symbol_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#f0f0f0", height=50)
        symbol_frame.pack(fill="x", pady=5)
        self.symbol_widgets[symbol] = symbol_frame

        symbol_frame.bind("<Enter>", lambda e, frame=symbol_frame: frame.configure(fg_color="#d3d3d3"))
        symbol_frame.bind("<Leave>", lambda e, frame=symbol_frame: frame.configure(fg_color="#f0f0f0"))

        ticker_label = ctk.CTkLabel(symbol_frame, text=symbol, font=("Arial", 16), anchor="w")
        ticker_label.place(relx=0.02, rely=0.5, anchor="w")

        remove_button = ctk.CTkButton(symbol_frame, text="Remove", width=100,
                                    command=lambda sym=symbol: self.remove_ticker_symbol(sym))
        remove_button.place(relx=0.95, rely=0.5, anchor="e")

    def terminate_program(self):
        """Terminate the keyboard listener and close the GUI."""
        if hasattr(self, "listener"):
            self.listener.stop()
        self.root.destroy()

    def on_press(self, key):
        """Handle key press events to trigger actions based on arrow key inputs."""
        try:
            if key == Key.down:
                if self.current_node:
                    if self.last_direction == "up":
                        # Reset to the node after the current one when switching direction
                        self.current_node = self.current_node.next.next
                    self.type_word(self.current_node.symbol)  # Type the current ticker
                    self.current_node = self.current_node.next  # Move to the next node
                    self.last_direction = "down"

            elif key == Key.up:
                if self.current_node:
                    if self.last_direction == "down":
                        # Reset to the node before the current one when switching direction
                        self.current_node = self.current_node.prev.prev
                    self.type_word(self.current_node.symbol)  # Type the current ticker
                    self.current_node = self.current_node.prev  # Move to the previous node
                    self.last_direction = "up"

            elif key == Key.left:
                self.controller.press(self.shortcut_key)
                self.controller.press('w')
                self.controller.release('w')
                self.controller.release(self.shortcut_key)

            elif key == Key.right:
                if self.last_direction in ["up", "down"]:
                    self.controller.press(self.shortcut_key)
                    self.controller.press('t')
                    self.controller.release('t')
                    self.controller.release(self.shortcut_key)
                    
                    # Determine the word to type based on the direction
                    next_symbol = self.current_node.next.symbol if self.last_direction == "up" else self.current_node.prev.symbol
                    word_to_type = next_symbol + ' stock'
                    
                    for char in word_to_type:
                        self.controller.type(char)
                        time.sleep(0.01)
                    
                    # Press Enter
                    self.controller.press(Key.enter)
                    self.controller.release(Key.enter)

        except AttributeError:
            pass

    def type_word(self, word):
        """Type a given word using the keyboard controller."""
        for char in word:
            self.controller.type(char)
        self.controller.press(Key.enter)
        self.controller.release(Key.enter)

    def start(self):
        """Start the program with a keyboard listener and the GUI."""
        self.listener = Listener(on_press=self.on_press)
        threading.Thread(target=self.listener.start).start()
        self.root.mainloop()

# Start the TypingProgram
if __name__ == "__main__":
    typing_program = TypingProgram()
    typing_program.start()
import customtkinter as ctk
from tkinter import simpledialog, messagebox
import os
import time
import threading
from pynput.keyboard import Controller, Key, Listener
from pynput.mouse import Button, Controller as MouseController
import platform
import sys

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
        data_path = os.path.join(base_path, "ticker_symbols.txt")

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
        data_path = os.path.join(base_path, "ticker_symbols.txt")

        with open(data_path, "w") as file:
            for symbol in self.ticker_symbols:
                file.write(symbol + "\n")

    def add_ticker_symbol(self):
        """Prompt the user to input a new ticker symbol and add it to the list."""
        new_ticker = simpledialog.askstring("Add Ticker Symbol", "Enter the new ticker symbol:")
        if new_ticker:
            self.ticker_symbols.add(new_ticker.upper())
            self.save_ticker_symbols()
            messagebox.showinfo("Success", f"Added '{new_ticker.upper()}' to the list.")
            self.update_ticker_list()
            self.root.focus_force()

    def remove_ticker_symbol(self, ticker_to_remove=None):
        """Remove a ticker symbol directly from the list."""
        if ticker_to_remove:
            if self.ticker_symbols.remove(ticker_to_remove.upper()):
                self.save_ticker_symbols()
                messagebox.showinfo("Success", f"Removed '{ticker_to_remove.upper()}' from the list.")
                self.update_ticker_list()
                self.root.focus_force()
            else:
                messagebox.showerror("Error", "Ticker symbol not found.")

    def remove_all_ticker_symbols(self):
        """Remove all ticker symbols from the list."""
        if messagebox.askyesno("Confirm", "Are you sure you want to remove all ticker symbols?"):
            self.ticker_symbols = TickerLinkedList()  # Reset the linked list
            self.save_ticker_symbols()
            self.update_ticker_list()
            messagebox.showinfo("Success", "All ticker symbols have been removed.")
            self.root.focus_force()

    def create_gui(self):
        """Create the main GUI window."""
        self.root = ctk.CTk()
        self.root.title("Ticker Symbol Manager")
        self.root.geometry("800x700")

        ctk.set_appearance_mode("light")

        title_label = ctk.CTkLabel(self.root, text="Stock Ticker Manager", font=("Arial", 28, "bold"))
        title_label.pack(pady=20)

        self.scrollable_frame = ctk.CTkScrollableFrame(self.root, height=500, width=750)
        self.scrollable_frame.pack(pady=10)

        add_button = ctk.CTkButton(self.root, text="Add Ticker Symbol", command=self.add_ticker_symbol, width=200)
        add_button.pack(pady=10)

        remove_all_button = ctk.CTkButton(self.root, text="Remove All", command=self.remove_all_ticker_symbols, width=200)
        remove_all_button.pack(pady=10)

        self.update_ticker_list()

    def update_ticker_list(self):
        """Update the ticker list display with the current symbols."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for symbol in self.ticker_symbols:
            symbol_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#f0f0f0", height=50)
            symbol_frame.pack(fill="x", pady=5)

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

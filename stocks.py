import customtkinter as ctk
from tkinter import simpledialog, messagebox
import os
import time
import threading
from pynput.keyboard import Controller, Key, Listener
from pynput.mouse import Button, Controller as MouseController
import platform

class TypingProgram:
    def __init__(self):
        """Initialize the program, load ticker symbols, and set up the GUI."""
        self.load_ticker_symbols()
        self.current_index = 0
        self.prev_index = (len(self.ticker_symbols) - 1) % len(self.ticker_symbols)
        self.prev_key_value = ""
        self.controller = Controller()
        self.mouse = MouseController()
        
        # Determine the appropriate modifier key for shortcuts
        if platform.system() == "Darwin":  # macOS
            self.shortcut_key = Key.cmd
        else:  # Windows/Linux
            self.shortcut_key = Key.ctrl_l
        
        self.create_gui()

    def load_ticker_symbols(self):
        """Load ticker symbols from a file, or initialize an empty list if the file doesn't exist."""
        if os.path.exists("ticker_symbols.txt"):
            with open("ticker_symbols.txt", "r") as file:
                self.ticker_symbols = [line.strip() for line in file.readlines()]
        else:
            self.ticker_symbols = []

    def save_ticker_symbols(self):
        """Save the current list of ticker symbols to a file."""
        with open("ticker_symbols.txt", "w") as file:
            for ticker_symbol in self.ticker_symbols:
                file.write(ticker_symbol + "\n")

    def add_ticker_symbol(self):
        """Prompt the user to input a new ticker symbol and add it to the list."""
        new_ticker = simpledialog.askstring("Add Ticker Symbol", "Enter the new ticker symbol:")
        if new_ticker:
            self.ticker_symbols.append(new_ticker.upper())
            self.save_ticker_symbols()
            messagebox.showinfo("Success", f"Added '{new_ticker.upper()}' to the list.")
            self.update_ticker_list()
            self.root.focus_force()

    def remove_ticker_symbol(self, ticker_to_remove=None):
        """Remove a ticker symbol directly from the list."""
        if ticker_to_remove:
            ticker_to_remove_upper = ticker_to_remove.upper()
            for symbol in self.ticker_symbols:
                if symbol.upper() == ticker_to_remove_upper:
                    self.ticker_symbols.remove(symbol)
                    self.save_ticker_symbols()
                    messagebox.showinfo("Success", f"Removed '{symbol}' from the list.")
                    self.update_ticker_list()
                    self.root.focus_force()
                    return
        messagebox.showerror("Error", "Ticker symbol not found.")

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
        add_button.pack(pady=20)

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
                # Down arrow key: Type current ticker symbol and move to the next
                if self.prev_key_value == "up":  # Special handling for up-down sequence
                    self.prev_index = (self.current_index + 1) % len(self.ticker_symbols)
                    self.current_index = (self.current_index + 2) % len(self.ticker_symbols)
                    self.prev_key_value = "up"
                    self.type_word(self.current_index)
                    print("Current Index: ", self.current_index)
                    print("Prev Index: ", self.prev_index)
                    return

                self.type_word(self.current_index)
                self.prev_index = self.current_index
                self.current_index = (self.current_index + 1) % len(self.ticker_symbols)
                self.prev_key_value = "down"

            elif key == Key.up:
                # Up arrow key: Type the previous ticker symbol
                if self.prev_key_value == "down":  # Special handling for down-up sequence
                    self.current_index = self.prev_index
                    self.prev_index = (self.prev_index - 1 + len(self.ticker_symbols)) % len(self.ticker_symbols)
                    self.prev_key_value = "down"
                    self.type_word(self.prev_index)
                    return
                print("Current Index: ", self.current_index)
                print("Prev Index: ", self.prev_index)
                self.type_word(self.current_index)
                self.current_index = self.prev_index
                self.prev_index = (self.prev_index - 1 + len(self.ticker_symbols)) % len(self.ticker_symbols)
                self.prev_key_value = "up"

            elif key == Key.left:
                self.controller.press(self.shortcut_key)
                self.controller.press('w')
                self.controller.release('w')
                self.controller.release(self.shortcut_key)

            elif key == Key.right:
                current_ticker = self.ticker_symbols[self.prev_index]
                print("Prev Index: ", self.ticker_symbols[self.prev_index])
                print("Current Index: ", self.ticker_symbols[self.current_index])

                self.controller.press(self.shortcut_key)
                self.controller.press('t')
                self.controller.release('t')
                self.controller.release(self.shortcut_key)

                word_to_type = current_ticker + ' stock'
                for char in word_to_type:
                    self.controller.type(char)
                    time.sleep(0.01)

                self.controller.press(Key.enter)
                self.controller.release(Key.enter)

                time.sleep(1)

        except AttributeError:
            pass

    def type_word(self, index):
        """Type the ticker symbol at the given index."""
        word_to_type = self.ticker_symbols[index]
        for char in word_to_type:
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

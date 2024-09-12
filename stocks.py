from pynput.keyboard import Controller, Key, Listener
import time
import os
import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
from pynput.mouse import Button, Controller as MouseController

class TypingProgram:
    def __init__(self):
        """Initialize the program, load ticker symbols, set defaults, and create the GUI."""
        self.load_ticker_symbols()
        self.current_index = 0
        self.prev_index = 0
        self.prev_key_value = ""
        self.mouse = MouseController()
        self.controller = Controller()
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

    def type_word(self, index):
        """Type out the ticker symbol at the given index followed by the 'Enter' key."""
        word_to_type = self.ticker_symbols[index]
        for char in word_to_type:
            self.controller.type(char)
            time.sleep(0.01)  # Pause slightly between each character
        # Simulate pressing the 'Enter' key
        self.controller.press(Key.enter)
        self.controller.release(Key.enter)

    def add_ticker_symbol(self):
        """Prompt the user to input a new ticker symbol and add it to the list."""
        new_ticker = simpledialog.askstring("Add Ticker Symbol", "Enter the new ticker symbol:")
        if new_ticker:
            self.ticker_symbols.append(new_ticker.upper())
            self.save_ticker_symbols()
            messagebox.showinfo("Ticker Symbol Added", f"Added '{new_ticker.upper()}' to the ticker symbols list.")

    def remove_ticker_symbol(self):
        """Prompt the user to remove a ticker symbol from the list."""
        if self.ticker_symbols:
            remove_ticker = simpledialog.askstring("Remove Ticker Symbol", "Enter the ticker symbol to remove:")
            if remove_ticker and remove_ticker.upper() in self.ticker_symbols:
                self.ticker_symbols.remove(remove_ticker.upper())
                self.save_ticker_symbols()
                messagebox.showinfo("Ticker Symbol Removed", f"Removed '{remove_ticker.upper()}' from the ticker symbols list.")
            else:
                messagebox.showwarning("Invalid Ticker Symbol", f"'{remove_ticker}' is not in the ticker symbols list.")
        else:
            messagebox.showwarning("No Ticker Symbols", "No ticker symbols to remove.")

    def create_gui(self):
        """Create the main GUI window for adding/removing ticker symbols."""
        self.root = tk.Tk()
        self.root.title("Ticker Symbol Typing Program")
        self.root.geometry("300x200")

        add_button = tk.Button(self.root, text="Add Ticker Symbol", command=self.add_ticker_symbol)
        add_button.pack(pady=30)

        remove_button = tk.Button(self.root, text="Remove Ticker Symbol", command=self.remove_ticker_symbol)
        remove_button.pack(pady=30)

        self.status_label = tk.Label(self.root, text="")
        self.status_label.pack(pady=10)

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.terminate_program)

    def terminate_program(self):
        """Terminate the listener and close the GUI when the window is closed."""
        self.listener.stop()  # Stop the keyboard listener thread
        self.root.destroy()   # Destroy the GUI window

    def on_press(self, key):
        """Handle key press events to trigger actions based on arrow key inputs."""
        try:
            if key == Key.down:
                # Down arrow key: Type current ticker symbol and move to the next
                if self.prev_key_value == "up":  # Special handling for up-down sequence
                    self.prev_index = self.current_index
                    self.current_index = (self.current_index + 1) % len(self.ticker_symbols)
                    self.prev_key_value = "up"
                    self.type_word(self.current_index)
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

                self.current_index = self.prev_index
                self.type_word(self.prev_index)
                self.prev_index = (self.prev_index - 1 + len(self.ticker_symbols)) % len(self.ticker_symbols)
                self.prev_key_value = "up"

            elif key == Key.left:
                # Left arrow key: Close current tab and switch to the previous tab
                self.controller.press(Key.ctrl_l)
                self.controller.press('w')
                self.controller.release('w')
                self.controller.release(Key.ctrl_l)

                self.controller.press(Key.ctrl_l)
                self.controller.press(Key.shift_l)
                self.controller.press(Key.tab)
                self.controller.release(Key.tab)
                self.controller.release(Key.shift_l)
                self.controller.release(Key.ctrl_l)

                # Simulate mouse click at a specific location
                self.mouse.position = (500, 200)  # Replace with actual coordinates
                self.mouse.click(Button.left, 1)

            elif key == Key.right:
                # Right arrow key: Open a new tab, type the ticker symbol + ' stock'
                current_ticker = self.ticker_symbols[self.prev_index]
                
                self.controller.press(Key.ctrl_l)
                self.controller.press('t')
                self.controller.release('t')
                self.controller.release(Key.ctrl_l)

                # Type the ticker symbol and ' stock'
                word_to_type = current_ticker + ' stock'
                for char in word_to_type:
                    self.controller.type(char)
                    time.sleep(0.01)

                self.controller.press(Key.enter)
                self.controller.release(Key.enter)

                time.sleep(1)

                # Simulate mouse click at a specific location
                self.mouse.position = (590, 530)  # Replace with actual coordinates
                self.mouse.click(Button.left, 1)

        except AttributeError:
            pass  # Ignore special keys that don't have a character representation

    def start(self):
        """Start the keyboard listener and launch the GUI."""
        self.listener = Listener(on_press=self.on_press)
        threading.Thread(target=self.listener.start).start()  # Start listener in a separate thread
        time.sleep(0.1)  # Short delay to ensure listener is ready
        self.root.mainloop()  # Start the GUI main loop

# Start the TypingProgram
if __name__ == "__main__":
    typing_program = TypingProgram()
    typing_program.start()

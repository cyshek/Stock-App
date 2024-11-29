import customtkinter as ctk
from tkinter import simpledialog, messagebox
import os
import threading
from pynput.keyboard import Controller, Key, Listener

class TypingProgram:
    def __init__(self):
        """Initialize the program, load ticker symbols, and set up the GUI."""
        self.load_ticker_symbols()
        self.current_index = 0
        self.prev_index = 0
        self.prev_key_value = ""
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

    def add_ticker_symbol(self):
        """Prompt the user to input a new ticker symbol and add it to the list."""
        new_ticker = simpledialog.askstring("Add Ticker Symbol", "Enter the new ticker symbol:")
        if new_ticker:
            self.ticker_symbols.append(new_ticker.upper())
            self.save_ticker_symbols()
            messagebox.showinfo("Success", f"Added '{new_ticker.upper()}' to the list.")
            self.update_ticker_list()  # Automatically refresh the list

    def remove_ticker_symbol(self, ticker_to_remove=None):
        """Remove a ticker symbol directly from the list."""
        if ticker_to_remove and ticker_to_remove.upper() in self.ticker_symbols:
            self.ticker_symbols.remove(ticker_to_remove.upper())
            self.save_ticker_symbols()
            messagebox.showinfo("Success", f"Removed '{ticker_to_remove.upper()}' from the list.")
            self.update_ticker_list()  # Automatically refresh the list
        else:
            messagebox.showerror("Error", "Ticker symbol not found.")

    def create_gui(self):
        """Create the main GUI window with a scrollable ticker list on the main page."""
        self.root = ctk.CTk()
        self.root.title("Ticker Symbol Manager")
        self.root.geometry("800x700")  # Adjusted GUI size

        # Main page layout
        title_label = ctk.CTkLabel(self.root, text="Stock Ticker Manager", font=("Arial", 28, "bold"))
        title_label.pack(pady=20)

        # Scrollable frame for ticker list
        self.scrollable_frame = ctk.CTkScrollableFrame(self.root, height=500, width=750)
        self.scrollable_frame.pack(pady=10)

        # Add button at the bottom
        add_button = ctk.CTkButton(self.root, text="Add Ticker Symbol", command=self.add_ticker_symbol, width=200)
        add_button.pack(pady=20)

        self.update_ticker_list()

    def update_ticker_list(self):
        """Update the ticker list display with the current symbols."""
        # Clear previous widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Display all ticker symbols
        for symbol in self.ticker_symbols:
            # Create a frame for each ticker symbol row
            symbol_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#f0f0f0")  # Default background
            symbol_frame.pack(fill="x", pady=2)

            # Apply hover effect to the entire frame
            symbol_frame.bind("<Enter>", lambda e, frame=symbol_frame: frame.configure(fg_color="#d3d3d3"))
            symbol_frame.bind("<Leave>", lambda e, frame=symbol_frame: frame.configure(fg_color="#f0f0f0"))

            # Add ticker symbol label
            ticker_label = ctk.CTkLabel(symbol_frame, text=symbol, width=500, anchor="w", font=("Arial", 16))
            ticker_label.pack(side="left", padx=10)

            # Add remove button
            remove_button = ctk.CTkButton(symbol_frame, text="Remove", width=100,
                                          command=lambda sym=symbol: self.remove_ticker_symbol(sym))
            remove_button.pack(side="right", padx=10)

    def terminate_program(self):
        """Terminate the keyboard listener and close the GUI."""
        if hasattr(self, "listener"):
            self.listener.stop()
        self.root.destroy()

    def on_press(self, key):
        """Handle key press events to manage the typing of ticker symbols."""
        try:
            if key == Key.down:
                self.type_word(self.current_index)
                self.prev_index = self.current_index
                self.current_index = (self.current_index + 1) % len(self.ticker_symbols)

            elif key == Key.up:
                self.type_word(self.prev_index)
                self.current_index = self.prev_index
                self.prev_index = (self.prev_index - 1 + len(self.ticker_symbols)) % len(self.ticker_symbols)
        except IndexError:
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

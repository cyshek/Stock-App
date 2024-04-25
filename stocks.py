from pynput.keyboard import Controller, Key, Listener
import time
import sys
import os
import tkinter as tk
from tkinter import messagebox, simpledialog
import threading

class TypingProgram:
    def __init__(self):
        self.load_ticker_symbols()
        self.current_index = 0
        self.prev_index = 0
        self.prev_key_value = ""
        self.controller = Controller()
        self.create_gui()

    def load_ticker_symbols(self):
        if os.path.exists("ticker_symbols.txt"):
            with open("ticker_symbols.txt", "r") as file:
                self.ticker_symbols = [line.strip() for line in file.readlines()]
        else:
            self.ticker_symbols = []

    def save_ticker_symbols(self):
        with open("ticker_symbols.txt", "w") as file:
            for ticker_symbol in self.ticker_symbols:
                file.write(ticker_symbol + "\n")

    def type_word(self, index):
        word_to_type = self.ticker_symbols[index]
        for char in word_to_type:
            self.controller.type(char)
            time.sleep(0.01)
        # Type the 'enter' key
        self.controller.press(Key.enter)
        self.controller.release(Key.enter)

    def add_ticker_symbol(self):
        new_ticker = simpledialog.askstring("Add Ticker Symbol", "Enter the new ticker symbol:")
        if new_ticker:
            self.ticker_symbols.append(new_ticker.upper())
            self.save_ticker_symbols()
            messagebox.showinfo("Ticker Symbol Added", f"Added '{new_ticker.upper()}' to the ticker symbols list.")

    def remove_ticker_symbol(self):
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
        # Stop the listener thread
        self.listener.stop()

        # Close the GUI
        self.root.destroy()


    def on_press(self, key):
        try:
            if key == Key.down:
                if self.prev_key_value == "up":
                    # Move to the next word
                    self.prev_index = self.current_index
                    self.current_index = (self.current_index + 1) % len(self.ticker_symbols)
                    self.prev_key_value = "up"

                    # Type the current word
                    self.type_word(self.current_index)
                    return

                # Type the current word
                self.type_word(self.current_index)

                # Move to the next word
                self.prev_index = self.current_index
                self.current_index = (self.current_index + 1) % len(self.ticker_symbols)
                self.prev_key_value = "down"

            elif key == Key.up:
                if self.prev_key_value == "down":
                    # Move to the previous word
                    self.current_index = self.prev_index
                    self.prev_index = (self.prev_index - 1 + len(self.ticker_symbols)) % len(self.ticker_symbols)
                    self.prev_key_value = "down"

                    # Type the previous word
                    self.type_word(self.prev_index)
                    return

                # Move to the previous word
                self.current_index = self.prev_index
                # Type the previous word
                self.type_word(self.prev_index)

                # Update the previous index
                self.prev_index = (self.prev_index - 1 + len(self.ticker_symbols)) % len(self.ticker_symbols)
                self.prev_key_value = "up"

        except AttributeError:
            pass

    def start(self):
        # Create the listener
        self.listener = Listener(on_press=self.on_press)

        # Start the listener in a separate thread
        threading.Thread(target=self.listener.start).start()

        # Start the GUI main loop
        self.root.mainloop()

    def start_listener(self):
        with Listener(on_press=self.on_press) as listener:
            listener.join()

# Create an instance of TypingProgram and start it
typing_program = TypingProgram()
typing_program.start()

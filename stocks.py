import customtkinter as ctk
from tkinter import messagebox
import os
import time
import threading
from pynput.keyboard import Controller, Key, Listener
from pynput.mouse import Controller as MouseController
import platform
import sys

from finviz_scraper import main as run_scraper

class TickerNode:
    def __init__(self, symbol):
        self.symbol = symbol
        self.next = None
        self.prev = None

class TickerLinkedList:
    def __init__(self):
        self.head = None

    def add(self, symbol):
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
        if not self.head:
            return False
        current = self.head
        while True:
            if current.symbol == symbol:
                if current == self.head and current.next == self.head:
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
        self.symbol_widgets = {}

        self.stock_url = "https://finviz.com/screener.ashx?v=111&f=cap_largeover,ta_alltime_b40h"
        self.etf_url   = "https://finviz.com/screener.ashx?v=111&f=ind_exchangetradedfund,sh_avgvol_o1000,ta_alltime_b40h"

        scraped_tickers = run_scraper(self.stock_url, self.etf_url)
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))

        backup_path = os.path.join(base_path, "original.txt")
        backup_tickers = []
        if os.path.exists(backup_path):
            with open(backup_path, "r") as backup_file:
                backup_tickers = [line.strip().upper() for line in backup_file if line.strip()]

        excluded_path = os.path.join(base_path, "excluded.txt")
        excluded_tickers = []
        if os.path.exists(excluded_path):
            with open(excluded_path, "r") as excl_file:
                excluded_tickers = [line.strip().upper() for line in excl_file if line.strip()]

        combined_tickers = sorted(set(ticker.upper() for ticker in scraped_tickers + backup_tickers))

        filtered_tickers = [t for t in combined_tickers if t not in excluded_tickers]

        data_path = os.path.join(base_path, "original_and_fetched.txt")
        with open(data_path, "w") as f:
            for ticker in filtered_tickers:
                f.write(ticker + "\n")

        self.load_ticker_symbols()
        self.controller = Controller()
        self.mouse = MouseController()
        self.current_node = self.ticker_symbols.head if self.ticker_symbols.head else None
        self.last_direction = None

        if platform.system() == "Darwin":
            self.shortcut_key = Key.cmd
        else:
            self.shortcut_key = Key.ctrl_l
        
        self.create_gui()

    def load_ticker_symbols(self):
        self.ticker_symbols = TickerLinkedList()

        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        data_path = os.path.join(base_path, "original_and_fetched.txt")

        if not os.path.exists(data_path):
            with open(data_path, "w") as file:
                pass

        with open(data_path, "r") as file:
            for line in file:
                self.ticker_symbols.add(line.strip().upper())

    def save_ticker_symbols(self):
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        data_path = os.path.join(base_path, "original_and_fetched.txt")

        with open(data_path, "w") as file:
            for symbol in self.ticker_symbols:
                file.write(symbol + "\n")

    def add_ticker_symbol(self):
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

                base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
                original_path = os.path.join(base_path, "original.txt")
                with open(original_path, "a") as orig_file:
                    orig_file.write(new_ticker + "\n")

                self.root.after(0, lambda: finalize_add(new_ticker))

            def finalize_add(ticker):
                self._create_symbol_row(ticker)
                messagebox.showinfo("Success", f"Added '{ticker}' to the list.")
                dialog.destroy()

            threading.Thread(target=do_add).start()

        submit_button = ctk.CTkButton(dialog, text="Submit", command=on_submit)
        submit_button.pack(pady=10)

        dialog.grab_set()

    def remove_ticker_symbol(self, ticker_to_remove=None):
        if not ticker_to_remove:
            return

        def do_removal():
            removed = self.ticker_symbols.remove(ticker_to_remove.upper())
            if removed:
                base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
                excluded_path = os.path.join(base_path, "excluded.txt")

                excluded_tickers = []
                if os.path.exists(excluded_path):
                    with open(excluded_path, "r") as excl_file:
                        excluded_tickers = [line.strip().upper() for line in excl_file if line.strip()]

                ticker_upper = ticker_to_remove.upper()

                if ticker_upper not in excluded_tickers:
                    with open(excluded_path, "a") as excl_file:
                        excl_file.write(ticker_upper + "\n")

                self.save_ticker_symbols()
                self.root.after(0, lambda: self._finalize_removal(ticker_upper))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Ticker symbol not found."))

        threading.Thread(target=do_removal).start()

    def _finalize_removal(self, symbol):
        frame = self.symbol_widgets.pop(symbol, None)
        if frame:
            frame.destroy()
        messagebox.showinfo("Success", f"Removed '{symbol}' from the list.")
        self.root.focus_force()

    def remove_all_ticker_symbols(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to remove all ticker symbols?"):
            self.ticker_symbols = TickerLinkedList()
            self.save_ticker_symbols()

            base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
            original_path = os.path.join(base_path, "original.txt")

            if os.path.exists(original_path):
                with open(original_path, "w") as f:
                    pass

            self.update_ticker_list()
            messagebox.showinfo("Success", "All ticker symbols have been removed.")
            self.root.focus_force()

    def bulk_add_ticker_symbols(self):
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

                base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
                original_path = os.path.join(base_path, "original.txt")
                with open(original_path, "a") as orig_file:
                    for symbol in symbol_list:
                        orig_file.write(symbol + "\n")

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

    def reload_tickers_from_urls(self):
        combined = run_scraper(self.stock_url, self.etf_url)
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        data_path = os.path.join(base_path, "original_and_fetched.txt")

        with open(data_path, "w") as f:
            for sym in sorted(set(s.upper() for s in combined)):
                f.write(sym + "\n")

        self.load_ticker_symbols()
        self.update_ticker_list(full_refresh=True)
        messagebox.showinfo("Reloaded", "Tickers updated from the new URLs.")

    def create_gui(self):
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

        config_button = ctk.CTkButton(
            button_frame,
            text="Configure URLs",
            command=self.configure_urls,
            width=200
        )
        config_button.grid(row=0, column=3, padx=10)

        self.update_ticker_list()

    def update_ticker_list(self, full_refresh=True):
        if full_refresh:
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self.symbol_widgets.clear()

            for symbol in self.ticker_symbols:
                self._create_symbol_row(symbol)

    def configure_urls(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Configure Finviz URLs")

        dialog.geometry("600x300")
        dialog.minsize(500, 250)   

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth()  - dialog.winfo_reqwidth())  // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_reqheight()) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(dialog, text="Stock URL:", anchor="w").pack(fill="x", padx=20, pady=(20, 5))
        stock_entry = ctk.CTkEntry(dialog, width=560)
        stock_entry.insert(0, self.stock_url)
        stock_entry.pack(padx=20)

        ctk.CTkLabel(dialog, text="ETF URL:", anchor="w").pack(fill="x", padx=20, pady=(15, 5))
        etf_entry = ctk.CTkEntry(dialog, width=560)
        etf_entry.insert(0, self.etf_url)
        etf_entry.pack(padx=20)

        def on_submit():
            self.stock_url = stock_entry.get().strip()
            self.etf_url   = etf_entry.get().strip()
            dialog.destroy()
            self.reload_tickers_from_urls()

        save_btn = ctk.CTkButton(dialog, text="Save", command=on_submit)
        save_btn.pack(pady=20)

        dialog.grab_set()

    def _create_symbol_row(self, symbol):
        if symbol in self.symbol_widgets:
            return

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
        if hasattr(self, "listener"):
            self.listener.stop()
        self.root.destroy()

    def on_press(self, key):
        try:
            if key == Key.down:
                if self.current_node:
                    if self.last_direction == "up":
                        self.current_node = self.current_node.next.next
                    self.type_word(self.current_node.symbol)
                    self.current_node = self.current_node.next
                    self.last_direction = "down"

            elif key == Key.up:
                if self.current_node:
                    if self.last_direction == "down":
                        self.current_node = self.current_node.prev.prev
                    self.type_word(self.current_node.symbol)
                    self.current_node = self.current_node.prev
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

                    next_symbol = self.current_node.next.symbol if self.last_direction == "up" else self.current_node.prev.symbol
                    word_to_type = next_symbol + ' stock'
                    
                    for char in word_to_type:
                        self.controller.type(char)
                        time.sleep(0.01)

                    self.controller.press(Key.enter)
                    self.controller.release(Key.enter)

        except AttributeError:
            pass

    def type_word(self, word):
        for char in word:
            self.controller.type(char)
        self.controller.press(Key.enter)
        self.controller.release(Key.enter)

    def start(self):
        self.listener = Listener(on_press=self.on_press)
        threading.Thread(target=self.listener.start).start()
        self.root.mainloop()

if __name__ == "__main__":
    typing_program = TypingProgram()
    typing_program.start()

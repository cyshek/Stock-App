import customtkinter as ctk
from tkinter import messagebox
import os
import time
import threading
import platform
import sys
from pynput.keyboard import Controller, Key, Listener
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
        symbol = (symbol or "").strip().upper()
        if not symbol:
            return
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
        symbol = symbol.strip().upper()
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

    def find(self, symbol):
        if not self.head:
            return None
        current = self.head
        while True:
            if current.symbol == symbol:
                return current
            current = current.next
            if current == self.head:
                break
        return None

class TypingProgram:
    def __init__(self):
        self.symbol_widgets = {}
        self.stock_url = "https://finviz.com/screener.ashx?v=111&f=cap_largeover,ta_alltime_b40h"
        self.etf_url   = "https://finviz.com/screener.ashx?v=111&f=ind_exchangetradedfund,sh_avgvol_o1000,ta_alltime_b40h"

        self.base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.original_file = os.path.join(self.base_path, "original.txt")
        self.fetched_file  = os.path.join(self.base_path, "fetched.txt")
        self.blacklist_file = os.path.join(self.base_path, "blacklist.txt")
        self.visible_symbols = []
        self.original_ticker_symbols = TickerLinkedList()
        self.ticker_symbols = TickerLinkedList()
        self.fetched_tickers = []

        if os.path.exists(self.original_file):
            with open(self.original_file, "r") as cf:
                local_count = sum(1 for _ in cf)
            print(f"Loaded {local_count} tickers from original.txt")
        else:
            print("original.txt not found — starting with an empty ticker list.")
            open(self.original_file, "a").close()

        if os.path.exists(self.fetched_file):
            with open(self.fetched_file, "r") as ff:
                self.fetched_tickers = [line.strip().upper() for line in ff if line.strip()]
            print(f"Loaded {len(self.fetched_tickers)} cached fetched tickers from fetched.txt")

        self._load_original_from_file()

        self.controller = Controller()
        self.current_node = None
        self.last_direction = None

        if platform.system() == "Darwin":
            self.shortcut_key = Key.cmd
        else:
            self.shortcut_key = Key.ctrl_l

        self.create_gui()

    def _atomic_write(self, path, lines):
        tmp = path + ".tmp"
        try:
            with open(tmp, "w") as f:
                for line in lines:
                    f.write(line.rstrip("\n") + "\n")
            os.replace(tmp, path)
        except Exception:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            raise

    def _load_fetched_from_file(self):
        if os.path.exists(self.fetched_file):
            with open(self.fetched_file, "r") as ff:
                self.fetched_tickers = [line.strip().upper() for line in ff if line.strip()]
        else:
            self.fetched_tickers = []

    def _load_original_from_file(self):
        self.original_ticker_symbols = TickerLinkedList()
        if not os.path.exists(self.original_file):
            open(self.original_file, "w").close()
        with open(self.original_file, "r") as file:
            for line in file:
                s = line.strip().upper()
                if s:
                    self.original_ticker_symbols.add(s)

    def add_to_blacklist(self, tickers):
        if not isinstance(tickers, (list, set)):
            tickers = [tickers]

        blacklist = self.load_blacklist()
        blacklist.update([t.upper() for t in tickers])
        sorted_blacklist = sorted(blacklist)

        try:
            self._atomic_write(self.blacklist_file, sorted_blacklist)
        except Exception as e:
            print(f"Failed to write blacklist: {e}")
            with open(self.blacklist_file, "w") as bf:
                for symbol in sorted_blacklist:
                    bf.write(symbol + "\n")

    def load_blacklist(self):
        if not os.path.exists(self.blacklist_file):
            open(self.blacklist_file, "a").close()
        with open(self.blacklist_file, "r") as bf:
            return {line.strip().upper() for line in bf if line.strip()}

    def save_ticker_symbols(self):
        symbols = sorted(set(self.original_ticker_symbols))

        try:
            self._atomic_write(self.original_file, symbols)
        except Exception as e:
            print(f"Failed atomic write original.txt: {e}")
            with open(self.original_file, "w") as file:
                for symbol in symbols:
                    file.write(symbol + "\n")

        self.original_ticker_symbols = TickerLinkedList()
        for s in symbols:
            self.original_ticker_symbols.add(s)

    def schedule_update(self, full_refresh=True, delay=50):
        if hasattr(self, "_update_job") and self._update_job:
            self.root.after_cancel(self._update_job)

        self._update_job = self.root.after(delay, lambda: self.update_ticker_list(full_refresh))

    def _rebuild_ui_linked_list(self, visible_symbols):
        prev_symbol = None
        if self.current_node:
            try:
                prev_symbol = self.current_node.symbol
            except Exception:
                prev_symbol = None

        self.ticker_symbols = TickerLinkedList()
        for s in visible_symbols:
            self.ticker_symbols.add(s)

        if prev_symbol:
            node = self.ticker_symbols.find(prev_symbol)
            if node:
                self.current_node = node
                return
        self.current_node = self.ticker_symbols.head if self.ticker_symbols.head else None

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
                self.original_ticker_symbols.add(new_ticker)
                self.save_ticker_symbols()
                self.root.after(0, lambda: (self.schedule_update(full_refresh=True),
                                           finalize_add(new_ticker)))

            def finalize_add(ticker):
                messagebox.showinfo("Success", f"Added '{ticker}' to the list.")
                dialog.destroy()

            threading.Thread(target=do_add, daemon=True).start()

        submit_button = ctk.CTkButton(dialog, text="Submit", command=on_submit)
        submit_button.pack(pady=10)
        dialog.grab_set()

    def remove_ticker_symbol(self, ticker_to_remove=None):
        if not ticker_to_remove:
            return

        ticker_upper = ticker_to_remove.upper()
        frame = self.symbol_widgets.pop(ticker_upper, None)
        if frame:
            try:
                frame.destroy()
            except Exception:
                pass

        def do_removal():
            try:
                self.add_to_blacklist(ticker_upper)
            except Exception as e:
                print(f"Error blacklisting {ticker_upper}: {e}")
            finally:
                self.root.after(0, lambda: self.schedule_update(full_refresh=True))

        threading.Thread(target=do_removal, daemon=True).start()

        self.root.after(0, lambda: (messagebox.showinfo("Success", f"Removed '{ticker_upper}' from the view (blacklisted)."),
                                   self.root.focus_force()))

    def remove_all_ticker_symbols(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to remove all ticker symbols from view?"):
            all_symbols = [s for s in self.original_ticker_symbols]
            if all_symbols:
                for frame in list(self.symbol_widgets.values()):
                    try:
                        frame.destroy()
                    except Exception:
                        pass
                self.symbol_widgets.clear()

                def do_all_remove():
                    try:
                        self.add_to_blacklist(all_symbols)
                    except Exception as e:
                        print(f"Failed to add all to blacklist: {e}")
                    finally:
                        self.root.after(0, lambda: self.schedule_update(full_refresh=True))

                threading.Thread(target=do_all_remove, daemon=True).start()

            messagebox.showinfo("Success", "All ticker symbols have been removed from view (blacklisted).")
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
                    self.original_ticker_symbols.add(symbol)
                self.save_ticker_symbols()
                self.root.after(0, lambda: (self.schedule_update(full_refresh=True),
                                           finalize_bulk_add(symbol_list)))

            def finalize_bulk_add(symbols_added):
                messagebox.showinfo("Success", "Added all valid symbols to the list.")
                dialog.destroy()

            threading.Thread(target=do_bulk_add, daemon=True).start()

        submit_button = ctk.CTkButton(dialog, text="Submit", command=on_submit)
        submit_button.pack(pady=10)

        dialog.grab_set()

    def reload_tickers_from_urls(self):
        threading.Thread(target=self._fetch_and_save, daemon=True).start()

    def create_gui(self):
        self.root = ctk.CTk()
        self.root.title("Ticker Symbol Manager")
        self.root.geometry("900x800")

        from tkinter import BooleanVar
        self.show_fetched_var = BooleanVar(master=self.root, value=False)

        ctk.set_appearance_mode("light")

        title_label = ctk.CTkLabel(self.root, text="Stock Ticker Manager", font=("Arial", 28, "bold"))
        title_label.pack(pady=20)

        self.scrollable_frame = ctk.CTkScrollableFrame(self.root, height=600, width=850)
        self.scrollable_frame.pack(pady=10)

        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(pady=10, fill="x")

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

        button_frame.grid_columnconfigure(3, weight=1)

        controls_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        controls_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=(10,0), sticky="w")

        fetch_switch = ctk.CTkSwitch(controls_frame,
                                    text="Show fetched tickers",
                                    command=self.on_fetch_toggle,
                                    variable=self.show_fetched_var)
        fetch_switch.pack(side="left", padx=(0,8))

        self.update_ticker_list()

    def update_ticker_list(self, full_refresh=True):
        blacklist = self.load_blacklist()

        if self.show_fetched_var.get():
            if not self.fetched_tickers and os.path.exists(self.fetched_file):
                self._load_fetched_from_file()
            local_list = [s.upper() for s in self.original_ticker_symbols]
            merged = sorted(set(local_list + self.fetched_tickers))
            new_visible = [s for s in merged if s not in blacklist]
        else:
            new_visible = [s for s in self.original_ticker_symbols if s not in blacklist]
            new_visible = sorted(set(new_visible))

        old_visible = getattr(self, "visible_symbols", [])

        if new_visible == old_visible and not full_refresh:
            return

        old_set = set(old_visible)
        new_set = set(new_visible)

        removed = old_set - new_set
        for symbol in removed:
            frame = self.symbol_widgets.pop(symbol, None)
            if frame:
                try:
                    frame.destroy()
                except Exception:
                    pass

        added = [s for s in new_visible if s not in old_set]
        for symbol in added:
            self._create_symbol_row(symbol)

        for widget in self.scrollable_frame.winfo_children():
            try:
                widget.pack_forget()
            except Exception:
                pass

        for symbol in new_visible:
            frame = self.symbol_widgets.get(symbol)
            if frame:
                try:
                    frame.pack(fill="x", pady=5)
                except Exception:
                    pass

        self.visible_symbols = new_visible
        self._rebuild_ui_linked_list(new_visible)

        try:
            self.root.update_idletasks()
        except Exception:
            pass

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
            if self.show_fetched_var.get():
                threading.Thread(target=self._fetch_and_save, daemon=True).start()

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

    def on_fetch_toggle(self):
        if self.show_fetched_var.get():
            if os.path.exists(self.fetched_file):
                if not self.fetched_tickers:
                    self._load_fetched_from_file()
                self.schedule_update(full_refresh=True)
            else:
                threading.Thread(target=self._fetch_and_save, daemon=True).start()
        else:
            self.schedule_update(full_refresh=True)

    def _fetch_and_save(self):
        try:
            fetched = run_scraper(self.stock_url, self.etf_url)
            fetched_set = sorted({s.strip().upper() for s in fetched if s and s.strip()})

            try:
                self._atomic_write(self.fetched_file, fetched_set)
            except Exception as e:
                print(f"Atomic write failed for fetched.txt: {e}")
                with open(self.fetched_file, "w") as ff:
                    for t in fetched_set:
                        ff.write(t + "\n")

            self.fetched_tickers = fetched_set

            self.root.after(0, lambda: (self.schedule_update(full_refresh=True),
                                       messagebox.showinfo("Fetched", f"Fetched {len(fetched_set)} tickers and updated files.")))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch tickers: {e}"))

    def on_press(self, key):
        try:
            if key == Key.down:
                if self.current_node:
                    if self.last_direction == "up":
                        if self.current_node.next and self.current_node.next.next:
                            self.current_node = self.current_node.next.next
                    self.type_word(self.current_node.symbol)
                    self.current_node = self.current_node.next if self.current_node.next else self.current_node
                    self.last_direction = "down"

            elif key == Key.up:
                if self.current_node:
                    if self.last_direction == "down":
                        if self.current_node.prev and self.current_node.prev.prev:
                            self.current_node = self.current_node.prev.prev
                    self.type_word(self.current_node.symbol)
                    self.current_node = self.current_node.prev if self.current_node.prev else self.current_node
                    self.last_direction = "up"

            elif key == Key.left:
                self.controller.press(self.shortcut_key)
                self.controller.press('w')
                self.controller.release('w')
                self.controller.release(self.shortcut_key)

            elif key == Key.right:
                if self.last_direction in ["up", "down"] and self.current_node:
                    self.controller.press(self.shortcut_key)
                    self.controller.press('t')
                    self.controller.release('t')
                    self.controller.release(self.shortcut_key)

                    if self.last_direction == "up":
                        next_node = self.current_node.next if self.current_node.next else self.current_node
                    else:
                        next_node = self.current_node.prev if self.current_node.prev else self.current_node

                    next_symbol = next_node.symbol
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
        threading.Thread(target=self.listener.start, daemon=True).start()
        self.root.mainloop()

if __name__ == "__main__":
    typing_program = TypingProgram()
    typing_program.start()
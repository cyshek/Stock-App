# Ticker-symbol-typer
A program that allows users to navigate through a stock watchlist using the up and down arrow keys. When a key is pressed, the program types the current stock ticker symbol and quickly updates to type the next stock in the chosen direction. This feature significantly speeds up the process of reviewing a watchlist.


- Close the GUI tab to terminate
- Press “arrow down & up” keys to navigate the watchlist
- Press "arrow right" to open up a new tab with the 5-year chart of the current ticker symbol in Google
- Press "arrow left" to close the tab
- You can add or remove stocks by pressing either respective button


To build the project, run:
```python
pyinstaller --onefile --noconsole stocks.py
```
Then move the `ticker_symbols.txt` to the directory with the application.






Stock Ticker Manager

This Python application provides an easy-to-use graphical interface for managing and typing stock ticker symbols. It leverages customtkinter for the GUI, alongside other libraries for handling user inputs and interactions.

Features

Ticker Management

Add Ticker Symbols: Add new stock ticker symbols to the list using a simple dialog box.

Remove Ticker Symbols: Remove existing ticker symbols with a single button click.

Persistent Storage: Automatically saves and loads ticker symbols to/from a ticker_symbols.txt file.

Navigation and Typing

Circular Navigation: Browse ticker symbols in a circular doubly-linked list using the up/down arrow keys.

Auto Typing: Automatically type ticker symbols into any application when navigating through the list.

Shortcut Commands: Built-in support for key commands, such as opening a new tab (Ctrl+T or Cmd+T) and closing a tab (Ctrl+W or Cmd+W).

Intuitive GUI

Modern Design: A clean and responsive interface using customtkinter.

Dynamic Updates: Automatically updates the displayed list when ticker symbols are added or removed.

Prerequisites

Python 3.6 or higher

Required Python libraries:

customtkinter

pynput

To install dependencies, run:

pip install customtkinter pynput

Installation

Clone or download this repository.

Place the stocks.py file in your working directory.

Ensure a ticker_symbols.txt file exists in the same directory for persistent ticker storage. If not, it will be created automatically when the program runs.

Usage

Run the script:

python stocks.py

Use the GUI to:

Add or remove ticker symbols.

View and manage the list of symbols.

Use the arrow keys for navigation and automatic typing of ticker symbols.

How It Works

Ticker Symbols

The program uses a circular doubly-linked list to manage ticker symbols. This ensures efficient navigation and a seamless "wrap-around" effect when browsing symbols.

Keyboard Interaction

The program listens for specific keyboard events:

Up Arrow: Navigate to the previous ticker symbol and type it.

Down Arrow: Navigate to the next ticker symbol and type it.

Left Arrow: Close the current tab.

Right Arrow: Open a new tab and search for the next/previous ticker symbol.

GUI

The GUI is built using customtkinter, providing a visually appealing and modern user interface. It features dynamic updates to reflect changes in the ticker list.

File Structure

stocks.py: Main application file.

ticker_symbols.txt: File for storing ticker symbols (created automatically).

Customization

Appearance: Modify the customtkinter appearance settings in stocks.py.

Hotkeys: Adjust keyboard shortcuts by editing the on_press method.

Known Issues

Ensure the ticker_symbols.txt file has appropriate read/write permissions.

Compatibility may vary slightly depending on the operating system (Windows, macOS, Linux).

Contributing

Contributions are welcome! Feel free to fork the repository and submit pull requests for bug fixes or new features.

License

This project is licensed under the MIT License. See the LICENSE file for details.

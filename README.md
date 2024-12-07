# Ticker-symbol-typer
A program that allows users to navigate through a stock watchlist using the up and down arrow keys. When a key is pressed, the program types the current stock ticker symbol and quickly updates to type the next stock in the chosen direction. This feature significantly speeds up the process of reviewing a watchlist.

- Close the GUI tab to terminate
- Press “arrow down & up” keys to navigate the watchlist
- Press "arrow right" to open up a new tab with the current ticker symbol in Google
- Press "arrow left" to close the tab
- You can add or remove stocks by pressing either respective button
- You can bulk add and remove everything

## Steps (for Windows)
1. Download the zip: https://drive.google.com/drive/folders/1eVDY6OlM9P0cRmuVEZ7RrlC4ArOdOfje?usp=sharing
2. Extract the files and move them to a new folder
3. Open the application

## If you are on MacOS or prefer to run the script manually

Make sure you have Python installed.

Required Python libraries:
- `customtkinter`
- `pynput`

To install dependencies, run:
```
pip install customtkinter pynput
```

### Installation
1. Clone or download this repository.
2. Place the `stocks.py` file in your working directory.
3. Ensure a `ticker_symbols.txt` file exists in the same directory for persistent ticker storage. Feel free to modify the current one with your own symbols.

### Usage
1. Run the script in your directory
   ```
   python stocks.py
   ```
2. Use the GUI to:
   - Add or remove ticker symbols.
   - View and manage the list of symbols.
3. Use the arrow keys for navigation and automatic typing of ticker symbols

# Ticker-symbol-typer
A program I made that navigates through a list of stocks by pressing either the up or down arrow key. Makes it faster to sift through a watchlist.


- Close the GUI tab to terminate
- Press “arrow down & up” keys to navigate the watchlist
- You can add or remove stocks by pressing either respective button


To build the project, run:
```python
pyinstaller --onefile --noconsole stocks.py
```
Then move the `ticker_symbols.txt` to the directory with the application.


You can also run `watcher.py` to recreate the app whenever you save backend changes in `stocks.py`.

from pynput.keyboard import Controller, Key, Listener
import time
import sys

class TypingProgram:
    def __init__(self, ticker_symbols):
        self.ticker_symbols = ticker_symbols
        self.current_index = 0
        self.prev_index = 0
        self.prev_key_value = ""
        self.controller = Controller()
    
    def type_word(self, index):
        word_to_type = self.ticker_symbols[index]
        for char in word_to_type:
            self.controller.type(char)
            time.sleep(0.01)
        # Type the 'enter' key
        self.controller.press(Key.enter)
        self.controller.release(Key.enter)

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

            elif key == Key.esc:
                # Terminate the program
                sys.exit()
            
        except AttributeError:
            pass
    
    def start(self):
        # Start listening for key presses
        with Listener(on_press=self.on_press) as listener:
            listener.join()

# List of ticker symbols to type
ticker_symbols = ["SHOP", "QCOM", "WFC", "INTC", "QQQ", "TQQQ", "RTX", "ABNB", "SNOW", "EOG", "CRWD", "TEAM", "CRM", "OKTA", "CHGG", "CFLT", "ONON", "MNDY", "RBLX", "ARM", "LULU", "NKE"]

# Create an instance of TypingProgram and start it
typing_program = TypingProgram(ticker_symbols)
typing_program.start()

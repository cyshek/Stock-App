import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("stocks.py"):
            print("Detected change in stocks.py. Rebuilding executable...")
            subprocess.run(["pyinstaller", "--noconfirm", "stocks.py"])

print("Press Ctrl+C to end the program.")
observer = Observer()
observer.schedule(MyHandler(), path=".", recursive=True)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()

import time

from functions import sync

if __name__ == "__main__":
    while True:
        sync()
        time.sleep(60)

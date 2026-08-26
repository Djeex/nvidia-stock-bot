import logging
import signal
import sys
import time

from env_config import REFRESH_TIME
from gpu_checker import check_rtx_50_founders


# Signal handler function
def handle_exit(signum, frame):
    logging.info(f"🛑 Received signal {signum}. Exiting gracefully...")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, handle_exit)  # Ctrl+C
signal.signal(signal.SIGTERM, handle_exit)  # docker stop / kill -15

if __name__ == "__main__":
    try:
        while True:
            start = time.time()
            check_rtx_50_founders()
            elapsed = time.time() - start
            time.sleep(max(0, REFRESH_TIME - elapsed))
    except KeyboardInterrupt:
        logging.info("🛑 Script interrupted by user (KeyboardInterrupt). Exiting gracefully.")
        sys.exit(0)

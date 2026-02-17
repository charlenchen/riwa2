import time
import os
import json
from src.utils.logger import logger

class Simulation:
    def __init__(self, inbox_path="data/inbox", tick_rate=1.0):
        self.inbox_path = inbox_path
        self.tick_rate = tick_rate
        self.is_running = False
        self.tick_count = 0

    def start(self):
        logger.info("Starting RIW2 Simulation Engine...")
        self.is_running = True
        self.run_loop()

    def stop(self):
        logger.info("Stopping Simulation Engine...")
        self.is_running = False

    def run_loop(self):
        while self.is_running:
            start_time = time.time()
            self.tick()
            
            # Sleep to maintain tick rate
            elapsed = time.time() - start_time
            sleep_time = max(0, self.tick_rate - elapsed)
            time.sleep(sleep_time)

    def tick(self):
        self.tick_count += 1
        logger.info(f"--- Tick {self.tick_count} ---")
        
        # 1. Check for injections
        self.check_inbox()
        
        # 2. Update world state (placeholder for now)
        self.update_world()
        
        # 3. Handle scheduled events (placeholder)

    def check_inbox(self):
        if not os.path.exists(self.inbox_path):
            return

        for filename in os.listdir(self.inbox_path):
            if filename.endswith(".json"):
                file_path = os.path.join(self.inbox_path, filename)
                try:
                    with open(file_path, 'r') as f:
                        injection_data = json.load(f)
                    
                    logger.info(f"Hot Injection Detected: {filename}")
                    self.apply_injection(injection_data)
                    
                    # Remove the file after processing
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error processing injection {filename}: {e}")

    def apply_injection(self, data):
        # Placeholder for actual injection logic
        logger.info(f"Applying injection: {data}")

    def update_world(self):
        # Placeholder for world logic update
        pass

if __name__ == "__main__":
    sim = Simulation(tick_rate=2.0)
    try:
        sim.start()
    except KeyboardInterrupt:
        sim.stop()

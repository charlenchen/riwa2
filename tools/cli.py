import sys
import os

# Add the project root to sys.path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.simulation import Simulation

def main():
    print("RIW2 CLI - World Engine")
    sim = Simulation(tick_rate=2.0)
    try:
        sim.start()
    except KeyboardInterrupt:
        sim.stop()
        print("\nSimulation terminated.")

if __name__ == "__main__":
    main()

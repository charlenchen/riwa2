import pickle
import os
from datetime import datetime
from typing import Any, Optional, List
from src.utils.logger import logger


class StateManager:
    """
    Manages save/load/snapshot/rollback functionality for the simulation.
    Implements the "Time Machine" feature for world state persistence.
    """

    def __init__(self, snapshot_dir: str = "data/snapshots"):
        self.snapshot_dir = snapshot_dir
        self._ensure_snapshot_dir()

    def _ensure_snapshot_dir(self):
        """Ensure the snapshot directory exists."""
        os.makedirs(self.snapshot_dir, exist_ok=True)

    def _generate_snapshot_filename(self, world_id: str, tick: int) -> str:
        """Generate a standardized snapshot filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(
            self.snapshot_dir,
            f"{world_id}_tick_{tick}_{timestamp}.pkl"
        )

    def save_snapshot(self, world_state: Any, world_id: str, tick: int) -> str:
        """
        Save a snapshot of the current world state.

        Args:
            world_state: The world state object to serialize
            world_id: Unique identifier for the world
            tick: Current simulation tick number

        Returns:
            Path to the saved snapshot file
        """
        filename = self._generate_snapshot_filename(world_id, tick)
        try:
            with open(filename, 'wb') as f:
                pickle.dump({
                    'world_state': world_state,
                    'world_id': world_id,
                    'tick': tick,
                    'timestamp': datetime.now().isoformat()
                }, f)
            logger.info(f"Snapshot saved: {filename} (tick {tick})")
            return filename
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            raise

    def load_snapshot(self, snapshot_path: str) -> dict:
        """
        Load a world state from a snapshot file.

        Args:
            snapshot_path: Path to the snapshot file

        Returns:
            Dictionary containing world_state, world_id, tick, and timestamp
        """
        try:
            with open(snapshot_path, 'rb') as f:
                data = pickle.load(f)
            logger.info(f"Snapshot loaded: {snapshot_path} (tick {data['tick']})")
            return data
        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}")
            raise

    def list_snapshots(self, world_id: Optional[str] = None) -> List[str]:
        """
        List available snapshots.

        Args:
            world_id: Optional filter by world ID

        Returns:
            List of snapshot file paths
        """
        if not os.path.exists(self.snapshot_dir):
            return []

        snapshots = []
        for filename in os.listdir(self.snapshot_dir):
            if filename.endswith('.pkl'):
                if world_id is None or filename.startswith(world_id):
                    snapshots.append(os.path.join(self.snapshot_dir, filename))

        return sorted(snapshots)

    def get_latest_snapshot(self, world_id: str) -> Optional[str]:
        """
        Get the most recent snapshot for a given world.

        Args:
            world_id: World ID to find snapshots for

        Returns:
            Path to the latest snapshot, or None if not found
        """
        snapshots = self.list_snapshots(world_id)
        return snapshots[-1] if snapshots else None

    def delete_snapshot(self, snapshot_path: str) -> bool:
        """
        Delete a snapshot file.

        Args:
            snapshot_path: Path to the snapshot to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            os.remove(snapshot_path)
            logger.info(f"Snapshot deleted: {snapshot_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete snapshot: {e}")
            return False

    def rollback(self, world_state: Any, snapshot_path: str) -> Any:
        """
        Rollback to a previous snapshot state.

        Args:
            world_state: Current world state (will be replaced)
            snapshot_path: Path to the snapshot to rollback to

        Returns:
            The world state from the snapshot
        """
        data = self.load_snapshot(snapshot_path)
        logger.info(f"Rolling back to tick {data['tick']}")
        return data['world_state']

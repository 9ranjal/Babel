"""
Checkpointing system for crash recovery and progress tracking.
"""

import json
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass 
class CheckpointMetadata:
    """Metadata for a checkpoint."""
    timestamp: float
    total_files: int
    processed_files: int
    total_rows: int
    processed_rows: int
    current_file: str
    current_row: int
    performance_stats: Dict[str, Any]
    
class CheckpointManager:
    """
    Manages checkpointing for Excel processing pipeline with crash recovery.
    """
    
    def __init__(self, checkpoint_dir: Path, session_id: Optional[str] = None, checkpoint_interval: int = 100):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_dir: Directory to store checkpoint files
            session_id: Unique session identifier (auto-generated if None)
            checkpoint_interval: Save checkpoint every N processed rows
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_id = session_id or self._generate_session_id()
        self.checkpoint_interval = checkpoint_interval
        
        self.checkpoint_file = self.checkpoint_dir / f"checkpoint_{self.session_id}.json"
        self.chunks_file = self.checkpoint_dir / f"chunks_{self.session_id}.json"
        
        self.processed_chunks: List[Dict] = []
        self.processed_rows = 0
        self.start_time = time.time()
        
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        return f"{timestamp}_{random_hash}"
    
    def save_checkpoint(self, metadata: CheckpointMetadata, chunks: List[Dict]):
        """
        Save current progress to checkpoint files.
        
        Args:
            metadata: Checkpoint metadata
            chunks: List of processed chunks
        """
        try:
            # Save metadata
            checkpoint_data = {
                "session_id": self.session_id,
                "metadata": asdict(metadata),
                "chunks_file": str(self.chunks_file),
                "created_at": datetime.now().isoformat()
            }
            
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            
            # Save chunks (append mode for incremental saves)
            if chunks:
                with open(self.chunks_file, 'w') as f:
                    json.dump(chunks, f, indent=2)
            
            print(f"✅ Checkpoint saved: {len(chunks)} chunks, row {metadata.processed_rows}")
            
        except Exception as e:
            print(f"⚠️ Failed to save checkpoint: {e}")
    
    def load_checkpoint(self) -> Optional[Tuple[CheckpointMetadata, List[Dict]]]:
        """
        Load existing checkpoint if available.
        
        Returns:
            Tuple of (metadata, chunks) if checkpoint exists, None otherwise
        """
        if not self.checkpoint_file.exists():
            return None
        
        try:
            # Load metadata
            with open(self.checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
            
            metadata_dict = checkpoint_data["metadata"]
            metadata = CheckpointMetadata(**metadata_dict)
            
            # Load chunks
            chunks = []
            chunks_file = Path(checkpoint_data["chunks_file"])
            if chunks_file.exists():
                with open(chunks_file, 'r') as f:
                    chunks = json.load(f)
            
            print(f"🔄 Checkpoint loaded: {len(chunks)} chunks, resuming from row {metadata.processed_rows}")
            return metadata, chunks
            
        except Exception as e:
            print(f"⚠️ Failed to load checkpoint: {e}")
            return None
    
    def should_checkpoint(self, current_row: int) -> bool:
        """
        Determine if a checkpoint should be saved.
        
        Args:
            current_row: Current row being processed
            
        Returns:
            True if checkpoint should be saved
        """
        return current_row > 0 and current_row % self.checkpoint_interval == 0
    
    def create_metadata(self, total_files: int, processed_files: int, total_rows: int, 
                       processed_rows: int, current_file: str, current_row: int,
                       performance_stats: Optional[Dict] = None) -> CheckpointMetadata:
        """
        Create checkpoint metadata.
        
        Args:
            total_files: Total number of files to process
            processed_files: Number of files already processed
            total_rows: Total number of rows to process
            processed_rows: Number of rows already processed
            current_file: Currently processing file
            current_row: Currently processing row
            performance_stats: Performance statistics
            
        Returns:
            CheckpointMetadata object
        """
        return CheckpointMetadata(
            timestamp=time.time(),
            total_files=total_files,
            processed_files=processed_files,
            total_rows=total_rows,
            processed_rows=processed_rows,
            current_file=current_file,
            current_row=current_row,
            performance_stats=performance_stats or {}
        )
    
    def cleanup_checkpoints(self, keep_latest: int = 3):
        """
        Clean up old checkpoint files, keeping only the latest N.
        
        Args:
            keep_latest: Number of latest checkpoints to keep
        """
        try:
            # Find all checkpoint files
            checkpoint_files = list(self.checkpoint_dir.glob("checkpoint_*.json"))
            chunks_files = list(self.checkpoint_dir.glob("chunks_*.json"))
            
            # Sort by modification time
            checkpoint_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            chunks_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old files
            for old_file in checkpoint_files[keep_latest:]:
                old_file.unlink()
            
            for old_file in chunks_files[keep_latest:]:
                old_file.unlink()
                
            if len(checkpoint_files) > keep_latest:
                print(f"🧹 Cleaned up {len(checkpoint_files) - keep_latest} old checkpoints")
                
        except Exception as e:
            print(f"⚠️ Failed to cleanup checkpoints: {e}")
    
    def get_recovery_info(self) -> Optional[Dict]:
        """
        Get information about available recovery options.
        
        Returns:
            Dictionary with recovery information or None
        """
        checkpoint_files = list(self.checkpoint_dir.glob("checkpoint_*.json"))
        if not checkpoint_files:
            return None
        
        # Find most recent checkpoint
        latest_checkpoint = max(checkpoint_files, key=lambda x: x.stat().st_mtime)
        
        try:
            with open(latest_checkpoint, 'r') as f:
                data = json.load(f)
            
            metadata = data["metadata"]
            
            progress_pct = (metadata["processed_rows"] / metadata["total_rows"]) * 100 if metadata["total_rows"] > 0 else 0
            
            return {
                "checkpoint_file": str(latest_checkpoint),
                "session_id": data["session_id"],
                "created_at": data["created_at"],
                "progress_percent": progress_pct,
                "processed_rows": metadata["processed_rows"],
                "total_rows": metadata["total_rows"],
                "current_file": metadata["current_file"],
                "estimated_time_remaining": self._estimate_remaining_time(metadata)
            }
            
        except Exception as e:
            print(f"⚠️ Failed to get recovery info: {e}")
            return None
    
    def _estimate_remaining_time(self, metadata: Dict) -> str:
        """
        Estimate remaining processing time based on current progress.
        
        Args:
            metadata: Checkpoint metadata
            
        Returns:
            Estimated time remaining as human-readable string
        """
        processed_rows = metadata["processed_rows"]
        total_rows = metadata["total_rows"]
        elapsed_time = time.time() - metadata["timestamp"]
        
        if processed_rows == 0:
            return "unknown"
        
        rows_per_second = processed_rows / elapsed_time
        remaining_rows = total_rows - processed_rows
        
        if rows_per_second > 0:
            remaining_seconds = remaining_rows / rows_per_second
            
            if remaining_seconds < 60:
                return f"{remaining_seconds:.0f} seconds"
            elif remaining_seconds < 3600:
                return f"{remaining_seconds/60:.1f} minutes"
            else:
                return f"{remaining_seconds/3600:.1f} hours"
        
        return "unknown"
    
    def finalize_session(self, final_chunks: List[Dict]) -> Path:
        """
        Finalize the session and return path to final output.
        
        Args:
            final_chunks: Final list of all processed chunks
            
        Returns:
            Path to final output file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_output = self.checkpoint_dir.parent / f"excel_chunks_{timestamp}.json"
        
        with open(final_output, 'w') as f:
            json.dump(final_chunks, f, indent=2)
        
        # Clean up checkpoint files
        try:
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
            if self.chunks_file.exists():
                self.chunks_file.unlink()
        except:
            pass  # Don't fail on cleanup errors
        
        print(f"✅ Session finalized: {len(final_chunks)} chunks saved to {final_output}")
        return final_output

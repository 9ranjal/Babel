"""
Performance profiler for chunking pipeline with timing, memory, and bottleneck analysis.
"""

import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager
from functools import wraps
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class StageMetrics:
    """Metrics for a single pipeline stage."""
    name: str
    start_time: float
    end_time: float
    duration: float
    memory_before: float
    memory_after: float
    memory_delta: float
    chunk_count: int = 0
    items_per_second: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProfileResults:
    """Complete profiling results for a pipeline run."""
    total_duration: float
    total_chunks: int
    overall_throughput: float  # chunks per second
    stage_metrics: List[StageMetrics]
    bottlenecks: List[str]
    memory_peak: float
    memory_total_delta: float
    recommendations: List[str]

class PerformanceProfiler:
    """
    Thread-safe performance profiler for chunking pipeline stages.
    """
    
    def __init__(self, enabled: bool = True, log_memory: bool = True):
        """
        Initialize the profiler.
        
        Args:
            enabled: Whether profiling is enabled
            log_memory: Whether to track memory usage
        """
        self.enabled = enabled
        self.log_memory = log_memory
        self.stages: Dict[str, StageMetrics] = {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.chunk_count = 0
        self.memory_peak = 0.0
        self.lock = threading.Lock()
        
        # Stage timing thresholds for bottleneck detection (seconds per chunk)
        self.bottleneck_thresholds = {
            "template_application": 0.01,      # 10ms per chunk
            "text_polishing": 0.50,            # 500ms per chunk (T5 is expensive)
            "glossary_expansion": 0.05,        # 50ms per chunk
            "entity_extraction": 0.10,         # 100ms per chunk
            "quality_assessment": 0.02,        # 20ms per chunk
            "schema_creation": 0.01,           # 10ms per chunk
        }
    
    def start_session(self, chunk_count: int = 0):
        """Start a profiling session."""
        if not self.enabled:
            return
            
        with self.lock:
            self.start_time = time.time()
            self.chunk_count = chunk_count
            self.stages.clear()
            self.memory_peak = self._get_memory_usage()
            
        logger.info(f"🔍 Performance profiling started for {chunk_count} chunks")
    
    def end_session(self) -> ProfileResults:
        """End profiling session and return results."""
        if not self.enabled:
            return ProfileResults(0, 0, 0, [], [], 0, 0, [])
            
        with self.lock:
            self.end_time = time.time()
            total_duration = self.end_time - (self.start_time or 0)
            overall_throughput = self.chunk_count / total_duration if total_duration > 0 else 0
            
            # Analyze results
            stage_list = list(self.stages.values())
            bottlenecks = self._identify_bottlenecks(stage_list)
            recommendations = self._generate_recommendations(stage_list, bottlenecks)
            memory_total_delta = self._get_memory_usage() - (self.memory_peak if self.memory_peak else 0)
            
            results = ProfileResults(
                total_duration=total_duration,
                total_chunks=self.chunk_count,
                overall_throughput=overall_throughput,
                stage_metrics=stage_list,
                bottlenecks=bottlenecks,
                memory_peak=self.memory_peak,
                memory_total_delta=memory_total_delta,
                recommendations=recommendations
            )
            
            logger.info(f"🏁 Profiling complete: {total_duration:.2f}s for {self.chunk_count} chunks "
                       f"({overall_throughput:.2f} chunks/sec)")
            
            return results
    
    @contextmanager
    def stage(self, name: str, chunk_count: int = 1, metadata: Optional[Dict] = None):
        """
        Context manager for timing a pipeline stage.
        
        Args:
            name: Stage name
            chunk_count: Number of chunks processed in this stage
            metadata: Additional metadata for this stage
        """
        if not self.enabled:
            yield
            return
            
        start_time = time.time()
        memory_before = self._get_memory_usage() if self.log_memory else 0.0
        
        try:
            yield
        finally:
            end_time = time.time()
            memory_after = self._get_memory_usage() if self.log_memory else 0.0
            duration = end_time - start_time
            
            # Update peak memory
            if self.log_memory:
                self.memory_peak = max(self.memory_peak, memory_after)
            
            # Calculate throughput
            items_per_second = chunk_count / duration if duration > 0 else 0
            
            # Store metrics
            with self.lock:
                self.stages[name] = StageMetrics(
                    name=name,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    memory_before=memory_before,
                    memory_after=memory_after,
                    memory_delta=memory_after - memory_before,
                    chunk_count=chunk_count,
                    items_per_second=items_per_second,
                    metadata=metadata or {}
                )
            
            logger.debug(f"⏱️ {name}: {duration:.3f}s ({items_per_second:.1f} items/sec)")
    
    def time_function(self, stage_name: str):
        """
        Decorator to time function execution.
        
        Args:
            stage_name: Name of the stage for profiling
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                    
                with self.stage(stage_name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except:
            return 0.0
    
    def _identify_bottlenecks(self, stages: List[StageMetrics]) -> List[str]:
        """Identify performance bottlenecks based on timing thresholds."""
        bottlenecks = []
        
        for stage in stages:
            if stage.chunk_count == 0:
                continue
                
            time_per_chunk = stage.duration / stage.chunk_count
            threshold = self.bottleneck_thresholds.get(stage.name, 0.1)  # Default 100ms
            
            if time_per_chunk > threshold:
                bottlenecks.append(f"{stage.name}: {time_per_chunk*1000:.1f}ms/chunk "
                                 f"(threshold: {threshold*1000:.1f}ms)")
        
        # Sort by severity (highest time per chunk first)
        bottlenecks.sort(key=lambda x: float(x.split(":")[1].split("ms")[0]), reverse=True)
        
        return bottlenecks
    
    def _generate_recommendations(self, stages: List[StageMetrics], bottlenecks: List[str]) -> List[str]:
        """Generate optimization recommendations based on profiling results."""
        recommendations = []
        
        # Check for text polishing bottleneck
        polishing_stage = next((s for s in stages if "polishing" in s.name.lower()), None)
        if polishing_stage and polishing_stage.duration > 0 and polishing_stage.chunk_count > 0:
            time_per_chunk = polishing_stage.duration / polishing_stage.chunk_count
            if time_per_chunk > 0.3:  # More than 300ms per chunk
                recommendations.extend([
                    "🚀 CRITICAL: Implement batch T5 polishing (8-16 chunks at once)",
                    "⚡ Add is_clean_sentence() heuristic to skip good chunks",
                    "🔧 Consider using flan-t5-small for faster processing",
                    "💾 Enable polishing bypass for clean sentences"
                ])
        
        # Check for glossary expansion bottleneck
        glossary_stage = next((s for s in stages if "glossary" in s.name.lower()), None)
        if glossary_stage and glossary_stage.duration > 0 and glossary_stage.chunk_count > 0:
            time_per_chunk = glossary_stage.duration / glossary_stage.chunk_count
            if time_per_chunk > 0.04:  # More than 40ms per chunk
                recommendations.extend([
                    "🧵 Parallelize glossary expansion with ThreadPoolExecutor",
                    "🔍 Optimize fuzzy matching with shared instances",
                    "📋 Consider disabling glossary injection (embeddings handle synonyms)"
                ])
        
        # Check for entity extraction bottleneck
        entity_stage = next((s for s in stages if "entity" in s.name.lower()), None)
        if entity_stage and entity_stage.duration > 0 and entity_stage.chunk_count > 0:
            time_per_chunk = entity_stage.duration / entity_stage.chunk_count
            if time_per_chunk > 0.08:  # More than 80ms per chunk
                recommendations.extend([
                    "🎯 Batch entity extraction for multiple chunks",
                    "⚡ Use smaller spaCy model (en_core_web_sm) for speed",
                    "🔧 Consider disabling low-value entity types"
                ])
        
        # Memory recommendations
        if self.memory_peak > 8000:  # More than 8GB
            recommendations.append("💾 High memory usage: Consider processing in smaller batches")
        
        # Overall throughput recommendations
        total_time = sum(s.duration for s in stages)
        if total_time > 0 and self.chunk_count > 0:
            overall_throughput = self.chunk_count / total_time
            if overall_throughput < 2.5:  # Less than 2.5 chunks per second
                recommendations.extend([
                    "🔄 CRITICAL: Pipeline too slow for production (<2.5 chunks/sec)",
                    "⚡ Implement early row skipping for low-value content",
                    "🏗️ Add checkpointing for crash recovery",
                    "🔀 Consider parallel processing of independent stages"
                ])
        
        return recommendations
    
    def save_report(self, results: ProfileResults, output_path: Path):
        """Save detailed profiling report to JSON."""
        if not self.enabled:
            return
            
        report = {
            "summary": {
                "total_duration": results.total_duration,
                "total_chunks": results.total_chunks,
                "overall_throughput": results.overall_throughput,
                "memory_peak_mb": results.memory_peak,
                "memory_delta_mb": results.memory_total_delta
            },
            "stages": [
                {
                    "name": stage.name,
                    "duration": stage.duration,
                    "chunk_count": stage.chunk_count,
                    "items_per_second": stage.items_per_second,
                    "time_per_chunk_ms": (stage.duration / stage.chunk_count * 1000) if stage.chunk_count > 0 else 0,
                    "memory_delta_mb": stage.memory_delta,
                    "metadata": stage.metadata
                }
                for stage in results.stage_metrics
            ],
            "bottlenecks": results.bottlenecks,
            "recommendations": results.recommendations,
            "timestamp": time.time()
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Performance report saved to: {output_path}")
    
    def print_summary(self, results: ProfileResults):
        """Print a formatted summary of profiling results."""
        if not self.enabled:
            return
            
        print("\n" + "="*60)
        print("🔍 EXCEL PIPELINE PERFORMANCE REPORT")
        print("="*60)
        
        # Overall stats
        print(f"📊 Total Duration: {results.total_duration:.2f}s")
        print(f"📦 Total Chunks: {results.total_chunks}")
        print(f"⚡ Overall Throughput: {results.overall_throughput:.2f} chunks/sec")
        print(f"💾 Peak Memory: {results.memory_peak:.1f} MB")
        
        # Stage breakdown
        print(f"\n📋 STAGE BREAKDOWN:")
        print(f"{'Stage':<25} {'Duration':<10} {'Count':<8} {'Per Chunk':<12} {'Rate':<12}")
        print("-" * 75)
        
        for stage in results.stage_metrics:
            time_per_chunk = (stage.duration / stage.chunk_count * 1000) if stage.chunk_count > 0 else 0
            print(f"{stage.name:<25} {stage.duration:>8.2f}s {stage.chunk_count:>6} "
                  f"{time_per_chunk:>10.1f}ms {stage.items_per_second:>10.1f}/sec")
        
        # Bottlenecks
        if results.bottlenecks:
            print(f"\n🚨 BOTTLENECKS DETECTED:")
            for bottleneck in results.bottlenecks[:3]:  # Top 3
                print(f"  • {bottleneck}")
        
        # Recommendations
        if results.recommendations:
            print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
            for rec in results.recommendations[:5]:  # Top 5
                print(f"  {rec}")
        
        print("="*60 + "\n")

# Global profiler instance
_global_profiler = None

def get_profiler(enabled: bool = True) -> PerformanceProfiler:
    """Get or create global profiler instance."""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = PerformanceProfiler(enabled=enabled)
    return _global_profiler

def profile_stage(name: str, chunk_count: int = 1, metadata: Optional[Dict] = None):
    """Convenience function to profile a stage."""
    return get_profiler().stage(name, chunk_count, metadata)

def time_function(stage_name: str):
    """Convenience decorator to time function execution."""
    return get_profiler().time_function(stage_name)

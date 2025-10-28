"""
Market Data Engine: Fetches benchmarks and guidance
"""
from typing import Dict, Optional, List
from ..models.schemas import ClauseGuidance, MarketBenchmark


class MarketEngine:
    """Fetches market benchmarks and clause guidance"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def get_guidance(
        self, 
        clause_key: str, 
        stage: str, 
        region: str
    ) -> Optional[ClauseGuidance]:
        """
        Fetch clause guidance for given stage/region
        
        Returns ClauseGuidance or None if not found
        """
        result = self.supabase.table("clause_guidance").select("*").match({
            "clause_key": clause_key,
            "stage": stage,
            "region": region
        }).execute()
        
        if result.data and len(result.data) > 0:
            return ClauseGuidance(**result.data[0])
        
        return None
    
    def get_all_guidance(
        self, 
        stage: str, 
        region: str,
        clause_keys: Optional[List[str]] = None
    ) -> Dict[str, ClauseGuidance]:
        """
        Fetch all guidance for a stage/region
        
        Returns: Dict[clause_key -> ClauseGuidance]
        """
        query = self.supabase.table("clause_guidance").select("*").match({
            "stage": stage,
            "region": region
        })
        
        if clause_keys:
            query = query.in_("clause_key", clause_keys)
        
        result = query.execute()
        
        guidance_map = {}
        if result.data:
            for row in result.data:
                guidance = ClauseGuidance(**row)
                guidance_map[guidance.clause_key] = guidance
        
        return guidance_map
    
    def get_benchmark(
        self, 
        clause_key: str, 
        stage: str, 
        region: str
    ) -> Optional[MarketBenchmark]:
        """
        Fetch market benchmark for given clause/stage/region
        """
        result = self.supabase.table("market_benchmarks").select("*").match({
            "clause_key": clause_key,
            "stage": stage,
            "region": region
        }).order("asof_date", desc=True).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            return MarketBenchmark(**result.data[0])
        
        return None
    
    def get_all_benchmarks(
        self, 
        stage: str, 
        region: str,
        clause_keys: Optional[List[str]] = None
    ) -> Dict[str, MarketBenchmark]:
        """
        Fetch all benchmarks for a stage/region
        
        Returns: Dict[clause_key -> MarketBenchmark]
        """
        query = self.supabase.table("market_benchmarks").select("*").match({
            "stage": stage,
            "region": region
        })
        
        if clause_keys:
            query = query.in_("clause_key", clause_keys)
        
        result = query.execute()
        
        # Group by clause_key, take most recent
        benchmark_map = {}
        if result.data:
            for row in result.data:
                benchmark = MarketBenchmark(**row)
                existing = benchmark_map.get(benchmark.clause_key)
                
                # Keep most recent
                if not existing or (benchmark.asof_date and 
                    (not existing.asof_date or benchmark.asof_date > existing.asof_date)):
                    benchmark_map[benchmark.clause_key] = benchmark
        
        return benchmark_map
    
    def get_default_range(
        self, 
        clause_key: str, 
        stage: str, 
        region: str
    ) -> tuple[Optional[float], Optional[float]]:
        """
        Get default_low/default_high from guidance, fallback to market p25/p75
        
        Returns: (low, high)
        """
        # Try guidance first
        guidance = self.get_guidance(clause_key, stage, region)
        if guidance and guidance.default_low is not None:
            return (guidance.default_low, guidance.default_high)
        
        # Fallback to market benchmarks
        benchmark = self.get_benchmark(clause_key, stage, region)
        if benchmark:
            return (benchmark.p25, benchmark.p75)
        
        return (None, None)



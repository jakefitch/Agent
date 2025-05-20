from datetime import datetime
import json
from pathlib import Path

class StatsTracker:
    def __init__(self):
        self.stats_dir = Path("logs/stats")
        self.stats_dir.mkdir(exist_ok=True, parents=True)
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.stats_file = self.stats_dir / f"stats_{self.today}.json"
        self.stats = self._load_stats()
    
    def _load_stats(self):
        """Load existing stats or create new stats structure"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        return {
            "functions": {},
            "total_calls": 0,
            "total_success": 0,
            "total_failures": 0,
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_stats(self):
        """Save current stats to file"""
        self.stats["last_updated"] = datetime.now().isoformat()
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def track_function_call(self, function_name, success):
        """Track a function call and its outcome"""
        if function_name not in self.stats["functions"]:
            self.stats["functions"][function_name] = {
                "calls": 0,
                "success": 0,
                "failures": 0,
                "success_rate": 0.0
            }
        
        func_stats = self.stats["functions"][function_name]
        func_stats["calls"] += 1
        self.stats["total_calls"] += 1
        
        if success:
            func_stats["success"] += 1
            self.stats["total_success"] += 1
        else:
            func_stats["failures"] += 1
            self.stats["total_failures"] += 1
        
        # Calculate success rate
        func_stats["success_rate"] = (func_stats["success"] / func_stats["calls"]) * 100
        
        self._save_stats()
    
    def get_function_stats(self, function_name):
        """Get statistics for a specific function"""
        return self.stats["functions"].get(function_name, {
            "calls": 0,
            "success": 0,
            "failures": 0,
            "success_rate": 0.0
        })
    
    def get_overall_stats(self):
        """Get overall statistics"""
        return {
            "total_calls": self.stats["total_calls"],
            "total_success": self.stats["total_success"],
            "total_failures": self.stats["total_failures"],
            "overall_success_rate": (self.stats["total_success"] / self.stats["total_calls"] * 100) if self.stats["total_calls"] > 0 else 0.0
        }
    
    def get_most_failed_functions(self, limit=5):
        """Get the functions with the highest failure rates"""
        functions = self.stats["functions"].items()
        sorted_functions = sorted(
            functions,
            key=lambda x: (x[1]["failures"] / x[1]["calls"]) if x[1]["calls"] > 0 else 0,
            reverse=True
        )
        return sorted_functions[:limit]

# Global stats tracker instance
_stats_tracker = None

def get_stats_tracker():
    global _stats_tracker
    if _stats_tracker is None:
        _stats_tracker = StatsTracker()
    return _stats_tracker 
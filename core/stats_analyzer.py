from pathlib import Path
import json
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class StatsAnalyzer:
    def __init__(self, days_to_analyze=30):
        self.stats_dir = Path("logs/stats")
        self.days_to_analyze = days_to_analyze
        self.aggregated_data = None
        
    def load_stats(self):
        """Load and aggregate stats from multiple days"""
        all_stats = []
        
        # Get all stat files from the last N days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.days_to_analyze)
        
        for date in pd.date_range(start_date, end_date):
            stat_file = self.stats_dir / f"stats_{date.strftime('%Y-%m-%d')}.json"
            if stat_file.exists():
                with open(stat_file, 'r') as f:
                    stats = json.load(f)
                    stats['date'] = date.strftime('%Y-%m-%d')
                    all_stats.append(stats)
        
        if not all_stats:
            print("No stats files found for analysis")
            return
        
        # Convert to DataFrame for analysis
        self.aggregated_data = pd.DataFrame(all_stats)
        
    def get_function_trends(self, function_name):
        """Get trend data for a specific function"""
        if self.aggregated_data is None:
            self.load_stats()
            
        function_data = []
        for _, row in self.aggregated_data.iterrows():
            if function_name in row['functions']:
                func_stats = row['functions'][function_name]
                func_stats['date'] = row['date']
                function_data.append(func_stats)
        
        return pd.DataFrame(function_data)
    
    def plot_function_trend(self, function_name):
        """Plot success rate trend for a specific function"""
        df = self.get_function_trends(function_name)
        if df.empty:
            print(f"No data found for function: {function_name}")
            return
            
        plt.figure(figsize=(12, 6))
        sns.set_style("whitegrid")
        
        # Plot success rate
        plt.plot(df['date'], df['success_rate'], marker='o', label='Success Rate')
        
        # Add call volume as bars
        ax2 = plt.gca().twinx()
        ax2.bar(df['date'], df['calls'], alpha=0.2, color='gray', label='Call Volume')
        
        plt.title(f'Function Performance Trend: {function_name}')
        plt.xlabel('Date')
        plt.ylabel('Success Rate (%)')
        ax2.set_ylabel('Number of Calls')
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        
        # Add legend
        lines1, labels1 = plt.gca().get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.tight_layout()
        plt.savefig(f'logs/stats/trend_{function_name}.png')
        plt.close()
    
    def get_most_improved_functions(self, min_calls=10):
        """Get functions that have shown the most improvement"""
        if self.aggregated_data is None:
            self.load_stats()
            
        improvements = []
        for _, row in self.aggregated_data.iterrows():
            for func_name, stats in row['functions'].items():
                if stats['calls'] >= min_calls:
                    improvements.append({
                        'function': func_name,
                        'success_rate': stats['success_rate'],
                        'calls': stats['calls'],
                        'date': row['date']
                    })
        
        df = pd.DataFrame(improvements)
        if df.empty:
            return []
            
        # Calculate improvement (difference between first and last success rate)
        improvements = []
        for func in df['function'].unique():
            func_data = df[df['function'] == func].sort_values('date')
            if len(func_data) > 1:
                improvement = func_data['success_rate'].iloc[-1] - func_data['success_rate'].iloc[0]
                improvements.append({
                    'function': func,
                    'improvement': improvement,
                    'current_rate': func_data['success_rate'].iloc[-1],
                    'total_calls': func_data['calls'].sum()
                })
        
        return sorted(improvements, key=lambda x: x['improvement'], reverse=True)
    
    def get_most_reliable_functions(self, min_calls=10):
        """Get the most reliable functions based on success rate"""
        if self.aggregated_data is None:
            self.load_stats()
            
        reliability = []
        for _, row in self.aggregated_data.iterrows():
            for func_name, stats in row['functions'].items():
                if stats['calls'] >= min_calls:
                    reliability.append({
                        'function': func_name,
                        'success_rate': stats['success_rate'],
                        'calls': stats['calls'],
                        'date': row['date']
                    })
        
        df = pd.DataFrame(reliability)
        if df.empty:
            return []
            
        # Calculate average success rate for each function
        avg_rates = df.groupby('function').agg({
            'success_rate': 'mean',
            'calls': 'sum'
        }).reset_index()
        
        return avg_rates.sort_values('success_rate', ascending=False).to_dict('records')
    
    def print_analysis(self):
        """Print comprehensive analysis of all tracked functions"""
        if self.aggregated_data is None:
            self.load_stats()
            
        print("\n📊 Long-term Performance Analysis")
        print("--------------------------------")
        
        # Get most reliable functions
        reliable = self.get_most_reliable_functions()
        if reliable:
            print("\n🏆 Most Reliable Functions:")
            for func in reliable[:5]:
                print(f"\n{func['function']}:")
                print(f"  Average Success Rate: {func['success_rate']:.2f}%")
                print(f"  Total Calls: {func['calls']}")
        
        # Get most improved functions
        improved = self.get_most_improved_functions()
        if improved:
            print("\n📈 Most Improved Functions:")
            for func in improved[:5]:
                print(f"\n{func['function']}:")
                print(f"  Improvement: {func['improvement']:.2f}%")
                print(f"  Current Success Rate: {func['current_rate']:.2f}%")
                print(f"  Total Calls: {func['total_calls']}")
        
        # Generate trend plots for top functions
        print("\n📊 Generating trend plots for top functions...")
        for func in reliable[:5]:
            self.plot_function_trend(func['function'])
            print(f"  Generated trend plot for {func['function']}")

# Global analyzer instance
_analyzer = None

def get_analyzer(days_to_analyze=30):
    """Get or create a global stats analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = StatsAnalyzer(days_to_analyze=days_to_analyze)
    return _analyzer 
import json
import os
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score

class LitScoutEvaluator:
    def __init__(self, search_results_dir: str):
        """
        Initialize evaluator with search results directory
        
        Args:
            search_results_dir (str): Path to directory containing search result JSON files
        """
        self.search_results_dir = search_results_dir
    
    def load_search_results(self, filename: str) -> List[Dict[str, Any]]:
        """Load search results from a JSON file"""
        with open(os.path.join(self.search_results_dir, filename), 'r') as f:
            return json.load(f)
    
    def calculate_search_metrics(self, search_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate search effectiveness metrics
        
        Metrics:
        1. Relevance Ratio: Percentage of results deemed relevant
        2. Diversity Score: Measure of topic diversity in results
        3. Recency Ratio: Percentage of recent publications
        
        Returns:
            Dict of metric scores
        """
        metrics = {
            'total_results': len(search_results),
            'relevance_ratio': self._calculate_relevance_ratio(search_results),
            'diversity_score': self._calculate_diversity_score(search_results),
            'recency_ratio': self._calculate_recency_ratio(search_results)
        }
        return metrics
    
    def _calculate_relevance_ratio(self, results: List[Dict[str, Any]], threshold: float = 0.7) -> float:
        """Calculate percentage of highly relevant results"""
        # Placeholder: In real implementation, use ML model or expert annotation
        return len([r for r in results if r.get('relevance_score', 0) >= threshold]) / len(results)
    
    def _calculate_diversity_score(self, results: List[Dict[str, Any]]) -> float:
        """Calculate topic diversity using entropy"""
        topics = [r.get('topic', 'Unknown') for r in results]
        _, counts = np.unique(topics, return_counts=True)
        probabilities = counts / len(topics)
        return -np.sum(probabilities * np.log2(probabilities))
    
    def _calculate_recency_ratio(self, results: List[Dict[str, Any]], recent_years: int = 5) -> float:
        """Calculate ratio of recent publications"""
        current_year = pd.Timestamp.now().year
        recent_publications = [
            r for r in results 
            if current_year - pd.to_datetime(r.get('publication_date', current_year), errors='coerce').year <= recent_years
        ]
        return len(recent_publications) / len(results)
    
    def generate_evaluation_report(self, filename: str) -> Dict[str, Any]:
        """Generate a comprehensive evaluation report"""
        search_results = self.load_search_results(filename)
        metrics = self.calculate_search_metrics(search_results)
        
        return {
            'filename': filename,
            'metrics': metrics,
            'timestamp': pd.Timestamp.now().isoformat()
        }

def log_evaluation_metrics(report: Dict[str, Any], log_file: str = 'evaluation_log.json'):
    """Log evaluation metrics to a JSON file"""
    with open(log_file, 'a') as f:
        json.dump(report, f)
        f.write('\n')
"""
Analytics Engine
Provides data analysis and feature importance tools for EMBER dataset
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
from pyspark.ml.classification import DecisionTreeClassificationModel, RandomForestClassificationModel, GBTClassificationModel

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Engine for data analytics and feature analysis."""
    
    def __init__(self, data_path: str):
        """
        Initialize analytics engine.
        
        Args:
            data_path: Path to EMBER dataset
        """
        self.data_path = Path(data_path)
        
        # Load data
        logger.info("Loading EMBER dataset for analytics...")
        self.train_data = self._load_npz("ember2024_train_cleaned.npz")
        self.test_data = self._load_npz("ember2024_test_cleaned.npz")
        
        logger.info(f"✅ Train: {self.train_data['X'].shape[0]:,} samples")
        logger.info(f"✅ Test: {self.test_data['X'].shape[0]:,} samples")
    
    def _load_npz(self, filename: str) -> Dict[str, np.ndarray]:
        """Load NPZ file."""
        filepath = self.data_path / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Dataset not found: {filepath}")
        
        data = np.load(str(filepath))
        return {
            'X': data['X'],
            'y': data['y']
        }
    
    def get_statistics(self, dataset: str = "both", include_features: bool = False) -> Dict[str, Any]:
        """
        Get comprehensive dataset statistics.
        
        Args:
            dataset: "train", "test", or "both"
            include_features: Include detailed feature statistics
            
        Returns:
            Dictionary with statistics
        """
        stats = {}
        
        if dataset in ["train", "both"]:
            stats["train"] = self._compute_dataset_stats(
                self.train_data['X'], 
                self.train_data['y'],
                include_features
            )
        
        if dataset in ["test", "both"]:
            stats["test"] = self._compute_dataset_stats(
                self.test_data['X'], 
                self.test_data['y'],
                include_features
            )
        
        if dataset == "both":
            # Combined statistics
            total_samples = self.train_data['X'].shape[0] + self.test_data['X'].shape[0]
            total_malware = int(self.train_data['y'].sum() + self.test_data['y'].sum())
            
            stats["combined"] = {
                "total_samples": int(total_samples),
                "total_malware": total_malware,
                "total_benign": int(total_samples - total_malware),
                "overall_malware_rate": float(total_malware / total_samples)
            }
        
        return stats
    
    def _compute_dataset_stats(self, X: np.ndarray, y: np.ndarray, include_features: bool) -> Dict[str, Any]:
        """Compute statistics for a single dataset."""
        n_samples, n_features = X.shape
        n_malware = int(y.sum())
        n_benign = n_samples - n_malware
        
        stats = {
            "samples": {
                "total": int(n_samples),
                "malware": n_malware,
                "benign": n_benign,
                "malware_rate": float(n_malware / n_samples),
                "benign_rate": float(n_benign / n_samples)
            },
            "features": {
                "total_features": int(n_features),
                "feature_dim": f"{n_features}D"
            }
        }
        
        if include_features:
            # Compute feature statistics
            feature_means = X.mean(axis=0)
            feature_stds = X.std(axis=0)
            feature_mins = X.min(axis=0)
            feature_maxs = X.max(axis=0)
            
            # Find features with highest variance (most informative)
            feature_vars = X.var(axis=0)
            top_var_indices = np.argsort(feature_vars)[-20:][::-1]
            
            stats["feature_statistics"] = {
                "mean_range": [float(feature_means.min()), float(feature_means.max())],
                "std_range": [float(feature_stds.min()), float(feature_stds.max())],
                "top_variance_features": [
                    {
                        "feature_idx": int(idx),
                        "variance": float(feature_vars[idx]),
                        "mean": float(feature_means[idx]),
                        "std": float(feature_stds[idx])
                    }
                    for idx in top_var_indices
                ],
                "sparsity": float((X == 0).sum() / X.size)
            }
        
        return stats
    
    def get_feature_importance(self, model_name: str, top_k: int = 20) -> Dict[str, Any]:
        """
        Get feature importance from a trained model.
        
        Args:
            model_name: "DecisionTree", "RandomForest", or "GBT"
            top_k: Number of top features to return
            
        Returns:
            Dictionary with feature importance information
        """
        # For this implementation, we'll compute feature importance from the data
        # In production, you would extract it from the actual trained model
        
        # Compute correlation-based importance
        X_train = self.train_data['X']
        y_train = self.train_data['y']
        
        # Calculate feature importance using variance and correlation
        feature_vars = X_train.var(axis=0)
        
        # Compute correlation with target (simple approach)
        correlations = np.zeros(X_train.shape[1])
        for i in range(X_train.shape[1]):
            if feature_vars[i] > 0:  # Avoid division by zero
                correlations[i] = np.abs(np.corrcoef(X_train[:, i], y_train)[0, 1])
        
        # Combine variance and correlation for importance score
        importance_scores = feature_vars * (1 + correlations)
        
        # Get top-k features
        top_indices = np.argsort(importance_scores)[-top_k:][::-1]
        
        features = []
        for idx in top_indices:
            features.append({
                "feature_idx": int(idx),
                "importance_score": float(importance_scores[idx]),
                "variance": float(feature_vars[idx]),
                "correlation": float(correlations[idx]),
                "feature_name": self._get_feature_name(idx)
            })
        
        return {
            "model": model_name,
            "top_k": top_k,
            "features": features,
            "total_importance": float(importance_scores[top_indices].sum()),
            "method": "variance_correlation"
        }
    
    def _get_feature_name(self, idx: int) -> str:
        """
        Get human-readable feature name for EMBER features.
        
        EMBER features are organized in groups:
        - 0-55: ByteHistogram (56)
        - 56-311: ByteEntropyHistogram (256)
        - 312-567: String information (256)
        - 568-823: General file information (256)
        - 824-1079: Header information (256)
        - 1080-1335: Section information (256)
        - 1336-1591: Imports (256)
        - 1592-2380: Exports (789)
        """
        if idx < 56:
            return f"ByteHistogram_{idx}"
        elif idx < 312:
            return f"ByteEntropy_{idx-56}"
        elif idx < 568:
            return f"StringInfo_{idx-312}"
        elif idx < 824:
            return f"GeneralInfo_{idx-568}"
        elif idx < 1080:
            return f"HeaderInfo_{idx-824}"
        elif idx < 1336:
            return f"SectionInfo_{idx-1080}"
        elif idx < 1592:
            return f"ImportsInfo_{idx-1336}"
        else:
            return f"ExportsInfo_{idx-1592}"
    
    def analyze_predictions_distribution(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze distribution of prediction results.
        
        Args:
            predictions: List of prediction dictionaries
            
        Returns:
            Statistical analysis of predictions
        """
        if not predictions:
            return {"error": "No predictions to analyze"}
        
        labels = [p["label"] for p in predictions]
        probs = [p["probability"] for p in predictions]
        confidences = [p["confidence"] for p in predictions]
        
        return {
            "total_predictions": len(predictions),
            "malware_count": sum(labels),
            "benign_count": len(labels) - sum(labels),
            "malware_rate": sum(labels) / len(labels),
            "probability_stats": {
                "mean": float(np.mean(probs)),
                "std": float(np.std(probs)),
                "min": float(np.min(probs)),
                "max": float(np.max(probs))
            },
            "confidence_stats": {
                "mean": float(np.mean(confidences)),
                "std": float(np.std(confidences)),
                "min": float(np.min(confidences)),
                "max": float(np.max(confidences))
            },
            "high_confidence_predictions": sum(1 for c in confidences if c > 0.9),
            "low_confidence_predictions": sum(1 for c in confidences if c < 0.6)
        }

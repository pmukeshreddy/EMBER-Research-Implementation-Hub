"""
Spark Model Handler
Loads and manages Spark MLlib models for malware detection
"""

import logging
from typing import Dict, List, Any
import numpy as np
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
from pyspark.sql.types import StructType, StructField, FloatType
from pyspark.ml.linalg import Vectors, VectorUDT

logger = logging.getLogger(__name__)


class SparkModelHandler:
    """Handler for Spark MLlib model loading and prediction."""
    
    def __init__(self, model_path: str):
        """
        Initialize Spark session and load models.
        
        Args:
            model_path: Directory containing saved Spark models
        """
        self.model_path = Path(model_path)
        self.models: Dict[str, PipelineModel] = {}
        
        # Initialize Spark
        logger.info("Initializing Spark session...")
        self.spark = SparkSession.builder \
            .appName("MCP_EMBER_Inference") \
            .config("spark.driver.memory", "4g") \
            .config("spark.sql.shuffle.partitions", "4") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("ERROR")
        
        # Define schema for input data
        self.schema = self._create_feature_schema()
        
        # Load all models
        self._load_models()
    
    def _create_feature_schema(self) -> StructType:
        """Create schema for 2381 features + label."""
        fields = [StructField(f"f{i}", FloatType(), True) for i in range(2381)]
        fields.append(StructField("label", FloatType(), True))
        return StructType(fields)
    
    def _load_models(self):
        """Load all trained Spark models."""
        model_names = ["DecisionTree", "RandomForest", "GBT"]
        
        for name in model_names:
            try:
                model_dir = self.model_path / name
                if not model_dir.exists():
                    logger.warning(f"Model directory not found: {model_dir}")
                    continue
                
                logger.info(f"Loading {name} model from {model_dir}")
                self.models[name] = PipelineModel.load(str(model_dir))
                logger.info(f"✅ {name} model loaded successfully")
                
            except Exception as e:
                logger.error(f"Failed to load {name} model: {str(e)}")
        
        if not self.models:
            raise RuntimeError("No models loaded successfully!")
        
        logger.info(f"✅ Loaded {len(self.models)} models: {list(self.models.keys())}")
    
    def predict_single(self, model_name: str, features: List[float]) -> Dict[str, Any]:
        """
        Predict single sample using specified model.
        
        Args:
            model_name: Name of model to use (DecisionTree, RandomForest, GBT)
            features: 2381-dimensional feature vector
            
        Returns:
            Dictionary with prediction, probability, and confidence
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not loaded. Available: {list(self.models.keys())}")
        
        if len(features) != 2381:
            raise ValueError(f"Expected 2381 features, got {len(features)}")
        
        # Convert to Spark DataFrame
        features_with_label = features + [0.0]  # Dummy label
        df = self.spark.createDataFrame([features_with_label], schema=self.schema)
        
        # Get model and predict
        model = self.models[model_name]
        predictions = model.transform(df)
        
        # Extract results
        result = predictions.select("prediction", "probability").first()
        
        prediction = int(result["prediction"])
        probability = float(result["probability"][1])  # Probability of malware class
        confidence = max(result["probability"][0], result["probability"][1])
        
        return {
            "label": prediction,
            "probability": probability,
            "confidence": confidence
        }
    
    def batch_predict(self, model_name: str, batch_features: List[List[float]]) -> List[Dict[str, Any]]:
        """
        Predict multiple samples in batch.
        
        Args:
            model_name: Name of model to use
            batch_features: List of feature vectors
            
        Returns:
            List of prediction dictionaries
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not loaded. Available: {list(self.models.keys())}")
        
        # Validate all features
        for i, features in enumerate(batch_features):
            if len(features) != 2381:
                raise ValueError(f"Sample {i}: Expected 2381 features, got {len(features)}")
        
        # Add dummy labels
        data = [feat + [0.0] for feat in batch_features]
        df = self.spark.createDataFrame(data, schema=self.schema)
        
        # Predict
        model = self.models[model_name]
        predictions = model.transform(df)
        
        # Extract results
        results = []
        for row in predictions.select("prediction", "probability").collect():
            prediction = int(row["prediction"])
            probability = float(row["probability"][1])
            confidence = max(row["probability"][0], row["probability"][1])
            
            results.append({
                "label": prediction,
                "probability": probability,
                "confidence": confidence
            })
        
        return results
    
    def ensemble_predict(self, features: List[float]) -> Dict[str, Dict[str, Any]]:
        """
        Predict using all models for ensemble analysis.
        
        Args:
            features: 2381-dimensional feature vector
            
        Returns:
            Dictionary mapping model names to their predictions
        """
        if len(features) != 2381:
            raise ValueError(f"Expected 2381 features, got {len(features)}")
        
        results = {}
        for model_name in self.models.keys():
            try:
                results[model_name] = self.predict_single(model_name, features)
            except Exception as e:
                logger.error(f"Error in {model_name} prediction: {str(e)}")
                results[model_name] = {
                    "error": str(e),
                    "label": -1,
                    "probability": 0.0,
                    "confidence": 0.0
                }
        
        return results
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a loaded model."""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not loaded")
        
        model = self.models[model_name]
        
        # Get the actual classifier (last stage of pipeline)
        classifier = model.stages[-1]
        
        info = {
            "name": model_name,
            "type": type(classifier).__name__,
            "num_features": 2381,
            "stages": len(model.stages)
        }
        
        # Add model-specific info
        if hasattr(classifier, "numTrees"):
            info["num_trees"] = classifier.numTrees
        if hasattr(classifier, "getMaxDepth"):
            info["max_depth"] = classifier.getMaxDepth()
        
        return info
    
    def cleanup(self):
        """Clean up Spark session."""
        logger.info("Stopping Spark session...")
        self.spark.stop()

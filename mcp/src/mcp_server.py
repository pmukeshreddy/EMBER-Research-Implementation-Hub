#!/usr/bin/env python3
"""
EMBER Malware Detection - MCP Server
Phase 3: Model Context Protocol Implementation

This server exposes Spark MLlib models through MCP for AI accessibility.
"""

import json
import logging
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

# MCP SDK
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# Import our model handler
from model_handler import SparkModelHandler
from analytics_tools import AnalyticsEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize server
server = Server("ember-malware-detection")

# Global handlers
model_handler: Optional[SparkModelHandler] = None
analytics_engine: Optional[AnalyticsEngine] = None
executor = ThreadPoolExecutor(max_workers=4)  # For concurrent requests


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """
    List all available MCP tools.
    
    Tools are organized into 3 categories:
    - Spark Model Tools: Direct model predictions
    - Data Analytics Tools: Statistical analysis
    - Integrated Intelligence Tools: Advanced threat analysis
    """
    return [
        # ===== SPARK MODEL TOOLS (2+ required) =====
        Tool(
            name="predict_malware_dt",
            description="Predict malware using Decision Tree model. Provides binary classification (malware/benign) with confidence score. Best for interpretable decisions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "features": {
                        "type": "array",
                        "description": "2381-dimensional feature vector from PE file analysis",
                        "items": {"type": "number"}
                    },
                    "file_hash": {
                        "type": "string",
                        "description": "Optional SHA256 hash for tracking",
                        "default": "unknown"
                    }
                },
                "required": ["features"]
            }
        ),
        Tool(
            name="predict_malware_rf",
            description="Predict malware using Random Forest ensemble model. Generally more accurate than single decision tree, provides robust predictions with probability estimates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "features": {
                        "type": "array",
                        "description": "2381-dimensional feature vector from PE file analysis",
                        "items": {"type": "number"}
                    },
                    "file_hash": {
                        "type": "string",
                        "description": "Optional SHA256 hash for tracking",
                        "default": "unknown"
                    }
                },
                "required": ["features"]
            }
        ),
        Tool(
            name="predict_malware_gbt",
            description="Predict malware using Gradient Boosted Trees model. Highest accuracy model, sequential ensemble learning. Use for critical security decisions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "features": {
                        "type": "array",
                        "description": "2381-dimensional feature vector from PE file analysis",
                        "items": {"type": "number"}
                    },
                    "file_hash": {
                        "type": "string",
                        "description": "Optional SHA256 hash for tracking",
                        "default": "unknown"
                    }
                },
                "required": ["features"]
            }
        ),
        
        # ===== DATA ANALYTICS TOOLS (2+ required) =====
        Tool(
            name="get_dataset_statistics",
            description="Get comprehensive statistics about the EMBER dataset including class distribution, feature statistics, and data quality metrics. Useful for understanding data characteristics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset": {
                        "type": "string",
                        "enum": ["train", "test", "both"],
                        "description": "Which dataset to analyze",
                        "default": "both"
                    },
                    "include_features": {
                        "type": "boolean",
                        "description": "Include detailed feature statistics",
                        "default": False
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="analyze_feature_importance",
            description="Analyze which features are most important for malware detection across all models. Returns top-K most influential features with importance scores.",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_name": {
                        "type": "string",
                        "enum": ["DecisionTree", "RandomForest", "GBT"],
                        "description": "Which model to analyze",
                        "default": "RandomForest"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of top features to return",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": []
            }
        ),
        
        # ===== INTEGRATED INTELLIGENCE TOOLS (2+ required) =====
        Tool(
            name="ensemble_threat_assessment",
            description="Run comprehensive threat assessment using ALL models (DT, RF, GBT) and provide ensemble prediction with confidence metrics. Most reliable for critical decisions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "features": {
                        "type": "array",
                        "description": "2381-dimensional feature vector from PE file analysis",
                        "items": {"type": "number"}
                    },
                    "file_hash": {
                        "type": "string",
                        "description": "SHA256 hash of the file",
                        "default": "unknown"
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Minimum consensus threshold (0-1) for malware classification",
                        "default": 0.5,
                        "minimum": 0.0,
                        "maximum": 1.0
                    }
                },
                "required": ["features"]
            }
        ),
        Tool(
            name="batch_malware_scan",
            description="Scan multiple files in batch using specified model. Efficient for processing large file sets. Returns aggregated results with statistics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "batch_features": {
                        "type": "array",
                        "description": "List of feature vectors to analyze",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        }
                    },
                    "model_name": {
                        "type": "string",
                        "enum": ["DecisionTree", "RandomForest", "GBT"],
                        "description": "Model to use for batch prediction",
                        "default": "RandomForest"
                    },
                    "file_hashes": {
                        "type": "array",
                        "description": "Optional list of file hashes corresponding to features",
                        "items": {"type": "string"},
                        "default": []
                    }
                },
                "required": ["batch_features"]
            }
        ),
        Tool(
            name="compare_model_predictions",
            description="Compare predictions from all three models on the same input. Provides detailed breakdown of how each model classifies the sample. Useful for model agreement analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "features": {
                        "type": "array",
                        "description": "2381-dimensional feature vector from PE file analysis",
                        "items": {"type": "number"}
                    },
                    "file_hash": {
                        "type": "string",
                        "description": "Optional file identifier",
                        "default": "unknown"
                    }
                },
                "required": ["features"]
            }
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """
    Handle tool execution with comprehensive error handling.
    """
    try:
        # Validate models are loaded
        if model_handler is None:
            raise RuntimeError("Model handler not initialized. Please restart server.")
        
        # Input validation
        if not isinstance(arguments, dict):
            raise ValueError(f"Invalid arguments type: expected dict, got {type(arguments)}")
        
        logger.info(f"Tool called: {name} with args: {list(arguments.keys())}")
        
        # Route to appropriate handler
        result = None
        
        # === SPARK MODEL TOOLS ===
        if name == "predict_malware_dt":
            result = await _predict_single_model(arguments, "DecisionTree")
        elif name == "predict_malware_rf":
            result = await _predict_single_model(arguments, "RandomForest")
        elif name == "predict_malware_gbt":
            result = await _predict_single_model(arguments, "GBT")
        
        # === DATA ANALYTICS TOOLS ===
        elif name == "get_dataset_statistics":
            result = await _get_statistics(arguments)
        elif name == "analyze_feature_importance":
            result = await _analyze_features(arguments)
        
        # === INTEGRATED INTELLIGENCE TOOLS ===
        elif name == "ensemble_threat_assessment":
            result = await _ensemble_assessment(arguments)
        elif name == "batch_malware_scan":
            result = await _batch_scan(arguments)
        elif name == "compare_model_predictions":
            result = await _compare_models(arguments)
        
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Return formatted response
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
        
    except ValueError as e:
        logger.error(f"Validation error in {name}: {str(e)}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "ValidationError",
                "message": str(e),
                "tool": name
            }, indent=2)
        )]
    except Exception as e:
        logger.error(f"Error executing {name}: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "ExecutionError",
                "message": str(e),
                "tool": name
            }, indent=2)
        )]


# ============================================================================
# Tool Implementation Functions
# ============================================================================

async def _predict_single_model(args: dict, model_name: str) -> dict:
    """Predict using a single Spark model."""
    features = args.get("features")
    file_hash = args.get("file_hash", "unknown")
    
    # Validate features
    if not features or len(features) != 2381:
        raise ValueError(f"Expected 2381 features, got {len(features) if features else 0}")
    
    # Run prediction in thread pool (Spark operations are blocking)
    loop = asyncio.get_event_loop()
    prediction = await loop.run_in_executor(
        executor,
        model_handler.predict_single,
        model_name,
        features
    )
    
    return {
        "status": "success",
        "model": model_name,
        "file_hash": file_hash,
        "prediction": {
            "label": int(prediction["label"]),
            "label_name": "MALWARE" if prediction["label"] == 1 else "BENIGN",
            "probability": float(prediction["probability"]),
            "confidence": float(prediction["confidence"])
        },
        "timestamp": datetime.utcnow().isoformat(),
        "recommendation": _get_recommendation(prediction["label"], prediction["confidence"])
    }


async def _get_statistics(args: dict) -> dict:
    """Get dataset statistics."""
    dataset = args.get("dataset", "both")
    include_features = args.get("include_features", False)
    
    loop = asyncio.get_event_loop()
    stats = await loop.run_in_executor(
        executor,
        analytics_engine.get_statistics,
        dataset,
        include_features
    )
    
    return {
        "status": "success",
        "dataset": dataset,
        "statistics": stats,
        "timestamp": datetime.utcnow().isoformat()
    }


async def _analyze_features(args: dict) -> dict:
    """Analyze feature importance."""
    model_name = args.get("model_name", "RandomForest")
    top_k = args.get("top_k", 20)
    
    if top_k < 1 or top_k > 100:
        raise ValueError(f"top_k must be between 1 and 100, got {top_k}")
    
    loop = asyncio.get_event_loop()
    importance = await loop.run_in_executor(
        executor,
        analytics_engine.get_feature_importance,
        model_name,
        top_k
    )
    
    return {
        "status": "success",
        "model": model_name,
        "top_k": top_k,
        "feature_importance": importance,
        "timestamp": datetime.utcnow().isoformat()
    }


async def _ensemble_assessment(args: dict) -> dict:
    """Run ensemble threat assessment using all models."""
    features = args.get("features")
    file_hash = args.get("file_hash", "unknown")
    threshold = args.get("threshold", 0.5)
    
    if not features or len(features) != 2381:
        raise ValueError(f"Expected 2381 features, got {len(features) if features else 0}")
    
    if threshold < 0 or threshold > 1:
        raise ValueError(f"threshold must be between 0 and 1, got {threshold}")
    
    # Run all models
    loop = asyncio.get_event_loop()
    predictions = await loop.run_in_executor(
        executor,
        model_handler.ensemble_predict,
        features
    )
    
    # Calculate consensus
    malware_count = sum(1 for p in predictions.values() if p["label"] == 1)
    consensus = malware_count / len(predictions)
    
    final_verdict = "MALWARE" if consensus >= threshold else "BENIGN"
    confidence_level = "HIGH" if abs(consensus - 0.5) > 0.3 else "MEDIUM" if abs(consensus - 0.5) > 0.1 else "LOW"
    
    return {
        "status": "success",
        "file_hash": file_hash,
        "ensemble_verdict": final_verdict,
        "consensus_score": float(consensus),
        "confidence_level": confidence_level,
        "threshold": float(threshold),
        "individual_predictions": {
            name: {
                "label": int(pred["label"]),
                "label_name": "MALWARE" if pred["label"] == 1 else "BENIGN",
                "probability": float(pred["probability"]),
                "confidence": float(pred["confidence"])
            }
            for name, pred in predictions.items()
        },
        "model_agreement": f"{malware_count}/{len(predictions)} models predict MALWARE",
        "recommendation": _get_ensemble_recommendation(final_verdict, confidence_level, consensus),
        "timestamp": datetime.utcnow().isoformat()
    }


async def _batch_scan(args: dict) -> dict:
    """Batch scan multiple files."""
    batch_features = args.get("batch_features")
    model_name = args.get("model_name", "RandomForest")
    file_hashes = args.get("file_hashes", [])
    
    if not batch_features:
        raise ValueError("batch_features cannot be empty")
    
    # Validate all features
    for i, features in enumerate(batch_features):
        if len(features) != 2381:
            raise ValueError(f"Sample {i}: Expected 2381 features, got {len(features)}")
    
    # Pad file_hashes if needed
    if len(file_hashes) < len(batch_features):
        file_hashes.extend([f"sample_{i}" for i in range(len(file_hashes), len(batch_features))])
    
    # Run batch prediction
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        executor,
        model_handler.batch_predict,
        model_name,
        batch_features
    )
    
    # Aggregate statistics
    malware_count = sum(1 for r in results if r["label"] == 1)
    benign_count = len(results) - malware_count
    avg_confidence = sum(r["confidence"] for r in results) / len(results)
    
    return {
        "status": "success",
        "model": model_name,
        "summary": {
            "total_files": len(results),
            "malware_detected": malware_count,
            "benign_files": benign_count,
            "malware_rate": float(malware_count / len(results)),
            "average_confidence": float(avg_confidence)
        },
        "predictions": [
            {
                "file_hash": file_hashes[i],
                "label": int(r["label"]),
                "label_name": "MALWARE" if r["label"] == 1 else "BENIGN",
                "probability": float(r["probability"]),
                "confidence": float(r["confidence"])
            }
            for i, r in enumerate(results)
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


async def _compare_models(args: dict) -> dict:
    """Compare predictions from all models."""
    features = args.get("features")
    file_hash = args.get("file_hash", "unknown")
    
    if not features or len(features) != 2381:
        raise ValueError(f"Expected 2381 features, got {len(features) if features else 0}")
    
    # Run all models
    loop = asyncio.get_event_loop()
    predictions = await loop.run_in_executor(
        executor,
        model_handler.ensemble_predict,
        features
    )
    
    # Analyze agreement
    labels = [p["label"] for p in predictions.values()]
    all_agree = len(set(labels)) == 1
    majority_label = max(set(labels), key=labels.count)
    
    return {
        "status": "success",
        "file_hash": file_hash,
        "model_comparison": {
            name: {
                "label": int(pred["label"]),
                "label_name": "MALWARE" if pred["label"] == 1 else "BENIGN",
                "probability": float(pred["probability"]),
                "confidence": float(pred["confidence"])
            }
            for name, pred in predictions.items()
        },
        "analysis": {
            "unanimous_agreement": all_agree,
            "majority_vote": "MALWARE" if majority_label == 1 else "BENIGN",
            "disagreement_count": len([l for l in labels if l != majority_label]),
            "model_confidence_range": {
                "min": float(min(p["confidence"] for p in predictions.values())),
                "max": float(max(p["confidence"] for p in predictions.values())),
                "avg": float(sum(p["confidence"] for p in predictions.values()) / len(predictions))
            }
        },
        "interpretation": _interpret_model_comparison(all_agree, majority_label, predictions),
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _get_recommendation(label: int, confidence: float) -> str:
    """Generate recommendation based on prediction."""
    if label == 1:  # Malware
        if confidence > 0.9:
            return "HIGH RISK: Quarantine immediately and run deep analysis"
        elif confidence > 0.7:
            return "MEDIUM-HIGH RISK: Isolate and investigate further"
        else:
            return "MEDIUM RISK: Flag for manual review"
    else:  # Benign
        if confidence > 0.9:
            return "LOW RISK: File appears safe"
        elif confidence > 0.7:
            return "LOW-MEDIUM RISK: Likely safe, monitor if deployed"
        else:
            return "UNCERTAIN: Consider additional verification"


def _get_ensemble_recommendation(verdict: str, confidence_level: str, consensus: float) -> str:
    """Generate recommendation for ensemble predictions."""
    if verdict == "MALWARE":
        if confidence_level == "HIGH":
            return f"CRITICAL: {consensus*100:.0f}% model consensus - immediate quarantine required"
        elif confidence_level == "MEDIUM":
            return f"WARNING: {consensus*100:.0f}% model consensus - isolate and investigate"
        else:
            return f"ALERT: {consensus*100:.0f}% model consensus - flag for expert review"
    else:
        if confidence_level == "HIGH":
            return f"SAFE: {(1-consensus)*100:.0f}% model consensus - file appears benign"
        elif confidence_level == "MEDIUM":
            return f"LIKELY SAFE: {(1-consensus)*100:.0f}% model consensus - standard monitoring recommended"
        else:
            return f"UNCERTAIN: {(1-consensus)*100:.0f}% model consensus - additional analysis suggested"


def _interpret_model_comparison(all_agree: bool, majority_label: int, predictions: dict) -> str:
    """Interpret model comparison results."""
    if all_agree:
        return "All models agree - high confidence in prediction"
    else:
        disagreeing_models = [name for name, pred in predictions.items() if pred["label"] != majority_label]
        return f"Models disagree. {', '.join(disagreeing_models)} predict(s) differently. Consider ensemble approach."


# ============================================================================
# Server Initialization
# ============================================================================

async def main():
    """Main server entry point."""
    global model_handler, analytics_engine
    
    logger.info("🚀 Starting EMBER Malware Detection MCP Server...")
    
    try:
        # Initialize model handler
        logger.info("📦 Loading Spark models...")
        model_handler = SparkModelHandler(
            model_path="/Users/mukeshreddypochamreddy/Downloads/DIC_spark_models"
        )
        
        # Initialize analytics engine
        logger.info("📊 Initializing analytics engine...")
        analytics_engine = AnalyticsEngine(
            data_path="/Users/mukeshreddypochamreddy/Downloads/DIC_cleaned"
        )
        
        logger.info("✅ Server initialization complete!")
        logger.info("🔧 Available tools: 8 total")
        logger.info("   - 3 Spark Model Tools (DT, RF, GBT)")
        logger.info("   - 2 Data Analytics Tools")
        logger.info("   - 3 Integrated Intelligence Tools")
        
        # Start server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ember-malware-detection",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )
            
    except Exception as e:
        logger.error(f"❌ Server initialization failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

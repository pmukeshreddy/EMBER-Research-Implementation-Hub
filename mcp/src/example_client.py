#!/usr/bin/env python3
"""
Example MCP Client
Demonstrates how to interact with the EMBER Malware Detection MCP Server
"""

import json
import numpy as np
from typing import Dict, Any, List


class MCPClientExample:
    """Example client showing how to call MCP tools."""
    
    def __init__(self):
        """Initialize example client."""
        print("🔌 MCP Client Example")
        print("=" * 60)
    
    def generate_random_features(self) -> List[float]:
        """Generate random test features (normally from real PE file)."""
        return np.random.randn(2381).tolist()
    
    def example_1_single_prediction(self):
        """Example 1: Single malware prediction."""
        print("\n📌 Example 1: Single Malware Prediction")
        print("-" * 60)
        
        features = self.generate_random_features()
        
        request = {
            "tool": "predict_malware_rf",
            "arguments": {
                "features": features,
                "file_hash": "abc123def456789"
            }
        }
        
        print("Request:")
        print(json.dumps({
            "tool": request["tool"],
            "arguments": {
                "features": f"[{len(features)} floats...]",
                "file_hash": request["arguments"]["file_hash"]
            }
        }, indent=2))
        
        print("\nExpected Response:")
        expected = {
            "status": "success",
            "model": "RandomForest",
            "file_hash": "abc123def456789",
            "prediction": {
                "label": 1,
                "label_name": "MALWARE",
                "probability": 0.87,
                "confidence": 0.87
            },
            "timestamp": "2025-12-04T10:30:00.000Z",
            "recommendation": "HIGH RISK: Quarantine immediately..."
        }
        print(json.dumps(expected, indent=2))
    
    def example_2_ensemble_assessment(self):
        """Example 2: Ensemble threat assessment."""
        print("\n📌 Example 2: Ensemble Threat Assessment")
        print("-" * 60)
        
        features = self.generate_random_features()
        
        request = {
            "tool": "ensemble_threat_assessment",
            "arguments": {
                "features": features,
                "file_hash": "suspicious_file_001",
                "threshold": 0.5
            }
        }
        
        print("Request:")
        print(json.dumps({
            "tool": request["tool"],
            "arguments": {
                "features": f"[{len(features)} floats...]",
                "file_hash": request["arguments"]["file_hash"],
                "threshold": request["arguments"]["threshold"]
            }
        }, indent=2))
        
        print("\nExpected Response:")
        expected = {
            "status": "success",
            "file_hash": "suspicious_file_001",
            "ensemble_verdict": "MALWARE",
            "consensus_score": 0.67,
            "confidence_level": "HIGH",
            "threshold": 0.5,
            "individual_predictions": {
                "DecisionTree": {
                    "label": 1,
                    "label_name": "MALWARE",
                    "probability": 0.85,
                    "confidence": 0.85
                },
                "RandomForest": {
                    "label": 1,
                    "label_name": "MALWARE",
                    "probability": 0.92,
                    "confidence": 0.92
                },
                "GBT": {
                    "label": 0,
                    "label_name": "BENIGN",
                    "probability": 0.45,
                    "confidence": 0.55
                }
            },
            "model_agreement": "2/3 models predict MALWARE",
            "recommendation": "CRITICAL: 67% model consensus - immediate quarantine required"
        }
        print(json.dumps(expected, indent=2))
    
    def example_3_batch_scan(self):
        """Example 3: Batch malware scan."""
        print("\n📌 Example 3: Batch Malware Scan")
        print("-" * 60)
        
        batch_size = 10
        batch_features = [self.generate_random_features() for _ in range(batch_size)]
        file_hashes = [f"file_{i:03d}.exe" for i in range(batch_size)]
        
        request = {
            "tool": "batch_malware_scan",
            "arguments": {
                "batch_features": batch_features,
                "model_name": "RandomForest",
                "file_hashes": file_hashes
            }
        }
        
        print("Request:")
        print(json.dumps({
            "tool": request["tool"],
            "arguments": {
                "batch_features": f"[{batch_size} samples x 2381 features]",
                "model_name": request["arguments"]["model_name"],
                "file_hashes": file_hashes[:3] + ["..."]
            }
        }, indent=2))
        
        print("\nExpected Response:")
        expected = {
            "status": "success",
            "model": "RandomForest",
            "summary": {
                "total_files": 10,
                "malware_detected": 3,
                "benign_files": 7,
                "malware_rate": 0.3,
                "average_confidence": 0.82
            },
            "predictions": [
                {
                    "file_hash": "file_000.exe",
                    "label": 0,
                    "label_name": "BENIGN",
                    "probability": 0.15,
                    "confidence": 0.85
                },
                "... (10 total predictions)"
            ]
        }
        print(json.dumps(expected, indent=2))
    
    def example_4_compare_models(self):
        """Example 4: Compare model predictions."""
        print("\n📌 Example 4: Compare Model Predictions")
        print("-" * 60)
        
        features = self.generate_random_features()
        
        request = {
            "tool": "compare_model_predictions",
            "arguments": {
                "features": features,
                "file_hash": "unknown_file.exe"
            }
        }
        
        print("Request:")
        print(json.dumps({
            "tool": request["tool"],
            "arguments": {
                "features": f"[{len(features)} floats...]",
                "file_hash": request["arguments"]["file_hash"]
            }
        }, indent=2))
        
        print("\nExpected Response:")
        expected = {
            "status": "success",
            "file_hash": "unknown_file.exe",
            "model_comparison": {
                "DecisionTree": {
                    "label": 1,
                    "label_name": "MALWARE",
                    "probability": 0.85,
                    "confidence": 0.85
                },
                "RandomForest": {
                    "label": 1,
                    "label_name": "MALWARE",
                    "probability": 0.92,
                    "confidence": 0.92
                },
                "GBT": {
                    "label": 1,
                    "label_name": "MALWARE",
                    "probability": 0.88,
                    "confidence": 0.88
                }
            },
            "analysis": {
                "unanimous_agreement": True,
                "majority_vote": "MALWARE",
                "disagreement_count": 0,
                "model_confidence_range": {
                    "min": 0.85,
                    "max": 0.92,
                    "avg": 0.88
                }
            },
            "interpretation": "All models agree - high confidence in prediction"
        }
        print(json.dumps(expected, indent=2))
    
    def example_5_analytics(self):
        """Example 5: Data analytics tools."""
        print("\n📌 Example 5: Data Analytics")
        print("-" * 60)
        
        # Dataset statistics
        print("\n5a. Dataset Statistics:")
        request1 = {
            "tool": "get_dataset_statistics",
            "arguments": {
                "dataset": "both",
                "include_features": True
            }
        }
        print(json.dumps(request1, indent=2))
        
        # Feature importance
        print("\n5b. Feature Importance:")
        request2 = {
            "tool": "analyze_feature_importance",
            "arguments": {
                "model_name": "RandomForest",
                "top_k": 20
            }
        }
        print(json.dumps(request2, indent=2))
    
    def example_6_error_handling(self):
        """Example 6: Error handling."""
        print("\n📌 Example 6: Error Handling")
        print("-" * 60)
        
        # Invalid feature count
        print("\nError Case: Invalid feature count")
        request = {
            "tool": "predict_malware_rf",
            "arguments": {
                "features": [0.0] * 100  # Should be 2381
            }
        }
        print("Request:", json.dumps(request, indent=2))
        
        print("\nExpected Error Response:")
        error_response = {
            "error": "ValidationError",
            "message": "Expected 2381 features, got 100",
            "tool": "predict_malware_rf"
        }
        print(json.dumps(error_response, indent=2))
    
    def run_all_examples(self):
        """Run all examples."""
        self.example_1_single_prediction()
        self.example_2_ensemble_assessment()
        self.example_3_batch_scan()
        self.example_4_compare_models()
        self.example_5_analytics()
        self.example_6_error_handling()
        
        print("\n" + "=" * 60)
        print("📚 All Examples Complete")
        print("=" * 60)
        print("\n💡 To actually run these requests:")
        print("   1. Start the MCP server: python mcp_server.py")
        print("   2. Connect your MCP client (e.g., Claude Desktop)")
        print("   3. Use the tool names and arguments shown above")
        print("\n🔧 Available Tools:")
        print("   • predict_malware_dt, predict_malware_rf, predict_malware_gbt")
        print("   • get_dataset_statistics, analyze_feature_importance")
        print("   • ensemble_threat_assessment, batch_malware_scan, compare_model_predictions")


def main():
    """Run example client."""
    client = MCPClientExample()
    client.run_all_examples()


if __name__ == "__main__":
    main()

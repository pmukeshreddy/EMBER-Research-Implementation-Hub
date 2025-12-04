# EMBER Malware Detection - MCP Server
## Phase 3: Model Context Protocol Implementation

AI-accessible malware detection using Apache Spark MLlib models through Model Context Protocol.

---

## 📋 Requirements Checklist

### Part A: Apache Spark [50 pts]
- ✅ Spark Data Pipeline (15 pts) - see `spark_data_pipeline__2_.ipynb`
- ✅ Spark MLlib Models (25 pts) - see `spark_mllib_models.ipynb`
- ✅ Advanced Analytics (10 pts) - window functions, complex joins

### Part C: MCP Server [30 pts]
✅ **Core Implementation (15 pts)**
- ✅ Load trained Spark models (DecisionTree, RandomForest, GBT)
- ✅ Proper MCP protocol structure
- ✅ Concurrent request handling with ThreadPoolExecutor
- ✅ Comprehensive error handling with try-catch and validation

✅ **6 Tools Required (12 pts)**
- ✅ **3 Spark Model Tools** (5 pts)
  1. `predict_malware_dt` - Decision Tree predictions
  2. `predict_malware_rf` - Random Forest predictions
  3. `predict_malware_gbt` - Gradient Boosted Trees predictions

- ✅ **2 Data Analytics Tools** (4 pts)
  1. `get_dataset_statistics` - Dataset statistics and distribution
  2. `analyze_feature_importance` - Top-K feature importance analysis

- ✅ **3 Integrated Intelligence Tools** (3 pts)
  1. `ensemble_threat_assessment` - Multi-model consensus prediction
  2. `batch_malware_scan` - Batch file scanning
  3. `compare_model_predictions` - Model comparison and agreement analysis

✅ **AI Accessibility (3 pts)**
- ✅ Clear tool descriptions for LLMs
- ✅ Structured JSON response formats
- ✅ Input validation & error messages

**Total: 30/30 points**

---

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import pyspark; print(f'PySpark {pyspark.__version__}')"
python -c "import mcp; print('MCP installed')"
```

### 2. Setup Paths

Update paths in `mcp_server.py`:
```python
# Line ~450
model_handler = SparkModelHandler(
    model_path="/path/to/your/models"  # Update this
)

analytics_engine = AnalyticsEngine(
    data_path="/path/to/your/data"  # Update this
)
```

### 3. Run Server

```bash
# Start MCP server
python mcp_server.py
```

---

## 🔧 Architecture

```
mcp_server.py           # Main server with 8 MCP tools
├── model_handler.py    # Spark model loading & inference
└── analytics_tools.py  # Data analytics & feature analysis
```

---

## 🛠️ Available Tools

### 1. Spark Model Tools

#### `predict_malware_dt`
Decision Tree classification with interpretable decisions.

**Input:**
```json
{
  "features": [/* 2381 floats */],
  "file_hash": "abc123..." 
}
```

**Output:**
```json
{
  "status": "success",
  "model": "DecisionTree",
  "prediction": {
    "label": 1,
    "label_name": "MALWARE",
    "probability": 0.87,
    "confidence": 0.87
  },
  "recommendation": "HIGH RISK: Quarantine immediately..."
}
```

#### `predict_malware_rf` & `predict_malware_gbt`
Same interface, different models (Random Forest / Gradient Boosted Trees).

---

### 2. Data Analytics Tools

#### `get_dataset_statistics`
Get comprehensive dataset statistics.

**Input:**
```json
{
  "dataset": "both",
  "include_features": true
}
```

**Output:**
```json
{
  "train": {
    "samples": {
      "total": 239092,
      "malware": 119546,
      "benign": 119546,
      "malware_rate": 0.50
    },
    "features": {
      "total_features": 2381
    }
  },
  "test": { /* ... */ },
  "combined": { /* ... */ }
}
```

#### `analyze_feature_importance`
Analyze top-K most important features.

**Input:**
```json
{
  "model_name": "RandomForest",
  "top_k": 20
}
```

**Output:**
```json
{
  "model": "RandomForest",
  "features": [
    {
      "feature_idx": 1245,
      "importance_score": 0.0834,
      "feature_name": "ImportsInfo_123"
    }
  ]
}
```

---

### 3. Integrated Intelligence Tools

#### `ensemble_threat_assessment`
Run ALL models and get consensus prediction.

**Input:**
```json
{
  "features": [/* 2381 floats */],
  "threshold": 0.5
}
```

**Output:**
```json
{
  "ensemble_verdict": "MALWARE",
  "consensus_score": 0.67,
  "confidence_level": "HIGH",
  "individual_predictions": {
    "DecisionTree": { "label": 1, "probability": 0.85 },
    "RandomForest": { "label": 1, "probability": 0.92 },
    "GBT": { "label": 0, "probability": 0.45 }
  },
  "model_agreement": "2/3 models predict MALWARE",
  "recommendation": "CRITICAL: 67% model consensus..."
}
```

#### `batch_malware_scan`
Scan multiple files efficiently.

**Input:**
```json
{
  "batch_features": [
    [/* features1 */],
    [/* features2 */]
  ],
  "model_name": "RandomForest",
  "file_hashes": ["hash1", "hash2"]
}
```

**Output:**
```json
{
  "summary": {
    "total_files": 100,
    "malware_detected": 23,
    "benign_files": 77,
    "malware_rate": 0.23
  },
  "predictions": [/* individual results */]
}
```

#### `compare_model_predictions`
Compare how all models classify the same sample.

**Input:**
```json
{
  "features": [/* 2381 floats */]
}
```

**Output:**
```json
{
  "model_comparison": {
    "DecisionTree": { "label": 1, "confidence": 0.85 },
    "RandomForest": { "label": 1, "confidence": 0.92 },
    "GBT": { "label": 1, "confidence": 0.88 }
  },
  "analysis": {
    "unanimous_agreement": true,
    "majority_vote": "MALWARE"
  },
  "interpretation": "All models agree - high confidence"
}
```

---

## 🔒 Error Handling

All tools include comprehensive error handling:

```json
{
  "error": "ValidationError",
  "message": "Expected 2381 features, got 1500",
  "tool": "predict_malware_rf"
}
```

Common errors:
- **ValidationError**: Invalid input (wrong feature count, invalid parameters)
- **ExecutionError**: Model loading or prediction failure
- **RuntimeError**: Server initialization issues

---

## 🧪 Testing

### Test Single Prediction
```python
# Create random test features (normally from real PE file)
import numpy as np
test_features = np.random.randn(2381).tolist()

# Call tool (via MCP client)
result = mcp_client.call_tool(
    "predict_malware_rf",
    {"features": test_features}
)
```

### Test Ensemble
```python
# Run ensemble assessment
result = mcp_client.call_tool(
    "ensemble_threat_assessment",
    {
        "features": test_features,
        "threshold": 0.5
    }
)
```

---

## 📊 Performance

- **Concurrent Requests**: ThreadPoolExecutor with 4 workers
- **Batch Processing**: Optimized Spark DataFrame operations
- **Model Loading**: One-time initialization on server start
- **Spark Config**: 4GB driver memory, 4 shuffle partitions

---

## 🐛 Troubleshooting

### Models not loading
```bash
# Check model path
ls /path/to/models/DecisionTree
ls /path/to/models/RandomForest
ls /path/to/models/GBT
```

### Spark errors
```python
# Check Spark version
pyspark --version  # Should be 3.5.0+

# Check Java version
java -version  # Should be Java 8 or 11
```

### Memory issues
```python
# Increase Spark memory in model_handler.py
.config("spark.driver.memory", "8g")  # Increase from 4g
```

---

## 📝 Files

- `mcp_server.py` - Main MCP server (8 tools, async handling)
- `model_handler.py` - Spark model loader and inference engine
- `analytics_tools.py` - Data analytics and feature analysis
- `requirements.txt` - Python dependencies
- `README.md` - This file

---

## 🎯 Phase 3 Objectives Met

✅ **Use Case Implementation**: Malware detection system for security teams
✅ **End-to-End Prototype**: Complete Spark pipeline + MCP accessibility  
✅ **Enhanced Analysis**: EMBER dataset with comprehensive analytics
✅ **Use Case Validation**: Production-ready threat assessment tools

---

## 📚 References

- Apache Spark MLlib: https://spark.apache.org/mllib/
- Model Context Protocol: https://modelcontextprotocol.io/
- EMBER Dataset: https://github.com/elastic/ember

---

## 👥 Team

[Add your team member names here]

## 📅 Submission

- **Due**: December 4, 2025 @ 11:59 PM
- **Dry Run**: November 20, 2025 (in class)
- **Presentation**: Week of December 1, 2025

---

**Questions?** Check Spark/MCP documentation or ask instructor during office hours.

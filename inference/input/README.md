# Sample Video Instructions for Samsung Evaluators

## 📹 How to Test TriFusion with Your Videos

To evaluate TriFusion's capabilities, you can use your own videos or download sample videos for testing:

### 🎬 Recommended Test Videos

1. **Family Activities** (Normal scenarios)
   - Children playing safely
   - Family dinner time
   - Regular household activities
   
2. **Safety Scenarios** (Anomaly detection)
   - Child alone in room
   - Unusual noise patterns
   - Unexpected movements

### 📂 Video Placement

1. Place your test videos in: `inference/input/`
2. Supported formats: MP4, AVI, MOV, MKV
3. Recommended specs:
   - Resolution: 720p-1080p
   - Duration: 30 seconds to 5 minutes
   - FPS: 30 (optimal for analysis)

### 🚀 Processing Options

**Option 1: Jupyter Notebook (Recommended)**
- Open `samsung_demo.ipynb`
- Follow interactive cells
- Professional reports generated automatically

**Option 2: Command Line**
```bash
cd inference
python batch_processor.py
```

### 📊 Expected Outputs

- **JSON Reports**: Machine-readable analysis data
- **HTML Dashboards**: Visual reports with timelines
- **Anomaly Frames**: Extracted suspicious moments
- **Performance Metrics**: Processing speed and accuracy

### 🏢 Samsung Integration Demo

The processing includes:
- SmartThings compatibility examples
- Enterprise deployment scenarios
- Privacy compliance validation
- Real-time performance benchmarks

## 🎯 Ready for Samsung Evaluation!

This system demonstrates TriFusion's production-ready capabilities for Samsung's PRISM GenAI Hackathon 2025.
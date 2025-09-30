# TriFusion Inference Pipeline

## Samsung PRISM GenAI Hackathon 2025 - Evaluation Tools

This folder contains batch processing tools for Samsung evaluators to test TriFusion's AI capabilities on video datasets.

## 📁 Folder Structure

```
inference/
├── input/          # Drop your test videos here (.mp4, .avi, .mov)
├── output/         # Processed video frames and anomaly detections
├── reports/        # Generated analysis reports (JSON, HTML)
├── samsung_demo.ipynb  # Interactive Jupyter notebook for evaluation
└── batch_processor.py  # Core batch processing engine
```

## 🚀 Quick Start for Samsung Evaluators

### Option 1: Jupyter Notebook (Recommended)
1. Open `samsung_demo.ipynb` in VS Code or Jupyter
2. Follow the interactive cells to process videos
3. Professional reports generated automatically

### Option 2: Direct Processing
1. Place videos in `input/` folder
2. Run: `python batch_processor.py`
3. Check `reports/` for analysis results

## 📊 Generated Reports

- **JSON Report**: Machine-readable anomaly data
- **HTML Report**: Visual dashboard with timeline
- **Anomaly Frames**: Extracted frames with detected issues
- **SmartThings Integration**: Ready-to-deploy scenarios

## 🎯 Samsung Integration Examples

The reports include:
- SmartThings device compatibility scenarios
- Enterprise deployment recommendations
- Privacy-first local processing validation
- Real-time vs. batch processing comparisons

## 📋 Supported Video Formats

- MP4, AVI, MOV, MKV
- Resolution: 480p to 4K
- FPS: 15-60 (optimal: 30fps)
- Duration: Up to 30 minutes per video

## 🔧 Technical Details

This pipeline leverages TriFusion's production-ready architecture:
- **Tier 1**: Fast detection (&lt;100ms per frame)
- **Tier 2**: Deep AI reasoning (1-3s when anomaly detected)
- **Multimodal**: Vision + Audio + Pose analysis
- **Privacy**: 100% local processing, no cloud dependencies
# Set logging environment variables before any imports
import os
import sys
import logging

# Comprehensive logging suppression
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress all TensorFlow logs except errors
os.environ['GLOG_minloglevel'] = '3'      # Suppress GLOG info/warning logs  
os.environ['GLOG_logtostderr'] = '0'      # Don't log to stderr
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0' # Disable oneDNN optimizations logs
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "ERROR"
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['ABSL_STDERRTHRESHOLD'] = '3'  # Suppress ABSL logs

# Redirect stderr to suppress MediaPipe warnings
class SuppressStderr:
    def __enter__(self):
        self._original_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stderr.close()
        sys.stderr = self._original_stderr

# Configure Python logging to suppress INFO/WARNING
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('absl').setLevel(logging.ERROR)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from session_manager import session_manager
import warnings
from datetime import datetime
from typing import Dict, Any

# Suppress various warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

def print_startup_banner():
    """Print beautiful startup banner"""
    print("\n" + "="*80)
    print("█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█")
    print("█                                                                              █")
    print("█                    🤖 GenAI-Powered Anomaly Detection System                 █")
    print("█                    🛡️ SmartCare AI - Family Safety Monitoring               █")
    print("█                                                                              █")
    print("█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█")
    print("="*80)
    print("🔧 Initializing FastAPI server...")
    print("🤫 Verbose model logging suppressed for clean output")
    print("🧠 Loading AI models...")
    print("█                                                                              █")
    print("█                           🧠 Two-Tier AI Architecture                        █")
    print("█                                                                              █")
    print("█    🔍 Tier 1: Fast Detection  │  🧠 Tier 2: Deep AI Reasoning               █")
    print("█    • Pose Analysis            │  • Advanced Scene Understanding             █")
    print("█    • Scene Thresholds         │  • Multi-modal AI Fusion                   █")
    print("█    • Audio Processing         │  • Groq LLM Reasoning                      █")
    print("█                                                                              █")
    print("█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█")
    print("="*80 + "\n")
    
    print("🚀 Initializing AI Models...")
    print("┌──────────────────────────────────────────────────────────────────────────────┐")
    print("│                           🧠 Loading AI Components                           │")
    print("├──────────────────────────────────────────────────────────────────────────────┤")
    print("│ 🎯 MediaPipe Pose Detection    │ ✅ Loading pose_landmarker_heavy.task       │")
    print("│ 🎨 OpenAI CLIP Vision Models   │ ✅ Loading clip-vit-base & large models     │")
    print("│ 📷 BLIP Image Captioning       │ ✅ Loading Salesforce/blip-image-captioning │")
    print("│ 🎤 OpenAI Whisper STT          │ ✅ Loading whisper tiny & large models      │")
    print("│ 🧠 Groq LLM Reasoning          │ ✅ Connecting to llama-3.3-70b-versatile    │")
    print("└──────────────────────────────────────────────────────────────────────────────┘")
    print()

def print_mode_selection():
    """Print available modes"""
    print("🎯 Available Operating Modes:")
    print("┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│                                                                             │")
    print("│  🎥 LIVE MONITORING MODE        │  📁 UPLOAD ANALYSIS MODE                  │")
    print("│  ├─ Real-time camera feed       │  ├─ Video file upload                    │")
    print("│  ├─ Continuous Tier 1 analysis │  ├─ Batch processing                     │")
    print("│  ├─ Instant anomaly alerts     │  ├─ Detailed frame analysis              │")
    print("│  └─ Live WebSocket updates     │  └─ Comprehensive reporting              │")
    print("│                                                                             │")
    print("│  🌐 Access: /dashboard/live     │  🌐 Access: /dashboard/upload             │")
    print("│                                                                             │")
    print("└─────────────────────────────────────────────────────────────────────────────┘")
    print()
    print("🔗 Server running at: http://localhost:8000")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("="*80 + "\n")

# Print startup banner
print_startup_banner()

app = FastAPI(title="GenAI Anomaly Detection System", version="2.0.0")

print("📁 Setting up directories and static file mounts...")

# Create necessary directories
os.makedirs("anomaly_frames", exist_ok=True)
os.makedirs("recorded_videos", exist_ok=True)
os.makedirs("upload_results", exist_ok=True)
os.makedirs("uploaded_videos", exist_ok=True)

# Mount static files for anomaly frames and videos
app.mount("/anomaly_frames", StaticFiles(directory="anomaly_frames"), name="anomaly_frames")
app.mount("/recorded_videos", StaticFiles(directory="recorded_videos"), name="recorded_videos")
app.mount("/upload_results", StaticFiles(directory="upload_results"), name="upload_results")

print("✅ Directories and static mounts configured")
print_mode_selection()

# ==================== DASHBOARD ROUTES ====================

@app.get("/dashboard/live")
async def live_dashboard():
    """Serve the live monitoring dashboard"""
    return FileResponse("live_dashboard.html")

@app.get("/dashboard/upload")
async def upload_dashboard():
    """Serve the upload processing dashboard"""
    return FileResponse("upload_dashboard.html")

@app.get("/dashboard")
async def upload_dashboard():
    """Serve the upload processing dashboard"""
    return FileResponse("upload_dashboard.html")

# ==================== SESSION MANAGEMENT API ====================

@app.get("/api/session/status")
async def get_session_status() -> Dict[str, Any]:
    """Get current session status"""
    return session_manager.get_status()

@app.post("/api/session/stop-live")
async def stop_live_session():
    """Gracefully stop live monitoring session"""
    success = session_manager.graceful_stop_live()
    return {
        "success": success,
        "message": "Live monitoring stopped" if success else "Error stopping live monitoring",
        "status": session_manager.get_status()
    }

@app.post("/api/session/force-stop")
async def force_stop_session():
    """Force stop current session"""
    success = session_manager.force_stop_all()
    return {
        "success": success,
        "message": "Session force stopped" if success else "Error during force stop",
        "status": session_manager.get_status()
    }

# ==================== WEBSOCKET ENDPOINTS ====================

@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live monitoring"""
    await websocket.accept()
    
    try:
        success = await session_manager.start_live_mode(websocket)
        if not success:
            await websocket.close(code=1000, reason="Could not start live mode")
            return
            
        # Keep connection alive and handle disconnection
        while session_manager.current_mode == "live":
            try:
                # Wait for client messages (ping/pong, etc.)
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Clean up when WebSocket closes - use graceful stop instead of force stop
        if session_manager.current_mode == "live":
            session_manager.graceful_stop_live()

@app.websocket("/ws/upload")
async def websocket_upload_endpoint(websocket: WebSocket):
    """WebSocket endpoint for upload processing"""
    await websocket.accept()
    
    try:
        # Wait for video file path from client
        message = await websocket.receive_json()
        video_file_path = message.get("video_file_path")
        
        if not video_file_path:
            await websocket.send_json({"error": "No video file path provided"})
            return
            
        success = await session_manager.start_upload_mode(websocket, video_file_path)
        if not success:
            await websocket.close(code=1000, reason="Could not start upload mode")
            return
            
        # Keep connection alive during processing
        while session_manager.current_mode == "upload":
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Clean up when WebSocket closes
        if session_manager.current_mode == "upload":
            session_manager.force_stop_all()

# ==================== FILE UPLOAD API ====================

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload video file for processing"""
    
    # Validate file type
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"upload_{timestamp}{file_extension}"
    file_path = f"uploaded_videos/{filename}"
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "success": True,
            "filename": filename,
            "file_path": file_path,
            "size": len(content),
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# ==================== ANOMALY DATA API ====================

@app.get("/api/anomalies")
async def get_anomaly_events():
    """Get all detected anomaly events"""
    return {
        "anomaly_events": session_manager.anomaly_events,
        "total_count": len(session_manager.anomaly_events)
    }

# Backward compatibility endpoint
@app.get("/anomaly_events")
async def get_anomaly_events_legacy():
    """Legacy endpoint for anomaly events (backward compatibility)"""
    return {
        "anomaly_events": session_manager.anomaly_events,
        "total_count": len(session_manager.anomaly_events)
    }

@app.get("/api/anomalies/{event_index}")
async def get_anomaly_event(event_index: int):
    """Get specific anomaly event by index"""
    if 0 <= event_index < len(session_manager.anomaly_events):
        return session_manager.anomaly_events[event_index]
    raise HTTPException(status_code=404, detail="Anomaly event not found")

@app.delete("/api/anomalies")
async def clear_anomaly_events():
    """Clear all anomaly events (manual reset)"""
    session_manager.anomaly_events.clear()
    return {"message": "All anomaly events cleared", "total_count": 0}

# ==================== VIDEO STREAMING (for live dashboard) ====================

@app.get("/video_stream")
async def video_stream():
    """Simple video stream endpoint for live dashboard"""
    from fastapi.responses import StreamingResponse
    import cv2
    
    def generate_stream():
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            # Return placeholder frames if camera not available
            for _ in range(100):
                placeholder = create_placeholder_frame("Camera not available")
                ret, buffer = cv2.imencode('.jpg', placeholder)
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                import time
                time.sleep(0.1)
            return
        
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        for _ in range(1000):  # Limit frames
            ret, frame = cap.read()
            if not ret:
                break
            
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
            import time
            time.sleep(0.05)
        
        cap.release()
    
    return StreamingResponse(
        generate_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

def create_placeholder_frame(message: str):
    """Create a placeholder frame with message"""
    import cv2
    import numpy as np
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, message, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    return frame

# ==================== ROOT ENDPOINT ====================

@app.get("/")
async def root():
    """Redirect to dashboard for web users, API info for programmatic access"""
    from fastapi.responses import RedirectResponse
    from fastapi.requests import Request

    # For now, let's redirect to dashboard
    # If you want API info, you can access /api/info
    return RedirectResponse(url="/dashboard/upload", status_code=302)

@app.get("/api/info")
async def api_info():
    """API information endpoint for programmatic access"""
    status = session_manager.get_status()
    return {
        "welcome": "Welcome to TriFusion - GenAI Powered Anomaly Detection System",
        "message": "🛡️ SmartCare AI - Family Safety Monitoring Platform v2.0",
        "description": "Revolutionary multimodal AI for elderly care and family safety monitoring",
        "session_status": status,
        "endpoints": {
            "dashboard": "/dashboard",
            "live_dashboard": "/dashboard/live",
            "upload_dashboard": "/dashboard/upload",
        },
        "features": [
            "Real-time anomaly detection",
            "Multimodal AI fusion (Vision + Audio + Pose)",
            "Two-tier AI architecture",
            "Privacy-first local processing"
        ]
    }
import asyncio
import threading
import time
import cv2
import os
import queue
from datetime import datetime
from threading import Thread, Lock
from fastapi import WebSocket, WebSocketDisconnect
from typing import Optional, Dict, Any
from utils.audio_processing import AudioStream
from tier1.tier1_pipeline import run_tier1_continuous
from tier2.tier2_pipeline import run_tier2_continuous
import numpy as np


class SessionManager:
    """
    Centralized session manager for handling live monitoring and upload processing.
    Manages WebSocket connections, threads, and resources with immediate termination capability.
    """
    
    def __init__(self):
        self.current_mode: Optional[str] = None  # "live" or "upload" or None
        self.active_websocket: Optional[WebSocket] = None
        self.processing_threads: list[Thread] = []
        self.lock = Lock()
        
        # Resource tracking
        self.resources = {
            'video_cap': None,
            'video_writer': None,
            'audio_stream': None,
            'frame_queue': None
        }
        
        # Control flags
        self.running = False
        self.frame_thread = None
        
        # Session data
        self.session_data = {}
        self.anomaly_events = []
        
        # Upload-specific
        self.upload_session_dir = None
        
    def get_status(self) -> Dict[str, Any]:
        """Get current session status"""
        with self.lock:
            return {
                "mode": self.current_mode,
                "active": self.running,
                "websocket_connected": self.active_websocket is not None,
                "threads_count": len(self.processing_threads),
                "resources_active": any(self.resources.values())
            }
    
    def graceful_stop_live(self) -> bool:
        """
        Gracefully stop live monitoring session without forcing thread termination.
        Returns True if successful, False if errors occurred.
        """
        print("🛑 Gracefully stopping live monitoring...")
        
        with self.lock:
            success = True
            
            # 1. Set stop flag - this will cause threads to exit naturally
            self.running = False
            self.current_mode = None
            self.active_websocket = None
            
            # 2. Release video resources gracefully
            if self.resources.get('video_capture'):
                try:
                    self.resources['video_capture'].release()
                    self.resources['video_capture'] = None
                    print("📹 Released video capture")
                except Exception as e:
                    print(f"❌ Error releasing video capture: {e}")
                    success = False
            
            # 3. Release video writer gracefully
            if self.resources.get('video_writer'):
                try:
                    self.resources['video_writer'].release()
                    self.resources['video_writer'] = None
                    print("💾 Released video writer")
                except Exception as e:
                    print(f"❌ Error releasing video writer: {e}")
                    success = False
            
            # 4. Stop audio stream gracefully
            if self.resources.get('audio_stream'):
                try:
                    self.resources['audio_stream'].stop()
                    self.resources['audio_stream'].close()
                    self.resources['audio_stream'] = None
                    print("🎤 Stopped audio stream")
                except Exception as e:
                    print(f"❌ Error stopping audio stream: {e}")
                    success = False
            
            # 5. Clear frame queue
            try:
                while not self.frame_queue.empty():
                    self.frame_queue.get_nowait()
                print("🗂️ Cleared frame queue")
            except Exception as e:
                print(f"❌ Error clearing frame queue: {e}")
                success = False
        
        # 6. Wait for threads to finish naturally (outside lock to avoid deadlock)
        for thread in self.processing_threads[:]:  # Copy list to avoid modification during iteration
            if thread.is_alive():
                try:
                    print(f"⏳ Waiting for thread {thread.name} to finish...")
                    thread.join(timeout=5.0)  # Wait up to 5 seconds
                    if not thread.is_alive():
                        print(f"✅ Thread {thread.name} finished gracefully")
                        self.processing_threads.remove(thread)
                    else:
                        print(f"⚠️ Thread {thread.name} did not finish in time")
                        success = False
                except Exception as e:
                    print(f"❌ Error waiting for thread {thread.name}: {e}")
                    success = False
        
        print(f"✅ Graceful stop completed {'successfully' if success else 'with errors'}")
        return success
    
    def force_stop_all(self) -> bool:
        """
        Immediately terminate all threads and release all resources.
        Returns True if successful, False if errors occurred.
        """
        print("🛑 Force stopping all sessions...")
        
        with self.lock:
            success = True
            
            # 1. Set stop flag
            self.running = False
            
            # 2. Force terminate all threads
            for thread in self.processing_threads:
                if thread.is_alive():
                    try:
                        # Force thread termination (unsafe but immediate)
                        thread._stop() if hasattr(thread, '_stop') else None
                        print(f"🔴 Terminated thread: {thread.name}")
                    except Exception as e:
                        print(f"❌ Error terminating thread {thread.name}: {e}")
                        success = False
            
            # 3. Release all resources immediately
            try:
                if self.resources['video_cap']:
                    self.resources['video_cap'].release()
                    self.resources['video_cap'] = None
                    print("📹 Released video capture")
                    
                if self.resources['video_writer']:
                    self.resources['video_writer'].release()
                    self.resources['video_writer'] = None
                    print("💾 Released video writer")
                    
                if self.resources['audio_stream']:
                    self.resources['audio_stream'].stop()
                    self.resources['audio_stream'] = None
                    print("🎤 Stopped audio stream")
                    
                if self.resources['frame_queue']:
                    # Clear queue
                    while not self.resources['frame_queue'].empty():
                        try:
                            self.resources['frame_queue'].get_nowait()
                        except:
                            break
                    self.resources['frame_queue'] = None
                    print("🗂️ Cleared frame queue")
                    
            except Exception as e:
                print(f"❌ Error releasing resources: {e}")
                success = False
            
            # 4. Clear state
            self.processing_threads.clear()
            self.current_mode = None
            self.active_websocket = None
            self.session_data.clear()
            self.upload_session_dir = None
            
            print(f"✅ Force stop completed {'successfully' if success else 'with errors'}")
            return success
    
    def can_start_mode(self, requested_mode: str) -> tuple[bool, str]:
        """
        Check if requested mode can be started.
        Returns (can_start, reason)
        """
        with self.lock:
            if self.current_mode is None:
                return True, "No active session"
            
            if self.current_mode == requested_mode:
                return False, f"{requested_mode.title()} mode already active"
            
            return False, f"{self.current_mode.title()} mode is currently active"
    
    async def start_live_mode(self, websocket: WebSocket) -> bool:
        """Start live monitoring mode"""
        print("\n" + "="*80)
        print("🎥 LIVE MONITORING MODE - Starting Real-time Analysis")
        print("="*80)
        print("🔧 Initializing live session...")
        
        can_start, reason = self.can_start_mode("live")
        if not can_start:
            print(f"❌ Cannot start: {reason}")
            await websocket.send_json({"error": reason, "current_mode": self.current_mode})
            return False
        
        try:
            with self.lock:
                self.current_mode = "live"
                self.active_websocket = websocket
                self.running = True
                # Don't clear anomaly_events - preserve previous detections
                # self.anomaly_events = []  # REMOVED: This was causing anomalies to be lost
            
            print("📹 Connecting to camera feed...")
            print("🧵 Starting processing thread...")
            
            # Start live processing in separate thread
            live_thread = Thread(target=self._live_processing_worker, args=(websocket,), name="LiveProcessor")
            self.processing_threads.append(live_thread)
            live_thread.start()
            
            print("✅ Live mode started successfully")
            print("🔍 Tier 1 continuous analysis active")
            print("🧠 Tier 2 AI reasoning on standby")
            print("="*80 + "\n")
            return True
            
        except Exception as e:
            print(f"❌ Error starting live mode: {e}")
            self.force_stop_all()
            return False
    
    async def start_upload_mode(self, websocket: WebSocket, video_file_path: str) -> bool:
        """Start upload processing mode"""
        print("\n" + "="*80)
        print("📁 UPLOAD ANALYSIS MODE - Starting Video Processing")
        print("="*80)
        print(f"📄 File: {os.path.basename(video_file_path)}")
        print("🔧 Initializing upload session...")
        
        can_start, reason = self.can_start_mode("upload")
        if not can_start:
            print(f"❌ Cannot start: {reason}")
            await websocket.send_json({"error": reason, "current_mode": self.current_mode})
            return False
        
        # Verify file exists
        if not os.path.exists(video_file_path):
            print(f"❌ File not found: {video_file_path}")
            await websocket.send_json({"error": f"Video file not found: {video_file_path}"})
            return False
        
        try:
            with self.lock:
                self.current_mode = "upload"
                self.active_websocket = websocket
                self.running = True
                
                # Create upload session directory
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.upload_session_dir = f"upload_results/session_{timestamp}"
                os.makedirs(f"{self.upload_session_dir}/anomaly_frames", exist_ok=True)
                
                print(f"📁 Session directory: {self.upload_session_dir}")
                
                self.session_data = {
                    "video_file": video_file_path,
                    "session_dir": self.upload_session_dir,
                    "start_time": datetime.now().isoformat()
                }
            
            print("🎬 Analyzing video properties...")
            print("🧵 Starting batch processing thread...")
            
            # Start upload processing in separate thread
            upload_thread = Thread(
                target=self._upload_processing_worker, 
                args=(websocket, video_file_path), 
                name="UploadProcessor"
            )
            self.processing_threads.append(upload_thread)
            upload_thread.start()
            
            print("✅ Upload mode started successfully")
            print("🔍 Tier 1 frame-by-frame analysis active")
            print("🧠 Tier 2 AI reasoning on anomaly detection")
            print("="*80 + "\n")
            return True
            
        except Exception as e:
            print(f"❌ Error starting upload mode: {e}")
            self.force_stop_all()
            return False
    
    def _live_processing_worker(self, websocket: WebSocket):
        """Worker thread for live processing (extracted from app.py)"""
        try:
            # Initialize camera
            video_cap = cv2.VideoCapture(0)
            if not self._setup_camera(video_cap):
                asyncio.run(websocket.send_json({"error": "Could not open camera"}))
                return
            
            self.resources['video_cap'] = video_cap
            
            # Setup video recording
            width = int(video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = video_cap.get(cv2.CAP_PROP_FPS) or 30
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f"recorded_videos/session_{timestamp}.mp4"
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(video_filename, fourcc, fps, (width, height))
            self.resources['video_writer'] = video_writer
            
            # Start audio stream
            audio_stream = AudioStream()
            audio_stream.start()
            self.resources['audio_stream'] = audio_stream
            
            # Setup frame capture
            frame_queue = queue.Queue(maxsize=10)
            self.resources['frame_queue'] = frame_queue
            
            frame_thread = Thread(target=self._capture_frames, args=(video_cap, frame_queue), name="FrameCapture")
            self.processing_threads.append(frame_thread)
            frame_thread.start()
            
            # Main processing loop
            self._live_processing_loop(websocket, frame_queue, video_writer, audio_stream, fps, video_filename)
            
        except Exception as e:
            print(f"❌ Live processing worker error: {e}")
            asyncio.run(websocket.send_json({"error": f"Live processing error: {str(e)}"}))
        finally:
            self._cleanup_live_resources()
    
    def _upload_processing_worker(self, websocket: WebSocket, video_file_path: str):
        """Worker thread for upload processing"""
        try:
            # Open video file
            video_cap = cv2.VideoCapture(video_file_path)
            if not video_cap.isOpened():
                asyncio.run(websocket.send_json({"error": "Could not open video file"}))
                return
            
            self.resources['video_cap'] = video_cap
            
            # Get video properties
            total_frames = int(video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = video_cap.get(cv2.CAP_PROP_FPS) or 30
            
            # Send initial progress
            asyncio.run(websocket.send_json({
                "type": "started",
                "total_frames": total_frames,
                "fps": fps,
                "session_dir": self.upload_session_dir
            }))
            
            # Process every 5th frame for speed
            frame_skip = 5
            frame_count = 0
            processed_count = 0
            anomaly_count = 0
            
            while self.running and video_cap.isOpened():
                ret, frame = video_cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Process every 5th frame
                if frame_count % frame_skip == 0:
                    processed_count += 1
                    current_timestamp = frame_count / fps
                    
                    # Run Tier 1 processing (no audio for upload)
                    try:
                        tier1_result = run_tier1_continuous(frame, None)
                        
                        # Send progress update
                        progress_data = {
                            "type": "progress",
                            "frame_count": frame_count,
                            "processed_count": processed_count,
                            "total_frames": total_frames,
                            "progress_percent": (frame_count / total_frames) * 100,
                            "timestamp": current_timestamp,
                            "status": tier1_result["status"]
                        }
                        asyncio.run(websocket.send_json(progress_data))
                        
                        # If anomaly detected, save frame and run Tier 2
                        if tier1_result["status"] == "Suspected Anomaly":
                            anomaly_count += 1
                            
                            # Save anomaly frame
                            frame_filename = f"{self.upload_session_dir}/anomaly_frames/anomaly_{frame_count}.jpg"
                            cv2.imwrite(frame_filename, frame)
                            
                            # Run Tier 2 analysis
                            tier2_result = run_tier2_continuous(frame, None, tier1_result)
                            
                            # Send anomaly data
                            anomaly_data = {
                                "type": "anomaly",
                                "frame_count": frame_count,
                                "timestamp": current_timestamp,
                                "frame_file": frame_filename,
                                "tier1_result": tier1_result,
                                "tier2_result": tier2_result,
                                "anomaly_index": anomaly_count
                            }
                            asyncio.run(websocket.send_json(anomaly_data))
                            
                            # Store anomaly
                            self.anomaly_events.append(anomaly_data)
                            
                    except Exception as e:
                        print(f"❌ Error processing frame {frame_count}: {e}")
                        continue
            
            # Send completion data
            completion_data = {
                "type": "complete",
                "total_frames": total_frames,
                "processed_frames": processed_count,
                "anomalies_found": anomaly_count,
                "session_dir": self.upload_session_dir,
                "anomaly_events": self.anomaly_events
            }
            asyncio.run(websocket.send_json(completion_data))
            
        except Exception as e:
            print(f"❌ Upload processing worker error: {e}")
            asyncio.run(websocket.send_json({"error": f"Upload processing error: {str(e)}"}))
        finally:
            self._cleanup_upload_resources()
    
    def _setup_camera(self, video_cap) -> bool:
        """Setup camera with optimal settings"""
        for attempt in range(3):
            video_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            video_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            video_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            video_cap.set(cv2.CAP_PROP_FPS, 30)  # Increased to 30 FPS for better capture
            
            if video_cap.isOpened():
                ret, test_frame = video_cap.read()
                if ret:
                    return True
                else:
                    video_cap.release()
            
            time.sleep(1)
        return False
    
    def _capture_frames(self, video_cap, frame_queue):
        """Frame capture thread"""
        while self.running:
            ret, frame = video_cap.read()
            if not ret:
                break
            if not frame_queue.full():
                frame_queue.put(frame)
    
    def _live_processing_loop(self, websocket, frame_queue, video_writer, audio_stream, fps, video_filename):
        """Main live processing loop (simplified from app.py)"""
        frame_count = 0
        frame_interval = 5  # Process every 5th frame for optimal balance
        
        while self.running:
            if frame_queue.empty():
                time.sleep(0.01)
                continue
            
            frame = frame_queue.get()
            frame_count += 1
            
            # Record frame
            if video_writer.isOpened():
                video_writer.write(frame)
            
            # Process every 5th frame (6 FPS analysis rate)
            if frame_count % frame_interval != 0:
                continue
            
            current_timestamp = frame_count / fps
            audio_chunk = audio_stream.get_chunk()
            
            try:
                # Run Tier 1 continuously
                tier1_result = run_tier1_continuous(frame, audio_chunk)
                tier1_result.update({
                    "frame_count": frame_count,
                    "timestamp": current_timestamp,
                    "video_file": video_filename
                })
                
                # Always send Tier 1 result for continuous monitoring
                tier1_message = {
                    "type": "tier1_update",
                    "frame_count": frame_count,
                    "timestamp": current_timestamp, 
                    "status": tier1_result["status"],
                    "details": tier1_result["details"],
                    "tier1_result": tier1_result
                }
                asyncio.run(websocket.send_json(tier1_message))
                
                # If anomaly detected, run Tier 2 and send combined anomaly event
                if tier1_result["status"] == "Suspected Anomaly":
                    anomaly_frame_filename = f"anomaly_frames/anomaly_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{frame_count}.jpg"
                    cv2.imwrite(anomaly_frame_filename, frame)
                    
                    # Run Tier 2 analysis
                    tier2_result = run_tier2_continuous(frame, audio_chunk, tier1_result)
                    
                    # Send combined anomaly data (matching upload mode format)
                    anomaly_data = {
                        "type": "anomaly",
                        "frame_count": frame_count,
                        "timestamp": current_timestamp,
                        "frame_file": anomaly_frame_filename,
                        "tier1_result": tier1_result,
                        "tier2_result": tier2_result,
                        "anomaly_index": len(self.anomaly_events) + 1
                    }
                    asyncio.run(websocket.send_json(anomaly_data))
                    self.anomaly_events.append(anomaly_data)
                    
            except Exception as e:
                print(f"❌ Live processing error: {e}")
                continue
            
            time.sleep(1 / fps)
    
    def _cleanup_live_resources(self):
        """Clean up live session resources"""
        print("🧹 Cleaning up live resources...")
        # Resources are cleaned up in force_stop_all()
    
    def _cleanup_upload_resources(self):
        """Clean up upload session resources"""
        print("🧹 Cleaning up upload resources...")
        # Resources are cleaned up in force_stop_all()

# Global session manager instance
session_manager = SessionManager()
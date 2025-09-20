#!/usr/bin/env python3
"""
Test script to check if logging suppression is working
"""

# Set environment variables before any imports
import os
import sys
import logging

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '3'
os.environ['GLOG_logtostderr'] = '0'
os.environ['ABSL_STDERRTHRESHOLD'] = '3'

# Suppress stderr during model loading
class SuppressStderr:
    def __enter__(self):
        self._original_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stderr.close()
        sys.stderr = self._original_stderr

print("Testing MediaPipe model loading with suppressed logs...")

try:
    with SuppressStderr():
        from utils import pose_processing
    print("✅ MediaPipe loaded successfully with suppressed logs!")
except Exception as e:
    print(f"❌ Error loading MediaPipe: {e}")

print("Log suppression test complete.")
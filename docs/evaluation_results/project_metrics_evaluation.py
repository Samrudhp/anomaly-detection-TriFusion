#!/usr/bin/env python3
"""
TriFusion Anomaly Detection System - AI Model Performance Evaluator
================================================================

This script evaluates the actual anomaly detection performance of our AI models:
- Tier 1 (Fast Detection) accuracy and speed
- Tier 2 (Deep Analysis) precision and threat assessment
- Real-world threat detection capabilities
- False positive/negative rates

Author: TriFusion Development Team
Date: September 20, 2025
"""

import os
import sys
import json
import time
import cv2
import numpy as np
from datetime import datetime
import logging
from typing import Dict, List, Tuple, Any
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our AI pipeline components
from tier1.tier1_pipeline import run_tier1_continuous
from tier2.tier2_pipeline import run_tier2_continuous

class AnomalyDetectionEvaluator:
    """
    Comprehensive evaluator for anomaly detection system performance
    """
    
    def __init__(self, output_dir: str = "evaluation_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup logging with UTF-8 encoding
        log_file = self.output_dir / 'evaluation.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Evaluation results storage
        self.results = {
            'tier1_results': [],
            'tier2_results': [],
            'performance_metrics': {},
            'accuracy_metrics': {},
            'speed_metrics': {},
            'threat_assessment': {},
            'evaluation_timestamp': datetime.now().isoformat()
        }
        
        # Test scenarios for evaluation
        self.test_scenarios = [
            {
                'name': 'Normal_Activity',
                'description': 'Person walking normally in room',
                'expected_anomaly': False,
                'threat_level': 0.0
            },
            {
                'name': 'Fall_Detection',
                'description': 'Person falling down simulation',
                'expected_anomaly': True,
                'threat_level': 0.8
            },
            {
                'name': 'Suspicious_Behavior',
                'description': 'Unusual movements or postures',
                'expected_anomaly': True,
                'threat_level': 0.6
            },
            {
                'name': 'Medical_Emergency',
                'description': 'Person in distress or collapsed',
                'expected_anomaly': True,
                'threat_level': 0.9
            }
        ]
        
        self.logger.info("TriFusion Anomaly Detection Evaluator Initialized")
        self.logger.info(f"Results will be saved to: {self.output_dir}")

    def generate_test_frames(self) -> List[np.ndarray]:
        """Generate synthetic test frames for evaluation"""
        self.logger.info("Generating synthetic test frames...")
        
        test_frames = []
        
        for scenario in self.test_scenarios:
            for i in range(3):  # 3 frames per scenario
                # Create 640x480 RGB frame
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                
                # Add gradient background
                for y in range(480):
                    for x in range(640):
                        frame[y, x] = [int(x/640*128), int(y/480*128), 64]
                
                # Add scenario-specific patterns
                scenario_name = scenario['name'].lower()
                if 'fall' in scenario_name:
                    # Horizontal rectangle (fallen person)
                    cv2.rectangle(frame, (200, 350), (450, 400), (255, 0, 0), -1)
                elif 'suspicious' in scenario_name:
                    # Irregular shapes
                    cv2.circle(frame, (320, 240), 50, (255, 255, 0), -1)
                elif 'emergency' in scenario_name:
                    # Alert pattern
                    cv2.rectangle(frame, (150, 150), (350, 350), (255, 0, 255), 5)
                else:  # normal
                    # Standing person rectangle
                    cv2.rectangle(frame, (300, 200), (340, 400), (0, 255, 0), -1)
                
                test_frames.append(frame)
        
        self.logger.info(f"Generated {len(test_frames)} test frames")
        return test_frames

    def evaluate_tier1_performance(self, test_frames: List[np.ndarray]) -> Dict:
        """Evaluate Tier 1 detection performance"""
        self.logger.info("Evaluating Tier 1 Fast Detection Performance...")
        
        metrics = {
            'total_frames': len(test_frames),
            'processing_times': [],
            'detection_results': [],
            'true_positives': 0,
            'true_negatives': 0,
            'false_positives': 0,
            'false_negatives': 0
        }
        
        for i, frame in enumerate(test_frames):
            start_time = time.time()
            
            try:
                # Run Tier 1 analysis
                result = run_tier1_continuous(frame, None)
                processing_time = time.time() - start_time
                
                metrics['processing_times'].append(processing_time)
                metrics['detection_results'].append(result)
                
                # Determine if anomaly detected
                is_anomaly = result.get('status') == 'Suspected Anomaly'
                
                # Get expected result from scenario
                scenario_idx = i // 3  # 3 frames per scenario
                if scenario_idx < len(self.test_scenarios):
                    expected_anomaly = self.test_scenarios[scenario_idx]['expected_anomaly']
                else:
                    expected_anomaly = False
                
                # Update confusion matrix
                if is_anomaly and expected_anomaly:
                    metrics['true_positives'] += 1
                elif not is_anomaly and not expected_anomaly:
                    metrics['true_negatives'] += 1
                elif is_anomaly and not expected_anomaly:
                    metrics['false_positives'] += 1
                else:
                    metrics['false_negatives'] += 1
                
                self.logger.info(f"Frame {i+1}/{len(test_frames)}: {result.get('status', 'Unknown')} ({processing_time:.3f}s)")
                
            except Exception as e:
                self.logger.error(f"Error processing frame {i}: {e}")
                metrics['processing_times'].append(0)
                metrics['detection_results'].append({'error': str(e)})
        
        # Calculate performance metrics
        total = len(test_frames)
        tp = metrics['true_positives']
        tn = metrics['true_negatives'] 
        fp = metrics['false_positives']
        fn = metrics['false_negatives']
        
        metrics['accuracy'] = (tp + tn) / total if total > 0 else 0
        metrics['precision'] = tp / (tp + fp) if (tp + fp) > 0 else 0
        metrics['recall'] = tp / (tp + fn) if (tp + fn) > 0 else 0
        metrics['f1_score'] = 2 * metrics['precision'] * metrics['recall'] / (metrics['precision'] + metrics['recall']) if (metrics['precision'] + metrics['recall']) > 0 else 0
        metrics['avg_processing_time'] = np.mean(metrics['processing_times']) if metrics['processing_times'] else 0
        metrics['fps_capability'] = 1.0 / metrics['avg_processing_time'] if metrics['avg_processing_time'] > 0 else 0
        
        self.results['tier1_results'] = metrics
        
        self.logger.info("Tier 1 Evaluation Complete:")
        self.logger.info(f"  Accuracy: {metrics['accuracy']:.3f}")
        self.logger.info(f"  Precision: {metrics['precision']:.3f}")
        self.logger.info(f"  Recall: {metrics['recall']:.3f}")
        self.logger.info(f"  F1 Score: {metrics['f1_score']:.3f}")
        self.logger.info(f"  Avg Processing Time: {metrics['avg_processing_time']:.3f}s")
        self.logger.info(f"  FPS Capability: {metrics['fps_capability']:.1f}")
        
        return metrics

    def evaluate_tier2_performance(self, anomaly_frames: List[np.ndarray]) -> Dict:
        """Evaluate Tier 2 deep analysis performance"""
        self.logger.info("Evaluating Tier 2 Deep Analysis Performance...")
        
        metrics = {
            'total_anomalies': len(anomaly_frames),
            'processing_times': [],
            'threat_assessments': [],
            'avg_threat_level': 0.0,
            'avg_confidence': 0.0
        }
        
        for i, frame in enumerate(anomaly_frames):
            start_time = time.time()
            
            try:
                # Create dummy Tier 1 result for Tier 2 input
                dummy_tier1 = {
                    'status': 'Suspected Anomaly',
                    'details': 'Test scenario anomaly',
                    'tier1_components': {'audio_analysis': {'transcript_text': ''}}
                }
                
                # Run Tier 2 analysis
                result = run_tier2_continuous(frame, None, dummy_tier1)
                processing_time = time.time() - start_time
                
                metrics['processing_times'].append(processing_time)
                metrics['threat_assessments'].append(result)
                
                self.logger.info(f"Anomaly {i+1}/{len(anomaly_frames)}: Processed in {processing_time:.3f}s")
                
            except Exception as e:
                self.logger.error(f"Error analyzing anomaly {i}: {e}")
                metrics['processing_times'].append(0)
                metrics['threat_assessments'].append({'error': str(e)})
        
        # Calculate averages
        if metrics['threat_assessments']:
            valid_assessments = [a for a in metrics['threat_assessments'] if 'error' not in a]
            if valid_assessments:
                metrics['avg_threat_level'] = np.mean([a.get('threat_severity_index', 0.5) for a in valid_assessments])
                metrics['avg_confidence'] = np.mean([a.get('confidence_score', 0.5) for a in valid_assessments])
        
        metrics['avg_processing_time'] = np.mean(metrics['processing_times']) if metrics['processing_times'] else 0
        
        self.results['tier2_results'] = metrics
        
        self.logger.info("Tier 2 Evaluation Complete:")
        self.logger.info(f"  Avg Threat Level: {metrics['avg_threat_level']:.3f}")
        self.logger.info(f"  Avg Confidence: {metrics['avg_confidence']:.3f}")
        self.logger.info(f"  Avg Processing Time: {metrics['avg_processing_time']:.3f}s")
        
        return metrics

    def calculate_overall_performance(self) -> Dict:
        """Calculate overall system performance"""
        self.logger.info("Calculating Overall System Performance...")
        
        tier1 = self.results.get('tier1_results', {})
        tier2 = self.results.get('tier2_results', {})
        
        overall = {
            'detection_accuracy': tier1.get('accuracy', 0.0),
            'detection_precision': tier1.get('precision', 0.0),
            'detection_recall': tier1.get('recall', 0.0),
            'detection_f1': tier1.get('f1_score', 0.0),
            'tier1_fps': tier1.get('fps_capability', 0.0),
            'tier1_latency': tier1.get('avg_processing_time', 0.0),
            'tier2_latency': tier2.get('avg_processing_time', 0.0),
            'threat_assessment_quality': tier2.get('avg_confidence', 0.0),
            'false_positive_rate': tier1.get('false_positives', 0) / max(1, tier1.get('total_frames', 1)),
            'false_negative_rate': tier1.get('false_negatives', 0) / max(1, tier1.get('total_frames', 1))
        }
        
        # Calculate overall score (weighted)
        detection_score = (overall['detection_accuracy'] * 0.4 + 
                          overall['detection_precision'] * 0.3 + 
                          overall['detection_recall'] * 0.3)
        
        speed_score = min(1.0, overall['tier1_fps'] / 10.0)  # Normalize to 10 FPS target
        
        overall_score = (detection_score * 0.6 + 
                        overall['threat_assessment_quality'] * 0.2 + 
                        speed_score * 0.2)
        
        overall['overall_score'] = overall_score
        
        # Assign grade
        if overall_score >= 0.9:
            grade = 'A+'
        elif overall_score >= 0.8:
            grade = 'A'
        elif overall_score >= 0.7:
            grade = 'B'
        elif overall_score >= 0.6:
            grade = 'C'
        else:
            grade = 'D'
        
        overall['grade'] = grade
        
        self.results['overall_performance'] = overall
        
        self.logger.info(f"Overall Performance Score: {overall_score:.3f}")
        self.logger.info(f"System Grade: {grade}")
        
        return overall

    def generate_report(self) -> str:
        """Generate performance report"""
        self.logger.info("Generating Performance Report...")
        
        report_lines = [
            "=" * 70,
            "TriFusion Anomaly Detection - AI Performance Evaluation Report",
            "=" * 70,
            f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "EXECUTIVE SUMMARY",
            "-" * 30
        ]
        
        overall = self.results.get('overall_performance', {})
        report_lines.extend([
            f"Overall Performance Score: {overall.get('overall_score', 0.0):.3f}",
            f"System Grade: {overall.get('grade', 'N/A')}",
            f"Detection Accuracy: {overall.get('detection_accuracy', 0.0):.3f}",
            f"Processing Speed: {overall.get('tier1_fps', 0.0):.1f} FPS",
            f"False Positive Rate: {overall.get('false_positive_rate', 0.0):.3f}",
            ""
        ])
        
        # Tier 1 Results
        tier1 = self.results.get('tier1_results', {})
        if tier1:
            report_lines.extend([
                "TIER 1 (FAST DETECTION) PERFORMANCE",
                "-" * 30,
                f"Accuracy: {tier1.get('accuracy', 0.0):.3f}",
                f"Precision: {tier1.get('precision', 0.0):.3f}",
                f"Recall: {tier1.get('recall', 0.0):.3f}",
                f"F1 Score: {tier1.get('f1_score', 0.0):.3f}",
                f"Average Processing Time: {tier1.get('avg_processing_time', 0.0):.3f}s",
                f"FPS Capability: {tier1.get('fps_capability', 0.0):.1f}",
                f"True Positives: {tier1.get('true_positives', 0)}",
                f"True Negatives: {tier1.get('true_negatives', 0)}",
                f"False Positives: {tier1.get('false_positives', 0)}",
                f"False Negatives: {tier1.get('false_negatives', 0)}",
                ""
            ])
        
        # Tier 2 Results
        tier2 = self.results.get('tier2_results', {})
        if tier2:
            report_lines.extend([
                "TIER 2 (DEEP ANALYSIS) PERFORMANCE",
                "-" * 30,
                f"Average Threat Level: {tier2.get('avg_threat_level', 0.0):.3f}",
                f"Average Confidence: {tier2.get('avg_confidence', 0.0):.3f}",
                f"Average Processing Time: {tier2.get('avg_processing_time', 0.0):.3f}s",
                f"Total Anomalies Analyzed: {tier2.get('total_anomalies', 0)}",
                ""
            ])
        
        # Recommendations
        report_lines.extend([
            "RECOMMENDATIONS",
            "-" * 30
        ])
        
        if overall.get('detection_accuracy', 0.0) < 0.8:
            report_lines.append("- Detection accuracy below 80% - Consider model improvements")
        if overall.get('tier1_fps', 0.0) < 5.0:
            report_lines.append("- Processing speed below 5 FPS - Optimize performance")
        if overall.get('false_positive_rate', 0.0) > 0.15:
            report_lines.append("- High false positive rate - Adjust thresholds")
        
        if overall.get('overall_score', 0.0) > 0.8:
            report_lines.append("- Excellent performance - Ready for production")
        elif overall.get('overall_score', 0.0) > 0.6:
            report_lines.append("- Good performance - Minor optimizations needed")
        else:
            report_lines.append("- Performance needs improvement")
        
        report_lines.extend([
            "",
            "=" * 70,
            "End of Report"
        ])
        
        report_text = "\n".join(report_lines)
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f"performance_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        self.logger.info(f"Report saved to: {report_file}")
        return report_text

    def save_results(self) -> str:
        """Save evaluation results to JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = self.output_dir / f"evaluation_results_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.logger.info(f"Results saved to: {results_file}")
        return str(results_file)

    def run_full_evaluation(self) -> Dict:
        """Run complete evaluation pipeline"""
        self.logger.info("Starting Full TriFusion Evaluation Pipeline...")
        
        try:
            # 1. Generate test frames (synthetic data, NOT using existing video files)
            test_frames = self.generate_test_frames()
            
            # 2. Evaluate Tier 1 Performance
            tier1_results = self.evaluate_tier1_performance(test_frames)
            
            # 3. Evaluate Tier 2 Performance (use first few frames as anomalies)
            anomaly_frames = test_frames[:6]  # First 6 frames
            tier2_results = self.evaluate_tier2_performance(anomaly_frames)
            
            # 4. Calculate overall performance
            overall_performance = self.calculate_overall_performance()
            
            # 5. Generate report
            report = self.generate_report()
            
            # 6. Save results
            results_file = self.save_results()
            
            self.logger.info("Full evaluation completed successfully!")
            
            return {
                'success': True,
                'overall_performance': overall_performance,
                'results_file': results_file,
                'summary': {
                    'score': overall_performance.get('overall_score', 0.0),
                    'grade': overall_performance.get('grade', 'N/A'),
                    'accuracy': overall_performance.get('detection_accuracy', 0.0),
                    'fps': overall_performance.get('tier1_fps', 0.0)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Evaluation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """Main evaluation execution"""
    print("TriFusion Anomaly Detection System - AI Performance Evaluator")
    print("=" * 60)
    print("NOTE: This script generates SYNTHETIC test frames - not using video files")
    print("=" * 60)
    
    # Initialize evaluator
    evaluator = AnomalyDetectionEvaluator()
    
    # Run evaluation
    results = evaluator.run_full_evaluation()
    
    if results['success']:
        summary = results['summary']
        print("\nEVALUATION COMPLETED SUCCESSFULLY!")
        print("-" * 40)
        print(f"Overall Performance Score: {summary['score']:.3f}")
        print(f"System Grade: {summary['grade']}")
        print(f"Detection Accuracy: {summary['accuracy']:.3f}")
        print(f"Processing Speed: {summary['fps']:.1f} FPS")
        print(f"Results saved to: {results['results_file']}")
    else:
        print(f"\nEVALUATION FAILED: {results['error']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
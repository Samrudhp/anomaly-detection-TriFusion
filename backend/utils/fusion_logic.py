from groq import Groq
import json
from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env file

# Test Groq client initialization
try:
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    print("✅ Groq client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize Groq client: {e}")
    groq_client = None



def tier1_fusion(pose_summary, audio_summary, scene_summary):
    print("\n" + "="*60)
    print("🔍 TIER 1 ANALYSIS - Fast Detection Engine")
    print("="*60)
    
    # Extract scene anomaly probability for threshold check
    scene_prob = 0.0
    if "Scene anomaly probability:" in scene_summary:
        try:
            prob_str = scene_summary.split("Scene anomaly probability:")[1].strip()
            scene_prob = float(prob_str)
        except:
            scene_prob = 0.0
    
    # Debug logging for scene probability parsing
    print(f"� Scene Analysis: {scene_summary}")
    print(f"🎯 Parsed Probability: {scene_prob:.3f}")
    
    # Simple thresholds - no AI reasoning in Tier 1
    pose_anomaly_detected = "True" in pose_summary
    print(f"🤸 Pose Analysis: {'🚨 ANOMALY' if pose_anomaly_detected else '✅ NORMAL'}")
    
    # Very sensitive thresholds to catch visual anomalies better
    if pose_anomaly_detected:
        scene_threshold = 0.15  # Lower threshold when pose anomaly is detected
    else:
        scene_threshold = 0.20  # Much lower threshold for scene-only anomalies
    
    moderate_scene_anomaly = scene_prob > scene_threshold
    print(f"🎬 Scene Threshold: {scene_threshold} | Scene Score: {scene_prob:.3f} | Result: {'🚨 ANOMALY' if moderate_scene_anomaly else '✅ NORMAL'}")
    
    # Quick decisions without AI reasoning - but be more lenient
    if not pose_anomaly_detected and scene_prob < 0.10:  # Only skip if very low scene probability
        print("✅ TIER 1 RESULT: NORMAL - Low threat indicators")
        print("="*60 + "\n")
        return "Normal", f"Scene probability ({scene_prob:.2f}) and pose analysis indicate normal activity"
    
    # Simple threshold-based detection for Tier 1
    if pose_anomaly_detected or moderate_scene_anomaly:
        result = "Suspected Anomaly"
        details = f"Pose anomaly: {pose_anomaly_detected}, Scene probability: {scene_prob:.2f}"
        print(f"🚨 TIER 1 RESULT: SUSPECTED ANOMALY")
        print(f"   └─ Pose: {'DETECTED' if pose_anomaly_detected else 'NORMAL'}")
        print(f"   └─ Scene: {scene_prob:.3f} (threshold: {scene_threshold})")
        print(f"   └─ 🧠 Triggering Tier 2 AI Analysis...")
        print("="*60 + "\n")
        return result, details
    else:
        result = "Normal"
        details = f"Pose anomaly: {pose_anomaly_detected}, Scene probability: {scene_prob:.2f}"
        print(f"✅ TIER 1 RESULT: NORMAL")
        print(f"   └─ Pose: {'DETECTED' if pose_anomaly_detected else 'NORMAL'}")
        print(f"   └─ Scene: {scene_prob:.3f} (threshold: {scene_threshold})")
        print("="*60 + "\n")
        return result, details

def tier2_fusion(audio_transcript, captions, visual_anomaly_max, tier1_details):
    print("\n" + "="*70)
    print("🧠 TIER 2 ANALYSIS - Deep AI Reasoning Engine")
    print("="*70)
    print("🔬 Input Data:")
    print(f"   🎤 Audio: {'Available' if audio_transcript and len(audio_transcript.strip()) > 0 else 'No audio detected'}")
    print(f"   👁️  Visual: {visual_anomaly_max:.3f} anomaly probability")
    print(f"   📝 Scene: {' | '.join(captions) if captions else 'No captions'}")
    print(f"   📊 Tier 1: {tier1_details}")
    print("-"*70)
    
    try:
        visual_summary = " | ".join(captions) if captions else "No captions."
        scene_summary = f"Highest visual anomaly probability: {visual_anomaly_max:.2f}"
        prompt = (
            f"You are an expert anomaly analyst. Provide detailed analysis and reasoning for this anomaly detection case. "
            f"Return ONLY a valid JSON object with no additional text or formatting.\n\n"
            f"INPUT DATA:\n"
            f"- Tier 1 Simple Detection: {tier1_details}\n"
            f"- Audio Transcript: {audio_transcript or 'No audio detected'}\n"
            f"- Visual Scene Description: {visual_summary}\n"
            f"- Visual Anomaly Probability: {visual_anomaly_max:.2f}\n\n"
            f"ANALYSIS REQUIREMENTS:\n"
            f"Provide detailed reasoning that MUST include:\n"
            f"1. POSE ANALYSIS: What does the pose data suggest? (normal posture, aggressive stance, fall position, etc.)\n"
            f"2. SCENE ANALYSIS: What does the visual scene show? How confident are we in this assessment?\n"
            f"3. AUDIO ANALYSIS: Any verbal indicators of distress, aggression, or normalcy?\n"
            f"4. MULTIMODAL CORRELATION: How do all the indicators align? Do they support each other or contradict?\n"
            f"5. ANOMALY TYPE: What specific type of anomaly is most likely? (fall, aggression, medical emergency, false positive)\n"
            f"6. CONFIDENCE ASSESSMENT: How certain is this detection and why?\n"
            f"7. THREAT LEVEL JUSTIFICATION: Why this specific threat severity score?\n\n"
            f"Return JSON with these exact keys:\n"
            f'{{"visual_score": <0-1 float>, "audio_score": <0-1 float>, "text_alignment_score": <0-1 float>, '
            f'"multimodal_agreement": <0-1 float>, "reasoning_summary": "<comprehensive 4-6 sentence analysis covering ALL points above>", "threat_severity_index": <0-1 float>}}'
        )
        
        print("🤖 Sending data to Groq LLM (llama-3.3-70b-versatile)...")
        print(f"🔑 API Key Status: {'Present' if os.getenv('GROQ_API_KEY') else 'Missing'}")
        
        if groq_client is None:
            raise Exception("Groq client not initialized - check API key and connection")
        
        try:
            response = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.1  # Lower temperature for more consistent JSON output
            )
            print("📡 Groq API call successful")
        except Exception as api_error:
            print(f"📡 Groq API call failed: {type(api_error).__name__}: {api_error}")
            raise api_error
            
        output = response.choices[0].message.content.strip()
        print("📨 Received LLM response, processing...")
        print(f"📄 Response preview: {output[:100]}...")  # Show first 100 chars
        
        # Clean up the response to extract JSON
        if "```json" in output:
            output = output.split("```json")[1].split("```")[0].strip()
        elif "```" in output:
            output = output.split("```")[1].split("```")[0].strip()
        
        # Remove any remaining markdown or extra formatting
        output = output.strip()
        if output.startswith('```'):
            output = output[3:].strip()
        if output.endswith('```'):
            output = output[:-3].strip()
        
        # Try to parse JSON
        result = json.loads(output)
        
        # Validate required keys
        required_keys = ["visual_score", "audio_score", "text_alignment_score", 
                        "multimodal_agreement", "reasoning_summary", "threat_severity_index"]
        
        for key in required_keys:
            if key not in result:
                raise KeyError(f"Missing required key: {key}")
        
        # Validate score ranges
        for score_key in ["visual_score", "audio_score", "text_alignment_score", 
                         "multimodal_agreement", "threat_severity_index"]:
            if not (0 <= result[score_key] <= 1):
                result[score_key] = max(0, min(1, result[score_key]))  # Clamp to 0-1
        
        # Beautiful output formatting
        threat_level = "🔴 HIGH" if result["threat_severity_index"] > 0.7 else "🟡 MEDIUM" if result["threat_severity_index"] > 0.4 else "🟢 LOW"
        confidence = "🎯 HIGH" if result["multimodal_agreement"] > 0.7 else "⚠️ MEDIUM" if result["multimodal_agreement"] > 0.4 else "❓ LOW"
        
        print("✅ TIER 2 AI ANALYSIS COMPLETE")
        print("-"*70)
        print(f"🎯 Threat Level: {threat_level} ({result['threat_severity_index']:.1%})")
        print(f"🤝 AI Confidence: {confidence} ({result['multimodal_agreement']:.1%})")
        print(f"👁️  Visual Score: {result['visual_score']:.1%}")
        print(f"🎤 Audio Score: {result['audio_score']:.1%}")
        print("-"*70)
        print("🧠 AI Reasoning:")
        print(f"   {result['reasoning_summary']}")
        print("="*70 + "\n")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error in Tier 2: {e}")
        print(f"📄 Raw LLM output: {output}")
        print(f"🔍 Debug - Output length: {len(output) if 'output' in locals() else 'undefined'}")
    except Exception as e:
        print(f"❌ Error in Tier 2 fusion: {type(e).__name__}: {e}")
        print(f"🔑 Groq API key present: {'Yes' if os.getenv('GROQ_API_KEY') else 'No'}")
        
        # Check for rate limiting specifically
        if "rate_limit_exceeded" in str(e) or "Rate limit reached" in str(e):
            print("⚠️  RATE LIMIT EXCEEDED - Groq API daily token limit reached!")
            print("💡 Solutions:")
            print("   1. Wait for rate limit reset (usually daily)")
            print("   2. Upgrade to Groq Pro tier for higher limits")
            print("   3. Using fallback analysis for now...")
        elif "Error code: 429" in str(e):
            print("⚠️  GROQ API RATE LIMITED - Too many requests")
            print("💡 Using fallback analysis until rate limit resets...")
        
        if hasattr(e, 'response'):
            print(f"📡 API Response: {e.response}")
        import traceback
        print(f"📋 Full traceback: {traceback.format_exc()}")
    
    # Enhanced fallback with actual data-based scoring
    fallback_visual_score = min(1.0, visual_anomaly_max * 2)  # Scale up the visual score
    fallback_audio_score = 0.3 if audio_transcript and len(audio_transcript.strip()) > 0 else 0.1
    fallback_threat = (fallback_visual_score + fallback_audio_score) / 2
    
    print("⚠️  USING FALLBACK ANALYSIS (Groq API Unavailable)")
    print("-"*70)
    
    # Determine fallback reasoning based on available data
    if "rate_limit" in str(e).lower():
        reasoning = f"Rate limit reached - using local analysis. Visual anomaly: {visual_anomaly_max:.2f}, Audio available: {bool(audio_transcript)}"
    else:
        reasoning = f"AI reasoning unavailable - using fallback. Visual anomaly: {visual_anomaly_max:.2f}, Audio available: {bool(audio_transcript)}"
    
    result = {
        "visual_score": fallback_visual_score,
        "audio_score": fallback_audio_score,
        "text_alignment_score": 0.4,
        "multimodal_agreement": 0.4,
        "reasoning_summary": reasoning,
        "threat_severity_index": fallback_threat
    }
    
    print(f"🎯 Fallback Threat: {fallback_threat:.1%}")
    print(f"👁️  Visual Score: {fallback_visual_score:.1%}")
    print(f"🎤 Audio Score: {fallback_audio_score:.1%}")
    print("💡 Note: Upgrade Groq API tier for full AI reasoning")
    print("="*70 + "\n")
    
    return result
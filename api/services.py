"""
Service layer for Bhashini and Gemini integrations with comprehensive error handling.
Implements complete Bhashini API pipeline according to working GeminiBackend.
"""
import os
import json
import logging
import requests
import base64
import tempfile
import copy
import librosa
import soundfile as sf
import io
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message: str, status_code: int = 500, service: str = "unknown"):
        self.message = message
        self.status_code = status_code
        self.service = service
        super().__init__(self.message)

class BhashiniService:
    """Service for Bhashini API integration following working GeminiBackend implementation"""
    
    def __init__(self):
        # Use the working API token from GeminiBackend as fallback
        self.api_token = (
            os.getenv('BHASHINI_AUTH_TOKEN') or 
            os.getenv('ULCA_API_KEY') or 
            os.getenv('BHASHINI_API_KEY') or
            "ujzb4jidEwJo1U-IDxGr2iMkRChAw8qrKcKUQsCA1RSOC2rt6ITU3TihElxkmoHA"  # Working token from GeminiBackend
        )
        
        self.compute_url = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
        
        if not self.api_token:
            raise APIError("Bhashini API Token not configured", 500, "bhashini")
        
        logger.info(f"Bhashini service initialized with token: {self.api_token[:20]}...")
    
    def safe_json(self, response):
        """Safely parse JSON response"""
        try:
            return response.json()
        except json.JSONDecodeError:
            logger.error(f"JSON decode failed: {response.text}")
            return {}
    
    def load_and_resample_audio(self, audio_data, target_sr=16000):
        """Load and resample audio data to target sample rate"""
        try:
            # Create a temporary file to save the audio data
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            # Load and resample using librosa
            y, sr = librosa.load(temp_path, sr=None)
            y_resampled = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            return y_resampled, target_sr
        except Exception as e:
            logger.error(f"Audio resampling failed: {str(e)}")
            raise APIError(f"Audio processing failed: {str(e)}", 500, "bhashini")
    
    def audio_to_base64(self, y, sr):
        """Convert audio array to base64"""
        try:
            buffer = io.BytesIO()
            sf.write(buffer, y, sr, format='wav')
            return base64.b64encode(buffer.getvalue()).decode()
        except Exception as e:
            logger.error(f"Audio encoding failed: {str(e)}")
            raise APIError(f"Audio encoding failed: {str(e)}", 500, "bhashini")
    
    def detect_language(self, audio_base64: str) -> str:
        """Detect language from audio"""
        try:
            lang_detect_payload = {
                "pipelineTasks": [
                    {
                        "taskType": "audio-lang-detection",
                        "config": {
                            "serviceId": "bhashini/iitmandi/audio-lang-detection/gpu"
                        }
                    }
                ],
                "inputData": {"audio": [{"audioContent": audio_base64}]}
            }
            
            headers = {"Authorization": self.api_token}
            response = requests.post(self.compute_url, headers=headers, json=lang_detect_payload, timeout=30)
            
            if response.status_code == 200:
                data = self.safe_json(response)
                lang_full = data.get("pipelineResponse", [{}])[0].get("output", [{}])[0].get("langPrediction", [{}])[0].get("langCode", "hi")
                lang = str(lang_full).split("-")[0]  # Converts 'en-US' → 'en'
                logger.info(f"🔤 Detected Language: {lang}")
                return lang
            else:
                logger.warning(f"Language detection failed: {response.status_code}")
                return "hi"  # Default to Hindi
                
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}")
            return "hi"  # Default to Hindi
    
    def process_audio(self, audio_base64: str, source_lang: str, target_lang: str, audio_format: str) -> Dict[str, Any]:
        """Process audio through Bhashini ASR and Translation pipeline using working GeminiBackend approach"""
        try:
            # Normalize language codes
            source_lang = source_lang.split('-')[0].lower()
            target_lang = target_lang.split('-')[0].lower()
            
            logger.info(f"Processing audio: {source_lang} -> {target_lang}, format: {audio_format}")
            
            # Decode base64 audio
            audio_data = base64.b64decode(audio_base64)
            
            # Resample audio to 16kHz (critical for Bhashini)
            try:
                y_resampled, sr = self.load_and_resample_audio(audio_data)
                resampled_audio_b64 = self.audio_to_base64(y_resampled, sr)
                logger.info("✅ Audio resampled to 16kHz")
            except Exception as e:
                logger.warning(f"Audio resampling failed, using original: {str(e)}")
                resampled_audio_b64 = audio_base64
            
            # Language detection (optional, use provided source_lang as fallback)
            try:
                detected_lang = self.detect_language(resampled_audio_b64)
                if detected_lang and detected_lang != source_lang:
                    logger.info(f"Language detection suggests: {detected_lang}, but using provided: {source_lang}")
            except Exception:
                pass
            
            # Use the exact working payload structure from GeminiBackend
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "asr",
                        "config": {
                            "language": {
                                "sourceLanguage": source_lang
                            },
                            "serviceId": "bhashini/ai4bharat/conformer-multilingual-asr",
                            "audioFormat": "wav",
                            "samplingRate": 16000,
                            "postprocessors": [
                                "itn"
                            ]
                        }
                    },
                    {
                        "taskType": "translation",
                        "config": {
                            "language": {
                                "sourceLanguage": source_lang,
                                "targetLanguage": target_lang
                            },
                            "serviceId": "ai4bharat/indictrans-v2-all-gpu--t4"
                        }
                    }
                ],
                "inputData": {
                    "audio": [
                        {
                            "audioContent": resampled_audio_b64
                        }
                    ]
                }
            }
            
            headers = {"Authorization": self.api_token}
            
            logger.info(f"Sending compute request to: {self.compute_url}")
            logger.info(f"Auth token: {self.api_token[:20]}...")
            
            response = requests.post(self.compute_url, headers=headers, json=payload, timeout=120)
            
            logger.info(f"Compute response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Bhashini compute request failed: {response.status_code} - {response.text}")
                raise APIError(f"Bhashini processing failed: {response.status_code} - {response.text}", response.status_code, "bhashini")
            
            result = self.safe_json(response)
            
            # Log full response for debugging
            logger.info("🧾 Bhashini ASR+Translation Response:")
            logger.info(json.dumps(result, indent=2))
            
            # Extract results using GeminiBackend approach
            outputs = result.get("pipelineResponse", [])
            if len(outputs) < 2:
                logger.error("❌ Bhashini response missing expected outputs")
                raise APIError("Incomplete Bhashini response", 500, "bhashini")
            
            # Extract transcription and translation
            transcript = ""
            translation = ""
            
            try:
                transcript = outputs[0].get("output", [{}])[0].get("source", "")
                translation = outputs[1].get("output", [{}])[0].get("target", "")
                
                logger.info(f"Transcription: {transcript}")
                logger.info(f"Translation: {translation}")
                
                # Build response in expected format
                formatted_result = {
                    "pipelineResponse": [
                        {
                            "taskType": "asr",
                            "output": [{"source": transcript}]
                        },
                        {
                            "taskType": "translation", 
                            "output": [{"target": translation}]
                        }
                    ]
                }
                
                logger.info("Bhashini processing completed successfully")
                return formatted_result
                
            except (IndexError, KeyError) as e:
                logger.error(f"Error extracting transcription/translation: {str(e)}")
                raise APIError("Failed to extract results from Bhashini response", 500, "bhashini")
            
        except APIError:
            raise
        except Exception as e:
            logger.error(f"Bhashini processing error: {str(e)}")
            raise APIError(f"Audio processing failed: {str(e)}", 500, "bhashini")
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get supported languages"""
        return [
            {"code": "hi", "name": "Hindi"},
            {"code": "en", "name": "English"},
            {"code": "bn", "name": "Bengali"},
            {"code": "te", "name": "Telugu"},
            {"code": "mr", "name": "Marathi"},
            {"code": "ta", "name": "Tamil"},
            {"code": "gu", "name": "Gujarati"},
            {"code": "kn", "name": "Kannada"},
            {"code": "ml", "name": "Malayalam"},
            {"code": "pa", "name": "Punjabi"},
            {"code": "or", "name": "Odia"},
            {"code": "as", "name": "Assamese"},
            {"code": "ur", "name": "Urdu"},
            {"code": "ne", "name": "Nepali"},
            {"code": "sa", "name": "Sanskrit"},
            {"code": "sd", "name": "Sindhi"},
            {"code": "ks", "name": "Kashmiri"},
            {"code": "mai", "name": "Maithili"},
            {"code": "mni", "name": "Manipuri"},
            {"code": "brx", "name": "Bodo"},
            {"code": "gom", "name": "Konkani"},
            {"code": "si", "name": "Sinhala"}
        ]
    
    def get_supported_audio_formats(self) -> List[str]:
        """Get supported audio formats"""
        return ["wav", "mp3", "flac", "m4a", "ogg"]

class GeminiService:
    """Service for Google Gemini AI integration"""
    
    def __init__(self):
        # Use the working API key from GeminiBackend as fallback
        self.api_key = (
            os.getenv('GEMINI_API_KEY') or 
            "AIzaSyDQq1B4ZAsHIwVvK49Sl99up4H4JA0GxGQ"  # Working key from GeminiBackend
        )
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
        
        if not self.api_key:
            raise APIError("Gemini API key not configured", 500, "gemini")
    
    def clean_json_string(self, text):
        """Clean JSON string from Gemini response"""
        return re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
    
    def generate_summary_and_actions(self, text: str, pre_meeting_notes: str = "") -> Dict[str, Any]:
        """Generate summary and action items using Gemini AI"""
        try:
            logger.info("Starting Gemini AI analysis...")
            
            if not text or text.strip() == "":
                return {
                    'summary': "No content available for summary",
                    'actionItems': [],
                    'keyDecisions': []
                }
            
            # Build context-aware prompt
            context_parts = []
            
            if pre_meeting_notes and pre_meeting_notes.strip():
                context_parts.append(f"Pre-meeting context and notes:\n{pre_meeting_notes.strip()}")
            
            context_parts.append(f"Meeting transcript/content:\n{text}")
            full_context = "\n\n".join(context_parts)
            
            # Enhanced prompt for better AI analysis
            prompt = f"""
You are an AI meeting assistant. Analyze the following meeting content and provide a comprehensive summary with actionable insights.

{full_context}

Please provide:

1. **SUMMARY**: A detailed, well-structured summary that:
   - Captures key discussion points and decisions
   - Incorporates context from pre-meeting notes (if provided)
   - Highlights important outcomes and agreements
   - Uses clear, professional language
   - Is organized with bullet points or sections where appropriate

2. **ACTION ITEMS**: Extract specific, actionable tasks with:
   - Clear task description
   - Assigned person (if mentioned, otherwise "Not specified")
   - Priority level (High/Medium/Low based on context)
   - Due date (if mentioned, otherwise "Not specified")

3. **KEY DECISIONS**: Important decisions made during the meeting

Format your response as valid JSON:
{{
    "summary": "Your detailed summary here...",
    "actionItems": [
        {{
            "item": "Task description",
            "assignee": "Person name or 'Not specified'",
            "priority": "High/Medium/Low",
            "dueDate": "Date or 'Not specified'"
        }}
    ],
    "keyDecisions": [
        "Decision 1",
        "Decision 2"
    ]
}}

Focus on being comprehensive yet concise. If pre-meeting notes were provided, ensure they are integrated naturally into the summary.
"""
            
            headers = {"Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            logger.info("Sending request to Gemini AI...")
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code != 200:
                logger.error(f"Gemini API request failed: {response.status_code} - {response.text}")
                raise APIError(f"Gemini AI request failed: {response.status_code}", response.status_code, "gemini")
            
            result = response.json()
            
            # Extract generated content
            if 'candidates' not in result or not result['candidates']:
                logger.error(f"No candidates in Gemini response: {result}")
                raise APIError("No response from Gemini AI", 500, "gemini")
            
            candidate = result['candidates'][0]
            if 'content' not in candidate or 'parts' not in candidate['content']:
                logger.error(f"Invalid Gemini response structure: {candidate}")
                raise APIError("Invalid Gemini AI response", 500, "gemini")
            
            generated_text = candidate['content']['parts'][0]['text']
            
            # Parse JSON response
            try:
                # Clean up the response (remove markdown code blocks if present)
                cleaned_text = self.clean_json_string(generated_text)
                parsed_result = json.loads(cleaned_text)
                
                summary = parsed_result.get('summary', 'Summary not available')
                action_items = parsed_result.get('actionItems', [])
                key_decisions = parsed_result.get('keyDecisions', [])
                
                # Validate action items structure
                validated_action_items = []
                for item in action_items:
                    if isinstance(item, dict):
                        validated_action_items.append({
                            'item': str(item.get('item', 'No description')),
                            'assignee': str(item.get('assignee', 'Not specified')),
                            'priority': str(item.get('priority', 'Medium')),
                            'dueDate': str(item.get('dueDate', 'Not specified'))
                        })
                
                # Validate key decisions
                validated_key_decisions = []
                for decision in key_decisions:
                    if isinstance(decision, str):
                        validated_key_decisions.append(decision)
                
                logger.info(f"Gemini AI analysis completed successfully")
                logger.info(f"Summary length: {len(summary)} characters")
                logger.info(f"Action items: {len(validated_action_items)} items")
                logger.info(f"Key decisions: {len(validated_key_decisions)} decisions")
                
                return {
                    'summary': summary,
                    'actionItems': validated_action_items,
                    'keyDecisions': validated_key_decisions
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON response: {str(e)}")
                logger.error(f"Raw response: {generated_text}")
                
                # Fallback: create a basic summary from the raw text
                return {
                    'summary': generated_text if generated_text else "AI analysis completed but summary format was invalid",
                    'actionItems': [],
                    'keyDecisions': []
                }
                
        except APIError:
            raise
        except Exception as e:
            logger.error(f"Gemini AI error: {str(e)}")
            raise APIError(f"AI analysis failed: {str(e)}", 500, "gemini")

# Service instances
_bhashini_service = None
_gemini_service = None

def get_bhashini_service() -> BhashiniService:
    """Get or create Bhashini service instance"""
    global _bhashini_service
    if _bhashini_service is None:
        _bhashini_service = BhashiniService()
    return _bhashini_service

def get_gemini_service() -> GeminiService:
    """Get or create Gemini service instance"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service

def validate_audio_file(audio_file) -> Dict[str, Any]:
    """Validate uploaded audio file"""
    try:
        # Check file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if audio_file.size > max_size:
            return {
                "valid": False,
                "error": f"File size too large. Maximum allowed size is {max_size // (1024*1024)}MB"
            }
        
        # Check file extension
        allowed_extensions = ['.wav', '.mp3', '.flac', '.m4a', '.ogg']
        file_extension = os.path.splitext(audio_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return {
                "valid": False,
                "error": f"Unsupported file format. Supported formats: {', '.join(allowed_extensions)}",
                "supported_formats": allowed_extensions
            }
        
        return {"valid": True}
        
    except Exception as e:
        logger.error(f"File validation error: {str(e)}")
        return {
            "valid": False,
            "error": f"File validation failed: {str(e)}"
        }

def get_audio_format_from_filename(filename: str) -> str:
    """Get audio format from filename"""
    extension = os.path.splitext(filename)[1].lower()
    format_mapping = {
        '.wav': 'wav',
        '.mp3': 'mp3',
        '.flac': 'flac',
        '.m4a': 'm4a',
        '.ogg': 'ogg'
    }
    return format_mapping.get(extension, 'wav')

def get_service_health() -> Dict[str, Any]:
    """Check health of all services"""
    try:
        health_data = {
            "status": "healthy",
            "services": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Check Bhashini service
        try:
            bhashini_service = get_bhashini_service()
            if bhashini_service.api_token:
                health_data["services"]["bhashini"] = "healthy"
            else:
                health_data["services"]["bhashini"] = "unhealthy - token missing"
                health_data["status"] = "degraded"
        except Exception as e:
            health_data["services"]["bhashini"] = f"unhealthy - {str(e)}"
            health_data["status"] = "degraded"
        
        # Check Gemini service
        try:
            gemini_service = get_gemini_service()
            if gemini_service.api_key:
                health_data["services"]["gemini"] = "healthy"
            else:
                health_data["services"]["gemini"] = "unhealthy - API key missing"
                health_data["status"] = "degraded"
        except Exception as e:
            health_data["services"]["gemini"] = f"unhealthy - {str(e)}"
            health_data["status"] = "degraded"
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

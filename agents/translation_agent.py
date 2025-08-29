"""
Translation Agent

Handles text translation and language processing operations.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from core.base_agent import BaseAgent
from core.message_bus import Message
from config.agent_config import AgentType


class Language(Enum):
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"
    HINDI = "hi"
    DUTCH = "nl"
    SWEDISH = "sv"
    NORWEGIAN = "no"
    DANISH = "da"
    FINNISH = "fi"
    POLISH = "pl"
    TURKISH = "tr"
    GREEK = "el"


class TranslationQuality(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    PREMIUM = "premium"


@dataclass
class TranslationRequest:
    request_id: str
    source_text: str
    source_language: Language
    target_language: Language
    quality: TranslationQuality = TranslationQuality.STANDARD
    context: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranslationResult:
    request_id: str
    translated_text: str
    confidence_score: float
    processing_time_ms: int
    detected_language: Optional[Language] = None
    created_at: datetime = field(default_factory=datetime.now)
    alternatives: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LanguageModel:
    model_id: str
    name: str
    supported_languages: List[Language]
    quality: TranslationQuality
    api_endpoint: str
    api_key: Optional[str] = None
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


class TranslationAgent(BaseAgent):
    """
    Translation Agent for handling text translation and language processing.
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.translation_requests: Dict[str, TranslationRequest] = {}
        self.translation_results: Dict[str, TranslationResult] = {}
        self.language_models: Dict[str, LanguageModel] = {}
        self.api_key: Optional[str] = None
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")
        
    async def start(self) -> bool:
        """Start the translation agent and initialize translation services."""
        if await super().start():
            self.logger.info("Translation agent started successfully")
            # Load API key from context
            self.api_key = await self.context_manager.get("translation_api_key", scope="global")
            # Initialize default language models
            await self._initialize_default_models()
            return True
        return False
    
    async def stop(self) -> bool:
        """Stop the translation agent."""
        if await super().stop():
            self.logger.info("Translation agent stopped successfully")
            return True
        return False
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages for translation operations."""
        try:
            if message.content.get("action") == "translate_text":
                return await self._handle_translate_text(message)
            elif message.content.get("action") == "detect_language":
                return await self._handle_detect_language(message)
            elif message.content.get("action") == "batch_translate":
                return await self._handle_batch_translate(message)
            elif message.content.get("action") == "add_language_model":
                return await self._handle_add_language_model(message)
            elif message.content.get("action") == "get_supported_languages":
                return await self._handle_get_supported_languages(message)
            elif message.content.get("action") == "get_translation_history":
                return await self._handle_get_translation_history(message)
            else:
                return await super().process_message(message)
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": str(e)},
                priority=message.priority
            )
    
    async def _handle_translate_text(self, message: Message) -> Message:
        """Handle text translation request."""
        source_text = message.content.get("source_text")
        source_language = message.content.get("source_language")
        target_language = message.content.get("target_language")
        quality = message.content.get("quality", "standard")
        context = message.content.get("context")
        
        if not source_text:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": "Source text is required"}
            )
        
        if not target_language:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": "Target language is required"}
            )
        
        try:
            # Create translation request
            request_id = f"translation_{len(self.translation_requests) + 1}"
            request = TranslationRequest(
                request_id=request_id,
                source_text=source_text,
                source_language=Language(source_language) if source_language else None,
                target_language=Language(target_language),
                quality=TranslationQuality(quality),
                context=context
            )
            
            # Perform translation
            result = await self._translate_text(request)
            
            # Store request and result
            self.translation_requests[request_id] = request
            self.translation_results[request_id] = result
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "text_translated",
                    "request_id": request_id,
                    "result": self._translation_result_to_dict(result)
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error translating text: {str(e)}"}
            )
    
    async def _handle_detect_language(self, message: Message) -> Message:
        """Handle language detection request."""
        text = message.content.get("text")
        
        if not text:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": "Text is required for language detection"}
            )
        
        try:
            detected_language = await self._detect_language(text)
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "language_detected",
                    "text": text,
                    "detected_language": detected_language.value if detected_language else None,
                    "confidence": 0.95  # Simulated confidence
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error detecting language: {str(e)}"}
            )
    
    async def _handle_batch_translate(self, message: Message) -> Message:
        """Handle batch translation request."""
        texts = message.content.get("texts", [])
        target_language = message.content.get("target_language")
        quality = message.content.get("quality", "standard")
        
        if not texts:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": "Texts list is required"}
            )
        
        if not target_language:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": "Target language is required"}
            )
        
        try:
            results = []
            for i, text in enumerate(texts):
                request_id = f"batch_translation_{len(self.translation_requests) + 1}"
                request = TranslationRequest(
                    request_id=request_id,
                    source_text=text,
                    target_language=Language(target_language),
                    quality=TranslationQuality(quality)
                )
                
                result = await self._translate_text(request)
                results.append({
                    "original_text": text,
                    "translated_text": result.translated_text,
                    "confidence": result.confidence_score
                })
                
                # Store request and result
                self.translation_requests[request_id] = request
                self.translation_results[request_id] = result
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "batch_translated",
                    "results": results,
                    "count": len(results)
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error in batch translation: {str(e)}"}
            )
    
    async def _handle_add_language_model(self, message: Message) -> Message:
        """Handle language model addition request."""
        model_data = message.content.get("model_data", {})
        
        model = LanguageModel(
            model_id=model_data.get("model_id", f"model_{len(self.language_models) + 1}"),
            name=model_data.get("name", "Untitled Model"),
            supported_languages=[Language(lang) for lang in model_data.get("supported_languages", [])],
            quality=TranslationQuality(model_data.get("quality", "standard")),
            api_endpoint=model_data.get("api_endpoint", ""),
            api_key=model_data.get("api_key"),
            enabled=model_data.get("enabled", True)
        )
        
        self.language_models[model.model_id] = model
        self.logger.info(f"Added language model: {model.model_id} - {model.name}")
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "language_model_added",
                "model_id": model.model_id,
                "model": {
                    "model_id": model.model_id,
                    "name": model.name,
                    "supported_languages": [lang.value for lang in model.supported_languages],
                    "quality": model.quality.value,
                    "api_endpoint": model.api_endpoint,
                    "enabled": model.enabled,
                    "created_at": model.created_at.isoformat()
                }
            }
        )
    
    async def _handle_get_supported_languages(self, message: Message) -> Message:
        """Handle supported languages request."""
        model_id = message.content.get("model_id")
        
        if model_id and model_id in self.language_models:
            model = self.language_models[model_id]
            languages = [lang.value for lang in model.supported_languages]
        else:
            # Return all supported languages
            languages = [lang.value for lang in Language]
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "supported_languages",
                "languages": languages,
                "count": len(languages)
            }
        )
    
    async def _handle_get_translation_history(self, message: Message) -> Message:
        """Handle translation history request."""
        limit = message.content.get("limit", 50)
        
        # Get recent translations
        recent_results = list(self.translation_results.values())
        recent_results.sort(key=lambda x: x.created_at, reverse=True)
        recent_results = recent_results[:limit]
        
        history = []
        for result in recent_results:
            request = self.translation_requests.get(result.request_id)
            if request:
                history.append({
                    "request_id": result.request_id,
                    "source_text": request.source_text,
                    "translated_text": result.translated_text,
                    "source_language": request.source_language.value if request.source_language else None,
                    "target_language": request.target_language.value,
                    "confidence": result.confidence_score,
                    "created_at": result.created_at.isoformat()
                })
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "translation_history",
                "history": history,
                "count": len(history),
                "limit": limit
            }
        )
    
    async def _initialize_default_models(self):
        """Initialize default language models."""
        # Add a default translation model
        default_model = LanguageModel(
            model_id="default_translator",
            name="Default Translation Model",
            supported_languages=list(Language),
            quality=TranslationQuality.STANDARD,
            api_endpoint="https://api.translation.service/default",
            enabled=True
        )
        self.language_models["default_translator"] = default_model
    
    async def _translate_text(self, request: TranslationRequest) -> TranslationResult:
        """Translate text using available models."""
        import time
        start_time = time.time()
        
        # Find suitable model
        suitable_models = [
            model for model in self.language_models.values()
            if model.enabled and 
            request.target_language in model.supported_languages and
            (request.source_language is None or request.source_language in model.supported_languages)
        ]
        
        if not suitable_models:
            raise Exception(f"No suitable translation model found for {request.target_language.value}")
        
        # Select best model based on quality
        best_model = max(suitable_models, key=lambda m: m.quality.value)
        
        # Simulate translation (in real implementation, call actual API)
        translated_text = await self._simulate_translation(
            request.source_text, 
            request.source_language, 
            request.target_language,
            request.context
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        result = TranslationResult(
            request_id=request.request_id,
            translated_text=translated_text,
            confidence_score=0.95,  # Simulated confidence
            detected_language=request.source_language,
            processing_time_ms=processing_time,
            alternatives=[translated_text]  # Simulated alternatives
        )
        
        return result
    
    async def _detect_language(self, text: str) -> Optional[Language]:
        """Detect the language of the given text."""
        # Simple language detection based on common words
        text_lower = text.lower()
        
        # Common words in different languages
        language_indicators = {
            Language.ENGLISH: ["the", "and", "is", "to", "of", "a", "in", "that", "it", "with"],
            Language.SPANISH: ["el", "la", "de", "que", "y", "a", "en", "un", "es", "se"],
            Language.FRENCH: ["le", "la", "de", "et", "à", "un", "il", "est", "en", "que"],
            Language.GERMAN: ["der", "die", "das", "und", "in", "den", "von", "zu", "mit", "sich"],
            Language.ITALIAN: ["il", "la", "di", "e", "a", "in", "un", "che", "è", "con"],
            Language.PORTUGUESE: ["o", "a", "de", "e", "do", "da", "em", "um", "para", "é"],
            Language.RUSSIAN: ["и", "в", "не", "на", "я", "быть", "тот", "он", "о", "как"],
            Language.CHINESE: ["的", "是", "在", "有", "和", "了", "人", "我", "他", "这"],
            Language.JAPANESE: ["の", "に", "は", "を", "た", "が", "で", "て", "と", "し"],
            Language.KOREAN: ["이", "가", "을", "를", "의", "에", "도", "는", "로", "하"]
        }
        
        # Count matches for each language
        language_scores = {}
        for lang, indicators in language_indicators.items():
            score = sum(1 for word in indicators if word in text_lower)
            language_scores[lang] = score
        
        # Return language with highest score
        if language_scores:
            best_language = max(language_scores.items(), key=lambda x: x[1])
            return best_language[0] if best_language[1] > 0 else None
        
        return None
    
    async def _simulate_translation(self, source_text: str, source_lang: Optional[Language], target_lang: Language, context: Optional[str] = None) -> str:
        """Simulate translation (in real implementation, call actual translation API)."""
        # Simple translation simulation
        # In a real implementation, you would call Google Translate, DeepL, or similar API
        
        # Simulate some basic translations
        translations = {
            "hello": {
                Language.SPANISH: "hola",
                Language.FRENCH: "bonjour",
                Language.GERMAN: "hallo",
                Language.ITALIAN: "ciao",
                Language.PORTUGUESE: "olá",
                Language.RUSSIAN: "привет",
                Language.CHINESE: "你好",
                Language.JAPANESE: "こんにちは",
                Language.KOREAN: "안녕하세요",
                Language.ARABIC: "مرحبا"
            },
            "goodbye": {
                Language.SPANISH: "adiós",
                Language.FRENCH: "au revoir",
                Language.GERMAN: "auf wiedersehen",
                Language.ITALIAN: "arrivederci",
                Language.PORTUGUESE: "adeus",
                Language.RUSSIAN: "до свидания",
                Language.CHINESE: "再见",
                Language.JAPANESE: "さようなら",
                Language.KOREAN: "안녕히 가세요",
                Language.ARABIC: "وداعا"
            },
            "thank you": {
                Language.SPANISH: "gracias",
                Language.FRENCH: "merci",
                Language.GERMAN: "danke",
                Language.ITALIAN: "grazie",
                Language.PORTUGUESE: "obrigado",
                Language.RUSSIAN: "спасибо",
                Language.CHINESE: "谢谢",
                Language.JAPANESE: "ありがとう",
                Language.KOREAN: "감사합니다",
                Language.ARABIC: "شكرا"
            }
        }
        
        source_lower = source_text.lower()
        
        # Check for exact matches
        for english_word, lang_translations in translations.items():
            if english_word in source_lower and target_lang in lang_translations:
                return source_text.replace(english_word, lang_translations[target_lang])
        
        # If no exact match, return a simulated translation
        if target_lang == Language.SPANISH:
            return f"[ES] {source_text}"
        elif target_lang == Language.FRENCH:
            return f"[FR] {source_text}"
        elif target_lang == Language.GERMAN:
            return f"[DE] {source_text}"
        elif target_lang == Language.ITALIAN:
            return f"[IT] {source_text}"
        elif target_lang == Language.PORTUGUESE:
            return f"[PT] {source_text}"
        elif target_lang == Language.RUSSIAN:
            return f"[RU] {source_text}"
        elif target_lang == Language.CHINESE:
            return f"[ZH] {source_text}"
        elif target_lang == Language.JAPANESE:
            return f"[JA] {source_text}"
        elif target_lang == Language.KOREAN:
            return f"[KO] {source_text}"
        elif target_lang == Language.ARABIC:
            return f"[AR] {source_text}"
        else:
            return f"[{target_lang.value.upper()}] {source_text}"
    
    def _translation_result_to_dict(self, result: TranslationResult) -> Dict[str, Any]:
        """Convert translation result to dictionary for serialization."""
        return {
            "request_id": result.request_id,
            "translated_text": result.translated_text,
            "confidence_score": result.confidence_score,
            "detected_language": result.detected_language.value if result.detected_language else None,
            "processing_time_ms": result.processing_time_ms,
            "created_at": result.created_at.isoformat(),
            "alternatives": result.alternatives,
            "metadata": result.metadata
        }
    
    async def _process_message_impl(self, message: Message) -> Dict[str, Any]:
        """Implementation of message processing for translation agent."""
        try:
            action = message.content.get("action")
            
            if action == "translate_text":
                return await self._handle_translate_text(message)
            elif action == "detect_language":
                return await self._handle_detect_language(message)
            elif action == "batch_translate":
                return await self._handle_batch_translate(message)
            elif action == "add_language_model":
                return await self._handle_add_language_model(message)
            elif action == "get_supported_languages":
                return await self._handle_get_supported_languages(message)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            self.logger.error(f"Error in _process_message_impl: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get translation agent metrics."""
        metrics = super().get_metrics()
        metrics.update({
            "total_requests": len(self.translation_requests),
            "total_results": len(self.translation_results),
            "total_models": len(self.language_models),
            "enabled_models": len([m for m in self.language_models.values() if m.enabled]),
            "supported_languages": len(Language),
            "api_key_configured": self.api_key is not None
        })
        return metrics

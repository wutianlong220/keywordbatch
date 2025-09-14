"""
API Client Service for DeepSeek Integration
Handles API calls for keyword translation and processing
"""

import requests
import json
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APIResult:
    """Data class for API results"""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    tokens_used: int = 0
    processing_time: float = 0.0


class DeepSeekAPI:
    """Service class for DeepSeek API integration"""
    
    def __init__(self, api_key: str = None, api_base: str = None):
        """
        Initialize DeepSeek API client
        
        Args:
            api_key: DeepSeek API key (defaults to config)
            api_base: API base URL (defaults to config)
        """
        self.api_key = api_key or Config.DEEPSEEK_API_KEY
        self.api_base = api_base or Config.DEEPSEEK_API_BASE
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        if not self.api_key:
            logger.warning("DeepSeek API key not configured")
    
    def translate_keywords(self, keywords: List[Dict[str, Any]], target_language: str = "Chinese") -> APIResult:
        """
        Translate a batch of keywords using DeepSeek API
        
        Args:
            keywords: List of keyword dictionaries
            target_language: Target language for translation
            
        Returns:
            APIResult with translated data or error
        """
        start_time = time.time()
        
        if not self.api_key:
            return APIResult(
                success=False,
                error_message="DeepSeek API key not configured"
            )
        
        try:
            # Prepare the prompt for translation
            keyword_list = [kw.get('keyword', '') for kw in keywords if kw.get('keyword')]
            
            if not keyword_list:
                return APIResult(
                    success=False,
                    error_message="No valid keywords found for translation"
                )
            
            # Create the system prompt
            system_prompt = f"""You are a professional keyword translator. Translate the following keywords from English to {target_language}.
            
            Requirements:
            1. Provide accurate, natural-sounding translations
            2. Keep the same meaning and context as the original keywords
            3. Return the results in JSON format with the original keyword as key and translation as value
            4. Do not translate brand names or technical terms that should remain in English
            5. If a keyword is already in the target language, return it as-is
            
            Example format:
            {{
                "best running shoes": "最佳跑步鞋",
                "iPhone 15 review": "iPhone 15评测",
                "how to learn Python": "如何学习Python"
            }}
            """
            
            # Create the user prompt with keywords
            user_prompt = f"Please translate these keywords:\n{json.dumps(keyword_list, indent=2)}"
            
            # Make API request
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                json={
                    'model': 'deepseek-chat',
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 4000,
                    'response_format': {'type': 'json_object'}
                },
                timeout=30
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code != 200:
                return APIResult(
                    success=False,
                    error_message=f"API request failed: {response.status_code} - {response.text}",
                    processing_time=processing_time
                )
            
            # Parse response
            response_data = response.json()
            content = response_data['choices'][0]['message']['content']
            tokens_used = response_data.get('usage', {}).get('total_tokens', 0)
            
            # Parse the JSON response
            try:
                translations = json.loads(content)
                
                # Update keywords with translations
                translated_keywords = []
                for kw in keywords:
                    keyword = kw.get('keyword', '')
                    if keyword in translations:
                        kw_copy = kw.copy()
                        kw_copy['translation'] = translations[keyword]
                        translated_keywords.append(kw_copy)
                    else:
                        # Keep original if no translation found
                        translated_keywords.append(kw)
                
                logger.info(f"Successfully translated {len(translated_keywords)} keywords in {processing_time:.2f}s")
                
                return APIResult(
                    success=True,
                    data=translated_keywords,
                    tokens_used=tokens_used,
                    processing_time=processing_time
                )
                
            except json.JSONDecodeError as e:
                return APIResult(
                    success=False,
                    error_message=f"Failed to parse API response: {str(e)}",
                    processing_time=processing_time
                )
            
        except requests.exceptions.RequestException as e:
            processing_time = time.time() - start_time
            return APIResult(
                success=False,
                error_message=f"Network error: {str(e)}",
                processing_time=processing_time
            )
        except Exception as e:
            processing_time = time.time() - start_time
            return APIResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                processing_time=processing_time
            )
    
    def calculate_kdroi_for_batch(self, keywords: List[Dict[str, Any]]) -> APIResult:
        """
        Calculate Kdroi values for a batch of keywords
        
        Args:
            keywords: List of keyword dictionaries with volume, cpc, difficulty
            
        Returns:
            APIResult with keywords containing Kdroi values
        """
        start_time = time.time()
        
        try:
            # Calculate Kdroi for each keyword
            processed_keywords = []
            for kw in keywords:
                try:
                    volume = float(kw.get('volume', 0))
                    cpc = float(kw.get('cpc', 0))
                    difficulty = float(kw.get('difficulty', 1))
                    
                    # Calculate Kdroi: Volume × CPC ÷ Keyword Difficulty
                    if difficulty > 0:
                        kdroi = (volume * cpc) / difficulty
                    else:
                        kdroi = 0
                    
                    kw_copy = kw.copy()
                    kw_copy['kdroi'] = round(kdroi, 2)
                    processed_keywords.append(kw_copy)
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error calculating Kdroi for keyword {kw.get('keyword', 'unknown')}: {e}")
                    kw_copy = kw.copy()
                    kw_copy['kdroi'] = 0
                    processed_keywords.append(kw_copy)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Successfully calculated Kdroi for {len(processed_keywords)} keywords in {processing_time:.2f}s")
            
            return APIResult(
                success=True,
                data=processed_keywords,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return APIResult(
                success=False,
                error_message=f"Error calculating Kdroi: {str(e)}",
                processing_time=processing_time
            )
    
    def generate_platform_links(self, keywords: List[Dict[str, Any]]) -> APIResult:
        """
        Generate platform-specific links for keywords
        
        Args:
            keywords: List of keyword dictionaries
            
        Returns:
            APIResult with keywords containing platform links
        """
        start_time = time.time()
        
        try:
            processed_keywords = []
            for kw in keywords:
                keyword = kw.get('keyword', '')
                if not keyword:
                    processed_keywords.append(kw)
                    continue
                
                kw_copy = kw.copy()
                
                # Google Search link
                kw_copy['google_search_link'] = f"https://www.google.com/search?q={requests.utils.quote(keyword)}"
                
                # Google Trends link
                kw_copy['google_trends_link'] = f"https://trends.google.com/trends/explore?q={requests.utils.quote(keyword)}"
                
                # Ahrefs link
                kw_copy['ahrefs_link'] = f"https://ahrefs.com/keyword-explorer?keyword={requests.utils.quote(keyword)}"
                
                processed_keywords.append(kw_copy)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Successfully generated platform links for {len(processed_keywords)} keywords in {processing_time:.2f}s")
            
            return APIResult(
                success=True,
                data=processed_keywords,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return APIResult(
                success=False,
                error_message=f"Error generating platform links: {str(e)}",
                processing_time=processing_time
            )
    
    def process_keyword_batch(self, keywords: List[Dict[str, Any]], translate: bool = True) -> APIResult:
        """
        Process a complete batch of keywords (translation, Kdroi, links)
        
        Args:
            keywords: List of keyword dictionaries
            translate: Whether to translate keywords
            
        Returns:
            APIResult with fully processed keywords
        """
        start_time = time.time()
        
        try:
            processed_keywords = keywords.copy()
            
            # Step 1: Translation (if requested)
            if translate:
                translation_result = self.translate_keywords(processed_keywords)
                if translation_result.success:
                    processed_keywords = translation_result.data
                else:
                    logger.warning(f"Translation failed: {translation_result.error_message}")
            
            # Step 2: Calculate Kdroi
            kdroi_result = self.calculate_kdroi_for_batch(processed_keywords)
            if kdroi_result.success:
                processed_keywords = kdroi_result.data
            else:
                logger.error(f"Kdroi calculation failed: {kdroi_result.error_message}")
                return kdroi_result
            
            # Step 3: Generate platform links
            links_result = self.generate_platform_links(processed_keywords)
            if links_result.success:
                processed_keywords = links_result.data
            else:
                logger.error(f"Link generation failed: {links_result.error_message}")
                return links_result
            
            processing_time = time.time() - start_time
            
            logger.info(f"Successfully processed batch of {len(processed_keywords)} keywords in {processing_time:.2f}s")
            
            return APIResult(
                success=True,
                data=processed_keywords,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return APIResult(
                success=False,
                error_message=f"Error processing keyword batch: {str(e)}",
                processing_time=processing_time
            )
    
    def test_connection(self) -> bool:
        """
        Test API connection
        
        Returns:
            True if connection is successful
        """
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                json={
                    'model': 'deepseek-chat',
                    'messages': [
                        {'role': 'user', 'content': 'Hello, this is a test message.'}
                    ],
                    'max_tokens': 10
                },
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False
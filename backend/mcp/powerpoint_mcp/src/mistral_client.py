"""Mistral API client wrapper with error handling and retry logic."""

import json
import re
import time
import unicodedata
from typing import Optional, Dict, Any, List
from mistralai import Mistral
from loguru import logger
from config import config


class MistralClient:
    """Wrapper for Mistral API with enhanced error handling."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Mistral client."""
        self.api_key = api_key or config.mistral.api_key
        if not self.api_key:
            raise ValueError("Mistral API key not provided. Set MISTRAL_API_KEY environment variable.")
        
        self.client = Mistral(api_key=self.api_key)
        self.model = config.mistral.model
        self.temperature = config.mistral.temperature
        self.max_tokens = config.mistral.max_tokens
        self.top_p = config.mistral.top_p
        
        logger.info(f"Initialized Mistral client with model: {self.model}")
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: str,
        examples: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate JSON response from Mistral.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            examples: Few-shot examples
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            Parsed JSON dictionary
        """
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add few-shot examples if provided
        if examples:
            for example in examples:
                if "user" in example:
                    messages.append({"role": "user", "content": example["user"]})
                if "assistant" in example:
                    messages.append({"role": "assistant", "content": example["assistant"]})
        
        # Add main prompt
        messages.append({"role": "user", "content": prompt})
        
        # Generate response with retry logic
        response = self._generate_with_retry(
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens
        )
        
        # Parse JSON from response
        return self._parse_json_response(response)
    
    def _generate_with_retry(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate response with retry logic."""
        for attempt in range(config.mistral.retry_attempts):
            try:
                logger.debug(f"Attempt {attempt + 1}/{config.mistral.retry_attempts}")
                
                response = self.client.chat.complete(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=self.top_p,
                    response_format={"type": "json_object"}  # Force JSON response
                )
                
                if response.choices and response.choices[0].message:
                    content = response.choices[0].message.content
                    logger.debug(f"Generated response length: {len(content)} chars")
                    return content
                else:
                    raise ValueError("Empty response from Mistral API")
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < config.mistral.retry_attempts - 1:
                    time.sleep(config.mistral.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"All retry attempts failed")
                    raise
        
        raise RuntimeError("Failed to generate response after all retries")
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from response text."""
        try:
            # Clean the response before parsing
            response = self._clean_json_string(response)
            # Try direct JSON parsing
            result = json.loads(response)
            # Additional validation - clean any strings in the result
            return self._clean_json_content(result)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parsing failed: {e}")
            
            # Try to extract JSON from markdown code blocks
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    json_str = response[start:end].strip()
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
            
            # Try to extract JSON from plain code blocks
            if "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                if end > start:
                    json_str = response[start:end].strip()
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
            
            # Try to find JSON-like structure
            for start_char, end_char in [("{", "}"), ("[", "]")]:
                if start_char in response:
                    start = response.find(start_char)
                    # Find matching closing bracket
                    count = 0
                    end = -1
                    for i in range(start, len(response)):
                        if response[i] == start_char:
                            count += 1
                        elif response[i] == end_char:
                            count -= 1
                            if count == 0:
                                end = i + 1
                                break
                    
                    if end > start:
                        json_str = response[start:end]
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            pass
            
            logger.error(f"Could not parse JSON from response: {response[:500]}...")
            raise ValueError("Failed to parse JSON from Mistral response")
    
    def _clean_json_content(self, data):
        """Recursively clean strings in parsed JSON data."""
        if isinstance(data, dict):
            return {key: self._clean_json_content(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._clean_json_content(item) for item in data]
        elif isinstance(data, str):
            # Remove null characters and other control characters
            cleaned = data.replace('\u0000', '')
            cleaned = cleaned.replace('\x00', '')
            # Remove other control characters except newlines and tabs
            cleaned = ''.join(
                char for char in cleaned
                if char in '\n\t\r' or not unicodedata.category(char).startswith('C')
            )
            return cleaned
        else:
            return data
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean JSON string before parsing to fix encoding issues."""
        # Fix Unicode escape sequences
        cleaned = json_str
        
        # Remove null characters first - they break JSON parsing
        cleaned = cleaned.replace('\\u0000', '')
        cleaned = cleaned.replace('\u0000', '')
        cleaned = cleaned.replace('\\x00', '')
        cleaned = cleaned.replace('\x00', '')
        
        # Common French character fixes
        cleaned = cleaned.replace('\\u000e', 'é')
        cleaned = cleaned.replace('\\u0009', '\t')  # Tab character, not é
        cleaned = cleaned.replace('\\u000E', 'é')
        cleaned = cleaned.replace('\\u000a', ' ')  # Replace line feeds with space
        cleaned = cleaned.replace('\\u000d', '')  # Remove carriage returns
        
        # Fix specific patterns
        cleaned = re.sub(r'R\\u000e9', 'Ré', cleaned)
        cleaned = re.sub(r'\\u000e9', 'é', cleaned)
        cleaned = re.sub(r'\\u000e8', 'è', cleaned)
        cleaned = re.sub(r'\\u000e0', 'à', cleaned)
        cleaned = re.sub(r'\\u000e2', 'â', cleaned)
        cleaned = re.sub(r'\\u000e7', 'ç', cleaned)
        
        # Remove any remaining control characters
        cleaned = re.sub(r'\\u00[0-1][0-9a-fA-F]', '', cleaned)
        
        return cleaned
    
    def test_connection(self) -> bool:
        """Test connection to Mistral API."""
        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": "Say 'OK' if you can hear me"}],
                max_tokens=10
            )
            return bool(response.choices)
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
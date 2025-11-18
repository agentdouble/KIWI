"""Local LLM client for PowerPoint generation using VLLM/Ollama."""

import json
import asyncio
from typing import Optional, Dict, Any, List
from loguru import logger
import httpx
from pydantic import BaseModel, Field


class LocalLLMConfig(BaseModel):
    """Configuration for local LLM."""
    base_url: str = Field(default="http://localhost:5263/v1")
    model_path: str = Field(default="/home/llama/models/base_models/Mistral-Small-3.1-24B-Instruct-2503")
    api_key: str = Field(default="local-key")
    temperature: float = Field(default=0.3)
    max_tokens: int = Field(default=128000)
    timeout: int = Field(default=180)


class LocalLLMClient:
    """Client for local LLM inference using VLLM or similar."""
    
    def __init__(self, config: Optional[LocalLLMConfig] = None):
        """Initialize local LLM client."""
        self.config = config or LocalLLMConfig()
        logger.info(f"Local LLM client initialized with {self.config.base_url}")
    
    async def _create_client(self) -> httpx.AsyncClient:
        """Create a new HTTP client for each request."""
        return httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout),
            base_url=self.config.base_url,
            limits=httpx.Limits(max_connections=5, max_keepalive_connections=2)
        )
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = 0.95
    ) -> str:
        """
        Generate response from local LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        try:
            payload = {
                "model": self.config.model_path,
                "messages": messages,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
                "top_p": top_p,
                "response_format": {"type": "json_object"}
            }
            
            logger.debug(f"Sending request to local LLM with {len(messages)} messages")
            
            async with await self._create_client() as client:
                response = await client.post(
                    "/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json"
                    }
                )
            
                if response.status_code != 200:
                    logger.error(f"Local LLM error: {response.status_code} - {response.text}")
                    raise Exception(f"Local LLM returned status {response.status_code}")
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Try to parse as JSON to validate
                try:
                    json.loads(content)
                except json.JSONDecodeError:
                    logger.warning("Response is not valid JSON, attempting to extract JSON")
                    # Try to extract JSON from the response
                    content = self._extract_json(content)
                
                return content
            
        except httpx.TransportError as e:
            # Handle connection errors by retrying with a new client
            logger.warning(f"Transport error, retrying with new client: {e}")
            try:
                async with await self._create_client() as client:
                    response = await client.post(
                        "/chat/completions",
                        json={
                            "model": self.config.model_path,
                            "messages": messages,
                            "temperature": temperature or self.config.temperature,
                            "max_tokens": max_tokens or self.config.max_tokens,
                            "top_p": top_p,
                            "response_format": {"type": "json_object"}
                        },
                        headers={
                            "Authorization": f"Bearer {self.config.api_key}",
                            "Content-Type": "application/json"
                        }
                    )
                    if response.status_code != 200:
                        raise Exception(f"Local LLM returned status {response.status_code}")
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    try:
                        json.loads(content)
                    except json.JSONDecodeError:
                        content = self._extract_json(content)
                    return content
            except Exception as retry_error:
                logger.error(f"Retry failed: {retry_error}")
                raise
        except Exception as e:
            logger.error(f"Error generating from local LLM: {e}")
            raise
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Generate streaming response from local LLM.
        
        Args:
            messages: List of message dicts
            temperature: Generation temperature
            max_tokens: Maximum tokens
            
        Yields:
            Chunks of generated text
        """
        try:
            payload = {
                "model": self.config.model_path,
                "messages": messages,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
                "stream": True
            }
            
            async with await self._create_client() as client:
                async with client.stream(
                    "POST",
                    "/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json"
                    }
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and chunk["choices"]:
                                    delta = chunk["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue
                            
        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            raise
    
    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text that might contain other content.
        
        Args:
            text: Text potentially containing JSON
            
        Returns:
            Extracted JSON string
        """
        # Try to find JSON boundaries
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_str = text[start_idx:end_idx + 1]
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                pass
        
        # If that didn't work, raise an error
        raise ValueError("Could not extract valid JSON from response")
    
    async def close(self):
        """No-op since we create clients per request."""
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class LocalPowerPointConverter:
    """PowerPoint converter using local LLM."""
    
    def __init__(self, config: Optional[LocalLLMConfig] = None):
        """Initialize converter with local LLM."""
        self.config = config or LocalLLMConfig()
        self.client = None
        logger.info("Local PowerPoint converter initialized")
    
    def _get_client(self) -> LocalLLMClient:
        """Get or create LLM client."""
        if self.client is None:
            self.client = LocalLLMClient(self.config)
        return self.client
    
    async def convert_text(
        self,
        text: str,
        system_prompt: str,
        temperature: float = 0.3,
        examples: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Convert text to PowerPoint JSON using local LLM.
        
        Args:
            text: Input text to convert
            system_prompt: System prompt for the model
            temperature: Generation temperature
            
        Returns:
            PowerPoint JSON structure
        """
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add few-shot examples if provided
        if examples:
            for example in examples:
                if "user" in example:
                    messages.append({"role": "user", "content": example["user"]})
                if "assistant" in example:
                    messages.append({"role": "assistant", "content": example["assistant"]})
        
        # Add the actual user request
        messages.append({"role": "user", "content": text})
        
        try:
            client = self._get_client()
            response = await client.generate(
                messages=messages,
                temperature=temperature
            )
            
            # Parse JSON response
            presentation_json = json.loads(response)
            
            logger.success(f"Generated presentation with {len(presentation_json.get('slides', []))} slides")
            return presentation_json
            
        except Exception as e:
            logger.error(f"Failed to convert text: {e}")
            raise
    
    async def close(self):
        """Close the client."""
        if self.client:
            await self.client.close()
            self.client = None


# Example usage for testing
async def test_local_llm():
    """Test the local LLM client."""
    config = LocalLLMConfig()
    
    async with LocalLLMClient(config) as client:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Count from 1 to 5 in JSON format."}
        ]
        
        response = await client.generate(messages)
        print(f"Response: {response}")


if __name__ == "__main__":
    asyncio.run(test_local_llm())
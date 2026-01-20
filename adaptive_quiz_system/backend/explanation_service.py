# -*- coding: utf-8 -*-
"""
Explanation service using OpenRouter API (supports multiple AI models).
Generates personalized explanations for trail recommendations.
"""

import os
from typing import Dict, List, Optional
from openai import OpenAI


class ExplanationService:
    """Generates explanations using OpenRouter API with graceful fallback."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "openai/gpt-3.5-turbo", 
        timeout: int = 5,
        use_openrouter: bool = None
    ):
        """
        Initialize the explanation service.
        
        Args:
            api_key: API key (defaults to OPENROUTER_API_KEY or OPENAI_API_KEY env var)
            model: Model to use (default: openai/gpt-3.5-turbo for OpenRouter)
                   For OpenAI, use: gpt-3.5-turbo
                   For OpenRouter, use: openai/gpt-3.5-turbo, anthropic/claude-3-haiku, etc.
            timeout: Request timeout in seconds (default: 5)
            use_openrouter: Whether to use OpenRouter (defaults to checking for OPENROUTER_API_KEY)
        """
        # Determine which service to use
        if use_openrouter is None:
            # Auto-detect: prefer OpenRouter if key exists, otherwise use OpenAI
            use_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
        
        if use_openrouter:
            self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
            self.base_url = "https://openrouter.ai/api/v1"
            # Default to a cost-effective model if using OpenRouter
            if model == "gpt-3.5-turbo":
                self.model = "openai/gpt-3.5-turbo"
            else:
                self.model = model
        else:
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            self.base_url = None  # Use default OpenAI base URL
            self.model = model
        
        self.timeout = timeout
        self.client = None
        self.use_openrouter = use_openrouter
        
        if self.api_key:
            try:
                if self.base_url:
                    # Use OpenRouter
                    # OpenRouter requires default_headers for credits attribution
                    default_headers = {
                        "HTTP-Referer": "https://github.com/your-repo",  # Optional: your website
                        "X-Title": "Trail Recommendation System"  # Optional: your app name
                    }
                    self.client = OpenAI(
                        api_key=self.api_key,
                        base_url=self.base_url,
                        default_headers=default_headers,
                        timeout=self.timeout
                    )
                else:
                    # Use OpenAI directly
                    self.client = OpenAI(
                        api_key=self.api_key,
                        timeout=self.timeout
                    )
            except Exception as e:
                print(f"Failed to initialize API client: {e}")
                self.client = None
    
    def generate_explanation(self, prompt: str) -> Optional[Dict]:
        """
        Generate explanation from prompt using OpenRouter/OpenAI API.
        
        Args:
            prompt: The prompt string to send to the API
        
        Returns:
            {
                "explanation_text": str,  # Main paragraph
                "key_factors": List[str]   # Bullet points
            }
            Returns None if API call fails
        """
        if not self.client:
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful hiking trail recommendation assistant. Generate brief, personalized explanations (2-3 sentences) explaining why trails are recommended. IMPORTANT: Also mention what aspects don't perfectly match the user's profile (e.g., if a trail is too long for a beginner, or weather doesn't match). Be honest and transparent. Provide 3-5 key factors as bullet points, including both matches and important mismatches. Be friendly, concise, and specific."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            content = response.choices[0].message.content
            return self._parse_response(content)
            
        except Exception as e:
            service_name = "OpenRouter" if self.use_openrouter else "OpenAI"
            print(f"{service_name} API error: {e}")
            return None
    
    def _parse_response(self, content: str) -> Dict:
        """
        Parse OpenAI response to extract explanation text and key factors.
        
        Args:
            content: Raw response from OpenAI
        
        Returns:
            {
                "explanation_text": str,
                "key_factors": List[str]
            }
        """
        # Try to split by common separators
        lines = content.strip().split('\n')
        
        explanation_text = ""
        key_factors = []
        
        # Look for bullet points (starting with -, *, •, or numbered)
        in_factors = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a bullet point
            if line.startswith('-') or line.startswith('*') or line.startswith('•') or \
               (line and line[0].isdigit() and ('.' in line[:3] or ')' in line[:3])):
                # Remove bullet marker
                factor = line.lstrip('-*•0123456789.) ').strip()
                if factor:
                    key_factors.append(factor)
                in_factors = True
            elif in_factors:
                # Continue adding to last factor if it's a continuation
                if key_factors:
                    key_factors[-1] += " " + line
                else:
                    key_factors.append(line)
            else:
                # This is part of the explanation text
                if explanation_text:
                    explanation_text += " " + line
                else:
                    explanation_text = line
        
        # If no key factors found, try to extract them from the text
        if not key_factors and explanation_text:
            # Fallback: use the explanation text as-is
            # Split by sentences and use first 2-3 as explanation, rest as factors
            sentences = explanation_text.split('. ')
            if len(sentences) > 2:
                explanation_text = '. '.join(sentences[:2]) + '.'
                key_factors = [s.strip('.') for s in sentences[2:5] if s.strip()]
        
        # Ensure we have at least something
        if not explanation_text:
            explanation_text = content
        
        if not key_factors:
            key_factors = ["Based on your profile and preferences", 
                          "Matches your experience level",
                          "Fits your available time"]
        
        return {
            "explanation_text": explanation_text.strip(),
            "key_factors": key_factors[:5]  # Limit to 5 factors
        }
    
    def generate_fallback_explanation(self, matched_criteria: List[Dict]) -> Dict:
        """
        Generate a fallback explanation from matched criteria.
        Used when the API is unavailable.
        
        Args:
            matched_criteria: List of matched criteria dictionaries
        
        Returns:
            {
                "explanation_text": str,
                "key_factors": List[str]
            }
        """
        if not matched_criteria:
            return {
                "explanation_text": "This trail was recommended based on your profile and current search context.",
                "key_factors": [
                    "Matches your hiking profile",
                    "Fits your search criteria",
                    "Suitable for your experience level"
                ]
            }
        
        # Extract messages from matched criteria
        factors = [c.get("message", c.get("name", "")) for c in matched_criteria if c.get("message")]
        
        # Build explanation text
        explanation = "This trail was recommended because it matches your preferences and search context. "
        if factors:
            explanation += f"Specifically, it aligns with: {', '.join(factors[:3])}."
        
        return {
            "explanation_text": explanation,
            "key_factors": factors[:5] if factors else [
                "Matches your hiking profile",
                "Fits your search criteria"
            ]
        }

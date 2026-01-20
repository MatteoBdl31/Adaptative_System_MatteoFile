# -*- coding: utf-8 -*-
"""
Explanation enricher for trail recommendations.
Handles batch processing, caching, and async generation of explanations.
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict
from backend.explanation_service import ExplanationService
from .context_builder import ContextBuilder


class ExplanationEnricher:
    """Enriches recommendations with AI-generated explanations using caching and async processing."""
    
    def __init__(self, max_cache_size: int = 100, cache_ttl: int = 300):
        """
        Initialize the explanation enricher.
        
        Args:
            max_cache_size: Maximum number of cached explanations (LRU eviction)
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        self.explanation_service = ExplanationService()
        self.context_builder = ContextBuilder()
        self._cache: OrderedDict = OrderedDict()  # LRU cache
        self.max_cache_size = max_cache_size
        self.cache_ttl = cache_ttl
    
    def generate_general_explanation(
        self,
        user: Dict,
        context: Dict,
        exact_matches: List[Dict],
        suggestions: List[Dict],
        active_rules: List[Dict]
    ) -> Optional[Dict]:
        """
        Generate general explanation for all recommendations.
        
        Args:
            user: User profile dictionary
            context: Search context dictionary
            exact_matches: List of exact match trails
            suggestions: List of suggestion trails
            active_rules: List of active matching rules
        
        Returns:
            {
                "explanation_text": str,
                "key_factors": List[str]
            }
            Returns None if generation fails
        """
        # Check cache first
        cache_key = self._generate_cache_key(user.get("id"), context, None)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        # Build context and prompt
        context_dict = self.context_builder.build_general_context(
            user, context, exact_matches, suggestions, active_rules
        )
        prompt = self.context_builder.build_prompt(context_dict, "general")
        
        # Generate explanation
        explanation = self.explanation_service.generate_explanation(prompt)
        
        # Fallback to rule-based if OpenAI fails
        if not explanation:
            matched_criteria = []
            for trail in exact_matches + suggestions:
                matched = trail.get("matched_criteria", [])
                if matched:
                    matched_criteria.extend(matched)
            
            explanation = self.explanation_service.generate_fallback_explanation(matched_criteria)
        
        # Cache the result
        if explanation:
            self._add_to_cache(cache_key, explanation)
        
        return explanation
    
    def generate_trail_explanation(
        self,
        trail: Dict,
        user: Dict,
        context: Dict,
        matched_criteria: List[Dict],
        unmatched_criteria: List[Dict]
    ) -> Optional[Dict]:
        """
        Generate explanation for a specific trail.
        
        Args:
            trail: Trail dictionary
            user: User profile dictionary
            context: Search context dictionary
            matched_criteria: List of matched criteria
            unmatched_criteria: List of unmatched criteria
        
        Returns:
            {
                "explanation_text": str,
                "key_factors": List[str]
            }
            Returns None if generation fails
        """
        trail_id = trail.get("trail_id")
        
        # Check cache first
        cache_key = self._generate_cache_key(user.get("id"), context, trail_id)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        # Build context and prompt
        context_dict = self.context_builder.build_trail_context(
            trail, user, context, matched_criteria, unmatched_criteria
        )
        prompt = self.context_builder.build_prompt(context_dict, "trail")
        
        # Generate explanation
        explanation = self.explanation_service.generate_explanation(prompt)
        
        # Fallback to rule-based if OpenAI fails
        if not explanation:
            explanation = self.explanation_service.generate_fallback_explanation(matched_criteria)
        
        # Cache the result
        if explanation:
            self._add_to_cache(cache_key, explanation)
        
        return explanation
    
    def _generate_cache_key(
        self,
        user_id: Optional[int],
        context: Dict,
        trail_id: Optional[str]
    ) -> str:
        """
        Generate cache key from user_id, context, and optional trail_id.
        
        Args:
            user_id: User ID
            context: Context dictionary
            trail_id: Optional trail ID for per-trail explanations
        
        Returns:
            Cache key string
        """
        # Create a hashable representation of context (excluding non-deterministic fields)
        context_copy = {
            "time_available": context.get("time_available"),
            "device": context.get("device"),
            "weather": context.get("weather"),
            "season": context.get("season"),
            "connection": context.get("connection"),
            "hike_start_date": context.get("hike_start_date") or context.get("hike_date")
        }
        
        # Create hash
        key_data = {
            "user_id": user_id,
            "context": context_copy,
            "trail_id": trail_id
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """
        Get explanation from cache if valid.
        
        Args:
            cache_key: Cache key
        
        Returns:
            Cached explanation or None
        """
        if cache_key not in self._cache:
            return None
        
        cached_entry = self._cache[cache_key]
        cached_time, explanation = cached_entry
        
        # Check if cache entry is still valid
        if time.time() - cached_time > self.cache_ttl:
            # Expired, remove from cache
            del self._cache[cache_key]
            return None
        
        # Move to end (most recently used)
        self._cache.move_to_end(cache_key)
        return explanation
    
    def _add_to_cache(self, cache_key: str, explanation: Dict) -> None:
        """
        Add explanation to cache with LRU eviction.
        
        Args:
            cache_key: Cache key
            explanation: Explanation dictionary
        """
        # Remove oldest entry if cache is full
        if len(self._cache) >= self.max_cache_size:
            self._cache.popitem(last=False)  # Remove oldest (first) item
        
        # Add new entry
        self._cache[cache_key] = (time.time(), explanation)
    
    def clear_cache(self) -> None:
        """Clear the explanation cache."""
        self._cache.clear()

"""
Cache module for caching query results.
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from ..utils.logger import get_logger

logger = get_logger(__name__)

class QueryCache:
    """Class for caching query results."""
    
    def __init__(self, config: Dict):
        """
        Initialize the query cache with configuration.
        
        Args:
            config: Configuration dictionary with cache settings
        """
        self.config = config
        self.cache_enabled = config.get('cache_results', True)
        self.cache_dir = Path(config.get('cache_dir', '../data/cache'))
        self.ttl = config.get('cache_ttl', 3600)  # Default TTL: 1 hour
        
        if self.cache_enabled:
            self.cache_dir.mkdir(exist_ok=True, parents=True)
            logger.info(f"Query cache initialized at {self.cache_dir}")
    
    def _get_cache_key(self, query_type: str, query_params: Dict[str, Any]) -> str:
        """
        Generate a cache key for a query.
        
        Args:
            query_type: Type of query
            query_params: Query parameters
            
        Returns:
            Cache key as a string
        """
        # Convert query parameters to a sorted, deterministic string
        query_str = json.dumps(query_params, sort_keys=True)
        
        # Generate a hash of the query type and parameters
        key = hashlib.md5(f"{query_type}:{query_str}".encode()).hexdigest()
        
        return key
    
    def _get_cache_file(self, cache_key: str) -> Path:
        """
        Get the cache file path for a cache key.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Path to the cache file
        """
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, query_type: str, query_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cached results for a query.
        
        Args:
            query_type: Type of query
            query_params: Query parameters
            
        Returns:
            Cached results, or None if not found or expired
        """
        if not self.cache_enabled:
            return None
            
        cache_key = self._get_cache_key(query_type, query_params)
        cache_file = self._get_cache_file(cache_key)
        
        if not cache_file.exists():
            return None
            
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            # Check if cache is expired
            if time.time() - cache_data.get('timestamp', 0) > self.ttl:
                logger.info(f"Cache expired for key: {cache_key}")
                return None
                
            logger.info(f"Cache hit for key: {cache_key}")
            return cache_data.get('results')
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None
    
    def set(self, query_type: str, query_params: Dict[str, Any], results: Dict[str, Any]):
        """
        Cache results for a query.
        
        Args:
            query_type: Type of query
            query_params: Query parameters
            results: Query results to cache
        """
        if not self.cache_enabled:
            return
            
        cache_key = self._get_cache_key(query_type, query_params)
        cache_file = self._get_cache_file(cache_key)
        
        try:
            cache_data = {
                'timestamp': time.time(),
                'query_type': query_type,
                'query_params': query_params,
                'results': results
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.info(f"Cached results for key: {cache_key}")
        except Exception as e:
            logger.error(f"Error writing cache: {e}")
    
    def invalidate(self, query_type: Optional[str] = None):
        """
        Invalidate cache entries.
        
        Args:
            query_type: Optional query type to invalidate (None for all)
        """
        if not self.cache_enabled:
            return
            
        if query_type is None:
            # Invalidate all cache entries
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Invalidated all cache entries")
        else:
            # Invalidate entries for a specific query type
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                        
                    if cache_data.get('query_type') == query_type:
                        cache_file.unlink()
                except Exception:
                    # If we can't read the file, just skip it
                    pass
                    
            logger.info(f"Invalidated cache entries for query type: {query_type}")
    
    def clear_expired(self):
        """Clear expired cache entries."""
        if not self.cache_enabled:
            return
            
        current_time = time.time()
        cleared_count = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    
                if current_time - cache_data.get('timestamp', 0) > self.ttl:
                    cache_file.unlink()
                    cleared_count += 1
            except Exception:
                # If we can't read the file, just skip it
                pass
                
        logger.info(f"Cleared {cleared_count} expired cache entries")
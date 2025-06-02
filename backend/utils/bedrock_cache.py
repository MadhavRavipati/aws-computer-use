# ABOUTME: Caching layer for Bedrock AI responses
# ABOUTME: Reduces costs by caching common UI patterns and actions

import hashlib
import json
import time
import logging
from typing import Dict, Any, Optional, Tuple
import boto3
from botocore.exceptions import ClientError
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BedrockCache:
    """Cache for Bedrock AI responses to reduce API calls and costs"""
    
    def __init__(self, table_name: str = 'computer-use-agent-cache-dev', ttl_hours: int = 24):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        self.table = self.dynamodb.Table(table_name)
        self.ttl_hours = ttl_hours
        self.cloudwatch = boto3.client('cloudwatch')
        
        # In-memory cache for frequently accessed items
        self.memory_cache: Dict[str, Tuple[Any, float]] = {}
        self.memory_cache_ttl = 300  # 5 minutes
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'memory_hits': 0
        }
    
    def _generate_cache_key(self, action_type: str, screenshot_hash: str, context: Dict[str, Any]) -> str:
        """Generate unique cache key for the request"""
        # Create a normalized context string
        context_str = json.dumps(context, sort_keys=True)
        
        # Combine all elements
        key_elements = f"{action_type}:{screenshot_hash}:{context_str}"
        
        # Generate SHA256 hash
        return hashlib.sha256(key_elements.encode()).hexdigest()
    
    def _hash_screenshot(self, screenshot_base64: str) -> str:
        """Generate hash of screenshot for caching"""
        # Use first 10KB of screenshot to generate hash (for performance)
        truncated = screenshot_base64[:10240] if len(screenshot_base64) > 10240 else screenshot_base64
        return hashlib.md5(truncated.encode()).hexdigest()
    
    async def get(self, action_type: str, screenshot: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached response if available"""
        screenshot_hash = self._hash_screenshot(screenshot)
        cache_key = self._generate_cache_key(action_type, screenshot_hash, context)
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            cached_value, cached_time = self.memory_cache[cache_key]
            if time.time() - cached_time < self.memory_cache_ttl:
                self.stats['memory_hits'] += 1
                self.stats['hits'] += 1
                logger.info(f"Memory cache hit for action: {action_type}")
                return cached_value
            else:
                # Expired, remove from memory cache
                del self.memory_cache[cache_key]
        
        # Check DynamoDB
        try:
            response = self.table.get_item(
                Key={'cache_key': cache_key}
            )
            
            if 'Item' in response:
                item = response['Item']
                
                # Check if item is still valid
                if item.get('ttl', 0) > int(time.time()):
                    self.stats['hits'] += 1
                    
                    # Store in memory cache
                    cached_response = {
                        'action': item.get('action'),
                        'coordinates': item.get('coordinates'),
                        'confidence': item.get('confidence'),
                        'reasoning': item.get('reasoning'),
                        'cached': True,
                        'cache_hit_time': datetime.now().isoformat()
                    }
                    
                    self.memory_cache[cache_key] = (cached_response, time.time())
                    
                    logger.info(f"Cache hit for action: {action_type}, confidence: {item.get('confidence')}")
                    
                    # Update metrics
                    await self._update_metrics('cache_hit')
                    
                    return cached_response
            
            self.stats['misses'] += 1
            await self._update_metrics('cache_miss')
            return None
            
        except ClientError as e:
            logger.error(f"Error accessing cache: {e}")
            return None
    
    async def put(
        self, 
        action_type: str, 
        screenshot: str, 
        context: Dict[str, Any], 
        response: Dict[str, Any],
        confidence: float = 1.0
    ):
        """Store response in cache"""
        # Only cache high-confidence responses
        if confidence < 0.8:
            logger.info(f"Skipping cache for low confidence response: {confidence}")
            return
        
        screenshot_hash = self._hash_screenshot(screenshot)
        cache_key = self._generate_cache_key(action_type, screenshot_hash, context)
        
        # Calculate TTL
        ttl = int(time.time()) + (self.ttl_hours * 3600)
        
        try:
            # Store in DynamoDB
            self.table.put_item(
                Item={
                    'cache_key': cache_key,
                    'action_type': action_type,
                    'screenshot_hash': screenshot_hash,
                    'action': response.get('action'),
                    'coordinates': response.get('coordinates'),
                    'confidence': confidence,
                    'reasoning': response.get('reasoning', ''),
                    'context': context,
                    'created_at': int(time.time()),
                    'ttl': ttl,
                    'hit_count': 0
                }
            )
            
            # Store in memory cache
            self.memory_cache[cache_key] = (response, time.time())
            
            logger.info(f"Cached response for action: {action_type}")
            
        except ClientError as e:
            logger.error(f"Error storing in cache: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching a pattern"""
        # Clear memory cache entries matching pattern
        keys_to_remove = [k for k in self.memory_cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self.memory_cache[key]
        
        logger.info(f"Invalidated {len(keys_to_remove)} memory cache entries")
    
    async def _update_metrics(self, metric_name: str):
        """Update CloudWatch metrics"""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='ComputerUse/Cache',
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': 1,
                        'Unit': 'Count'
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'memory_hits': self.stats['memory_hits'],
            'hit_rate': hit_rate,
            'memory_cache_size': len(self.memory_cache)
        }

class CachedComputerUseAgent:
    """Enhanced Computer Use Agent with caching"""
    
    def __init__(self, base_agent, cache: BedrockCache):
        self.base_agent = base_agent
        self.cache = cache
    
    async def execute_task(self, user_intent: str, screenshot: Optional[str] = None) -> Dict[str, Any]:
        """Execute task with caching"""
        if not screenshot:
            # No caching without screenshot
            return await self.base_agent.execute_task(user_intent, screenshot)
        
        # Prepare context for caching
        context = {
            'intent': user_intent,
            'timestamp': int(time.time() // 300) * 300  # Round to 5 minutes
        }
        
        # Try to get from cache
        cached_response = await self.cache.get('execute_task', screenshot, context)
        
        if cached_response:
            logger.info("Using cached response for task execution")
            return cached_response
        
        # Execute actual task
        result = await self.base_agent.execute_task(user_intent, screenshot)
        
        # Cache successful results
        if result.get('success'):
            confidence = result.get('confidence', 0.9)
            await self.cache.put('execute_task', screenshot, context, result, confidence)
        
        return result

# Pattern cache for common UI elements
class UIPatternCache:
    """Cache for common UI patterns to speed up recognition"""
    
    def __init__(self):
        self.patterns = {
            'button': {
                'indicators': ['btn', 'button', 'submit', 'click'],
                'confidence_boost': 0.1
            },
            'input': {
                'indicators': ['input', 'textbox', 'field', 'form'],
                'confidence_boost': 0.1
            },
            'link': {
                'indicators': ['href', 'link', 'anchor', 'url'],
                'confidence_boost': 0.05
            },
            'menu': {
                'indicators': ['menu', 'nav', 'dropdown', 'select'],
                'confidence_boost': 0.05
            }
        }
    
    def enhance_recognition(self, element_description: str, base_confidence: float) -> Tuple[str, float]:
        """Enhance element recognition using cached patterns"""
        element_lower = element_description.lower()
        
        for pattern_type, pattern_data in self.patterns.items():
            for indicator in pattern_data['indicators']:
                if indicator in element_lower:
                    enhanced_confidence = min(
                        base_confidence + pattern_data['confidence_boost'], 
                        1.0
                    )
                    return pattern_type, enhanced_confidence
        
        return 'unknown', base_confidence
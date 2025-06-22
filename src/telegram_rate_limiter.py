"""
Minimal Telegram API Rate Limiter
"""

import asyncio
import time
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class SimpleRateLimiter:
    """Simple rate limiter with token bucket"""
    
    def __init__(self, rate_per_second: int = 20):
        self.rate = rate_per_second
        self.buckets = defaultdict(lambda: {'tokens': rate_per_second, 'last_refill': time.time()})
    
    async def wait_if_needed(self, bot_token: str):
        """Wait if rate limit would be exceeded"""
        bucket = self.buckets[bot_token]
        now = time.time()
        
        # Refill tokens
        elapsed = now - bucket['last_refill']
        bucket['tokens'] = min(self.rate, bucket['tokens'] + elapsed * self.rate)
        bucket['last_refill'] = now
        
        # Check if we need to wait
        if bucket['tokens'] < 1:
            wait_time = (1 - bucket['tokens']) / self.rate
            logger.debug(f"Rate limiting bot {bot_token[:10]}... waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            bucket['tokens'] = 0
        else:
            bucket['tokens'] -= 1


# Global rate limiter
rate_limiter = SimpleRateLimiter()


async def rate_limited_call(bot_token: str, coro):
    """Rate limit a coroutine call"""
    await rate_limiter.wait_if_needed(bot_token)
    
    # Log the API call for monitoring
    try:
        from .test_monitor import log_api_call
        method_name = getattr(coro, '__name__', 'telegram_api_call')
        await log_api_call(method_name, bot_token)
    except ImportError:
        pass  # Monitoring not available
    
    return await coro
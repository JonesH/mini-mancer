"""
Adaptive Telegram API Rate Limiter with 429 Error Handling
"""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


class AdaptiveRateLimiter:
    """Adaptive rate limiter with 429 error handling and exponential backoff"""

    def __init__(self, base_rate_per_second: int = 20, min_rate: int = 1, max_rate: int = 30):
        self.base_rate = base_rate_per_second
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.buckets = defaultdict(lambda: {
            'tokens': base_rate_per_second,
            'last_refill': time.time(),
            'current_rate': base_rate_per_second,
            'consecutive_429s': 0,
            'last_429_time': 0,
            'recovery_start': None,
            'backoff_until': 0
        })

    def _adjust_rate_after_429(self, bot_token: str, retry_after: int | None = None):
        """Adjust rate after receiving 429 error"""
        bucket = self.buckets[bot_token]
        bucket['consecutive_429s'] += 1
        bucket['last_429_time'] = time.time()

        # Exponential backoff - reduce rate more aggressively with repeated 429s
        reduction_factor = 0.5 ** bucket['consecutive_429s']
        bucket['current_rate'] = max(
            self.min_rate,
            int(self.base_rate * reduction_factor)
        )

        # Set backoff period based on Retry-After header or exponential backoff
        if retry_after:
            bucket['backoff_until'] = time.time() + retry_after
            logger.warning(f"Bot {bot_token[:10]}: 429 error, backing off for {retry_after}s (Retry-After header)")
        else:
            backoff_time = min(60, 2 ** bucket['consecutive_429s'])  # Max 60s backoff
            bucket['backoff_until'] = time.time() + backoff_time
            logger.warning(f"Bot {bot_token[:10]}: 429 error #{bucket['consecutive_429s']}, backing off for {backoff_time}s")

        logger.info(f"Bot {bot_token[:10]}: Rate reduced from {self.base_rate} to {bucket['current_rate']}/sec")

    def _maybe_recover_rate(self, bot_token: str):
        """Gradually recover rate after successful period"""
        bucket = self.buckets[bot_token]
        now = time.time()

        # Only attempt recovery if we've had 429s and some time has passed
        if bucket['consecutive_429s'] == 0 or bucket['current_rate'] >= self.base_rate:
            return

        # Start recovery timer if not already started
        if bucket['recovery_start'] is None:
            bucket['recovery_start'] = now
            return

        # Recovery after 30 seconds of no 429s
        recovery_period = 30
        if now - bucket['recovery_start'] >= recovery_period:
            # Increase rate by 25% but don't exceed base rate
            new_rate = min(self.base_rate, int(bucket['current_rate'] * 1.25))
            if new_rate > bucket['current_rate']:
                bucket['current_rate'] = new_rate
                bucket['recovery_start'] = now  # Reset recovery timer
                logger.info(f"Bot {bot_token[:10]}: Rate recovered to {new_rate}/sec")

            # If we've fully recovered, reset 429 count
            if bucket['current_rate'] >= self.base_rate:
                bucket['consecutive_429s'] = 0
                bucket['recovery_start'] = None
                logger.info(f"Bot {bot_token[:10]}: Rate fully recovered to {self.base_rate}/sec")

    async def wait_if_needed(self, bot_token: str):
        """Wait if rate limit would be exceeded or we're in backoff period"""
        bucket = self.buckets[bot_token]
        now = time.time()

        # Check if we're in forced backoff period
        if now < bucket['backoff_until']:
            wait_time = bucket['backoff_until'] - now
            logger.debug(f"Bot {bot_token[:10]}: In backoff period, waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            return

        # Try to recover rate if conditions are met
        self._maybe_recover_rate(bot_token)

        # Use current adjusted rate
        current_rate = bucket['current_rate']

        # Refill tokens based on current rate
        elapsed = now - bucket['last_refill']
        bucket['tokens'] = min(current_rate, bucket['tokens'] + elapsed * current_rate)
        bucket['last_refill'] = now

        # Check if we need to wait
        if bucket['tokens'] < 1:
            wait_time = (1 - bucket['tokens']) / current_rate
            logger.debug(f"Bot {bot_token[:10]}: Rate limiting at {current_rate}/sec, waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            bucket['tokens'] = 0
        else:
            bucket['tokens'] -= 1

    def handle_successful_call(self, bot_token: str):
        """Call this after successful API call to help with recovery"""
        bucket = self.buckets[bot_token]
        # Reset recovery start if we had consecutive 429s but now have success
        if bucket['consecutive_429s'] > 0 and bucket['recovery_start'] is None:
            bucket['recovery_start'] = time.time()

    def get_rate_info(self, bot_token: str) -> dict[str, Any]:
        """Get current rate limiting info for monitoring"""
        bucket = self.buckets[bot_token]
        now = time.time()
        return {
            'base_rate': self.base_rate,
            'current_rate': bucket['current_rate'],
            'tokens_available': bucket['tokens'],
            'consecutive_429s': bucket['consecutive_429s'],
            'in_backoff': now < bucket['backoff_until'],
            'backoff_remaining': max(0, bucket['backoff_until'] - now),
            'recovery_active': bucket['recovery_start'] is not None
        }


# Global adaptive rate limiter
rate_limiter = AdaptiveRateLimiter()


async def rate_limited_call(bot_token: str, coro):
    """Adaptive rate limited coroutine call with 429 error handling
    
    Note: This function adjusts the rate limiter based on 429 errors but does not 
    automatically retry failed calls, as coroutines cannot be awaited twice.
    The rate limiter will adapt for future calls.
    """
    from telegram.error import RetryAfter, TelegramError

    await rate_limiter.wait_if_needed(bot_token)

    # Log the API call for monitoring
    try:
        from .test_monitor import log_api_call
        method_name = getattr(coro, '__name__', 'telegram_api_call')
        await log_api_call(method_name, bot_token)
    except ImportError:
        pass  # Monitoring not available

    try:
        result = await coro
        # Successful call - help with rate recovery
        rate_limiter.handle_successful_call(bot_token)
        return result

    except RetryAfter as e:
        # Handle Telegram's built-in RetryAfter exception
        logger.warning(f"Bot {bot_token[:10]}: RetryAfter exception, retry_after={e.retry_after}")
        rate_limiter._adjust_rate_after_429(bot_token, e.retry_after)

        # Log the 429 error for monitoring
        try:
            from .test_monitor import log_api_call
            await log_api_call(f"{method_name}_429_retry", bot_token, error="RetryAfter", retry_after=e.retry_after)
        except ImportError:
            pass

        # Re-raise - caller should handle retry if needed
        # Rate limiter has been adjusted for future calls
        raise

    except TelegramError as e:
        # Check if this is a 429 error (rate limit)
        if "429" in str(e) or "Too Many Requests" in str(e):
            logger.warning(f"Bot {bot_token[:10]}: 429 error detected: {e}")

            # Try to extract retry_after from error message
            retry_after = None
            if "retry after" in str(e).lower():
                import re
                match = re.search(r'retry after (\d+)', str(e), re.IGNORECASE)
                if match:
                    retry_after = int(match.group(1))

            rate_limiter._adjust_rate_after_429(bot_token, retry_after)

            # Log the 429 error for monitoring
            try:
                from .test_monitor import log_api_call
                await log_api_call(f"{method_name}_429_error", bot_token, error=str(e), retry_after=retry_after)
            except ImportError:
                pass

            # Re-raise - caller should handle retry if needed
            # Rate limiter has been adjusted for future calls
            raise
        else:
            # Re-raise non-429 TelegramErrors
            raise


def get_rate_limiter_status() -> dict[str, Any]:
    """Get current rate limiter status for all bots"""
    status = {}
    for bot_token in rate_limiter.buckets.keys():
        token_key = f"bot_{bot_token[:10]}"
        status[token_key] = rate_limiter.get_rate_info(bot_token)
    return status

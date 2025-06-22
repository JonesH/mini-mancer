#!/usr/bin/env python3
"""
Demo script showing adaptive rate limiter functionality
"""

import asyncio
import time
from telegram.error import TelegramError, RetryAfter

from src.telegram_rate_limiter import rate_limited_call, get_rate_limiter_status, rate_limiter


async def simulate_telegram_api_call(call_id: int, fail_with_429: bool = False):
    """Simulate a Telegram API call that might fail with 429"""
    if fail_with_429:
        if call_id % 2 == 0:
            raise RetryAfter(retry_after=1)
        else:
            raise TelegramError("429 Too Many Requests: retry after 2")
    return f"Success call {call_id}"


async def demo_adaptive_rate_limiter():
    """Demonstrate adaptive rate limiter behavior"""
    print("🚀 Adaptive Rate Limiter Demo")
    print("=" * 50)
    
    bot_token = "demo_bot_token_12345"
    
    print(f"Initial rate limiter status:")
    status = get_rate_limiter_status()
    print(f"Status: {status}")
    print()
    
    # Make some successful calls
    print("Making 3 successful calls...")
    for i in range(3):
        try:
            result = await rate_limited_call(bot_token, simulate_telegram_api_call(i))
            print(f"  ✅ Call {i}: {result}")
        except Exception as e:
            print(f"  ❌ Call {i}: {e}")
        await asyncio.sleep(0.1)
    
    print(f"\\nRate limiter status after successful calls:")
    status = get_rate_limiter_status()
    print(f"Status: {status}")
    print()
    
    # Simulate 429 errors to trigger adaptive behavior
    print("Simulating 429 errors to trigger adaptive behavior...")
    for i in range(3, 6):
        try:
            result = await rate_limited_call(bot_token, simulate_telegram_api_call(i, fail_with_429=True))
            print(f"  ✅ Call {i}: {result}")
        except RetryAfter as e:
            print(f"  ⏱️  Call {i}: RetryAfter({e.retry_after}s) - Rate limiter adapted")
        except TelegramError as e:
            print(f"  🔄 Call {i}: 429 Error - Rate limiter adapted")
        except Exception as e:
            print(f"  ❌ Call {i}: {e}")
        await asyncio.sleep(0.1)
    
    print(f"\\nRate limiter status after 429 errors:")
    status = get_rate_limiter_status()
    print(f"Status: {status}")
    
    # Show detailed info
    info = rate_limiter.get_rate_info(bot_token)
    print(f"\\nDetailed rate info for {bot_token[:15]}:")
    print(f"  Base rate: {info['base_rate']}/sec")
    print(f"  Current rate: {info['current_rate']}/sec")
    print(f"  Consecutive 429s: {info['consecutive_429s']}")
    print(f"  In backoff: {info['in_backoff']}")
    print(f"  Backoff remaining: {info['backoff_remaining']:.2f}s")
    print(f"  Recovery active: {info['recovery_active']}")
    
    print("\\n🎯 Demo complete! The rate limiter has:")
    print("  - Detected 429 errors automatically")
    print("  - Reduced rate limits exponentially")
    print("  - Set appropriate backoff periods")
    print("  - Is ready to gradually recover rates on success")


if __name__ == "__main__":
    asyncio.run(demo_adaptive_rate_limiter())
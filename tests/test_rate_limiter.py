"""
Comprehensive Rate Limiter Testing
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from telegram.error import TelegramError, RetryAfter

from src.telegram_rate_limiter import AdaptiveRateLimiter, rate_limited_call, get_rate_limiter_status, rate_limiter


class TestAdaptiveRateLimiter:
    """Test adaptive rate limiter functionality"""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initializes with correct defaults"""
        limiter = AdaptiveRateLimiter()
        assert limiter.base_rate == 20
        assert limiter.min_rate == 1
        assert limiter.max_rate == 30
        assert len(limiter.buckets) == 0
        
    def test_rate_limiter_custom_params(self):
        """Test rate limiter with custom parameters"""
        limiter = AdaptiveRateLimiter(base_rate_per_second=10, min_rate=2, max_rate=50)
        assert limiter.base_rate == 10
        assert limiter.min_rate == 2
        assert limiter.max_rate == 50
    
    @pytest.mark.asyncio
    async def test_basic_rate_limiting(self):
        """Test basic rate limiting without 429 errors"""
        limiter = AdaptiveRateLimiter(base_rate_per_second=2)  # 2 req/sec for testing
        bot_token = "test_token_123"
        
        # First call should be immediate
        start_time = time.time()
        await limiter.wait_if_needed(bot_token)
        first_call_time = time.time() - start_time
        assert first_call_time < 0.1  # Should be very fast
        
        # Exhaust tokens to test rate limiting
        await limiter.wait_if_needed(bot_token)  # Second call, should still be fast
        
        # Third call should be rate limited
        start_time = time.time()
        await limiter.wait_if_needed(bot_token)  
        wait_time = time.time() - start_time
        
        # Should wait approximately 0.5 seconds (1/2 req/sec)
        assert wait_time >= 0.4  # Allow some tolerance
    
    def test_429_error_rate_adjustment(self):
        """Test rate adjustment after 429 errors"""
        limiter = AdaptiveRateLimiter(base_rate_per_second=20)
        bot_token = "test_token_429"
        
        # Initial rate should be base rate
        info = limiter.get_rate_info(bot_token)
        assert info['current_rate'] == 20
        assert info['consecutive_429s'] == 0
        
        # Simulate 429 error
        limiter._adjust_rate_after_429(bot_token)
        info = limiter.get_rate_info(bot_token)
        assert info['current_rate'] < 20  # Rate should be reduced
        assert info['consecutive_429s'] == 1
        assert info['in_backoff'] is True
        
        # Second 429 should reduce rate further
        limiter._adjust_rate_after_429(bot_token)
        info = limiter.get_rate_info(bot_token)
        assert info['consecutive_429s'] == 2
        assert info['current_rate'] < 10  # Even more reduced
    
    def test_429_error_with_retry_after(self):
        """Test 429 error handling with Retry-After header"""
        limiter = AdaptiveRateLimiter()
        bot_token = "test_token_retry"
        
        # Simulate 429 with retry_after
        limiter._adjust_rate_after_429(bot_token, retry_after=30)
        info = limiter.get_rate_info(bot_token)
        
        assert info['in_backoff'] is True
        assert info['backoff_remaining'] > 25  # Should be close to 30 seconds
        assert info['consecutive_429s'] == 1
    
    def test_rate_recovery(self):
        """Test gradual rate recovery after 429 errors"""
        limiter = AdaptiveRateLimiter()
        bot_token = "test_token_recovery"
        
        # Cause 429 error to reduce rate
        limiter._adjust_rate_after_429(bot_token)
        reduced_rate = limiter.get_rate_info(bot_token)['current_rate']
        
        # Signal successful call to start recovery
        limiter.handle_successful_call(bot_token)
        
        # Simulate time passage for recovery
        bucket = limiter.buckets[bot_token]
        bucket['recovery_start'] = time.time() - 31  # 31 seconds ago
        
        # Try recovery
        limiter._maybe_recover_rate(bot_token)
        recovered_rate = limiter.get_rate_info(bot_token)['current_rate']
        
        assert recovered_rate > reduced_rate  # Should have increased
    
    @pytest.mark.asyncio
    async def test_backoff_period_blocking(self):
        """Test that backoff period blocks calls"""
        limiter = AdaptiveRateLimiter()
        bot_token = "test_token_backoff"
        
        # Set backoff period
        limiter._adjust_rate_after_429(bot_token, retry_after=1)
        
        # Call during backoff should wait
        start_time = time.time()
        await limiter.wait_if_needed(bot_token)
        wait_time = time.time() - start_time
        
        assert wait_time >= 0.9  # Should wait close to 1 second
    
    def test_multiple_bots_isolation(self):
        """Test that rate limiting is isolated per bot"""
        limiter = AdaptiveRateLimiter()
        bot1 = "bot_token_1"
        bot2 = "bot_token_2"
        
        # Cause 429 for bot1 only
        limiter._adjust_rate_after_429(bot1)
        
        info1 = limiter.get_rate_info(bot1)
        info2 = limiter.get_rate_info(bot2)
        
        assert info1['current_rate'] < 20  # Bot1 rate reduced
        assert info2['current_rate'] == 20  # Bot2 rate unchanged
        assert info1['consecutive_429s'] == 1
        assert info2['consecutive_429s'] == 0


class TestRateLimitedCall:
    """Test the rate_limited_call function"""
    
    @pytest.mark.asyncio
    async def test_successful_call(self):
        """Test successful API call"""
        bot_token = "test_success_token"
        
        # Mock coroutine that succeeds
        mock_coro = AsyncMock(return_value="success")
        
        result = await rate_limited_call(bot_token, mock_coro())
        assert result == "success"
        mock_coro.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retry_after_exception(self):
        """Test handling of RetryAfter exception - should adjust rate limiter and re-raise"""
        bot_token = "test_retry_token"
        
        async def mock_coro():
            raise RetryAfter(retry_after=0.1)
        
        # Should raise RetryAfter but adjust rate limiter
        with pytest.raises(RetryAfter) as exc_info:
            await rate_limited_call(bot_token, mock_coro())
            
        assert exc_info.value.retry_after == 0.1
        
        # Rate limiter should have been adjusted
        info = rate_limiter.get_rate_info(bot_token)
        assert info['consecutive_429s'] == 1
        assert info['current_rate'] < 20  # Rate should be reduced
    
    @pytest.mark.asyncio
    async def test_telegram_429_error(self):
        """Test handling of general TelegramError with 429 - should adjust rate limiter and re-raise"""
        bot_token = "test_429_token"
        
        async def mock_coro():
            raise TelegramError("429 Too Many Requests: retry after 5")
        
        # Should raise TelegramError but adjust rate limiter
        with pytest.raises(TelegramError) as exc_info:
            await rate_limited_call(bot_token, mock_coro())
            
        assert "429 Too Many Requests" in str(exc_info.value)
        
        # Rate limiter should have been adjusted
        info = rate_limiter.get_rate_info(bot_token)
        assert info['consecutive_429s'] == 1
        assert info['current_rate'] < 20  # Rate should be reduced
    
    @pytest.mark.asyncio
    async def test_non_429_telegram_error(self):
        """Test that non-429 TelegramErrors are re-raised"""
        bot_token = "test_other_error_token"
        
        # Create coroutine that raises non-429 error
        async def mock_coro():
            raise TelegramError("Message not found")
        
        with pytest.raises(TelegramError) as exc_info:
            await rate_limited_call(bot_token, mock_coro())
            
        assert "Message not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_monitoring_integration(self):
        """Test that monitoring calls work when available"""
        bot_token = "test_monitor_token"
        
        async def mock_coro():
            return "success"
        mock_coro.__name__ = "test_method"
        
        # Mock the test_monitor module import
        with patch('src.test_monitor.log_api_call', new_callable=AsyncMock) as mock_log:
            result = await rate_limited_call(bot_token, mock_coro())
            
        assert result == "success"
        # Monitoring should be called if available
        assert mock_log.called


class TestRateLimiterStatus:
    """Test rate limiter status reporting"""
    
    def test_empty_status(self):
        """Test status when no bots have been used"""
        # Reset global rate limiter
        from src.telegram_rate_limiter import rate_limiter
        rate_limiter.buckets.clear()
        
        status = get_rate_limiter_status()
        assert status == {}
    
    def test_status_with_bots(self):
        """Test status reporting with active bots"""
        from src.telegram_rate_limiter import rate_limiter
        
        bot_tokens = ["bot_123", "bot_456"]
        
        # Trigger bucket creation
        for token in bot_tokens:
            rate_limiter.get_rate_info(token)
        
        status = get_rate_limiter_status()
        
        assert len(status) == 2
        assert "bot_bot_123" in status
        assert "bot_bot_456" in status
        
        # Check status structure
        for bot_status in status.values():
            assert 'base_rate' in bot_status
            assert 'current_rate' in bot_status
            assert 'consecutive_429s' in bot_status
            assert 'in_backoff' in bot_status


@pytest.mark.asyncio
async def test_integration_stress_test():
    """Integration test with multiple concurrent calls"""
    limiter = AdaptiveRateLimiter(base_rate_per_second=10)
    bot_token = "stress_test_token"
    
    async def mock_api_call(call_id: int):
        """Mock API call that occasionally fails with 429"""
        await limiter.wait_if_needed(bot_token)
        # Simulate some 429 errors
        if call_id % 7 == 0:  # Every 7th call fails
            limiter._adjust_rate_after_429(bot_token)
            raise TelegramError("429 Too Many Requests")
        return f"success_{call_id}"
    
    # Run many concurrent calls
    tasks = [mock_api_call(i) for i in range(20)]
    results = []
    errors = []
    
    for task in tasks:
        try:
            result = await task
            results.append(result)
        except TelegramError as e:
            errors.append(e)
    
    # Should have some successes and some 429 errors
    assert len(results) > 0
    assert len(errors) > 0
    
    # Rate should be adjusted down
    info = limiter.get_rate_info(bot_token)
    assert info['current_rate'] < 10  # Should be reduced from initial rate


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
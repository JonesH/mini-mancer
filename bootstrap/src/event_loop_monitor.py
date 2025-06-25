"""
Event Loop Health Monitor - Emergency Observability for Mini-Mancer

Provides real-time monitoring of all event loops, database connections,
and async task health to expose hidden problems.
"""

import asyncio
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional
import psutil
import weakref

logger = logging.getLogger(__name__)


@dataclass
class EventLoopHealth:
    """Health metrics for a single event loop"""
    loop_id: str
    thread_id: int
    is_running: bool
    is_blocked: bool
    last_heartbeat: float
    blocked_duration: float = 0.0
    total_tasks: int = 0
    pending_tasks: int = 0
    failed_tasks: int = 0
    avg_task_duration: float = 0.0
    recent_exceptions: List[str] = field(default_factory=list)


@dataclass
class DatabaseConnectionHealth:
    """Health metrics for database connections"""
    active_connections: int
    max_connections: int
    connection_pool_size: int
    waiting_for_connection: int
    failed_connections: int
    avg_query_time: float
    slow_queries: List[str] = field(default_factory=list)


@dataclass
class AgnoCallMetrics:
    """Performance metrics for Agno agent calls"""
    total_calls: int = 0
    avg_duration: float = 0.0
    max_duration: float = 0.0
    blocking_calls: int = 0
    failed_calls: int = 0
    recent_call_times: deque = field(default_factory=lambda: deque(maxlen=100))


class EventLoopMonitor:
    """Comprehensive event loop and system health monitor"""
    
    def __init__(self):
        self.event_loops: Dict[str, EventLoopHealth] = {}
        self.db_health = DatabaseConnectionHealth(0, 0, 0, 0, 0, 0.0)
        self.agno_metrics = AgnoCallMetrics()
        self.monitoring_active = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        
        # Critical thresholds
        self.BLOCKED_THRESHOLD = 5.0  # seconds
        self.SLOW_QUERY_THRESHOLD = 2.0  # seconds  
        self.HIGH_TASK_COUNT_THRESHOLD = 100
        
        # Weak references to tracked tasks to avoid memory leaks
        self.tracked_tasks: weakref.WeakSet = weakref.WeakSet()
        
    async def start_monitoring(self, loop_id: str = None):
        """Start comprehensive monitoring of current event loop"""
        current_loop = asyncio.get_running_loop()
        
        if not loop_id:
            loop_id = f"loop_{id(current_loop)}_{threading.get_ident()}"
            
        # Initialize health tracking for this loop
        self.event_loops[loop_id] = EventLoopHealth(
            loop_id=loop_id,
            thread_id=threading.get_ident(),
            is_running=True,
            is_blocked=False,
            last_heartbeat=time.time()
        )
        
        # Start heartbeat monitoring
        self.heartbeat_tasks[loop_id] = asyncio.create_task(
            self._heartbeat_monitor(loop_id)
        )
        
        # Start main monitoring task if not already running
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            
        logger.info(f"🔍 Event loop monitoring started for {loop_id}")
        
    async def stop_monitoring(self):
        """Stop all monitoring"""
        self.monitoring_active = False
        
        # Cancel all heartbeat tasks
        for task in self.heartbeat_tasks.values():
            if not task.done():
                task.cancel()
                
        # Cancel main monitor task
        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()
            
        logger.info("🛑 Event loop monitoring stopped")
        
    async def _heartbeat_monitor(self, loop_id: str):
        """Monitor heartbeat for a specific event loop"""
        while self.monitoring_active:
            try:
                start_time = time.time()
                
                # This should execute quickly if event loop is healthy
                await asyncio.sleep(0.1)
                
                duration = time.time() - start_time
                health = self.event_loops[loop_id]
                
                # Update heartbeat
                health.last_heartbeat = time.time()
                
                # Check if loop appears blocked
                if duration > 1.0:  # Sleep took longer than expected
                    health.is_blocked = True
                    health.blocked_duration += duration
                    logger.warning(f"⚠️ Event loop {loop_id} appears blocked for {duration:.2f}s")
                else:
                    health.is_blocked = False
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Heartbeat monitor error for {loop_id}: {e}")
                self.event_loops[loop_id].recent_exceptions.append(str(e))
                
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                await self._collect_metrics()
                await self._check_critical_conditions()
                await asyncio.sleep(5)  # Monitor every 5 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Monitor loop error: {e}")
                
    async def _collect_metrics(self):
        """Collect comprehensive system metrics"""
        current_loop = asyncio.get_running_loop()
        
        # Get all tasks in current loop
        all_tasks = asyncio.all_tasks(current_loop)
        pending_tasks = [t for t in all_tasks if not t.done()]
        failed_tasks = [t for t in all_tasks if t.done() and t.exception()]
        
        # Update metrics for current loop
        current_loop_id = f"loop_{id(current_loop)}_{threading.get_ident()}"
        if current_loop_id in self.event_loops:
            health = self.event_loops[current_loop_id]
            health.total_tasks = len(all_tasks)
            health.pending_tasks = len(pending_tasks)
            health.failed_tasks = len(failed_tasks)
            
            # Log failed task exceptions
            for task in failed_tasks:
                if task.exception():
                    exc_str = str(task.exception())
                    if exc_str not in health.recent_exceptions:
                        health.recent_exceptions.append(exc_str)
                        logger.error(f"❌ Task failed in {current_loop_id}: {exc_str}")
                        
        # Memory usage monitoring
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        if memory_mb > 500:  # Over 500MB
            logger.warning(f"🧠 High memory usage: {memory_mb:.1f}MB")
            
    async def _check_critical_conditions(self):
        """Check for critical conditions that need immediate attention"""
        for loop_id, health in self.event_loops.items():
            # Check for blocked event loops
            if health.is_blocked and health.blocked_duration > self.BLOCKED_THRESHOLD:
                logger.critical(
                    f"🚨 CRITICAL: Event loop {loop_id} blocked for {health.blocked_duration:.1f}s"
                )
                
            # Check for high task count
            if health.pending_tasks > self.HIGH_TASK_COUNT_THRESHOLD:
                logger.critical(
                    f"🚨 CRITICAL: Event loop {loop_id} has {health.pending_tasks} pending tasks"
                )
                
            # Check for many failed tasks
            if health.failed_tasks > 10:
                logger.critical(
                    f"🚨 CRITICAL: Event loop {loop_id} has {health.failed_tasks} failed tasks"
                )
                
    def track_agno_call(self, func: Callable) -> Callable:
        """Decorator to track Agno agent call performance"""
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            current_loop = None
            
            # Check if we're in an event loop
            try:
                current_loop = asyncio.get_running_loop()
                logger.warning("⚠️ SYNCHRONOUS Agno call detected in event loop - this may block!")
            except RuntimeError:
                pass  # Not in event loop, this is fine
                
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Update metrics
                self.agno_metrics.total_calls += 1
                self.agno_metrics.recent_call_times.append(duration)
                
                # Calculate averages
                if self.agno_metrics.recent_call_times:
                    self.agno_metrics.avg_duration = sum(self.agno_metrics.recent_call_times) / len(self.agno_metrics.recent_call_times)
                    self.agno_metrics.max_duration = max(self.agno_metrics.max_duration, duration)
                
                # Check for blocking behavior
                if current_loop and duration > 0.1:  # Over 100ms in event loop
                    self.agno_metrics.blocking_calls += 1
                    logger.warning(
                        f"🐌 BLOCKING Agno call took {duration:.3f}s in event loop"
                    )
                    
                return result
                
            except Exception as e:
                self.agno_metrics.failed_calls += 1
                logger.error(f"❌ Agno call failed: {e}")
                raise
                
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                    
                duration = time.time() - start_time
                
                # Update metrics (same as sync version)
                self.agno_metrics.total_calls += 1
                self.agno_metrics.recent_call_times.append(duration)
                
                if self.agno_metrics.recent_call_times:
                    self.agno_metrics.avg_duration = sum(self.agno_metrics.recent_call_times) / len(self.agno_metrics.recent_call_times)
                    self.agno_metrics.max_duration = max(self.agno_metrics.max_duration, duration)
                
                if duration > 2.0:  # Over 2 seconds
                    logger.warning(f"🐌 Slow Agno call took {duration:.3f}s")
                    
                return result
                
            except Exception as e:
                self.agno_metrics.failed_calls += 1
                logger.error(f"❌ Async Agno call failed: {e}")
                raise
                
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        return {
            "event_loops": {
                loop_id: {
                    "thread_id": health.thread_id,
                    "is_running": health.is_running,
                    "is_blocked": health.is_blocked,
                    "blocked_duration": health.blocked_duration,
                    "total_tasks": health.total_tasks,
                    "pending_tasks": health.pending_tasks,
                    "failed_tasks": health.failed_tasks,
                    "recent_exceptions": health.recent_exceptions[-5:],  # Last 5 exceptions
                    "last_heartbeat_age": time.time() - health.last_heartbeat
                }
                for loop_id, health in self.event_loops.items()
            },
            "database": {
                "active_connections": self.db_health.active_connections,
                "max_connections": self.db_health.max_connections,
                "waiting_for_connection": self.db_health.waiting_for_connection,
                "failed_connections": self.db_health.failed_connections,
                "avg_query_time": self.db_health.avg_query_time,
                "slow_queries": self.db_health.slow_queries[-10:]  # Last 10 slow queries
            },
            "agno_metrics": {
                "total_calls": self.agno_metrics.total_calls,
                "avg_duration": self.agno_metrics.avg_duration,
                "max_duration": self.agno_metrics.max_duration,
                "blocking_calls": self.agno_metrics.blocking_calls,
                "failed_calls": self.agno_metrics.failed_calls,
                "recent_performance": list(self.agno_metrics.recent_call_times)[-20:]  # Last 20 calls
            },
            "system": {
                "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                "cpu_percent": psutil.Process().cpu_percent(),
                "open_files": len(psutil.Process().open_files())
            }
        }


# Global monitor instance
global_monitor = EventLoopMonitor()


def track_agno_call(func: Callable) -> Callable:
    """Convenience decorator for tracking Agno calls"""
    return global_monitor.track_agno_call(func)


async def start_monitoring(loop_id: str = None):
    """Start monitoring for current event loop"""
    await global_monitor.start_monitoring(loop_id)


async def stop_monitoring():
    """Stop all monitoring"""
    await global_monitor.stop_monitoring()


def get_health_report() -> Dict[str, Any]:
    """Get current health report"""
    return global_monitor.get_health_report()


# Database connection monitoring utilities
class DatabaseMonitor:
    """Monitor database connection health"""
    
    def __init__(self):
        self.connection_count = 0
        self.failed_connections = 0
        self.query_times: deque = deque(maxlen=100)
        
    def track_connection(self, func: Callable) -> Callable:
        """Decorator to track database connections"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            self.connection_count += 1
            
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                duration = time.time() - start_time
                self.query_times.append(duration)
                
                # Update global monitor
                if hasattr(global_monitor, 'db_health'):
                    global_monitor.db_health.active_connections = self.connection_count
                    global_monitor.db_health.avg_query_time = sum(self.query_times) / len(self.query_times) if self.query_times else 0.0
                    
                    if duration > 2.0:  # Slow query
                        query_info = f"Query took {duration:.3f}s"
                        global_monitor.db_health.slow_queries.append(query_info)
                        logger.warning(f"🐌 {query_info}")
                
                return result
                
            except Exception as e:
                self.failed_connections += 1
                global_monitor.db_health.failed_connections = self.failed_connections
                logger.error(f"❌ Database operation failed: {e}")
                raise
            finally:
                self.connection_count -= 1
                
        return wrapper


# Global database monitor
db_monitor = DatabaseMonitor()


def track_database_call(func: Callable) -> Callable:
    """Convenience decorator for tracking database calls"""
    return db_monitor.track_connection(func)
#!/usr/bin/env python3
"""
Health Check Script - Monitor All Event Loops
  
Tests event loop health across both main project and bootstrap MVP.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

import httpx
import psutil

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "bootstrap" / "src"))

try:
    from event_loop_monitor import get_health_report
except ImportError:
    print("❌ Event loop monitor not available - monitoring disabled")
    get_health_report = lambda: {"error": "monitoring_unavailable"}


async def check_main_project_health():
    """Check health of main project via FastAPI endpoint"""
    print("🔍 Checking main project health...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:14159/health", timeout=10.0)
            
            if response.status_code == 200:
                health_data = response.json()
                
                print(f"✅ Main project status: {health_data.get('status', 'unknown')}")
                
                # Check for issues
                issues = health_data.get('issues', [])
                if issues:
                    print("⚠️  Issues detected:")
                    for issue in issues:
                        print(f"   - {issue}")
                
                # Show monitoring summary
                monitoring = health_data.get('monitoring', {})
                print(f"📊 Event loops: {monitoring.get('event_loops_count', 0)}")
                print(f"📊 Total tasks: {monitoring.get('total_tasks', 0)}")
                print(f"📊 Pending tasks: {monitoring.get('pending_tasks', 0)}")
                print(f"📊 Failed tasks: {monitoring.get('failed_tasks', 0)}")
                print(f"📊 Agno calls: {monitoring.get('agno_total_calls', 0)}")
                print(f"📊 Agno blocking calls: {monitoring.get('agno_blocking_calls', 0)}")
                print(f"📊 Memory: {monitoring.get('memory_mb', 0):.1f}MB")
                
                return health_data
            else:
                print(f"❌ Main project health check failed: {response.status_code}")
                return None
                
    except httpx.ConnectError:
        print("❌ Main project not reachable (not running?)")
        return None
    except Exception as e:
        print(f"❌ Main project health check error: {e}")
        return None


async def check_bootstrap_health():
    """Check health of bootstrap project via FastAPI endpoint"""
    print("\n🔍 Checking bootstrap project health...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Bootstrap might be running on different port, try both
            for port in [8080, 14159, 8000]:
                try:
                    # Since bootstrap uses Agno Playground, try the default health endpoint
                    response = await client.get(f"http://localhost:{port}/health", timeout=5.0)
                    
                    if response.status_code == 200:
                        print(f"✅ Bootstrap project running on port {port}")
                        return response.json()
                        
                except httpx.ConnectError:
                    continue
                    
        print("❌ Bootstrap project not reachable (not running?)")
        return None
        
    except Exception as e:
        print(f"❌ Bootstrap health check error: {e}")
        return None


def check_system_health():
    """Check overall system health"""
    print("\n🔍 Checking system health...")
    
    process = psutil.Process()
    
    # Memory usage
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"📊 Memory usage: {memory_mb:.1f}MB")
    
    if memory_mb > 1000:
        print("⚠️  High memory usage detected")
    
    # CPU usage
    cpu_percent = process.cpu_percent(interval=1)
    print(f"📊 CPU usage: {cpu_percent:.1f}%")
    
    if cpu_percent > 80:
        print("⚠️  High CPU usage detected")
    
    # Open files
    try:
        open_files = len(process.open_files())
        print(f"📊 Open files: {open_files}")
        
        if open_files > 100:
            print("⚠️  High file descriptor usage")
    except Exception:
        print("📊 Open files: Unable to check")
    
    # Check for PostgreSQL processes
    postgres_procs = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'postgres' in proc.info['name'].lower():
                postgres_procs.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if postgres_procs:
        print(f"📊 PostgreSQL processes: {len(postgres_procs)}")
    else:
        print("⚠️  No PostgreSQL processes found")
    
    return {
        "memory_mb": memory_mb,
        "cpu_percent": cpu_percent,
        "open_files": open_files if 'open_files' in locals() else 0,
        "postgres_processes": len(postgres_procs)
    }


async def run_comprehensive_health_check():
    """Run comprehensive health check across all systems"""
    print("🏥 Mini-Mancer Comprehensive Health Check")
    print("=" * 50)
    
    start_time = time.time()
    
    # Check main project
    main_health = await check_main_project_health()
    
    # Check bootstrap project  
    bootstrap_health = await check_bootstrap_health()
    
    # Check system health
    system_health = check_system_health()
    
    # Get local event loop health if monitoring is available
    print("\n🔍 Checking local event loop health...")
    local_health = get_health_report()
    
    if local_health.get("error"):
        print("⚠️  Local monitoring not available")
    else:
        event_loops = local_health.get("event_loops", {})
        print(f"📊 Local event loops tracked: {len(event_loops)}")
        
        for loop_id, loop_health in event_loops.items():
            status = "🟢" if not loop_health.get("is_blocked") else "🔴"
            print(f"   {status} {loop_id}: {loop_health.get('total_tasks', 0)} tasks")
    
    # Summary
    print("\n📋 HEALTH CHECK SUMMARY")
    print("-" * 30)
    
    duration = time.time() - start_time
    print(f"⏱️  Check duration: {duration:.2f}s")
    
    # Determine overall status
    issues = []
    
    if main_health is None:
        issues.append("Main project not responding")
    elif main_health.get("status") != "healthy":
        issues.append(f"Main project status: {main_health.get('status')}")
    
    if bootstrap_health is None:
        issues.append("Bootstrap project not responding")
    
    if system_health["memory_mb"] > 1000:
        issues.append(f"High memory usage: {system_health['memory_mb']:.1f}MB")
    
    if system_health["cpu_percent"] > 80:
        issues.append(f"High CPU usage: {system_health['cpu_percent']:.1f}%")
    
    # Check for blocked event loops
    if not local_health.get("error"):
        for loop_id, loop_health in local_health.get("event_loops", {}).items():
            if loop_health.get("is_blocked"):
                issues.append(f"Event loop {loop_id} is blocked")
    
    if not issues:
        print("✅ ALL SYSTEMS HEALTHY")
        return True
    else:
        print("⚠️  ISSUES DETECTED:")
        for issue in issues:
            print(f"   - {issue}")
        return False


async def monitor_continuously(interval: int = 30):
    """Run continuous monitoring"""
    print(f"🔄 Starting continuous monitoring (every {interval}s)")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            print(f"\n{'='*60}")
            print(f"Health Check - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print('='*60)
            
            await run_comprehensive_health_check()
            
            print(f"\n💤 Sleeping for {interval}s...")
            await asyncio.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Mini-Mancer Health Check")
    parser.add_argument("--continuous", "-c", action="store_true", 
                       help="Run continuous monitoring")
    parser.add_argument("--interval", "-i", type=int, default=30,
                       help="Monitoring interval in seconds (default: 30)")
    parser.add_argument("--json", "-j", action="store_true",
                       help="Output in JSON format")
    
    args = parser.parse_args()
    
    if args.continuous:
        await monitor_continuously(args.interval)
    else:
        healthy = await run_comprehensive_health_check()
        
        if args.json:
            # Output summary in JSON format
            result = {
                "healthy": healthy,
                "timestamp": time.time(),
                "main_project_responsive": await check_main_project_health() is not None,
                "bootstrap_responsive": await check_bootstrap_health() is not None,
                "system_health": check_system_health(),
                "local_monitoring": get_health_report()
            }
            print(json.dumps(result, indent=2))
        
        # Exit with appropriate code
        sys.exit(0 if healthy else 1)


if __name__ == "__main__":
    asyncio.run(main())
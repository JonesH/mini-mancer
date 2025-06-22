"""
Real-time Test Monitoring Dashboard
WebSocket-based live monitoring of bot interactions during testing
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class TestEvent:
    """Represents a test event for monitoring"""
    timestamp: float
    event_type: str  # 'api_call', 'bot_message', 'ai_response', 'error', 'test_start', 'test_end'
    bot_token: Optional[str]
    user_id: Optional[str]
    chat_id: Optional[str]
    content: str
    metadata: Dict[str, Any]
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat(),
            'event_type': self.event_type,
            'bot_token': self.bot_token[:10] + '...' if self.bot_token else None,
            'user_id': self.user_id,
            'chat_id': self.chat_id,
            'content': self.content,
            'metadata': self.metadata
        }


class TestMonitor:
    """Real-time test monitoring system"""
    
    def __init__(self, max_events: int = 1000):
        self.events: deque = deque(maxlen=max_events)
        self.active_connections: List[WebSocket] = []
        self.is_monitoring = False
        
    async def log_event(self, 
                       event_type: str,
                       content: str,
                       bot_token: Optional[str] = None,
                       user_id: Optional[str] = None,
                       chat_id: Optional[str] = None,
                       **metadata):
        """Log a test event and broadcast to connected clients"""
        event = TestEvent(
            timestamp=time.time(),
            event_type=event_type,
            bot_token=bot_token,
            user_id=user_id,
            chat_id=chat_id,
            content=content,
            metadata=metadata
        )
        
        self.events.append(event)
        
        # Broadcast to all connected WebSocket clients
        if self.active_connections:
            await self._broadcast_event(event)
    
    async def _broadcast_event(self, event: TestEvent):
        """Broadcast event to all connected WebSocket clients"""
        message = json.dumps(event.to_dict())
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.active_connections.remove(conn)
    
    async def connect_websocket(self, websocket: WebSocket):
        """Add new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Send recent events to new connection
        recent_events = list(self.events)[-50:]  # Last 50 events
        for event in recent_events:
            try:
                await websocket.send_text(json.dumps(event.to_dict()))
            except Exception as e:
                logger.warning(f"Failed to send recent events: {e}")
                break
    
    def disconnect_websocket(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    def get_events(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict]:
        """Get recent events, optionally filtered by type"""
        events = list(self.events)
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return [e.to_dict() for e in events[-limit:]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        events = list(self.events)
        
        event_counts = {}
        for event in events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        return {
            'total_events': len(events),
            'active_connections': len(self.active_connections),
            'event_types': event_counts,
            'monitoring_active': self.is_monitoring,
            'oldest_event': events[0].timestamp if events else None,
            'newest_event': events[-1].timestamp if events else None
        }


# Global monitor instance
monitor = TestMonitor()


def get_dashboard_html() -> str:
    """Get the HTML dashboard for monitoring"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Mini-Mancer Test Monitor</title>
    <style>
        body { font-family: monospace; background: #1a1a1a; color: #00ff00; margin: 0; padding: 20px; }
        .header { border-bottom: 2px solid #00ff00; padding-bottom: 10px; margin-bottom: 20px; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat-box { border: 1px solid #00ff00; padding: 10px; border-radius: 5px; }
        .events { max-height: 70vh; overflow-y: auto; border: 1px solid #00ff00; padding: 10px; }
        .event { margin: 5px 0; padding: 8px; border-left: 3px solid; }
        .event.api_call { border-left-color: #00aaff; background: rgba(0, 170, 255, 0.1); }
        .event.bot_message { border-left-color: #ff6600; background: rgba(255, 102, 0, 0.1); }
        .event.ai_response { border-left-color: #00ff00; background: rgba(0, 255, 0, 0.1); }
        .event.error { border-left-color: #ff0000; background: rgba(255, 0, 0, 0.1); }
        .event.test_start { border-left-color: #ffff00; background: rgba(255, 255, 0, 0.1); }
        .event.test_end { border-left-color: #ff00ff; background: rgba(255, 0, 255, 0.1); }
        .timestamp { color: #888; font-size: 0.9em; }
        .content { margin: 5px 0; }
        .metadata { color: #ccc; font-size: 0.8em; }
        .connection-status { float: right; padding: 5px 10px; border-radius: 3px; }
        .connected { background: #00aa00; color: white; }
        .disconnected { background: #aa0000; color: white; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 Mini-Mancer Test Monitor 
            <span id="status" class="connection-status disconnected">Disconnected</span>
        </h1>
        <p>Real-time monitoring of bot interactions and test events</p>
    </div>
    
    <div class="stats">
        <div class="stat-box">
            <strong>Total Events:</strong> <span id="total-events">0</span>
        </div>
        <div class="stat-box">
            <strong>Active Connections:</strong> <span id="connections">0</span>
        </div>
        <div class="stat-box">
            <strong>Last Event:</strong> <span id="last-event">None</span>
        </div>
    </div>
    
    <div class="events" id="events"></div>

    <script>
        const ws = new WebSocket('ws://localhost:14159/test-monitor/ws');
        const status = document.getElementById('status');
        const events = document.getElementById('events');
        const totalEvents = document.getElementById('total-events');
        const connections = document.getElementById('connections');
        const lastEvent = document.getElementById('last-event');
        
        let eventCount = 0;
        
        ws.onopen = function() {
            status.textContent = 'Connected';
            status.className = 'connection-status connected';
        };
        
        ws.onclose = function() {
            status.textContent = 'Disconnected';
            status.className = 'connection-status disconnected';
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            addEvent(data);
            updateStats();
        };
        
        function addEvent(event) {
            const eventDiv = document.createElement('div');
            eventDiv.className = `event ${event.event_type}`;
            
            eventDiv.innerHTML = `
                <div class="timestamp">${event.datetime} | ${event.event_type.toUpperCase()}</div>
                <div class="content">${escapeHtml(event.content)}</div>
                <div class="metadata">
                    Bot: ${event.bot_token || 'N/A'} | 
                    User: ${event.user_id || 'N/A'} | 
                    Chat: ${event.chat_id || 'N/A'}
                    ${Object.keys(event.metadata).length > 0 ? ' | ' + JSON.stringify(event.metadata) : ''}
                </div>
            `;
            
            events.insertBefore(eventDiv, events.firstChild);
            eventCount++;
            
            // Keep only last 100 events visible
            while (events.children.length > 100) {
                events.removeChild(events.lastChild);
            }
        }
        
        function updateStats() {
            totalEvents.textContent = eventCount;
            lastEvent.textContent = new Date().toLocaleTimeString();
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Auto-scroll to top when new events arrive
        events.addEventListener('DOMNodeInserted', function() {
            events.scrollTop = 0;
        });
    </script>
</body>
</html>
    """


# Integration functions for easy use in tests and bot code
async def log_api_call(method_name: str, bot_token: str, **kwargs):
    """Log an API call event"""
    await monitor.log_event(
        'api_call',
        f"Called {method_name}",
        bot_token=bot_token,
        method=method_name,
        **kwargs
    )


async def log_bot_message(content: str, bot_token: str, user_id: str, chat_id: str):
    """Log a bot message event"""
    await monitor.log_event(
        'bot_message',
        content,
        bot_token=bot_token,
        user_id=user_id,
        chat_id=chat_id
    )


async def log_ai_response(prompt: str, response: str, bot_token: str):
    """Log an AI response event"""
    await monitor.log_event(
        'ai_response',
        f"Prompt: {prompt[:100]}... → Response: {response[:100]}...",
        bot_token=bot_token,
        prompt=prompt,
        response=response
    )


async def log_test_start(test_name: str, **metadata):
    """Log test start event"""
    await monitor.log_event(
        'test_start',
        f"Started test: {test_name}",
        test_name=test_name,
        **metadata
    )


async def log_test_end(test_name: str, result: str, **metadata):
    """Log test end event"""
    await monitor.log_event(
        'test_end',
        f"Test {test_name}: {result}",
        test_name=test_name,
        result=result,
        **metadata
    )


async def log_error(error: Exception, context: str, **metadata):
    """Log an error event"""
    await monitor.log_event(
        'error',
        f"Error in {context}: {str(error)}",
        error_type=type(error).__name__,
        context=context,
        **metadata
    )
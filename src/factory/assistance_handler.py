"""
Human Assistance Handler - Manages detection and notification of platform agent assistance requests.

This module handles the critical workflow of detecting when OpenServ platform agents
need human intervention and ensuring immediate notification via Telegram.
"""

import asyncio
import json
from typing import Dict, List, Any
from datetime import datetime

from ..factory.bot_factory_agent import HumanAssistanceRequest, ConversationState


class AssistanceHandler:
    """Handles human assistance requests from platform agents"""
    
    def __init__(self, factory_agent):
        self.factory_agent = factory_agent
        self.pending_requests: Dict[str, List[HumanAssistanceRequest]] = {}
        
    async def handle_assistance_requests(
        self, 
        requests: List[Dict[str, Any]], 
        conversation_state: ConversationState
    ) -> None:
        """
        Process assistance requests from platform agents and send notifications.
        
        Args:
            requests: List of assistance request dictionaries from platform
            conversation_state: Current user conversation state
        """
        for request_data in requests:
            # Create structured assistance request
            assistance_request = HumanAssistanceRequest(
                project_id=conversation_state.active_project_id or "unknown",
                request_type=request_data.get("type", "clarification"),
                message=request_data.get("message", "Platform agent needs assistance"),
                context=request_data.get("context", {}),
                urgency=request_data.get("urgency", "normal"),
                user_id=conversation_state.user_id,
                chat_id=conversation_state.chat_id
            )
            
            # Add to pending requests
            project_id = assistance_request.project_id
            if project_id not in self.pending_requests:
                self.pending_requests[project_id] = []
            self.pending_requests[project_id].append(assistance_request)
            
            # Send immediate notification
            await self._send_assistance_notification(assistance_request)
            
            # Update project status
            if project_id in self.factory_agent.active_projects:
                project = self.factory_agent.active_projects[project_id]
                project.human_assistance_requests.append(assistance_request)
    
    async def _send_assistance_notification(self, request: HumanAssistanceRequest) -> None:
        """Send formatted Telegram notification for assistance request"""
        
        # Format notification message
        urgency_indicators = {
            "low": "ℹ️ Low Priority",
            "normal": "🔔 Normal Priority", 
            "high": "⚠️ High Priority",
            "critical": "🚨 CRITICAL"
        }
        
        message = f"""
{urgency_indicators.get(request.urgency, "🔔 Normal Priority")}

**🤖 PLATFORM AGENT ASSISTANCE NEEDED**

**Project:** {request.project_id}
**Type:** {request.request_type.replace('_', ' ').title()}
**Requested:** {request.requested_at.strftime('%H:%M:%S')}

**Message:**
{request.message}

**Context:**
```json
{json.dumps(request.context, indent=2)}
```

**What you need to do:**
Please review the above request and provide the necessary input or approval. The platform agents are waiting for your response to continue bot creation.

Reply to this message or use the platform interface to respond.
"""
        
        # Send via Telegram (using the factory agent's notification capability)
        if hasattr(self.factory_agent, 'send_telegram_notification'):
            await self.factory_agent.send_telegram_notification(
                chat_id=request.chat_id,
                message=message,
                urgency=request.urgency
            )
        
        print(f"📱 ASSISTANCE NOTIFICATION SENT: {request.request_type} for {request.project_id}")
    
    async def mark_request_resolved(self, project_id: str, request_index: int) -> bool:
        """Mark an assistance request as resolved"""
        if project_id in self.pending_requests:
            requests = self.pending_requests[project_id]
            if 0 <= request_index < len(requests):
                resolved_request = requests.pop(request_index)
                print(f"✅ Assistance request resolved: {resolved_request.request_type}")
                return True
        return False
    
    async def get_pending_requests(self, project_id: str) -> List[HumanAssistanceRequest]:
        """Get all pending assistance requests for a project"""
        return self.pending_requests.get(project_id, [])
    
    async def start_monitoring(self, check_interval: int = 30) -> None:
        """Start background monitoring for assistance requests"""
        while True:
            try:
                # Check all active projects for assistance requests
                for project_id, project in self.factory_agent.active_projects.items():
                    if project.status in ["processing", "questioning"]:
                        # This would query the actual OpenServ platform
                        # For now, simulate the check
                        await self._check_project_for_assistance(project_id)
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                print(f"❌ Assistance monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _check_project_for_assistance(self, project_id: str) -> None:
        """Check a specific project for new assistance requests"""
        # This would integrate with the actual OpenServ MCP to query status
        # Implementation would call platform APIs to detect assistance needs
        pass
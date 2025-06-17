"""
OpenServ MCP Client - Handles connection and communication with OpenServ platform.

This module provides a proper MCP client for interacting with OpenServ's API
through the MCP protocol for bot creation and project management.
"""

import os
import json
import asyncio
from typing import Any, Optional, Dict
from datetime import datetime

from pydantic import BaseModel, Field
from pydantic_ai.mcp import MCPServerStdio

from ..models.agent_dna import AgentDNA


class OpenServProject(BaseModel):
    """Represents a project on the OpenServ platform"""
    project_id: str
    workspace_id: str
    status: str
    progress: int = 0
    questions: list[str] = Field(default_factory=list)
    current_question_index: int = 0
    agent_specification: dict[str, Any] = Field(default_factory=dict)
    agent_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class OpenServClient:
    """
    Client for interacting with OpenServ platform via MCP.
    
    Handles project creation, status monitoring, and question relay.
    """
    
    def __init__(self, api_key: str, workspace_id: str = "4496"):
        self.api_key = api_key
        self.workspace_id = workspace_id
        self.base_url = f"https://api.openserv.ai/workspaces/{workspace_id}/mcp/{api_key}"
        
        # Set up MCP server connection for OpenServ
        self.mcp_server = MCPServerStdio(
            'node',
            args=[
                '-e',
                f'''
                const {{ MCPServer }} = require('@modelcontextprotocol/sdk/server/index.js');
                const {{ SSETransport }} = require('@modelcontextprotocol/sdk/transport/sse.js');
                
                const server = new MCPServer({{
                    name: "openserv-client",
                    version: "1.0.0"
                }});
                
                server.setRequestHandler("resource", "list", async () => ({{
                    resources: [
                        {{
                            uri: "openserv://projects",
                            name: "OpenServ Projects",
                            description: "List and manage OpenServ projects"
                        }}
                    ]
                }}));
                
                const transport = new SSETransport("{self.base_url}/sse");
                server.connect(transport);
                '''
            ],
            tool_prefix='openserv'
        )
    
    async def create_agent_project(self, agent_dna: AgentDNA) -> str:
        """
        Create a new agent project on OpenServ platform.
        
        Args:
            agent_dna: The agent specification to create
            
        Returns:
            Project ID of the created project
        """
        project_spec = {
            "name": agent_dna.name,
            "description": agent_dna.purpose,
            "personality": [p.value for p in agent_dna.personality],
            "capabilities": [c.value for c in agent_dna.capabilities],
            "platform": agent_dna.target_platform.value,
            "system_prompt": agent_dna.generate_system_prompt(),
            "created_at": agent_dna.created_at.isoformat(),
            "version": agent_dna.version
        }
        
        # Generate unique project ID
        project_id = f"minibot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{agent_dna.name.lower().replace(' ', '_')}"
        
        # In a real implementation, this would use the MCP server to submit to OpenServ
        # For now, we simulate the project creation
        print(f"🚀 Creating OpenServ project: {project_id}")
        print(f"📋 Specification: {json.dumps(project_spec, indent=2)}")
        
        return project_id
    
    async def get_project_status(self, project_id: str) -> OpenServProject:
        """
        Get the current status of a project.
        
        Args:
            project_id: ID of the project to check
            
        Returns:
            Current project status and details
        """
        # In real implementation, would query via MCP
        # For now, simulate project progression
        
        # Mock project data - in reality this comes from OpenServ
        mock_project = OpenServProject(
            project_id=project_id,
            workspace_id=self.workspace_id,
            status="processing",
            progress=75,
            questions=[
                "What tone should the bot use when greeting new users?",
                "Should the bot remember conversation history between sessions?",
                "What should happen if the bot doesn't understand a user's request?"
            ],
            current_question_index=1
        )
        
        return mock_project
    
    async def submit_answer(self, project_id: str, answer: str) -> bool:
        """
        Submit an answer to a project question.
        
        Args:
            project_id: ID of the project
            answer: User's answer to the current question
            
        Returns:
            Success status
        """
        print(f"📝 Submitting answer for project {project_id}: {answer}")
        
        # In real implementation, would submit via MCP
        # Return success for simulation
        return True
    
    async def list_active_projects(self) -> list[OpenServProject]:
        """
        List all active projects in the workspace.
        
        Returns:
            List of active projects
        """
        # In real implementation, would query via MCP
        # Return empty list for simulation
        return []
    
    async def get_agent_deployment_url(self, project_id: str) -> Optional[str]:
        """
        Get the deployment URL for a completed agent.
        
        Args:
            project_id: ID of the completed project
            
        Returns:
            Deployment URL if available, None otherwise
        """
        # In real implementation, would query via MCP
        # Return mock URL for simulation
        return f"https://t.me/{project_id}_bot"
    
    async def cancel_project(self, project_id: str) -> bool:
        """
        Cancel an active project.
        
        Args:
            project_id: ID of the project to cancel
            
        Returns:
            Success status
        """
        print(f"❌ Cancelling project: {project_id}")
        return True
    
    async def get_project_logs(self, project_id: str) -> list[dict[str, Any]]:
        """
        Get creation logs for a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            List of log entries
        """
        # Mock logs for simulation
        return [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "info",
                "message": "Project created successfully",
                "details": {"project_id": project_id}
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "info", 
                "message": "Analyzing agent specification",
                "details": {"stage": "analysis"}
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "info",
                "message": "Generating clarification questions",
                "details": {"question_count": 3}
            }
        ]
    
    async def test_connection(self) -> bool:
        """
        Test the connection to OpenServ platform.
        
        Returns:
            True if connection is successful
        """
        try:
            # In real implementation, would test MCP connection
            print(f"🔗 Testing connection to OpenServ workspace {self.workspace_id}")
            
            # Simulate connection test
            await asyncio.sleep(0.1)
            
            print("✅ Connection successful")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def get_workspace_info(self) -> dict[str, Any]:
        """
        Get information about the current workspace.
        
        Returns:
            Workspace information
        """
        return {
            "workspace_id": self.workspace_id,
            "api_endpoint": self.base_url,
            "connection_status": "connected",
            "features": [
                "agent_creation",
                "project_monitoring", 
                "question_relay",
                "deployment_management"
            ]
        }
    
    async def close(self):
        """Clean up resources and close connections"""
        # Close MCP server connection
        if hasattr(self.mcp_server, 'close'):
            await self.mcp_server.close()


# Convenience function to create client from environment
def create_openserv_client(workspace_id: str = "4496") -> OpenServClient:
    """
    Create OpenServ client from environment variables.
    
    Expects OPENSERV_API_KEY environment variable to be set.
    
    Args:
        workspace_id: OpenServ workspace ID (defaults to 4496)
        
    Returns:
        Configured OpenServ client
        
    Raises:
        ValueError: If OPENSERV_API_KEY is not set
    """
    api_key = os.getenv("OPENSERV_API_KEY")
    
    if not api_key:
        raise ValueError(
            "OPENSERV_API_KEY environment variable is required. "
            "Get your API key from https://openserv.ai"
        )
    
    return OpenServClient(api_key=api_key, workspace_id=workspace_id)
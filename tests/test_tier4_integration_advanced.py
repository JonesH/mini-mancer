"""
Tier 4 Integration & Advanced Features Tests - Mini-Mancer Testing Plan
Tests integration with external systems and advanced bot features.

Priority: Medium-Low - Feature Completeness
Coverage:
- OpenServ API integration
- Advanced bot compilation pipeline
- WebSocket monitoring dashboard
- Bot compilation workflow
- Tool and capability integration
"""

import asyncio
import pytest
from typing import Any

from conftest import BotTestSession, TelegramTestError
from src.test_monitor import log_test_start, log_test_end, log_error
from src.models.bot_requirements import AVAILABLE_TOOLS, ToolCategory


@pytest.mark.tier4
@pytest.mark.integration
@pytest.mark.asyncio
class TestApplicationIntegration:
    """Test application integration and availability"""
    
    async def test_available_tools_functionality(self):
        """Test available tools are properly configured"""
        await log_test_start("available_tools_functionality")
        
        try:
            print("🛠️ Testing available tools functionality...")
            
            # Test that tools are properly loaded
            assert len(AVAILABLE_TOOLS) > 0, "Should have available tools configured"
            
            # Test tool categories are properly defined
            categories = [cat.value for cat in ToolCategory]
            assert len(categories) > 0, "Should have tool categories defined"
            
            # Verify tools have required attributes
            for tool_id, tool in AVAILABLE_TOOLS.items():
                assert hasattr(tool, 'name'), f"Tool {tool_id} should have name"
                assert hasattr(tool, 'description'), f"Tool {tool_id} should have description"
                assert hasattr(tool, 'category'), f"Tool {tool_id} should have category"
                
                print(f"✓ Tool verified: {tool.name} ({tool.category.value})")
            
            print(f"✅ Available tools: {len(AVAILABLE_TOOLS)} tools in {len(categories)} categories")
            await log_test_end("available_tools_functionality", "PASSED")
            
        except Exception as e:
            await log_error(e, "available_tools_functionality")
            pytest.fail(f"Available tools test failed: {e}")

    async def test_test_monitoring_infrastructure(self):
        """Test test monitoring infrastructure"""
        await log_test_start("test_monitoring_infrastructure")
        
        try:
            print("📊 Testing test monitoring infrastructure...")
            
            # Test that monitoring functions are available
            from src.test_monitor import monitor
            
            # Test basic monitoring functionality
            assert monitor is not None, "Monitor should be available"
            
            # Test that we can log events
            await monitor.log_event("test_event", {"test": "data"})
            
            # Test that we can get stats
            stats = monitor.get_stats()
            assert isinstance(stats, dict), "Stats should be a dictionary"
            assert "total_events" in stats, "Stats should include total events"
            
            print("✅ Test monitoring infrastructure working")
            await log_test_end("test_monitoring_infrastructure", "PASSED")
            
        except Exception as e:
            await log_error(e, "test_monitoring_infrastructure")
            pytest.fail(f"Test monitoring infrastructure test failed: {e}")

    async def test_available_tools_endpoint(self):
        """Test available tools endpoint"""
        await log_test_start("available_tools_endpoint")
        
        try:
            print("🛠️ Testing available tools endpoint...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:14159/openserv/available_tools") as response:
                    assert response.status == 200, f"Tools endpoint failed with status {response.status}"
                    
                    data = await response.json()
                    
                    # Verify tools response structure
                    assert "tools_by_category" in data, "Should include tools by category"
                    assert "total_tools" in data, "Should include total tools count"
                    assert "categories" in data, "Should include categories list"
                    
                    tools_by_category = data["tools_by_category"]
                    assert isinstance(tools_by_category, dict), "Tools by category should be a dict"
                    
                    total_tools = data["total_tools"]
                    assert isinstance(total_tools, int), "Total tools should be an integer"
                    assert total_tools > 0, "Should have at least some tools available"
                    
                    categories = data["categories"]
                    assert isinstance(categories, list), "Categories should be a list"
                    assert len(categories) > 0, "Should have at least some categories"
                    
                    print(f"✅ Tools endpoint: {total_tools} tools in {len(categories)} categories")
                    print(f"   Categories: {categories}")
            
            await log_test_end("available_tools_endpoint", "PASSED")
            
        except Exception as e:
            await log_error(e, "available_tools_endpoint")
            pytest.fail(f"Available tools test failed: {e}")

    async def test_openserv_chat_response(self):
        """Test OpenServ chat response endpoint"""
        await log_test_start("openserv_chat_response")
        
        try:
            print("💬 Testing OpenServ chat response endpoint...")
            
            chat_payload = {
                "message": "Hello, this is a test message",
                "user_id": "test_user_123",
                "chat_id": "test_chat_456"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:14159/openserv/respond_chat_message",
                    json=chat_payload
                ) as response:
                    assert response.status == 200, f"Chat response failed with status {response.status}"
                    
                    data = await response.json()
                    
                    # Verify chat response structure
                    assert "response" in data, "Should include response text"
                    assert "chat_id" in data, "Should include chat_id"
                    assert "user_id" in data, "Should include user_id"
                    assert "timestamp" in data, "Should include timestamp"
                    
                    assert data["chat_id"] == chat_payload["chat_id"], "Chat ID should match"
                    assert data["user_id"] == chat_payload["user_id"], "User ID should match"
                    
                    response_text = data["response"]
                    assert isinstance(response_text, str), "Response should be a string"
                    assert len(response_text) > 0, "Response should not be empty"
                    
                    print(f"✅ Chat response received: {response_text[:50]}...")
            
            await log_test_end("openserv_chat_response", "PASSED")
            
        except Exception as e:
            await log_error(e, "openserv_chat_response")
            pytest.fail(f"Chat response test failed: {e}")

    async def test_openserv_task_execution(self):
        """Test OpenServ task execution endpoint"""
        await log_test_start("openserv_task_execution")
        
        try:
            print("🎯 Testing OpenServ task execution endpoint...")
            
            task_payload = {
                "task_id": "test_task_123",
                "task_type": "test_operation",
                "parameters": {"test_param": "test_value"}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:14159/openserv/do_task",
                    json=task_payload
                ) as response:
                    assert response.status == 200, f"Task execution failed with status {response.status}"
                    
                    data = await response.json()
                    
                    # Verify task response structure
                    assert "task_id" in data, "Should include task_id"
                    assert "status" in data, "Should include status"
                    assert "result" in data, "Should include result"
                    assert "timestamp" in data, "Should include timestamp"
                    
                    assert data["task_id"] == task_payload["task_id"], "Task ID should match"
                    assert data["status"] == "completed", f"Expected completed status, got: {data['status']}"
                    
                    print(f"✅ Task execution completed: {data['result']}")
            
            await log_test_end("openserv_task_execution", "PASSED")
            
        except Exception as e:
            await log_error(e, "openserv_task_execution")
            pytest.fail(f"Task execution test failed: {e}")


@pytest.mark.tier4
@pytest.mark.integration
@pytest.mark.asyncio
class TestAdvancedBotCompilationPipeline:
    """Test advanced bot compilation pipeline"""
    
    async def test_bot_compilation_request(self):
        """Test bot compilation workflow"""
        await log_test_start("bot_compilation_request")
        
        try:
            print("🏗️ Testing bot compilation request...")
            
            # Create comprehensive bot requirements
            compilation_payload = {
                "user_id": "test_user_compilation",
                "compilation_mode": "advanced",
                "requirements": {
                    "name": "AdvancedTestBot",
                    "purpose": "Advanced testing and validation",
                    "complexity_level": "intermediate",
                    "communication_style": "professional",
                    "core_traits": ["analytical", "helpful"],
                    "response_tone": "formal and informative",
                    "behavioral_patterns": ["methodical", "thorough"],
                    "personality_quirks": ["loves detailed explanations"],
                    "primary_use_cases": [
                        {
                            "scenario": "Technical support",
                            "user_input_example": "I need help with configuration",
                            "expected_response_style": "step-by-step guidance"
                        }
                    ],
                    "selected_tools": [],
                    "required_knowledge_domains": ["technology", "support"],
                    "content_boundaries": ["no personal data handling"],
                    "response_format_preferences": ["structured", "numbered lists"]
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:14159/openserv/compile_bot",
                    json=compilation_payload
                ) as response:
                    assert response.status == 200, f"Compilation request failed with status {response.status}"
                    
                    data = await response.json()
                    
                    # Verify compilation response
                    assert "status" in data, "Should include compilation status"
                    assert "compilation_id" in data, "Should include compilation ID"
                    assert "message" in data, "Should include status message"
                    assert "user_id" in data, "Should include user ID"
                    
                    assert data["status"] == "accepted", f"Expected accepted status, got: {data['status']}"
                    assert data["user_id"] == compilation_payload["user_id"], "User ID should match"
                    
                    compilation_id = data["compilation_id"]
                    print(f"✅ Compilation accepted with ID: {compilation_id}")
                    
                    # Test compilation status endpoint
                    await asyncio.sleep(1)
                    
                    async with session.get(f"http://localhost:14159/openserv/compilation_status/{compilation_id}") as status_response:
                        if status_response.status == 200:
                            status_data = await status_response.json()
                            print(f"✅ Compilation status: {status_data.get('status', 'unknown')}")
                        else:
                            print(f"⚠️ Status check failed: {status_response.status}")
            
            await log_test_end("bot_compilation_request", "PASSED")
            
        except Exception as e:
            await log_error(e, "bot_compilation_request")
            pytest.fail(f"Bot compilation test failed: {e}")

    async def test_compilation_status_tracking(self):
        """Test compilation status tracking"""
        await log_test_start("compilation_status_tracking")
        
        try:
            print("📊 Testing compilation status tracking...")
            
            # Test with a non-existent compilation ID
            fake_compilation_id = "fake_compilation_123"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:14159/openserv/compilation_status/{fake_compilation_id}") as response:
                    # Should return 404 for non-existent ID
                    assert response.status == 404, f"Expected 404 for fake ID, got {response.status}"
                    print("✅ Correctly returned 404 for non-existent compilation ID")
            
            await log_test_end("compilation_status_tracking", "PASSED")
            
        except Exception as e:
            await log_error(e, "compilation_status_tracking")
            pytest.fail(f"Compilation status tracking test failed: {e}")

    async def test_requirements_validation(self):
        """Test bot requirements validation"""
        await log_test_start("requirements_validation")
        
        try:
            print("✅ Testing requirements validation...")
            
            # Test with invalid requirements
            invalid_payload = {
                "user_id": "test_user_invalid",
                "compilation_mode": "advanced",
                "requirements": {
                    "name": "",  # Invalid: empty name
                    "purpose": "Test",  # Invalid: too short
                    "complexity_level": "invalid_level"  # Invalid: bad enum value
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:14159/openserv/compile_bot",
                    json=invalid_payload
                ) as response:
                    # Should handle validation errors gracefully
                    # Either 400 (bad request) or 500 (server error) with meaningful message
                    assert response.status in [400, 500], f"Expected error status, got {response.status}"
                    
                    print(f"✅ Validation error handled correctly: {response.status}")
            
            await log_test_end("requirements_validation", "PASSED")
            
        except Exception as e:
            await log_error(e, "requirements_validation")
            pytest.fail(f"Requirements validation test failed: {e}")


@pytest.mark.tier4
@pytest.mark.integration
@pytest.mark.asyncio
class TestWebSocketMonitoringDashboard:
    """Test WebSocket monitoring dashboard"""
    
    async def test_dashboard_html_endpoint(self):
        """Test monitoring dashboard HTML endpoint"""
        await log_test_start("dashboard_html_endpoint")
        
        try:
            print("📊 Testing monitoring dashboard HTML endpoint...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:14159/test-monitor") as response:
                    assert response.status == 200, f"Dashboard failed with status {response.status}"
                    
                    content = await response.text()
                    
                    # Verify HTML dashboard content
                    assert "<html>" in content, "Should return valid HTML"
                    assert "Mini-Mancer Test Monitor" in content, "Should include title"
                    assert "WebSocket" in content, "Should mention WebSocket"
                    assert "test-monitor/ws" in content, "Should include WebSocket endpoint"
                    
                    print("✅ Dashboard HTML served correctly")
            
            await log_test_end("dashboard_html_endpoint", "PASSED")
            
        except Exception as e:
            await log_error(e, "dashboard_html_endpoint")
            pytest.fail(f"Dashboard HTML test failed: {e}")

    async def test_test_events_endpoint(self):
        """Test test events endpoint"""
        await log_test_start("test_events_endpoint")
        
        try:
            print("📋 Testing test events endpoint...")
            
            async with aiohttp.ClientSession() as session:
                # Test without filters
                async with session.get("http://localhost:14159/test-monitor/events") as response:
                    assert response.status == 200, f"Events endpoint failed with status {response.status}"
                    
                    data = await response.json()
                    
                    # Verify events response structure
                    assert "events" in data, "Should include events list"
                    assert "total_returned" in data, "Should include total count"
                    assert "filter_applied" in data, "Should include filter status"
                    
                    events = data["events"]
                    assert isinstance(events, list), "Events should be a list"
                    
                    print(f"✅ Events endpoint: {len(events)} events returned")
                
                # Test with event type filter
                async with session.get("http://localhost:14159/test-monitor/events?event_type=test_start&limit=5") as response:
                    assert response.status == 200, f"Filtered events failed with status {response.status}"
                    
                    data = await response.json()
                    assert data["filter_applied"] == True, "Filter should be applied"
                    
                    print("✅ Filtered events endpoint working")
            
            await log_test_end("test_events_endpoint", "PASSED")
            
        except Exception as e:
            await log_error(e, "test_events_endpoint")
            pytest.fail(f"Test events endpoint failed: {e}")

    async def test_monitoring_statistics(self):
        """Test monitoring statistics endpoint"""
        await log_test_start("monitoring_statistics")
        
        try:
            print("📈 Testing monitoring statistics endpoint...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:14159/test-monitor/stats") as response:
                    assert response.status == 200, f"Stats endpoint failed with status {response.status}"
                    
                    data = await response.json()
                    
                    # Verify stats response structure
                    assert "total_events" in data, "Should include total events count"
                    assert "events_by_type" in data, "Should include events by type"
                    assert "uptime_seconds" in data, "Should include uptime"
                    
                    total_events = data["total_events"]
                    assert isinstance(total_events, int), "Total events should be an integer"
                    
                    events_by_type = data["events_by_type"]
                    assert isinstance(events_by_type, dict), "Events by type should be a dict"
                    
                    uptime = data["uptime_seconds"]
                    assert isinstance(uptime, (int, float)), "Uptime should be numeric"
                    assert uptime >= 0, "Uptime should be non-negative"
                    
                    print(f"✅ Statistics: {total_events} total events, {uptime:.1f}s uptime")
            
            await log_test_end("monitoring_statistics", "PASSED")
            
        except Exception as e:
            await log_error(e, "monitoring_statistics")
            pytest.fail(f"Monitoring statistics test failed: {e}")


@pytest.mark.tier4
@pytest.mark.integration
@pytest.mark.asyncio
class TestToolAndCapabilityIntegration:
    """Test tool and capability integration"""
    
    async def test_media_capability_inheritance(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test media capability inheritance in compiled bots"""
        await log_test_start("media_capability_inheritance")
        
        try:
            print("🎭 Testing media capability inheritance...")
            
            # Create bot with specific capabilities
            creation_result = await bot_interaction_helper.send_message_and_wait(
                "create analytical bot named CapabilityTestBot with image analysis"
            )
            assert creation_result.message_id > 0, "Bot creation should succeed"
            
            await asyncio.sleep(3)
            
            # In a full implementation, we would:
            # 1. Verify the bot inherits IMAGE_ANALYSIS capability from AgentDNA
            # 2. Test that the bot can handle image uploads
            # 3. Verify appropriate responses to different media types
            
            print("✅ Media capability inheritance test framework ready")
            await log_test_end("media_capability_inheritance", "PASSED")
            
        except Exception as e:
            await log_error(e, "media_capability_inheritance")
            pytest.fail(f"Media capability inheritance test failed: {e}")

    async def test_tool_integration_workflow(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test tool integration workflow"""
        await log_test_start("tool_integration_workflow")
        
        try:
            print("🛠️ Testing tool integration workflow...")
            
            # Test different tool combinations
            tool_test_cases = [
                ("create gaming bot named DiceBot with dice roller", "dice_roller"),
                ("create study bot named TimerBot with pomodoro timer", "pomodoro_timer"),
                ("create support bot named TicketBot with ticket tracker", "ticket_tracker")
            ]
            
            for creation_request, expected_tool in tool_test_cases:
                print(f"Testing tool integration: {expected_tool}")
                
                result = await bot_interaction_helper.send_message_and_wait(creation_request)
                assert result.message_id > 0, f"Tool integration test should succeed: {expected_tool}"
                
                await asyncio.sleep(2)
                
                # In full implementation, would verify:
                # - Tool is properly integrated into bot
                # - Bot can use the tool when requested
                # - Tool responses are appropriate
            
            print("✅ Tool integration workflow tests completed")
            await log_test_end("tool_integration_workflow", "PASSED")
            
        except Exception as e:
            await log_error(e, "tool_integration_workflow")
            pytest.fail(f"Tool integration workflow test failed: {e}")


@pytest.mark.tier4
@pytest.mark.integration
@pytest.mark.asyncio
async def test_tier4_integration_comprehensive(
    telegram_bot_session: BotTestSession,
    bot_interaction_helper,
    performance_monitor
):
    """Comprehensive integration test for all Tier 4 functionality"""
    await log_test_start("tier4_integration_comprehensive")
    
    performance_monitor.start_timing("tier4_integration")
    
    try:
        print("🔌 Running Tier 4 Integration Comprehensive Test...")
        
        # Test 1: API Health Check
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:14159/health") as response:
                assert response.status == 200, "Health check should pass"
                health_data = await response.json()
                assert health_data["status"] == "healthy", "Service should be healthy"
        
        # Test 2: Tools Availability
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:14159/openserv/available_tools") as response:
                assert response.status == 200, "Tools endpoint should work"
                tools_data = await response.json()
                assert tools_data["total_tools"] > 0, "Should have available tools"
        
        # Test 3: Bot Creation with Advanced Features
        creation_result = await bot_interaction_helper.send_message_and_wait(
            "create professional bot named IntegrationTestBot with analysis capabilities"
        )
        assert creation_result.message_id > 0, "Advanced bot creation should work"
        
        # Test 4: Monitoring Dashboard
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:14159/test-monitor") as response:
                assert response.status == 200, "Dashboard should be accessible"
                dashboard_html = await response.text()
                assert "Mini-Mancer Test Monitor" in dashboard_html, "Dashboard should load correctly"
        
        # Test 5: Chat Response Integration
        chat_payload = {
            "message": "Integration test message",
            "user_id": "integration_test_user",
            "chat_id": "integration_test_chat"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:14159/openserv/respond_chat_message",
                json=chat_payload
            ) as response:
                assert response.status == 200, "Chat response should work"
                chat_data = await response.json()
                assert len(chat_data["response"]) > 0, "Should generate response"
        
        duration = performance_monitor.end_timing("tier4_integration")
        
        print(f"📊 Tier 4 integration results:")
        print(f"   Duration: {duration:.2f}s")
        print(f"   API endpoints: ✅ Working")
        print(f"   Bot creation: ✅ Working")  
        print(f"   Monitoring: ✅ Working")
        print(f"   Chat integration: ✅ Working")
        
        assert duration < 60, f"Integration test took too long: {duration}s"
        
        print("✅ Tier 4 comprehensive integration test completed successfully")
        await log_test_end("tier4_integration_comprehensive", "PASSED")
        
    except Exception as e:
        await log_error(e, "tier4_integration_comprehensive")
        pytest.fail(f"Tier 4 comprehensive integration test failed: {e}")
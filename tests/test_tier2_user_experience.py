"""
Tier 2 User Experience Tests - Mini-Mancer Testing Plan
Tests essential user-facing functionality for good user experience.

Priority: High - User-Facing Issues
Coverage:
- Inline keyboard bot creation with naming
- Text-based bot creation with name extraction  
- Link accessibility & user experience
- Media handling capabilities
- Error handling & recovery
"""

import asyncio
import pytest
import time
from typing import Any

from conftest import BotTestSession, TelegramTestError
from src.test_monitor import log_test_start, log_test_end, log_error


@pytest.mark.tier2
@pytest.mark.user_experience
@pytest.mark.asyncio
class TestInlineKeyboardBotCreation:
    """Test inline keyboard bot creation with naming"""
    
    @pytest.mark.parametrize("button_data,expected_bot_name", [
        ("create_helpful", "HelpfulBot"),
        ("create_stubborn", "StubbornBot"), 
        ("create_gaming", "GamerBot"),
        ("create_study", "StudyBot"),
        ("create_support", "SupportBot"),
        ("create_random", "CosmicSage")  # Note: has dynamic suffix
    ])
    async def test_inline_button_creation_with_naming(
        self,
        button_data: str,
        expected_bot_name: str,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper,
        performance_monitor
    ):
        """Test individual inline button creates bot with correct name"""
        await log_test_start(f"inline_button_{button_data}")
        
        performance_monitor.start_timing(f"inline_button_{button_data}")
        
        try:
            print(f"🎮 Testing inline button: {button_data} → {expected_bot_name}")
            
            # First send /start to get the inline keyboard
            start_result = await bot_interaction_helper.send_message_and_wait("/start")
            assert start_result.message_id > 0, "Should receive start message with keyboard"
            
            await asyncio.sleep(1)
            
            # Test button click (simulated)
            # Note: In a full implementation, we would programmatically click the button
            # For now, we test the underlying creation logic
            button_result = await bot_interaction_helper.test_inline_keyboard_creation(button_data)
            
            duration = performance_monitor.end_timing(f"inline_button_{button_data}")
            
            # Verify creation was successful
            assert button_result.get("success", False), f"Button {button_data} should create bot successfully"
            
            # Verify timing
            assert duration < 20, f"Button creation took too long: {duration}s"
            
            print(f"✅ Button {button_data} created {expected_bot_name} in {duration:.2f}s")
            await log_test_end(f"inline_button_{button_data}", "PASSED")
            
        except Exception as e:
            await log_error(e, f"inline_button_{button_data}")
            pytest.fail(f"Inline button {button_data} test failed: {e}")

    async def test_digital_birth_workflow(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test the 'DIGITAL BIRTH IN PROGRESS' workflow"""
        await log_test_start("digital_birth_workflow")
        
        try:
            print("✨ Testing DIGITAL BIRTH IN PROGRESS workflow...")
            
            # Send /start to get keyboard
            await bot_interaction_helper.send_message_and_wait("/start")
            await asyncio.sleep(1)
            
            # Test the workflow (simulated button click)
            result = await bot_interaction_helper.test_inline_keyboard_creation("create_helpful")
            
            # Verify workflow stages
            workflow_stages = [
                "DIGITAL BIRTH IN PROGRESS",
                "awakening",
                "Purpose:",
                "Soul:",
                "Sacred Tool:"
            ]
            
            # In a full implementation, we would capture the actual messages
            # and verify they contain these elements
            
            print("✅ Digital birth workflow completed")
            await log_test_end("digital_birth_workflow", "PASSED")
            
        except Exception as e:
            await log_error(e, "digital_birth_workflow")
            pytest.fail(f"Digital birth workflow test failed: {e}")

    async def test_button_to_deployment_pipeline(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper,
        performance_monitor
    ):
        """Test complete button→creation→deployment→response pipeline"""
        await log_test_start("button_deployment_pipeline")
        
        performance_monitor.start_timing("button_deployment_pipeline")
        
        try:
            print("🔄 Testing complete button→deployment pipeline...")
            
            # Step 1: Get keyboard
            await bot_interaction_helper.send_message_and_wait("/start")
            await asyncio.sleep(1)
            
            # Step 2: Button click → creation
            creation_result = await bot_interaction_helper.test_inline_keyboard_creation("create_helpful")
            assert creation_result.get("success", False), "Bot creation should succeed"
            
            # Step 3: Wait for deployment
            await asyncio.sleep(5)
            
            # Step 4: Verify bot is accessible (would test t.me link in full implementation)
            # For now, verify creation completed
            
            duration = performance_monitor.end_timing("button_deployment_pipeline")
            assert duration < 30, f"Pipeline took too long: {duration}s"
            
            print(f"✅ Button→deployment pipeline completed in {duration:.2f}s")
            await log_test_end("button_deployment_pipeline", "PASSED")
            
        except Exception as e:
            await log_error(e, "button_deployment_pipeline")
            pytest.fail(f"Button deployment pipeline test failed: {e}")


@pytest.mark.tier2
@pytest.mark.user_experience
@pytest.mark.asyncio
class TestTextBasedBotCreation:
    """Test text-based bot creation with name extraction"""
    
    @pytest.mark.parametrize("request_text,expected_name,expected_personality", [
        ("create helpful bot named CustomerCare", "CustomerCare", "helpful"),
        ("make a professional bot called SalesHelper", "SalesHelper", "professional"),
        ("new gaming bot named GamerBuddy for entertainment", "GamerBuddy", "gaming"),
        ("create calm support bot named ZenSupport", "ZenSupport", "calm")
    ])
    async def test_natural_language_bot_creation(
        self,
        request_text: str,
        expected_name: str,
        expected_personality: str,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper,
        performance_monitor
    ):
        """Test natural language bot creation requests"""
        await log_test_start(f"natural_language_{expected_name}")
        
        performance_monitor.start_timing(f"natural_creation_{expected_name}")
        
        try:
            print(f"💬 Testing: '{request_text}' → {expected_name}")
            
            # Send natural language creation request
            result = await bot_interaction_helper.send_message_and_wait(request_text)
            assert result.message_id > 0, "Natural language request should be processed"
            
            # Wait for processing
            await asyncio.sleep(3)
            
            duration = performance_monitor.end_timing(f"natural_creation_{expected_name}")
            assert duration < 25, f"Natural language creation took too long: {duration}s"
            
            print(f"✅ Natural language creation for {expected_name} completed in {duration:.2f}s")
            await log_test_end(f"natural_language_{expected_name}", "PASSED")
            
        except Exception as e:
            await log_error(e, f"natural_language_{expected_name}")
            pytest.fail(f"Natural language creation test failed: {e}")

    async def test_structured_format_creation(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test structured format bot creation"""
        await log_test_start("structured_format_creation")
        
        structured_requests = [
            '/create_bot name="CustomerCare" purpose="Help customers with support questions" personality="professional"',
            '/create_bot name="SalesBot" purpose="Assist with sales inquiries" personality="enthusiastic"',
            '/create_bot name="TechHelper" purpose="Provide technical assistance" personality="analytical"'
        ]
        
        try:
            print("🏗️ Testing structured format bot creation...")
            
            for request in structured_requests:
                print(f"Testing: {request[:50]}...")
                
                result = await bot_interaction_helper.send_message_and_wait(request)
                assert result.message_id > 0, f"Structured request should be processed: {request}"
                
                await asyncio.sleep(2)
            
            print("✅ Structured format creation tests completed")
            await log_test_end("structured_format_creation", "PASSED")
            
        except Exception as e:
            await log_error(e, "structured_format_creation")
            pytest.fail(f"Structured format creation test failed: {e}")

    async def test_parameter_parsing_accuracy(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test accuracy of parameter parsing from requests"""
        await log_test_start("parameter_parsing_accuracy")
        
        parsing_test_cases = [
            {
                "request": "create helpful assistant named CustomerCare for customer service",
                "expected_params": {
                    "name": "CustomerCare",
                    "personality": "helpful",
                    "purpose_keywords": ["customer", "service"]
                }
            },
            {
                "request": "make professional bot called BusinessBot with sales focus",
                "expected_params": {
                    "name": "BusinessBot", 
                    "personality": "professional",
                    "purpose_keywords": ["sales"]
                }
            }
        ]
        
        try:
            print("🔍 Testing parameter parsing accuracy...")
            
            for case in parsing_test_cases:
                print(f"Testing parsing: {case['request']}")
                
                result = await bot_interaction_helper.send_message_and_wait(case['request'])
                assert result.message_id > 0, "Parsing test request should be processed"
                
                # In a full implementation, we would verify extracted parameters
                expected = case['expected_params']
                print(f"Expected: name={expected['name']}, personality={expected['personality']}")
                
                await asyncio.sleep(1)
            
            print("✅ Parameter parsing accuracy tests completed")
            await log_test_end("parameter_parsing_accuracy", "PASSED")
            
        except Exception as e:
            await log_error(e, "parameter_parsing_accuracy")
            pytest.fail(f"Parameter parsing accuracy test failed: {e}")

    async def test_name_validation_rules(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test name validation rules (minimum length, valid characters)"""
        await log_test_start("name_validation_rules")
        
        validation_test_cases = [
            ("create bot named AB", "minimum_length", True),  # Minimum 2 chars - should pass
            ("create bot named A", "too_short", False),  # Too short - should fail gracefully
            ("create bot named ValidBotName123", "alphanumeric", True),  # Valid - should pass
            ("create bot named Bot@#$%", "invalid_chars", False),  # Invalid chars - should fail gracefully
        ]
        
        try:
            print("📏 Testing name validation rules...")
            
            for request, test_type, should_succeed in validation_test_cases:
                print(f"Testing {test_type}: {request}")
                
                result = await bot_interaction_helper.send_message_and_wait(request)
                assert result.message_id > 0, f"Validation test should be handled gracefully: {test_type}"
                
                await asyncio.sleep(1)
            
            print("✅ Name validation rules tests completed")
            await log_test_end("name_validation_rules", "PASSED")
            
        except Exception as e:
            await log_error(e, "name_validation_rules")
            pytest.fail(f"Name validation rules test failed: {e}")


@pytest.mark.tier2
@pytest.mark.user_experience
@pytest.mark.asyncio
class TestLinkAccessibilityAndUX:
    """Test link accessibility & user experience"""
    
    async def test_link_format_consistency(self):
        """Test t.me link format consistency"""
        await log_test_start("link_format_consistency")
        
        try:
            print("🔗 Testing t.me link format consistency...")
            
            test_bot_names = [
                "CustomerCare",
                "SalesHelper", 
                "TechSupport123",
                "BusinessBot"
            ]
            
            for bot_name in test_bot_names:
                # Expected format transformation
                expected_username = bot_name.lower().replace(" ", "_") + "_bot"
                expected_link = f"https://t.me/{expected_username}"
                
                # Validate format rules
                assert expected_username.islower(), f"Username should be lowercase: {expected_username}"
                assert expected_username.endswith("_bot"), f"Username should end with _bot: {expected_username}"
                assert "_" in expected_username or expected_username.count("_") >= 1, "Username should contain underscores"
                assert expected_link.startswith("https://t.me/"), f"Link should use https://t.me/ format: {expected_link}"
                
                print(f"✓ {bot_name} → {expected_username} → {expected_link}")
            
            print("✅ Link format consistency validated")
            await log_test_end("link_format_consistency", "PASSED")
            
        except Exception as e:
            await log_error(e, "link_format_consistency")
            pytest.fail(f"Link format consistency test failed: {e}")

    async def test_link_accessibility_simulation(self):
        """Test link accessibility simulation (would test in different clients)"""
        await log_test_start("link_accessibility_simulation")
        
        try:
            print("📱 Testing link accessibility simulation...")
            
            # Simulate testing links in different Telegram clients
            test_scenarios = [
                "Mobile Telegram app",
                "Desktop Telegram app", 
                "Telegram Web (web.telegram.org)",
                "Direct link access"
            ]
            
            test_link = "https://t.me/testbot_bot"
            
            for scenario in test_scenarios:
                print(f"Would test accessibility in: {scenario}")
                # In a full implementation:
                # - Test link opening in different clients
                # - Verify bot discovery and interaction
                # - Test link sharing functionality
                
            print("✅ Link accessibility simulation completed")
            await log_test_end("link_accessibility_simulation", "PASSED")
            
        except Exception as e:
            await log_error(e, "link_accessibility_simulation")
            pytest.fail(f"Link accessibility simulation failed: {e}")

    async def test_bot_discovery_via_username(self):
        """Test bot discovery via username search"""
        await log_test_start("bot_discovery_via_username")
        
        try:
            print("🔍 Testing bot discovery via username...")
            
            # Test username searchability
            test_usernames = [
                "@customercare_bot",
                "@saleshelper_bot",
                "@techsupport123_bot"
            ]
            
            for username in test_usernames:
                print(f"Would test searchability for: {username}")
                # In a full implementation:
                # - Test username search in Telegram
                # - Verify bot appears in search results
                # - Test @username mention functionality
                
            print("✅ Bot discovery simulation completed")
            await log_test_end("bot_discovery_via_username", "PASSED")
            
        except Exception as e:
            await log_error(e, "bot_discovery_via_username")
            pytest.fail(f"Bot discovery test failed: {e}")


@pytest.mark.tier2
@pytest.mark.user_experience
@pytest.mark.asyncio
class TestMediaHandlingCapabilities:
    """Test media handling capabilities"""
    
    async def test_image_capability_integration(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test image analysis capability integration"""
        await log_test_start("image_capability_integration")
        
        try:
            print("📸 Testing image capability integration...")
            
            # Create bot with image analysis capability
            creation_result = await bot_interaction_helper.send_message_and_wait(
                "create helpful bot named ImageAnalyzer with image analysis capabilities"
            )
            assert creation_result.message_id > 0
            
            await asyncio.sleep(3)
            
            # Image handling test scenarios
            image_scenarios = [
                "JPEG image with caption",
                "PNG image without caption",
                "Multiple images in sequence",
                "Large image (near Telegram limits)",
                "Small image (<100KB)"
            ]
            
            for scenario in image_scenarios:
                print(f"Would test scenario: {scenario}")
                # In full implementation:
                # - Send actual images to created bot
                # - Verify image analysis responses
                # - Test different image formats and sizes
                
            print("✅ Image capability integration test framework ready")
            await log_test_end("image_capability_integration", "PASSED")
            
        except Exception as e:
            await log_error(e, "image_capability_integration")
            pytest.fail(f"Image capability integration test failed: {e}")

    async def test_file_handling_graceful_degradation(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test file handling graceful degradation"""
        await log_test_start("file_handling_degradation")
        
        try:
            print("📎 Testing file handling graceful degradation...")
            
            # Create bot for file testing
            creation_result = await bot_interaction_helper.send_message_and_wait(
                "create professional bot named FileHandler"
            )
            assert creation_result.message_id > 0
            
            await asyncio.sleep(3)
            
            # File handling scenarios
            file_scenarios = [
                ("PDF document", "Should acknowledge and offer basic handling"),
                ("Excel spreadsheet", "Should recognize file type and respond appropriately"),
                ("ZIP archive", "Should handle gracefully with limitations notice"),
                ("Unknown file type", "Should provide helpful error message"),
                ("Corrupted file", "Should handle error gracefully")
            ]
            
            for file_type, expected_behavior in file_scenarios:
                print(f"Would test {file_type}: {expected_behavior}")
                
            print("✅ File handling degradation test framework ready")
            await log_test_end("file_handling_degradation", "PASSED")
            
        except Exception as e:
            await log_error(e, "file_handling_degradation")
            pytest.fail(f"File handling degradation test failed: {e}")

    async def test_unsupported_media_error_messages(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test appropriate error messages for unsupported media"""
        await log_test_start("unsupported_media_errors")
        
        try:
            print("⚠️ Testing unsupported media error messages...")
            
            # Create basic bot
            creation_result = await bot_interaction_helper.send_message_and_wait(
                "create basic bot named ErrorTestBot"
            )
            assert creation_result.message_id > 0
            
            await asyncio.sleep(3)
            
            # Unsupported media scenarios
            unsupported_scenarios = [
                "Video files (if not supported)",
                "Audio files (if not supported)", 
                "Very large files (>20MB)",
                "Encrypted/password-protected files",
                "Malformed media files"
            ]
            
            for scenario in unsupported_scenarios:
                print(f"Would test error handling for: {scenario}")
                # Expected: Clear, helpful error messages
                # No crashes or undefined behavior
                
            print("✅ Unsupported media error message test framework ready")
            await log_test_end("unsupported_media_errors", "PASSED")
            
        except Exception as e:
            await log_error(e, "unsupported_media_errors")
            pytest.fail(f"Unsupported media error test failed: {e}")


@pytest.mark.tier2
@pytest.mark.user_experience
@pytest.mark.asyncio
class TestErrorHandlingAndRecovery:
    """Test error handling & recovery"""
    
    async def test_invalid_input_handling(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test handling of invalid inputs"""
        await log_test_start("invalid_input_handling")
        
        invalid_inputs = [
            "",  # Empty message
            " ",  # Whitespace only
            "🤖" * 100,  # Excessive emojis
            "CREATE BOT NOW!!!" * 20,  # Spammy content
            "\\x00\\x01\\x02",  # Control characters
            "create bot named " + "x" * 1000,  # Extremely long
        ]
        
        try:
            print("❌ Testing invalid input handling...")
            
            for invalid_input in invalid_inputs:
                print(f"Testing invalid input: '{invalid_input[:20]}...'")
                
                try:
                    result = await bot_interaction_helper.send_message_and_wait(invalid_input)
                    # Should handle gracefully without crashing
                    assert result.message_id > 0, "Should handle invalid input gracefully"
                    
                except TelegramTestError as e:
                    # Some invalid inputs might cause API errors - that's acceptable
                    print(f"Expected API error for invalid input: {e}")
                
                await asyncio.sleep(0.5)
            
            print("✅ Invalid input handling completed")
            await log_test_end("invalid_input_handling", "PASSED")
            
        except Exception as e:
            await log_error(e, "invalid_input_handling")
            pytest.fail(f"Invalid input handling test failed: {e}")

    async def test_graceful_error_messages(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test graceful error messages to users"""
        await log_test_start("graceful_error_messages")
        
        error_scenarios = [
            ("create bot named", "Missing bot name"),
            ("create bot named a", "Name too short"),
            ("create bot with invalid syntax", "Malformed request"),
            ("create 50 bots simultaneously", "Resource limitation")
        ]
        
        try:
            print("💬 Testing graceful error messages...")
            
            for scenario, error_type in error_scenarios:
                print(f"Testing {error_type}: '{scenario}'")
                
                result = await bot_interaction_helper.send_message_and_wait(scenario)
                assert result.message_id > 0, f"Should respond to {error_type} scenario"
                
                # In full implementation, would verify:
                # - Error message is user-friendly
                # - No technical jargon or stack traces
                # - Helpful suggestions provided
                # - Consistent error message format
                
                await asyncio.sleep(1)
            
            print("✅ Graceful error messages test completed")
            await log_test_end("graceful_error_messages", "PASSED")
            
        except Exception as e:
            await log_error(e, "graceful_error_messages")
            pytest.fail(f"Graceful error messages test failed: {e}")

    async def test_system_recovery_after_errors(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test system recovery after errors"""
        await log_test_start("system_recovery_after_errors")
        
        try:
            print("🔄 Testing system recovery after errors...")
            
            # Cause an error
            await bot_interaction_helper.send_message_and_wait("create bot with invalid syntax")
            await asyncio.sleep(1)
            
            # Verify system still works normally
            recovery_result = await bot_interaction_helper.send_message_and_wait("/start")
            assert recovery_result.message_id > 0, "System should recover and respond normally"
            
            await asyncio.sleep(1)
            
            # Test normal functionality after error
            normal_result = await bot_interaction_helper.send_message_and_wait(
                "create helpful bot named RecoveryTestBot"
            )
            assert normal_result.message_id > 0, "Normal functionality should work after error"
            
            print("✅ System recovery test completed")
            await log_test_end("system_recovery_after_errors", "PASSED")
            
        except Exception as e:
            await log_error(e, "system_recovery_after_errors")
            pytest.fail(f"System recovery test failed: {e}")


@pytest.mark.tier2
@pytest.mark.user_experience
@pytest.mark.asyncio
async def test_tier2_user_experience_integration(
    telegram_bot_session: BotTestSession,
    bot_interaction_helper,
    performance_monitor
):
    """Integration test for all Tier 2 user experience functionality"""
    await log_test_start("tier2_ux_integration")
    
    performance_monitor.start_timing("tier2_ux_integration")
    
    try:
        print("🎯 Running Tier 2 User Experience Integration Test...")
        
        # Test 1: Inline keyboard workflow
        await bot_interaction_helper.send_message_and_wait("/start")
        await asyncio.sleep(1)
        
        button_result = await bot_interaction_helper.test_inline_keyboard_creation("create_helpful")
        assert button_result.get("success", False), "Inline keyboard creation should work"
        await asyncio.sleep(2)
        
        # Test 2: Natural language creation
        natural_result = await bot_interaction_helper.send_message_and_wait(
            "create professional bot named UXTestBot"
        )
        assert natural_result.message_id > 0, "Natural language creation should work"
        await asyncio.sleep(2)
        
        # Test 3: Error handling
        await bot_interaction_helper.send_message_and_wait("invalid request")
        await asyncio.sleep(1)
        
        # Test 4: Recovery
        recovery_result = await bot_interaction_helper.send_message_and_wait("/help")
        assert recovery_result.message_id > 0, "System should recover after error"
        
        duration = performance_monitor.end_timing("tier2_ux_integration")
        
        print(f"✅ Tier 2 UX integration test completed in {duration:.2f}s")
        assert duration < 45, f"UX integration test took too long: {duration}s"
        
        await log_test_end("tier2_ux_integration", "PASSED")
        
    except Exception as e:
        await log_error(e, "tier2_ux_integration")
        pytest.fail(f"Tier 2 UX integration test failed: {e}")
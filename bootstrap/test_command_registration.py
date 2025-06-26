#!/usr/bin/env python3
"""
Test Command Registration

Simple test to verify the command registration matches implementation.
"""

import sys
from pathlib import Path

# Add src paths
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

main_src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(main_src_path))

def test_command_definitions():
    """Test that command definitions match implementations"""
    print("🧪 Testing Command Registration Definitions")
    print("=" * 50)
    
    try:
        from botfather_integration import BotFatherIntegration
        
        # Test echo bot commands
        echo_commands = BotFatherIntegration.get_default_commands()
        print(f"📋 Echo Bot Commands ({len(echo_commands)}):")
        for cmd in echo_commands:
            print(f"   • /{cmd['command']} - {cmd['description']}")
        
        print()
        
        # Test botmother commands  
        botmother_commands = BotFatherIntegration.get_botmother_commands()
        print(f"🤖 BotMother Commands ({len(botmother_commands)}):")
        for cmd in botmother_commands:
            print(f"   • /{cmd['command']} - {cmd['description']}")
        
        print("\n" + "=" * 50)
        
        # Verify echo bot implementation matches
        print("🔍 Checking Echo Bot Implementation:")
        echo_implemented = ['start', 'help', 'stats']
        echo_registered = [cmd['command'] for cmd in echo_commands]
        
        for cmd in echo_implemented:
            status = "✅" if cmd in echo_registered else "❌"
            print(f"   {status} /{cmd} - {'Registered' if cmd in echo_registered else 'NOT REGISTERED'}")
        
        for cmd in echo_registered:
            if cmd not in echo_implemented:
                print(f"   ⚠️  /{cmd} - REGISTERED BUT NOT IMPLEMENTED")
        
        print()
        
        # Verify botmother implementation matches
        print("🔍 Checking BotMother Implementation:")
        botmother_implemented = ['start', 'help', 'create_bot', 'list_bots', 'start_bot', 'stop_bot', 'bot_status']
        botmother_registered = [cmd['command'] for cmd in botmother_commands]
        
        for cmd in botmother_implemented:
            status = "✅" if cmd in botmother_registered else "❌"
            print(f"   {status} /{cmd} - {'Registered' if cmd in botmother_registered else 'NOT REGISTERED'}")
        
        for cmd in botmother_registered:
            if cmd not in botmother_implemented:
                print(f"   ⚠️  /{cmd} - REGISTERED BUT NOT IMPLEMENTED")
        
        # Summary
        echo_match = set(echo_implemented) == set(echo_registered)
        botmother_match = set(botmother_implemented) == set(botmother_registered)
        
        print("\n" + "=" * 50)
        print("🎯 SUMMARY:")
        print(f"Echo Bot Commands: {'✅ MATCH' if echo_match else '❌ MISMATCH'}")
        print(f"BotMother Commands: {'✅ MATCH' if botmother_match else '❌ MISMATCH'}")
        
        if echo_match and botmother_match:
            print("\n🎉 All command registrations match implementations!")
            return True
        else:
            print("\n⚠️ Command registration mismatches found!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing commands: {e}")
        return False

if __name__ == "__main__":
    success = test_command_definitions()
    if success:
        print("\n✅ Command registration test passed!")
    else:
        print("\n❌ Command registration test failed!")
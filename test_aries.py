"""
A.R.I.E.S. Test Script
Tests the core components of the new architecture
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_config():
    """Test configuration module"""
    print("Testing Configuration...")
    try:
        import config
        config.Settings.create_directories()
        system_info = config.Settings.get_system_info()
        print(f"✅ Configuration: {system_info}")
        return True
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False

def test_guardian():
    """Test Guardian module"""
    print("\nTesting Guardian...")
    try:
        from guardian import Guardian
        guardian = Guardian()
        print("✅ Guardian created successfully")
        
        # Test initialization
        if guardian.initialize("test_password"):
            print("✅ Guardian initialized successfully")
            status = guardian.get_system_status()
            print(f"✅ Guardian status: {status}")
            return True
        else:
            print("❌ Guardian initialization failed")
            return False
    except Exception as e:
        print(f"❌ Guardian test failed: {e}")
        return False

def test_memory_core():
    """Test Memory Core module"""
    print("\nTesting Memory Core...")
    try:
        from memory_core import MemoryCore
        import config
        
        memory_core = MemoryCore(config.Settings)
        print("✅ Memory Core created successfully")
        
        status = memory_core.get_system_status()
        print(f"✅ Memory Core status: {status}")
        return True
    except Exception as e:
        print(f"❌ Memory Core test failed: {e}")
        return False

def test_tool_belt():
    """Test Tool Belt module"""
    print("\nTesting Tool Belt...")
    try:
        from tool_belt import ToolBelt
        import config
        
        tool_belt = ToolBelt(config.Settings)
        print("✅ Tool Belt created successfully")
        
        status = tool_belt.get_tool_status()
        print(f"✅ Tool Belt status: {status}")
        
        tools = tool_belt.get_available_tools()
        print(f"✅ Available tools: {tools}")
        return True
    except Exception as e:
        print(f"❌ Tool Belt test failed: {e}")
        return False

def test_aries_core():
    """Test Aries Core module"""
    print("\nTesting Aries Core...")
    try:
        from aries_core import AriesCore
        from guardian import Guardian
        from memory_core import MemoryCore
        from tool_belt import ToolBelt
        import config
        
        # Create dependencies
        guardian = Guardian()
        guardian.initialize("test_password")
        memory_core = MemoryCore(config.Settings)
        tool_belt = ToolBelt(config.Settings)
        
        # Create Aries Core
        aries_core = AriesCore(
            config=config.Settings,
            guardian=guardian,
            memory_core=memory_core,
            tool_belt=tool_belt
        )
        print("✅ Aries Core created successfully")
        
        status = aries_core.get_system_status()
        print(f"✅ Aries Core status: {status}")
        return True
    except Exception as e:
        print(f"❌ Aries Core test failed: {e}")
        return False

async def test_async_components():
    """Test async components"""
    print("\nTesting Async Components...")
    try:
        from memory_core import MemoryCore
        import config
        
        memory_core = MemoryCore(config.Settings)
        
        # Test async methods
        preferences = await memory_core.get_user_preferences()
        print(f"✅ User preferences retrieved: {preferences}")
        
        return True
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("A.R.I.E.S. Architecture Test Suite")
    print("=" * 60)
    
    tests = [
        ("Configuration", test_config),
        ("Guardian", test_guardian),
        ("Memory Core", test_memory_core),
        ("Tool Belt", test_tool_belt),
        ("Aries Core", test_aries_core),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    # Test async components
    try:
        if asyncio.run(test_async_components()):
            passed += 1
        total += 1
    except Exception as e:
        print(f"❌ Async test crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! A.R.I.E.S. architecture is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

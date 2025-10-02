# A.R.I.E.S. Migration Guide
## From Jarvis to A.R.I.E.S. Architecture

This guide will help you migrate from the old Jarvis system to the new A.R.I.E.S. architecture.

## 🔄 What's Changed

### Architecture Transformation
- **Old**: Monolithic agent with direct tool access
- **New**: Layered architecture with Guardian security, Memory Core, and Tool Belt

### Security Model
- **Old**: Basic permission checking
- **New**: Multi-layered security with Guardian, credential vault, and rollback capabilities

### Memory System
- **Old**: Simple conversation memory
- **New**: Vector-based memory with ChromaDB, project manifests, and learning

### Tool Management
- **Old**: Direct tool execution
- **New**: Guardian-protected execution with pre-flight verification

## 📋 Migration Checklist

### Phase 1: Environment Setup
- [ ] Install new dependencies: `pip install -r requirements.txt`
- [ ] Set up environment variables in `.env` file
- [ ] Run configuration initialization: `python config.py`
- [ ] Test basic components: `python test_aries.py`

### Phase 2: Data Migration
- [ ] Backup existing Jarvis data
- [ ] Export any important conversation history
- [ ] Document current project configurations
- [ ] Note any custom tool configurations

### Phase 3: System Testing
- [ ] Test Guardian security features
- [ ] Verify Memory Core functionality
- [ ] Test Tool Belt operations
- [ ] Validate Aries Core integration

### Phase 4: Production Deployment
- [ ] Set production master password
- [ ] Configure production permissions
- [ ] Test with real workloads
- [ ] Monitor system performance

## 🚀 Step-by-Step Migration

### Step 1: Backup Current System
```bash
# Create backup directory
mkdir jarvis_backup_$(date +%Y%m%d)
cp -r agent.py jarvis_backup_$(date +%Y%m%d)/
cp -r tools/ jarvis_backup_$(date +%Y%m%d)/
cp -r data/ jarvis_backup_$(date +%Y%m%d)/
```

### Step 2: Install New Dependencies
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install new requirements
pip install -r requirements.txt
```

### Step 3: Configure Environment
```bash
# Create .env file with your API keys
echo "GOOGLE_API_KEY=your_key_here" > .env
echo "TAVILY_API_KEY=your_key_here" >> .env
echo "DEEPGRAM_API_KEY=your_key_here" >> .env
echo "PICOVOICE_ACCESS_KEY=your_key_here" >> .env

# Initialize configuration
python config.py
```

### Step 4: Test New Architecture
```bash
# Run test suite
python test_aries.py

# Expected output:
# ✅ Configuration: {...}
# ✅ Guardian created successfully
# ✅ Guardian initialized successfully
# ✅ Guardian status: {...}
# ✅ Memory Core created successfully
# ✅ Memory Core status: {...}
# ✅ Tool Belt created successfully
# ✅ Tool Belt status: {...}
# ✅ Aries Core created successfully
# ✅ Aries Core status: {...}
# 🎉 All tests passed! A.R.I.E.S. architecture is ready.
```

### Step 5: Start New System
```bash
# Launch A.R.I.E.S.
python main.py
```

## 🔧 Configuration Changes

### Old Jarvis Config
```python
# Old config.py
class Settings:
    llm = GoogleGenAI(model="models/gemini-1.5-pro-latest")
    embed_model = "local:BAAI/bge-small-en-v1.5"
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
```

### New A.R.I.E.S. Config
```python
# New config.py
class Settings:
    # API Keys
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    
    # System Paths
    base_path = Path("./.aries_system")
    vault_path = base_path / "vault"
    
    # Security Settings
    master_password_required = True
    auto_backup_enabled = True
```

## 🛠️ Tool Migration

### Old Tool Usage
```python
# Old way - direct execution
from tools.file_system import write_file
result = write_file("test.txt", "Hello World")
```

### New Tool Usage
```python
# New way - Guardian protected
from guardian import Guardian
guardian = Guardian()
guardian.initialize("master_password")

result = await guardian.execute_tool_safely(
    "write_file",
    {"file_path": "test.txt", "content": "Hello World"},
    "File should be created successfully"
)
```

## 🧠 Memory System Changes

### Old Memory
```python
# Old - simple conversation memory
self.memory = ChatMemoryBuffer.from_defaults(token_limit=8000)
```

### New Memory
```python
# New - vector-based memory with ChromaDB
from memory_core import MemoryCore
memory_core = MemoryCore(config)

# Store interactions
await memory_core.store_interaction(query, plan, result, timestamp)

# Search memories
memories = await memory_core.search_relevant_memories(query, intent_type)
```

## 🔒 Security Enhancements

### New Security Features
1. **Credential Vault**: Encrypted storage for passwords and tokens
2. **Permission Manager**: Granular control over all actions
3. **Pre-Flight Verification**: Automatic backups before file changes
4. **Rollback Controller**: Automatic recovery from failures

### Setting Up Security
```python
from guardian import Guardian

guardian = Guardian()
guardian.initialize("your_master_password")

# Set user permissions
permissions = {
    "auto_approve_safe": True,
    "require_confirmation_moderate": True,
    "require_confirmation_high_risk": True,
    "require_confirmation_critical": True
}
guardian.permission_manager.set_user_permissions(permissions)
```

## 📊 Performance Monitoring

### System Status
```python
# Check all component statuses
controller = AriesController(aries_core, guardian, memory_core, tool_belt)
status = controller.get_system_status()

print(f"Guardian: {status['guardian']['guardian_status']}")
print(f"Memory Core: {status['memory_core']['status']}")
print(f"Tool Belt: {status['tool_belt']['system_provisioner']}")
```

### Memory Usage
```python
# Monitor memory usage
memory_status = memory_core.get_system_status()
print(f"Knowledge items: {memory_status['collections']['knowledge']}")
print(f"Project manifests: {memory_status['collections']['projects']}")
print(f"Interactions: {memory_status['collections']['interactions']}")
```

## 🚨 Troubleshooting

### Common Migration Issues

#### 1. Import Errors
```bash
# Error: ModuleNotFoundError: No module named 'aries_core'
# Solution: Ensure all new files are in the project directory
ls -la *.py
```

#### 2. Configuration Errors
```bash
# Error: Missing required environment variables
# Solution: Check .env file and run config.py
python config.py
```

#### 3. Guardian Initialization Failures
```bash
# Error: Guardian initialization failed
# Solution: Check file permissions and try different master password
```

#### 4. ChromaDB Connection Issues
```bash
# Error: ChromaDB connection failed
# Solution: Check database path and permissions
# Ensure agent_memory_db directory exists and is writable
```

### Debug Mode
```bash
# Enable debug logging
set ARIES_DEBUG=1  # Windows
export ARIES_DEBUG=1  # Linux/Mac

# Run with verbose output
python main.py
```

## 🔄 Rollback Plan

If migration fails, you can rollback to Jarvis:

```bash
# Restore backup
cp -r jarvis_backup_YYYYMMDD/* ./

# Restore old main.py
git checkout HEAD -- main.py

# Restore old config.py
git checkout HEAD -- config.py

# Restart old system
python main.py
```

## 📚 Additional Resources

- **README.md**: Complete A.R.I.E.S. documentation
- **test_aries.py**: Component testing suite
- **config.py**: Configuration management
- **Guardian Documentation**: Security system details
- **Memory Core Guide**: Vector database usage

## 🆘 Support

If you encounter issues during migration:

1. **Check the test suite**: `python test_aries.py`
2. **Review error logs**: Look for detailed error messages
3. **Verify configuration**: Run `python config.py`
4. **Check dependencies**: Ensure all packages are installed
5. **Review file permissions**: Ensure write access to project directories

## 🎯 Migration Success Criteria

Your migration is successful when:

- [ ] All tests pass: `python test_aries.py`
- [ ] System starts without errors: `python main.py`
- [ ] Guardian security is active
- [ ] Memory Core is operational
- [ ] Tool Belt tools are accessible
- [ ] Aries Core responds to queries
- [ ] No data loss from old system

---

**Remember**: A.R.I.E.S. is designed to be safer and more intelligent than Jarvis. Take your time with the migration and test thoroughly before using in production.

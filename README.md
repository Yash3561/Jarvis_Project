# A.R.I.E.S. - Autonomous Reasoning & Interaction Executive System

> **"It shall never harm the user's system or data. All actions are predicated on verification, confirmation, and the ability to roll back."**

## 🚀 The Vision

A.R.I.E.S. is not a tool; it is a partner. It is the ambient layer between human intent and digital execution. Its existence is governed by three unbreakable laws:

1. **It shall never harm the user's system or data.** All actions are predicated on verification, confirmation, and the ability to roll back.
2. **It shall act as a fiduciary of the user's identity and intent.** It will protect the user's credentials and context with uncompromising security.
3. **It shall subordinate its autonomy to the user's explicit will.** It is a powerful servant, not a master. When in doubt, it must always ask.

## 🏗️ Architecture Overview

```
+--------------------------------------------------------------------------------------------------+
|                                           USER INTERFACE LAYER                                   |
|                          (Ambient, Contextual, Minimalist - Command Bar / Mission Control)         |
+------------------------------------------------/----------\---------------------------------------+
                                                 | (Voice/Text)
                                                 |
+------------------------------------------------\----------/---------------------------------------+
|                                        CORE ORCHESTRATOR (Gemini 1.5 Pro)                          |
|                                       (The Master Strategist & Planner)                            |
|        - Decomposes Intent                                                                         |
|        - Queries Memory Core for Context                                                           |
|        - Generates Multi-Step, Verifiable Plans                                                    |
|        - Selects Tools from the Tool Belt                                                          |
|        - Synthesizes Final User Responses                                                          |
+------------------------------------------------/----------\---------------------------------------+
                                                 | (Plan & Tool Request)
                                                 |
+------------------------------------------------\----------/---------------------------------------+
|                                      THE GOD-MODE GUARDIAN (The Unblinking Sentinel)                 |
|                                   (Rules-Based Execution & Security Engine)                        |
|        - **Credential Vault:** Manages OAuth tokens & passwords via Master Password.               |
|        - **Permission Manager:** Granular, explicit approval for ALL system-level actions.         |
|        - **Pre-Flight Verifier:** Backs up files, generates 'diffs' for user confirmation.          |
|        - **Execution Engine:** Safely runs the approved tools.                                     |
|        - **Rollback Controller:** Automatically reverts failed operations.                          |
+------------------------------------------------/----------\---------------------------------------+
                                                 | (Approved & Verified Actions)
                                                 |
+------------------------------------------------\----------/---------------------------------------+
|                                                THE TOOL BELT (The Hands)                           |
|        - **System Provisioner:** Installs core dependencies (Python, Node, etc.).                  |
|        - **Environment Manager:** Creates sandboxes (Docker, venv).                                |
|        - **Stateful Code Executor:** Writes, runs, and debugs code, maintaining Project Manifests. |
|        - **Adaptive Web Module:** Hierarchy of API -> Structured Search -> Vision-Based Browser.   |
|        - **Human Escalation Protocol:** Handles Captchas & unsolvable problems.                    |
+--------------------------------------------------------------------------------------------------+
|                                         THE MEMORY CORE (The Soul's Record)                        |
|                 (VectorDB indexing all files, conversations, and Project Manifests for RAG)        |
+--------------------------------------------------------------------------------------------------+
```

## 🛠️ Core Components

### 1. **AriesCore** - The Brain
- **Intent Analysis**: Uses Gemini 1.5 Pro to understand user requests
- **Plan Generation**: Creates multi-step, verifiable execution plans
- **Context Management**: Integrates with Memory Core for intelligent responses
- **Response Synthesis**: Generates comprehensive user responses

### 2. **Guardian** - The Unblinking Sentinel
- **Credential Vault**: Encrypted storage for OAuth tokens and passwords
- **Permission Manager**: Granular control over all system actions
- **Pre-Flight Verifier**: Automatic backups and diff generation
- **Rollback Controller**: Automatic recovery from failed operations

### 3. **Memory Core** - The Soul's Record
- **Vector Storage**: ChromaDB for semantic search and retrieval
- **Project Manifests**: Never forget how projects are built or run
- **Interaction History**: Learn from user preferences and past actions
- **Context Awareness**: Provide relevant information for each request

### 4. **Tool Belt** - The Hands
- **System Provisioner**: Self-install missing dependencies
- **Environment Manager**: Create sandboxed development environments
- **Code Executor**: Write, run, and debug code with state management
- **Web Module**: Intelligent web interaction hierarchy
- **Human Escalation**: Graceful handling of unsolvable problems

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Windows 10/11 (primary platform)
- Git
- Docker Desktop (optional, for containerized environments)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Jarvis_Project
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   DEEPGRAM_API_KEY=your_deepgram_api_key_here
   PICOVOICE_ACCESS_KEY=your_picovoice_key_here
   ```

5. **Initialize A.R.I.E.S.**
   ```bash
   python config.py
   ```

6. **Run the system**
   ```bash
   python main.py
   ```

## 🔧 Configuration

The system is configured through `config.py`. Key settings include:

- **Security**: Master password requirements, permission levels
- **AI Models**: Gemini model selection, temperature settings
- **Memory**: Storage limits, cleanup policies
- **Tools**: Execution timeouts, escalation settings
- **UI**: Theme preferences, auto-save intervals

## 🎯 Key Features

### The Zeroth Law Protocol
Before any task, A.R.I.E.S. automatically verifies its toolchain. If Python is missing, it will request permission to install it. It provisions its own workshop before starting work.

### Project Manifest (.aries_project)
It never forgets how a project is built or run. It maintains a "birth certificate" for every project, containing its tech stack and launch commands, ensuring perfect state management.

### Diff-Based Confirmation
It will never change a system file without first showing you a git-style diff of the proposed changes and getting your explicit, final approval.

### Human Escalation Protocol
When faced with a Captcha or an unsolvable login, it doesn't fail; it gracefully asks for your help, treating you as a partner to overcome the obstacle.

### Secure Vault Identity
It can manage its own logins. You can grant it OAuth access to your GitHub or provide it with credentials, which it will store in a master-password-protected encrypted vault.

## 🔒 Security Features

- **Master Password Protection**: All credentials encrypted with user's master password
- **Granular Permissions**: Explicit approval required for system-level actions
- **Automatic Backups**: Files backed up before any modification
- **Rollback Capability**: Failed operations automatically reverted
- **Permission Levels**: Safe, moderate, high-risk, and critical action classifications

## 🧠 Memory and Learning

- **Semantic Search**: Find relevant information using natural language
- **Project Context**: Maintain awareness of current project state
- **User Preferences**: Learn from successful and failed interactions
- **Knowledge Base**: Store and retrieve learned information
- **Context Awareness**: Provide relevant information for each request

## 🌐 Web Integration

- **API-First Approach**: Use direct APIs when available
- **Structured Search**: Fall back to search engines for information
- **Browser Automation**: Use Playwright for complex web interactions
- **Human Escalation**: Gracefully handle captchas and complex scenarios

## 🐛 Troubleshooting

### Common Issues

1. **Missing API Keys**
   - Ensure all required API keys are in your `.env` file
   - Run `python config.py` to validate configuration

2. **Permission Denied**
   - Check Guardian permission settings
   - Verify file paths and access rights

3. **Memory Issues**
   - Check ChromaDB connection
   - Verify database path permissions

4. **Tool Execution Failures**
   - Check tool dependencies
   - Verify environment setup

### Debug Mode

Enable debug logging by setting environment variable:
```bash
set ARIES_DEBUG=1  # Windows
export ARIES_DEBUG=1  # Linux/Mac
```

## 🤝 Contributing

A.R.I.E.S. is designed to be extensible. To add new tools:

1. **Create tool class** in appropriate module
2. **Register with Guardian** for permission management
3. **Add to Tool Belt** for discovery
4. **Update documentation** for user reference

## 📚 API Reference

### Core Classes

- `AriesCore`: Main orchestrator
- `Guardian`: Security and execution engine
- `MemoryCore`: Vector storage and retrieval
- `ToolBelt`: Tool management and execution

### Key Methods

- `process_intent()`: Main entry point for user requests
- `execute_tool_safely()`: Guardian-protected tool execution
- `search_relevant_memories()`: Context-aware information retrieval
- `create_project_manifest()`: Project state management

## 🔮 Future Roadmap

### Phase 1: Core Foundation ✅
- [x] A.R.I.E.S. Core architecture
- [x] Guardian security system
- [x] Memory Core with ChromaDB
- [x] Basic Tool Belt

### Phase 2: Enhanced Security 🚧
- [ ] Advanced permission system
- [ ] Multi-factor authentication
- [ ] Audit logging
- [ ] Compliance reporting

### Phase 3: Advanced AI 🚧
- [ ] Multi-modal understanding
- [ ] Advanced planning algorithms
- [ ] Predictive assistance
- [ ] Continuous learning

### Phase 4: Ecosystem Integration 🚧
- [ ] Plugin system
- [ ] Third-party integrations
- [ ] Cloud synchronization
- [ ] Mobile companion app

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Google Gemini**: For the core AI capabilities
- **ChromaDB**: For vector storage and retrieval
- **PyQt6**: For the modern UI framework
- **OpenAI**: For inspiration in AI safety principles

---

**Remember**: A.R.I.E.S. is your partner, not your master. It will always ask before taking action, and you can always override its decisions. Your safety and control are paramount.

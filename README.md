# Jarvis Co-Pilot — The Autonomous Developer That Actually Ships

> "Every engineer deserves a staff-level partner. Jarvis decomposes intent, scaffolds projects, writes code, runs it, and iterates — all from a single command/UI."

[![Status](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com/) 
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue)](#)
[![LLM](https://img.shields.io/badge/LLM-Gemini%201.5%20Pro-%235B8CFF)](#)
[![UI](https://img.shields.io/badge/UI-PyQt6-%2300B894)](#)

## 🚀 What Jarvis Does

Jarvis is a fully functional autonomous software engineer that can:
- **Project Mode**: Turn product intent into running software in minutes
- **Chat Mode**: Smart assistant with browser, desktop, file system, and terminal tools
- **Voice-First UX**: Wake word detection, real-time transcription, and TTS responses
- **Follow-up Iteration**: Continue working on active projects with natural language

## 🎯 Why This Matters

- **Velocity**: Turn product intent into running software in minutes, not sprints
- **Reliability**: Deterministic playbooks and UI event loop ensure consistent results
- **Focus**: Engineers stay in the loop for strategy and review — Jarvis handles the rest
- **Voice-First**: Natural interaction through wake word detection and speech

## 🚀 Quickstart

1) Clone and setup
```bash
git clone <your-repo-url>
cd Jarvis_Project
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2) Add `.env` file
```env
GOOGLE_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
PICOVOICE_ACCESS_KEY=your_picovoice_key
```

3) Run
```bash
python main.py
```

## 📖 Usage Examples

**Project Mode:**
- "Build a React dashboard that shows crypto prices with live charts."
- Jarvis selects a playbook, creates workspace, writes code, installs deps, starts servers, opens browser.

**Follow-up Iteration:**
- "Change the primary color to teal and add dark mode."
- Jarvis recognizes the active workspace and applies modifications.

**Chat Mode:**
- Ask questions, request code snippets, browse websites, or control desktop.

## 🏗️ Architecture

```
User ↔ UI (PyQt6 + WebView)
         ↳ Agent (LlamaIndex ReAct) ↔ Tools (filesystem, terminal, browser, desktop)
         ↳ Controller (Project Mode) ↔ Playbooks → Writes code → Runs servers → Opens preview
```

## 🛠️ Core Components

### 1. **UI Layer** - Voice-First Interface
- PyQt6 desktop window with WebEngine frontend
- Wake word detection ("Jarvis")
- Real-time audio transcription (Deepgram)
- Text-to-speech responses
- Live terminal output and project status

### 2. **Agent** - The Brain
- LlamaIndex ReAct agent with curated toolbelt
- Intelligent query routing (CHAT vs PROJECT)
- Tool selection and execution
- Response formatting and synthesis

### 3. **Controller** - Project Orchestration
- Playbook-driven project generation
- Multi-file code planning and implementation
- Dependency management and environment setup
- Development server launch and browser preview

### 4. **Tools** - The Hands
- **Terminal**: Command execution, workspace management
- **Browser**: Web automation, navigation, content extraction
- **Desktop**: Screen analysis, mouse/keyboard control
- **File System**: File operations, image analysis
- **Memory**: Experience storage and recall

## 📁 Project Structure

```
Jarvis_Project/
├── main.py                 # Entry point
├── agent.py               # LlamaIndex ReAct agent
├── ui.py                  # PyQt6 UI with voice/chat
├── main_controller.py     # Project orchestration
├── config.py              # Environment configuration
├── tools/                 # Function tools
│   ├── terminal.py        # Terminal operations
│   ├── browser.py         # Web automation
│   ├── desktop.py         # Desktop control
│   ├── file_system.py     # File operations
│   └── ...
├── components/            # Audio components
│   ├── audio_transcriber.py
│   ├── speaker.py
│   └── wake_word_detector.py
├── data/playbooks/        # Project templates
│   ├── react.md
│   ├── python_flask.md
│   ├── python_pygame.md
│   └── ...
└── frontend/              # Web UI assets
    ├── index.html
    ├── main.js
    └── style.css
```

## 🎮 Playbooks

Jarvis uses playbooks to scaffold projects deterministically:

- **React**: Modern React apps with Vite, TypeScript, Tailwind
- **Python Flask**: Web APIs with SQLAlchemy, JWT auth
- **Python Pygame**: Games with physics, sprites, sound
- **HTML/CSS**: Static sites with modern styling
- **Go CLI**: Command-line tools with Cobra
- **R Scripts**: Data analysis with tidyverse

Each playbook defines:
- Setup commands (environment creation)
- Dependency installation
- Launch commands (dev servers)
- Default ports

## 🔧 Configuration

Key settings in `config.py`:
- **API Keys**: Gemini, Tavily, Deepgram, Picovoice
- **Model Settings**: Temperature, embedding model
- **UI Preferences**: Theme, auto-save intervals

## 🚀 Key Features

### The Zeroth Law Protocol
Before any task, Jarvis automatically verifies its toolchain. If Python is missing, it will request permission to install it. It provisions its own workshop before starting work.

### Project Manifest (.aries_project)
It never forgets how a project is built or run. It maintains a "birth certificate" for every project, containing its tech stack and launch commands, ensuring perfect state management.

### Follow-up Continuity
When you say "change that button to blue," Jarvis knows you're referring to the active project and applies the modification intelligently.

### Voice-First Interaction
- Wake word: "Jarvis" (configurable)
- Real-time transcription with Deepgram
- Natural conversation flow
- TTS responses with context awareness

## 🐛 Troubleshooting

### Common Issues

1. **Missing API Keys**
   - Ensure all required API keys are in your `.env` file
   - Run `python config.py` to validate configuration

2. **Permission Denied**
   - Check file paths and access rights
   - Ensure workspace directory is writable

3. **Audio Issues**
   - Check microphone permissions
   - Verify Deepgram API key
   - Test wake word detection

4. **Tool Execution Failures**
   - Check tool dependencies
   - Verify environment setup

### Debug Mode

Enable debug logging:
```bash
set ARIES_DEBUG=1  # Windows
export ARIES_DEBUG=1  # Linux/Mac
```

## 🤝 Contributing

Jarvis is designed to be extensible. To add new tools:

1. **Create tool function** in appropriate module
2. **Register with agent** for discovery
3. **Add to toolbelt** for routing
4. **Update documentation** for user reference

## 📚 API Reference

### Core Classes
- `AIAgent`: Main agent with tool routing
- `ChatWindow`: PyQt6 UI with voice integration
- `MainController`: Project orchestration
- `ManagedTerminal`: Terminal management

### Key Methods
- `ask()`: Main entry point for user requests
- `execute_project()`: Autonomous project creation
- `execute_follow_up()`: Project modification
- `process_user_query()`: Query triage and routing

## 🔮 Roadmap

### Phase 1: Core Foundation ✅
- [x] Voice-first UI with PyQt6
- [x] LlamaIndex ReAct agent
- [x] Project orchestration with playbooks
- [x] Follow-up iteration system
- [x] Comprehensive tool suite

### Phase 2: Enhanced UX 🚧
- [ ] Better error handling and recovery
- [ ] Improved voice recognition accuracy
- [ ] Enhanced project templates
- [ ] Multi-language support

### Phase 3: Advanced Features 🚧
- [ ] Plugin system for custom tools
- [ ] Cloud synchronization
- [ ] Team collaboration features
- [ ] Advanced project analytics

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **Google Gemini**: For the core AI capabilities
- **LlamaIndex**: For the agent framework
- **PyQt6**: For the modern UI framework
- **Deepgram**: For real-time transcription
- **Picovoice**: For wake word detection

---

**Ready to build?** Clone the repo, set up your `.env` file, and run `python main.py`. Jarvis is waiting to help you ship software faster than ever before.

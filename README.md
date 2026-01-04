# Autonomous Coding Agent

A long-running autonomous coding agent powered by the Claude Agent SDK. Builds complete applications over multiple sessions using a three-agent pattern with support for multiple technology stacks.

> Based on [leonvanzyl's autonomous-coding](https://github.com/leonvanzyl/autonomous-coding)

## Features

- **Multi-session development** - Maintains progress across context windows via SQLite database and git
- **Three agent types** - Initializer, Enhancement, and Coding agents for different phases
- **Multiple tech stacks** - Node.js/React (default) or Laravel with React/Vue/Blade
- **Post-build enhancements** - Add new features to existing projects without starting over
- **Browser automation testing** - Playwright MCP for end-to-end verification
- **Security sandboxing** - Restricted filesystem and command allowlist

---

## Prerequisites

### Claude Code CLI (Required)

**macOS / Linux:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://claude.ai/install.ps1 | iex
```

### Authentication

- **Claude Pro/Max Subscription** - Use `claude login` to authenticate (recommended)
- **Anthropic API Key** - Pay-per-use from https://console.anthropic.com/

### For Laravel Projects (Optional)

- PHP 8.2+
- Composer
- Node.js 18+

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/jacob8919/autonomous-coding.git
cd autonomous-coding
```

### 2. Run the Start Script

**Windows:**
```cmd
start.bat
```

**macOS / Linux:**
```bash
./start.sh
```

The start script will:
1. Check if Claude CLI is installed
2. Check authentication (prompt for `claude login` if needed)
3. Create Python virtual environment
4. Install dependencies
5. Launch the main menu

### 3. Main Menu Options

```
[1] Create new project          - Start fresh with AI-assisted spec generation
[2] Continue existing project   - Resume work on a previous project
[3] Add features to existing    - Add new features after initial build
[q] Quit
```

---

## Technology Stacks

When creating a new project, you can choose from:

| Stack | Frontend | Backend | Database |
|-------|----------|---------|----------|
| **Node.js + React** (default) | React | Express | SQLite |
| **Laravel + React** | React/Inertia | Laravel | SQLite |
| **Laravel + Vue** | Vue/Inertia | Laravel | SQLite |
| **Laravel + Blade** | Blade/Alpine.js | Laravel | SQLite |

Laravel stacks include automatic setup via Composer and Laravel Breeze, plus Laravel Boost MCP integration.

---

## How It Works

### Three-Agent Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS CODING WORKFLOW                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [1] INITIALIZER AGENT (First Session)                          │
│      • Reads app_spec.txt                                        │
│      • Creates features in SQLite database                       │
│      • Sets up project structure                                 │
│      • Initializes git repository                                │
│                          ↓                                       │
│  [2] CODING AGENT (Subsequent Sessions)                          │
│      • Gets next feature from database                           │
│      • Implements feature                                        │
│      • Tests with browser automation                             │
│      • Marks feature as passing                                  │
│      • Commits progress                                          │
│                          ↓                                       │
│  [3] ENHANCEMENT AGENT (When adding features)                    │
│      • Reads enhancement_spec.txt                                │
│      • Checks for duplicate features                             │
│      • Adds new features to database                             │
│      • Returns to Coding Agent                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Session Management

- Each session runs with a fresh context window
- Progress persisted via `features.db` (SQLite) and git commits
- Agent auto-continues between sessions (3 second delay)
- Press `Ctrl+C` to pause; run start script again to resume

### Adding Features After Build

Already built a project but need more features? Use menu option **[3]**:

1. Select "Add features to existing project"
2. Choose your project
3. Claude Code launches with `/add-features` command
4. Describe the new features you want
5. Choose priority (before or after pending features)
6. Exit and select "Continue existing project"
7. Enhancement Agent adds features, then Coding Agent implements them

---

## MCP Servers

The agent uses Model Context Protocol (MCP) servers for extended capabilities:

### Playwright (Browser Automation)
- Navigate, click, type, screenshot
- Form filling and element interaction
- Console and network monitoring
- End-to-end feature verification

### Features (Database Management)
- `feature_get_stats` - Progress statistics
- `feature_get_next` - Next feature to implement
- `feature_mark_passing` - Mark feature complete
- `feature_create_bulk` - Add multiple features
- `feature_search` - Find existing features

### Laravel Boost (Laravel Projects Only)
- `database-schema` - Inspect database structure
- `list-routes` - View application routes
- `tinker` - Run Tinker commands
- `search-docs` - Query Laravel documentation
- `last-error` - Get recent errors
- And 11 more tools...

---

## Project Structure

```
autonomous-coding/
├── start.bat / start.sh          # Platform start scripts
├── start.py                      # Main menu and project management
├── autonomous_agent_demo.py      # Agent entry point
├── agent.py                      # Session orchestration
├── client.py                     # Claude SDK configuration
├── security.py                   # Command allowlist
├── prompts.py                    # Prompt loading
├── progress.py                   # Progress tracking
├── api/
│   ├── database.py               # SQLAlchemy models
│   └── migration.py              # Schema migrations
├── mcp_server/
│   └── feature_mcp.py            # Feature management MCP
├── stacks/                       # Laravel stack configs
│   ├── laravel-react.md
│   ├── laravel-vue.md
│   └── laravel-blade.md
├── .claude/
│   ├── commands/
│   │   ├── create-spec.md        # /create-spec command
│   │   └── add-features.md       # /add-features command
│   └── templates/                # Agent prompt templates
└── generations/                  # Generated projects
```

### Generated Project Structure

```
generations/my_project/
├── features.db                   # SQLite database (source of truth)
├── prompts/
│   ├── app_spec.txt              # Application specification
│   ├── initializer_prompt.md     # First session prompt
│   ├── coding_prompt.md          # Coding session prompt
│   └── enhancement_spec.txt      # (If adding features)
├── .claude/
│   └── mcp_servers.json          # Project MCP config (Laravel)
├── init.sh                       # Environment setup
├── claude-progress.txt           # Session notes
└── [application files]           # Generated code
```

---

## Timing Expectations

| Phase | Duration |
|-------|----------|
| **Initialization** | 10-20+ minutes (generating features) |
| **Each coding session** | 5-15 minutes per feature |
| **Full application** | Hours across multiple sessions |

The feature count determines scope. Typical ranges:
- Simple apps: 20-50 features
- Medium apps: 100-150 features
- Complex apps: 200+ features

---

## Security Model

Defense-in-depth approach (see `security.py`):

1. **OS-level Sandbox** - Bash commands run isolated
2. **Filesystem Restrictions** - Operations restricted to project directory
3. **Command Allowlist** - Only permitted commands execute:

| Category | Commands |
|----------|----------|
| File inspection | `ls`, `cat`, `head`, `tail`, `wc`, `grep` |
| Node.js | `npm`, `npx`, `node` |
| PHP/Laravel | `php`, `composer` |
| Version control | `git` |
| Process mgmt | `ps`, `lsof`, `sleep`, `pkill` |

---

## Configuration

### N8N Webhook (Optional)

Send progress notifications to N8N:

```bash
# .env file
PROGRESS_N8N_WEBHOOK_URL=https://your-n8n.com/webhook/id
```

Payload:
```json
{
  "event": "test_progress",
  "passing": 45,
  "total": 200,
  "percentage": 22.5,
  "project": "my_project"
}
```

---

## Customization

### Application Specification
- Use `/create-spec` for interactive creation
- Or edit `prompts/app_spec.txt` directly

### Adding Commands
- Edit `ALLOWED_COMMANDS` in `security.py`

### Custom MCP Servers
- Add to `.claude/mcp_servers.json` in project directory

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Claude CLI not found" | Install CLI per Prerequisites section |
| "Not authenticated" | Run `claude login` |
| "Appears to hang on first run" | Normal - generating features takes time. Watch for `[Tool: ...]` output |
| "Command blocked" | Add to `ALLOWED_COMMANDS` in `security.py` |
| "Permission denied for MCP tool" | Add tool to `client.py` allowed list |

---

## License

Internal Anthropic use.

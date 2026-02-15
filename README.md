# Termical 📅

Stay in your terminal, stay on top of your day. Termical pipes your Google Calendar events through AI analysis to deliver concise summaries, prep notes, and auto-extracted to-do lists directly to your terminal.

## Features

- 🔐 **Secure Authentication**: OAuth 2.0 for Google Calendar, API key storage in system keyring
- 📊 **Smart Summaries**: AI-generated 1-2 sentence prep summaries for each activity
- ✅ **Action Item Extraction**: Automatically extract tasks and assignees from activity notes
- 💾 **Local Caching**: PostgreSQL database for fast, offline-capable access
- 🎨 **Beautiful CLI**: Rich formatting with tables, progress bars, and colors
- ⚡ **Fast Performance**: Sub-200ms response for cached data

## Tech Stack

- **Python 3.11+** - Modern Python with type hints
- **Typer + Rich** - Beautiful CLI interface
- **PostgreSQL 16** - Reliable data persistence (via Docker)
- **SQLAlchemy** - Powerful ORM for database operations
- **Google Calendar API** - Calendar integration with OAuth 2.0
- **OpenAI (gpt-4o-mini)** - AI-powered summarization
- **Keyring** - Secure credential storage

## Installation

### Prerequisites

1. **Python 3.11 or higher**

   ```bash
   python3 --version
   ```

2. **Docker** (for PostgreSQL)

   ```bash
   docker --version
   ```

3. **Google Cloud Project** with Calendar API enabled
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project (or select existing)
   - Enable the **Google Calendar API**
   - Create **OAuth 2.0 Credentials**:
     - Application type: **Desktop app**
     - Download the credentials as `credentials.json`

4. **OpenAI API Key**
   - Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

### Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd termical
   ```

2. **Create virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the package**

   ```bash
   pip install -e .
   ```

4. **Start PostgreSQL**

   ```bash
   docker-compose up -d
   ```

5. **Run setup wizard**

   ```bash
   termical setup
   ```

   The wizard will guide you through:
   - PostgreSQL connection details
   - OpenAI API key (stored securely)
   - Google Calendar OAuth setup

6. **Place credentials.json**

   Copy your Google OAuth credentials to:

   ```
   ~/.termical/credentials.json
   ```

## Usage

### View Today's Activities

```bash
termical today
```

**Output:**

```
                      Today's Activities (3 total)
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Time      ┃ Title               ┃ Duration ┃ Attendees ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━┩
│ 09:00 AM  │ Team Standup        │ 30m      │ 5         │
│ 11:00 AM  │ Design Review       │ 1h       │ 3         │
│ 02:00 PM  │ Sprint Planning     │ 2h       │ 8         │
└───────────┴─────────────────────┴──────────┴───────────┘
```

### Show AI Summaries (Verbose Mode)

```bash
termical today --verbose
```

**Output:**

```
                      Today's Activities (3 total)
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Time      ┃ Title               ┃ Duration ┃ Attendees ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━┩
│ 09:00 AM  │ Team Standup        │ 30m      │ 5         │
│           │ Daily sync to       │          │           │
│           │ discuss blockers    │          │           │
└───────────┴─────────────────────┴──────────┴───────────┘
```

### Check Version

```bash
termical --version
```

### Get Help

```bash
termical --help
termical today --help
```

## Configuration

Configuration is stored in `~/.termical/`:

```
~/.termical/
├── config.toml           # Database and app settings
├── credentials.json      # Google OAuth client secrets
└── token.json           # Google OAuth tokens (auto-generated)
```

### config.toml Example

```toml
[database]
host = "localhost"
port = 5432
name = "termical"
user = "termical_user"
password = "termical_pass"
```

**Note:** OpenAI API key is stored securely in your system keyring (macOS Keychain, Windows Credential Manager, or Linux Secret Service).

## Architecture

### Data Flow

1. User runs `termical today`
2. CLI checks PostgreSQL for cached data
3. If stale/missing:
   - Fetch events from Google Calendar API
   - Generate AI summaries via OpenAI API
   - Extract action items
   - Store in PostgreSQL
4. Display formatted output

### Database Schema

**activities** table:

- `event_id` (PK) - Google Calendar event ID
- `title` - Activity title
- `start_time` / `end_time` - UTC timestamps
- `description` - Raw activity notes
- `attendees` (JSONB) - List of attendees
- `ai_summary` - Generated prep summary
- `action_items` (JSONB) - Extracted tasks
- `last_synced` - Last refresh timestamp

## Troubleshooting

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart the database
docker-compose restart

# View logs
docker-compose logs postgres
```

### Google OAuth Issues

1. **"credentials.json not found"**
   - Place the file in `~/.termical/credentials.json`

2. **"Permission denied"**
   - Ensure Google Calendar API is enabled in Cloud Console
   - Check OAuth consent screen is configured

3. **Token expired**
   - Delete `~/.termical/token.json`
   - Re-run `termical setup`

### OpenAI API Errors

- **Rate limit**: Wait and retry
- **Invalid API key**: Run `termical setup` to reconfigure
- **Timeout**: Check internet connection

### Performance

- **Warm reads** (cached): < 200ms
- **Cold reads** (API + AI): 3-10 seconds depending on activity count

## Development

### Project Structure

```
src/termical/
├── __init__.py
├── cli.py              # CLI entry point
├── config.py           # Configuration & secrets
├── database.py         # Database connection
├── models.py           # SQLAlchemy models
├── calendar_client.py  # Google Calendar integration
├── ai_client.py        # OpenAI integration
├── sync.py             # Data synchronization
└── commands/
    ├── setup.py        # Setup wizard
    └── today.py        # Today command
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests (coming soon)
pytest
```

### Code Quality

```bash
# Format code
black src/

# Lint code
ruff check src/
```

## Roadmap

- [x] Core foundation (setup, calendar, today command)
- [ ] `actions` command - View and manage action items
- [ ] `search` command - Full-text search across activities
- [ ] Date range support (e.g., `termical week`)
- [ ] Interactive TUI mode
- [ ] Export to markdown/PDF
- [ ] Calendar event creation
- [ ] Multiple calendar support
- [ ] Team sharing features

## Security

- ✅ API keys stored in OS keyring (never in files)
- ✅ OAuth tokens encrypted at rest
- ✅ `.gitignore` excludes all credentials
- ✅ No sensitive data in logs
- ✅ PostgreSQL password never logged

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or contributions:

- 🐛 [Report a bug](https://github.com/your-repo/issues)
- 💡 [Request a feature](https://github.com/your-repo/issues)
- 📖 [Read the docs](https://github.com/your-repo/wiki)

---

**Built with ❤️ for developers who have too many activities**

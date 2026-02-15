# Quick Start Guide 🚀

Get started with Termical in 5 minutes!

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] Docker installed (for PostgreSQL)
- [ ] Google Cloud project created
- [ ] Google Calendar API enabled
- [ ] OAuth credentials downloaded as `credentials.json`
- [ ] OpenAI API key ready

## Installation Steps

### 1. Set Up the Project

```bash
cd termical
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 2. Start Database

```bash
docker-compose up -d
```

Verify it's running:

```bash
docker-compose ps
```

### 3. Run Setup Wizard

```bash
termical setup
```

Follow the prompts:

1. **Database Configuration**
   - Host: `localhost` (default)
   - Port: `5432` (default)
   - Database: `termical` (default)
   - User: `termical_user` (default)
   - Password: `termical_pass` (from docker-compose.yml)

2. **OpenAI API Key**
   - Paste your API key when prompted
   - It will be stored securely in system keyring

3. **Google Calendar**
   - Place `credentials.json` in `~/.termical/`
   - Answer "Yes" when asked if file is ready

### 4. Test It Out!

```bash
termical today
```

First run will:

- Open browser for Google OAuth
- Fetch today's activities
- Generate AI summaries
- Display beautiful table

### 5. Try Verbose Mode

```bash
termical today --verbose
```

See AI-generated prep summaries for each activity!

## Common Issues

### Docker not running

```bash
# Start Docker Desktop (macOS/Windows)
# Or start docker service (Linux)
sudo systemctl start docker
```

### Can't find module

```bash
# Make sure you're in the venv
source venv/bin/activate

# Reinstall if needed
pip install -e .
```

### OAuth browser doesn't open

- Check if port 8080 is available
- Try running setup again
- Manually visit the URL shown in terminal

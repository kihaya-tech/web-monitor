# Website Monitor Bot

**English** | [日本語](README.ja.md)

---

A Python-based bot that monitors multiple websites and sends Discord notifications when changes are detected. Runs automatically via GitHub Actions.

## Features

- Monitor multiple websites simultaneously
- Automatic change detection (SHA-256 hash-based)
- Real-time notifications via Discord Webhook
- Automated execution via GitHub Actions (default: hourly)
- Secure configuration (sensitive data stored in GitHub Secrets)
- Support for partial monitoring using CSS selectors

## Project Structure

```
monitor-web/
├── .github/
│   └── workflows/
│       └── monitor.yml       # GitHub Actions workflow
├── src/
│   └── monitor.py            # Main monitoring script
├── config/
│   └── sites.json            # Site configuration file
├── data/
│   ├── .gitkeep
│   └── *.json                # State files (auto-generated)
├── requirements.txt          # Python dependencies
├── .gitignore
└── README.md
```

## Setup

### 1. Repository Setup

1. Push this repository to GitHub
2. Enable GitHub Actions in repository settings
3. Configure Workflow permissions (important)

#### Workflow Permissions Configuration

Repository Settings → Actions → General → Workflow permissions:
- Select **"Read and write permissions"**
- Check "Allow GitHub Actions to create and approve pull requests" (optional)

Without this configuration, state file commits will fail.

### 2. Discord Webhook Setup

1. Discord Server Settings → Integrations → Webhooks
2. Create a new webhook and copy the URL
3. Go to GitHub repository Settings → Secrets and variables → Actions
4. Click "New repository secret"
5. Name: `DISCORD_WEBHOOK_URL`
6. Value: Your webhook URL

### 3. Configure Monitoring Sites

Edit `config/sites.json` to add sites you want to monitor:

```json
[
  {
    "name": "Example Site",
    "url": "https://example.com",
    "selector": "body",
    "check_interval": "hourly"
  },
  {
    "name": "Another Site",
    "url": "https://example.org/page",
    "selector": "main .content",
    "check_interval": "hourly"
  }
]
```

#### Configuration Parameters

##### `name` (string, required)
- Site identifier name
- Used in Discord notification title
- Used for state file name generation (non-alphanumeric chars converted to `_`)

##### `url` (string, required)
- Website URL to monitor
- Both HTTP/HTTPS supported (HTTPS recommended)
- Can include query parameters and fragment identifiers
- Example: `https://example.com/page?id=123#section`

##### `selector` (string, optional)
- CSS selector to narrow down monitoring target
- Default: `"body"` (entire page)
- Follows BeautifulSoup4 CSS Selector syntax
- Complex selectors are supported

**Selector examples:**
```json
"selector": "body"                          // Entire page
"selector": ".content"                      // class="content"
"selector": "#main-content"                 // id="main-content"
"selector": "article.post"                  // <article class="post">
"selector": "div.container > p"             // Direct child elements
"selector": ".news-list li:first-child"     // Pseudo-classes
"selector": "[data-id='123']"               // Attribute selectors
```

##### `check_interval` (string, currently unused)
- **Not implemented in current version**
- Reserved field for future extension
- Currently, all sites are checked simultaneously
- Actual check frequency is controlled GLOBALLY by GitHub Actions cron schedule

**Note:** The `check_interval` field can be specified in JSON, but is not currently used in the implementation. All sites are checked simultaneously according to the schedule set in `.github/workflows/monitor.yml`.

**Anticipated future values (not implemented):**
- `"realtime"` - Check as frequently as possible
- `"hourly"` - Every hour
- `"daily"` - Once per day
- `"custom"` - Custom schedule

### 4. Workflow Schedule Configuration

Configure check frequency in `.github/workflows/monitor.yml`. This determines the global execution frequency.

```yaml
on:
  schedule:
    - cron: '0 * * * *'  # Every hour
```

#### Cron Syntax Details

```
┌───────────── Minute (0 - 59)
│ ┌───────────── Hour (0 - 23)
│ │ ┌───────────── Day of month (1 - 31)
│ │ │ ┌───────────── Month (1 - 12)
│ │ │ │ ┌───────────── Day of week (0 - 7) (0 and 7 are Sunday)
│ │ │ │ │
* * * * *
```

#### Common Patterns

```yaml
# Every hour
- cron: '0 * * * *'

# Every 30 minutes
- cron: '*/30 * * * *'

# Every 15 minutes
- cron: '*/15 * * * *'

# Every 6 hours (0, 6, 12, 18)
- cron: '0 */6 * * *'

# Daily at 9 AM (UTC)
- cron: '0 9 * * *'

# Daily at midnight (UTC)
- cron: '0 0 * * *'

# Weekdays at 9 AM (UTC)
- cron: '0 9 * * 1-5'

# Monday and Friday at noon (UTC)
- cron: '0 12 * * 1,5'

# First day of each month at midnight (UTC)
- cron: '0 0 1 * *'
```

**Notes:**
- GitHub Actions cron runs in UTC (Coordinated Universal Time)
- GitHub Actions scheduled executions may be delayed by a few minutes
- High frequency execution (less than 5 minutes) is not recommended due to GitHub Actions constraints

#### Trigger Conditions Details

`monitor.yml` has multiple trigger conditions configured:

```yaml
on:
  # Scheduled execution (main execution method)
  schedule:
    - cron: '0 * * * *'

  # Manual execution (for testing)
  workflow_dispatch:

  # Execution on code changes (for development testing)
  push:
    branches:
      - main
    paths:
      - 'src/**'
      - 'config/**'
      - '.github/workflows/monitor.yml'
```

### Time Management Architecture: Cron vs JSON

**Important Design Understanding:**

This system has **two levels** of time management design, but **only one is currently implemented**.

#### Level 1: Global Schedule (Implemented)
Cron configuration in `.github/workflows/monitor.yml`
- **Role**: When GitHub Actions executes the script
- **Scope**: Applied to all sites
- **Control method**: Cron schedule
- **Example**: `cron: '0 * * * *'` → Script runs every hour

#### Level 2: Per-Site Schedule (Not Implemented)
`check_interval` field in `config/sites.json`
- **Role**: Check each site on individual schedules
- **Scope**: Configurable per site
- **Current status**: Field exists but not implemented
- **Future implementation idea**: Record last check time and skip based on interval

#### Current Behavior

```
GitHub Actions (cron: hourly)
  ↓ Execute script
  ↓
monitor.py starts
  ↓
Check all sites simultaneously
  ├─ Check Site 1
  ├─ Check Site 2
  └─ Check Site 3
```

All sites are checked at the **same timing**. The `check_interval` field value (such as `"hourly"`) is ignored.

#### Future Implementation Concept (Reference)

Behavior image if per-site scheduling is implemented:

```python
# Pseudo code (not implemented)
for site in sites:
    if should_check(site, last_check_time, site['check_interval']):
        check_site(site)
    else:
        skip_site(site)
```

In this case, cron runs frequently, and each site is checked according to its individual `check_interval`.

#### Recommended Usage

**In the current version:**
1. Want to check all sites at the same frequency → Configure cron only
2. Want to check specific sites more frequently → Create multiple workflows
3. Different frequency per site → Not supported (future feature)

**Example: Achieve different frequencies with multiple workflows**

`.github/workflows/monitor-hourly.yml`:
```yaml
name: Hourly Monitor
on:
  schedule:
    - cron: '0 * * * *'
env:
  CONFIG_PATH: config/sites-hourly.json
```

`.github/workflows/monitor-daily.yml`:
```yaml
name: Daily Monitor
on:
  schedule:
    - cron: '0 9 * * *'
env:
  CONFIG_PATH: config/sites-daily.json
```

## Usage

### Automatic Execution

The bot runs automatically on the configured schedule via GitHub Actions.

### Manual Execution

From the Actions tab in your GitHub repository:
1. Select "Website Monitor" workflow
2. Click "Run workflow"
3. Select branch (usually main)
4. Click "Run workflow" again

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable
export DISCORD_WEBHOOK_URL="your_webhook_url_here"

# Run the monitor
python src/monitor.py

# Use custom configuration file
export CONFIG_PATH="config/custom-sites.json"
export STATE_DIR="data/custom"
python src/monitor.py
```

Windows:
```cmd
pip install -r requirements.txt
set DISCORD_WEBHOOK_URL=your_webhook_url_here
python src/monitor.py
```

## How It Works

### Execution Flow

1. **Initialization**
   - Load `DISCORD_WEBHOOK_URL` from environment variable
   - Load monitoring site list from `config/sites.json`
   - Check/create `data/` directory

2. **Check Each Site**
   ```
   for each site in config:
     ├─ Fetch content via HTTP request
     ├─ Parse HTML with BeautifulSoup4
     ├─ Extract target element using CSS selector
     ├─ Get text content only
     ├─ Calculate SHA-256 hash value
     ├─ Load previous state from data/{site_name}.json
     ├─ Compare hash values
     ├─ If change detected → Send Discord notification
     └─ Save current state to data/{site_name}.json
   ```

3. **State Persistence**
   - GitHub Actions automatically commits changes in `data/` directory
   - Previous state can be referenced on next execution

### Change Detection Mechanism

#### SHA-256 Hash-Based Detection
Hash entire content with SHA-256 and detect changes by comparing with previous hash:

**Advantages:**
- Fast (O(1) comparison)
- Lightweight (stores only 64-character string)
- Detects HTML tag changes

**Disadvantages:**
- Detected even with single character change (ads changes, etc.)
- Doesn't show what changed (doesn't get diff)

#### First Run Behavior

```
First run:
├─ State file doesn't exist
├─ Calculate hash value
├─ Save to state file
└─ Don't send notification (initialization only)

Second run onwards:
├─ Load previous state file
├─ Compare with current hash value
├─ Send notification if changes detected
└─ Save new state
```

### State File Structure

`data/{sanitized_site_name}.json`:
```json
{
  "hash": "a3f5e8c...",
  "last_checked": "2025-10-30T12:34:56.789Z",
  "url": "https://example.com",
  "previous_hash": "b4e6f9d..."
}
```

**Field descriptions:**
- `hash`: SHA-256 hash of current content
- `last_checked`: Last check timestamp (ISO 8601 format, UTC)
- `url`: Monitored URL
- `previous_hash`: Previous hash (only when change detected)

## Discord Notification Format

Notifications are sent as Embeds containing the following information:

```
🔔 Change Detected: {site_name}

Site: {site_name}
URL: {url}
Previous Hash: `abc123...`
New Hash: `def456...`

Timestamp: 2025-10-30T12:34:56.789Z
Footer: Website Monitor Bot
```

### Notification Customization

You can modify notification content by editing the `_send_discord_notification` method in `src/monitor.py`:

```python
embed = {
    "title": f"🔔 Change Detected: {site_name}",  # Title
    "url": url,                                    # Clickable URL
    "color": 3447003,                              # Color (decimal RGB)
    "fields": [                                    # Field array
        {
            "name": "Site",
            "value": site_name,
            "inline": True
        },
        # ... additional fields
    ],
    "timestamp": datetime.utcnow().isoformat(),
    "footer": {
        "text": "Website Monitor Bot"
    }
}
```

**Color values:**
- Blue (default): `3447003`
- Green: `3066993`
- Yellow: `16776960`
- Orange: `15105570`
- Red: `15158332`

## Security

### Secure Design

1. **Webhook URL Protection**
   - Encrypted storage in GitHub Secrets
   - Not output to logs
   - Safe even with public repository

2. **State File Safety**
   - Contains no sensitive information (only hash, URL, timestamp)
   - Safe to commit in public repository

3. **Environment Variable Usage**
   ```python
   self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
   ```
   No hardcoded credentials exist

### GitHub Secrets Management

- Repository Secrets: Used for single repository only
- Environment Secrets: Used for specific environments (production, staging, etc.)
- Organization Secrets: Shared across organization

This project uses Repository Secrets.

## Advanced Configuration

### Using Multiple Configuration Files

Specify custom configuration file via environment variable:

```yaml
# .github/workflows/monitor-custom.yml
env:
  CONFIG_PATH: config/production-sites.json
  STATE_DIR: data/production
```

### Timeout Configuration

In `src/monitor.py` `_fetch_content` method:
```python
response = requests.get(url, headers=headers, timeout=30)  # 30 seconds
```

Adjust this value if site response is slow.

### User-Agent Configuration

Default:
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (compatible; WebsiteMonitorBot/1.0)'
}
```

Some sites block certain User-Agents, so modify as needed.

### Adding Custom Headers

```python
headers = {
    'User-Agent': 'Mozilla/5.0 ...',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    # Add as needed
}
```

## Dependencies

`requirements.txt`:
```
requests==2.32.3      # HTTP client
beautifulsoup4==4.12.3  # HTML parsing
```

### Version Updates

```bash
# Check for latest versions
pip list --outdated

# Update requirements.txt
pip install --upgrade requests beautifulsoup4
pip freeze > requirements.txt
```

## Troubleshooting

### Webhook Not Working

**Diagnosis:**
```bash
# Test locally
export DISCORD_WEBHOOK_URL="your_webhook_url"
python src/monitor.py
```

**Check:**
- Discord Webhook URL is correctly set in Secrets
- Webhook hasn't been deleted
- Discord channel access permissions

### No Notifications

**Cause 1**: First run
- First run only initializes state (no notification)

**Cause 2**: No site changes
- Wait for actual changes to occur
- Test: Modify `config/sites.json` and push

**Cause 3**: Errors in GitHub Actions logs
- Check logs in Actions tab

**Cause 4**: Site not accessible
- Test same URL locally

### Permission Errors

```
! [remote rejected] main -> main (refusing to allow a GitHub App to create or update workflow `.github/workflows/monitor.yml` without `workflows` permission)
```

**Solution:**
- Settings → Actions → General → Workflow permissions
- Select "Read and write permissions"

### Rate Limiting

Running too frequently on GitHub Actions may hit rate limits:

**Limits:**
- Scheduled execution: 5-minute minimum interval recommended
- Concurrent execution: Default 20 jobs max
- Execution time: Max 6 hours per job

**GitHub Actions free tier:**
- Public repo: Unlimited
- Private repo: 2000 minutes/month (free account)

### Site Fetch Failures

**Error message:**
```
Error fetching https://example.com: HTTPError 403 Forbidden
```

**Causes and solutions:**

1. **Bot protection (403/429)**
   - Change User-Agent
   - Reduce request frequency
   - Site may be unmonitorable

2. **Timeout (Timeout)**
   - Increase `timeout` value (default 30 seconds)
   ```python
   response = requests.get(url, headers=headers, timeout=60)
   ```

3. **DNS resolution failure**
   - Check URL spelling
   - Site may be down

4. **SSL certificate error**
   ```python
   response = requests.get(url, headers=headers, verify=False)  # Not recommended
   ```

## Performance Optimization

### Parallel Execution

Currently runs sequentially. Consider parallelization for monitoring many sites:

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(self.check_site, self.sites)
```

### Cache Utilization

For sites that don't change frequently, use HTTP cache headers:

```python
headers = {
    'Cache-Control': 'max-age=3600',
    'If-Modified-Since': last_modified,
}
```

## Limitations

1. **JavaScript-dependent sites**
   - Cannot fetch SPA or JavaScript-rendered content
   - Solution: Selenium/Puppeteer integration needed (not implemented)

2. **Sites requiring authentication**
   - Cannot monitor pages requiring login
   - Solution: Session management implementation needed (not implemented)

3. **Diff details**
   - Doesn't get details of what changed
   - Solution: difflib library integration needed (not implemented)

4. **CAPTCHA-protected sites**
   - Cannot monitor CAPTCHA-protected sites

5. **Rate limiting**
   - May get IP blocked if access frequency is too high
   - Recommended: 5+ minute interval per site

## Future Enhancements

1. **Per-site scheduling**
   - Implement `check_interval` field
   - Check each site at different frequencies

2. **Detailed diff detection**
   - Get HTML diffs and notify
   - Use `difflib` library

3. **Multiple notification destinations**
   - Support Slack, Email, LINE, Telegram
   - Select notification destination in config file

4. **JavaScript support**
   - Selenium/Puppeteer integration
   - Monitor SPA sites

5. **Screenshot feature**
   - Save before/after screenshots
   - Attach images to Discord

6. **Web dashboard**
   - Visualize monitoring status
   - View history

## Contributing

Pull requests are welcome!

### Development Environment Setup

```bash
# Clone repository
git clone https://github.com/yourusername/monitor-web.git
cd monitor-web

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Additional development packages
pip install pytest black flake8 mypy
```

### Testing

```bash
# Run unit tests (not implemented)
pytest tests/

# Code formatting
black src/

# Lint
flake8 src/

# Type checking
mypy src/
```

## License

MIT License

## Support

- Bug reports: Please post to GitHub Issues
- Questions: Please post to GitHub Discussions
- Feature requests: Please post to GitHub Issues

## Changelog

### v1.0.0 (Initial Release)
- Basic monitoring functionality
- Discord notifications
- GitHub Actions integration
- SHA-256 hash-based change detection
- CSS selector support

#!/usr/bin/env python3
"""
Website Monitoring Bot
Monitors multiple websites for changes and sends Discord notifications.
"""

import os
import sys
import json
import hashlib
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup


class WebsiteMonitor:
    """Monitor websites for changes and send notifications."""

    def __init__(self, config_path: str, state_dir: str):
        """
        Initialize the website monitor.

        Args:
            config_path: Path to the sites configuration JSON file
            state_dir: Directory to store state files
        """
        self.config_path = Path(config_path)
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Load Discord webhook URL from environment
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
        if not self.discord_webhook:
            raise ValueError("DISCORD_WEBHOOK_URL environment variable is not set")

        # Load sites configuration
        self.sites = self._load_config()

    def _load_config(self) -> List[Dict]:
        """Load sites configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_state_file(self, site_name: str) -> Path:
        """Get the state file path for a site."""
        safe_name = "".join(c if c.isalnum() else "_" for c in site_name)
        return self.state_dir / f"{safe_name}.json"

    def _load_state(self, site_name: str) -> Optional[Dict]:
        """Load the previous state for a site."""
        state_file = self._get_state_file(site_name)
        if not state_file.exists():
            return None

        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None

    def _save_state(self, site_name: str, state: Dict):
        """Save the current state for a site."""
        state_file = self._get_state_file(site_name)
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def _fetch_content(self, url: str, selector: str = "body") -> Optional[str]:
        """
        Fetch and extract content from a URL.

        Args:
            url: The URL to fetch
            selector: CSS selector to extract specific content

        Returns:
            The extracted content or None if fetch failed
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; WebsiteMonitorBot/1.0)'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract content using selector
            element = soup.select_one(selector)
            if element:
                content = element.get_text(strip=True, separator='\n')
            else:
                content = soup.get_text(strip=True, separator='\n')

            return content

        except Exception as e:
            print(f"Error fetching {url}: {e}", file=sys.stderr)
            return None

    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _send_discord_notification(self, site_name: str, url: str, changes: Dict):
        """
        Send a Discord notification about changes.

        Args:
            site_name: Name of the monitored site
            url: URL of the site
            changes: Dictionary containing change information
        """
        try:
            embed = {
                "title": f"🔔 Change Detected: {site_name}",
                "url": url,
                "color": 3447003,  # Blue color
                "fields": [
                    {
                        "name": "Site",
                        "value": site_name,
                        "inline": True
                    },
                    {
                        "name": "URL",
                        "value": url,
                        "inline": False
                    },
                    {
                        "name": "Previous Hash",
                        "value": f"`{changes['old_hash'][:16]}...`",
                        "inline": True
                    },
                    {
                        "name": "New Hash",
                        "value": f"`{changes['new_hash'][:16]}...`",
                        "inline": True
                    }
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "Website Monitor Bot"
                }
            }

            payload = {
                "embeds": [embed]
            }

            response = requests.post(
                self.discord_webhook,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            print(f"✓ Notification sent for {site_name}")

        except Exception as e:
            print(f"Error sending Discord notification: {e}", file=sys.stderr)

    def check_site(self, site: Dict) -> bool:
        """
        Check a single site for changes.

        Args:
            site: Site configuration dictionary

        Returns:
            True if changes were detected, False otherwise
        """
        name = site.get('name', 'Unknown')
        url = site.get('url')
        selector = site.get('selector', 'body')

        if not url:
            print(f"⚠ Skipping {name}: No URL specified", file=sys.stderr)
            return False

        print(f"Checking {name}...")

        # Fetch current content
        content = self._fetch_content(url, selector)
        if content is None:
            print(f"⚠ Failed to fetch content from {name}")
            return False

        # Calculate hash
        current_hash = self._calculate_hash(content)

        # Load previous state
        previous_state = self._load_state(name)

        # Check for changes
        if previous_state is None:
            print(f"📝 First check for {name} - saving initial state")
            self._save_state(name, {
                'hash': current_hash,
                'last_checked': datetime.utcnow().isoformat(),
                'url': url
            })
            return False

        previous_hash = previous_state.get('hash')

        if current_hash != previous_hash:
            print(f"🔔 Change detected in {name}!")

            # Send notification
            self._send_discord_notification(name, url, {
                'old_hash': previous_hash,
                'new_hash': current_hash
            })

            # Update state
            self._save_state(name, {
                'hash': current_hash,
                'last_checked': datetime.utcnow().isoformat(),
                'url': url,
                'previous_hash': previous_hash
            })

            return True
        else:
            print(f"✓ No changes in {name}")

            # Update last checked time
            self._save_state(name, {
                'hash': current_hash,
                'last_checked': datetime.utcnow().isoformat(),
                'url': url
            })

            return False

    def run(self):
        """Run the monitoring check for all sites."""
        print(f"Starting monitoring check at {datetime.utcnow().isoformat()}")
        print(f"Monitoring {len(self.sites)} site(s)")
        print("-" * 50)

        changes_detected = 0

        for site in self.sites:
            try:
                if self.check_site(site):
                    changes_detected += 1
            except Exception as e:
                print(f"Error checking {site.get('name', 'Unknown')}: {e}", file=sys.stderr)

        print("-" * 50)
        print(f"Monitoring check completed")
        print(f"Changes detected: {changes_detected}/{len(self.sites)}")


def main():
    """Main entry point."""
    # Get paths from environment or use defaults
    config_path = os.getenv('CONFIG_PATH', 'config/sites.json')
    state_dir = os.getenv('STATE_DIR', 'data')

    try:
        monitor = WebsiteMonitor(config_path, state_dir)
        monitor.run()
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

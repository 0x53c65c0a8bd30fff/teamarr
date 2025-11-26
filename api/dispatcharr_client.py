"""
Dispatcharr API Client with JIT Authentication

Provides just-in-time authentication with automatic token refresh
and session management for Dispatcharr API integration.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import requests

logger = logging.getLogger(__name__)


class DispatcharrAuth:
    """
    Just-In-Time authentication handler for Dispatcharr API.

    Features:
    - Automatic token caching per URL/username combination
    - Proactive token refresh before expiry
    - Automatic re-authentication on token failure
    - Thread-safe session management

    Usage:
        auth = DispatcharrAuth("http://localhost:9191", "admin", "password")
        token = auth.get_token()
        response = auth.request("GET", "/api/epg/sources/")
    """

    # Class-level session storage for multi-instance support
    _sessions: Dict[str, Dict] = {}

    # Token refresh buffer (refresh this many minutes before expiry)
    TOKEN_REFRESH_BUFFER_MINUTES = 1

    # Token validity duration (Dispatcharr default is ~5 minutes)
    TOKEN_VALIDITY_MINUTES = 5

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        timeout: int = 30
    ):
        """
        Initialize Dispatcharr authentication handler.

        Args:
            url: Base URL of Dispatcharr instance (e.g., "http://localhost:9191")
            username: Dispatcharr username
            password: Dispatcharr password
            timeout: Request timeout in seconds (default: 30)
        """
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self._session_key = f"{self.url}_{self.username}"

        # Initialize session if not exists
        if self._session_key not in self._sessions:
            self._sessions[self._session_key] = {
                "access_token": None,
                "refresh_token": None,
                "token_expiry": None
            }

    @property
    def _session(self) -> Dict:
        """Get current session data"""
        return self._sessions[self._session_key]

    def _is_token_valid(self) -> bool:
        """Check if current access token is still valid"""
        if not self._session["access_token"]:
            return False
        if not self._session["token_expiry"]:
            return False
        return datetime.now() < self._session["token_expiry"]

    def _refresh_token(self) -> bool:
        """
        Attempt to refresh the access token using refresh token.

        Returns:
            True if refresh successful, False otherwise
        """
        if not self._session["refresh_token"]:
            return False

        try:
            response = requests.post(
                f"{self.url}/api/accounts/token/refresh/",
                json={"refresh": self._session["refresh_token"]},
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                self._session["access_token"] = data.get("access")
                self._session["token_expiry"] = (
                    datetime.now() +
                    timedelta(minutes=self.TOKEN_VALIDITY_MINUTES - self.TOKEN_REFRESH_BUFFER_MINUTES)
                )
                logger.debug("Dispatcharr token refreshed successfully")
                return True
            else:
                logger.warning(f"Token refresh failed: {response.status_code}")
                return False

        except requests.RequestException as e:
            logger.warning(f"Token refresh request failed: {e}")
            return False

    def _authenticate(self) -> bool:
        """
        Perform full authentication with username/password.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            logger.debug(f"Authenticating to {self.url} as {self.username}")

            response = requests.post(
                f"{self.url}/api/accounts/token/",
                json={
                    "username": self.username,
                    "password": self.password
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                self._session["access_token"] = data.get("access")
                self._session["refresh_token"] = data.get("refresh")
                self._session["token_expiry"] = (
                    datetime.now() +
                    timedelta(minutes=self.TOKEN_VALIDITY_MINUTES - self.TOKEN_REFRESH_BUFFER_MINUTES)
                )
                logger.info("Dispatcharr authentication successful")
                return True

            elif response.status_code == 401:
                logger.error("Authentication failed: Invalid credentials")
                return False

            elif response.status_code == 403:
                logger.error(f"Authentication failed: Forbidden - {response.text}")
                return False

            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False

        except requests.RequestException as e:
            logger.error(f"Authentication request failed: {e}")
            return False

    def get_token(self) -> Optional[str]:
        """
        Get a valid access token, authenticating if necessary.

        Returns:
            Valid access token or None if authentication fails
        """
        # Check if current token is valid
        if self._is_token_valid():
            return self._session["access_token"]

        # Try to refresh token
        if self._session["refresh_token"] and self._refresh_token():
            return self._session["access_token"]

        # Full authentication
        if self._authenticate():
            return self._session["access_token"]

        return None

    def clear_session(self):
        """Clear cached tokens for this session"""
        self._session["access_token"] = None
        self._session["refresh_token"] = None
        self._session["token_expiry"] = None

    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        retry_on_401: bool = True
    ) -> Optional[requests.Response]:
        """
        Make an authenticated request to Dispatcharr API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (e.g., "/api/epg/sources/")
            data: JSON data for POST/PATCH requests
            retry_on_401: Whether to retry with fresh token on 401

        Returns:
            Response object or None if request fails
        """
        token = self.get_token()
        if not token:
            logger.error("Failed to obtain authentication token")
            return None

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        full_url = f"{self.url}{endpoint}"

        try:
            if method.upper() == "GET":
                response = requests.get(full_url, headers=headers, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(full_url, headers=headers, json=data, timeout=self.timeout)
            elif method.upper() == "PATCH":
                response = requests.patch(full_url, headers=headers, json=data, timeout=self.timeout)
            elif method.upper() == "DELETE":
                response = requests.delete(full_url, headers=headers, timeout=self.timeout)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None

            # Handle 401 with retry
            if response.status_code == 401 and retry_on_401:
                logger.info("Received 401, clearing session and retrying...")
                self.clear_session()
                return self.request(method, endpoint, data, retry_on_401=False)

            return response

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    # Convenience methods
    def get(self, endpoint: str) -> Optional[requests.Response]:
        """Make authenticated GET request"""
        return self.request("GET", endpoint)

    def post(self, endpoint: str, data: Dict = None) -> Optional[requests.Response]:
        """Make authenticated POST request"""
        return self.request("POST", endpoint, data)


class EPGManager:
    """
    High-level EPG management interface for Dispatcharr.

    Usage:
        manager = EPGManager("http://localhost:9191", "admin", "password")
        sources = manager.list_sources()
        manager.refresh(21)
    """

    def __init__(self, url: str, username: str, password: str):
        self.auth = DispatcharrAuth(url, username, password)

    def list_sources(self, include_dummy: bool = True) -> List[Dict]:
        """
        List all EPG sources.

        Args:
            include_dummy: Whether to include dummy sources (default: True)

        Returns:
            List of EPG source dictionaries
        """
        response = self.auth.get("/api/epg/sources/")
        if not response or response.status_code != 200:
            return []

        sources = response.json()

        if not include_dummy:
            sources = [s for s in sources if s.get("source_type") != "dummy"]

        return sources

    def get_source(self, epg_id: int) -> Optional[Dict]:
        """
        Get a specific EPG source by ID.

        Args:
            epg_id: EPG source ID

        Returns:
            EPG source dict or None if not found
        """
        response = self.auth.get(f"/api/epg/sources/{epg_id}/")
        if response and response.status_code == 200:
            return response.json()
        return None

    def find_by_name(self, name: str, exact: bool = False) -> Optional[Dict]:
        """
        Find EPG source by name.

        Args:
            name: Name to search for
            exact: If True, require exact match; otherwise partial match

        Returns:
            First matching EPG source or None
        """
        sources = self.list_sources()

        for source in sources:
            source_name = source.get("name", "")
            if exact:
                if source_name == name:
                    return source
            else:
                if name.lower() in source_name.lower():
                    return source

        return None

    def refresh(self, epg_id: int) -> Dict[str, Any]:
        """
        Trigger refresh for a single EPG source.

        Args:
            epg_id: EPG source ID to refresh

        Returns:
            Result dict with "success" and "message" keys
        """
        response = self.auth.post("/api/epg/import/", {"id": epg_id})

        if not response:
            return {"success": False, "message": "Request failed - could not connect"}

        if response.status_code == 202:
            return {"success": True, "message": "EPG refresh initiated"}
        elif response.status_code == 400:
            return {"success": False, "message": "Cannot refresh dummy EPG source"}
        elif response.status_code == 401:
            return {"success": False, "message": "Authentication failed"}
        elif response.status_code == 404:
            return {"success": False, "message": "EPG source not found"}
        else:
            try:
                msg = response.json().get("message", f"HTTP {response.status_code}")
            except:
                msg = f"HTTP {response.status_code}"
            return {"success": False, "message": msg}

    def refresh_by_name(self, name: str) -> Dict[str, Any]:
        """
        Refresh EPG source by name (partial match).

        Args:
            name: Name to search for

        Returns:
            Result dict with "success" and "message" keys
        """
        source = self.find_by_name(name)
        if not source:
            return {"success": False, "message": f"No EPG source found matching '{name}'"}

        return self.refresh(source["id"])

    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Dispatcharr.

        Returns:
            Result dict with "success", "message", and optionally "sources" keys
        """
        try:
            token = self.auth.get_token()
            if not token:
                return {
                    "success": False,
                    "message": "Authentication failed - check credentials"
                }

            sources = self.list_sources()
            return {
                "success": True,
                "message": f"Connected successfully. Found {len(sources)} EPG source(s).",
                "sources": sources
            }

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "Connection failed - check URL and ensure Dispatcharr is running"
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "Connection timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }


class M3UManager:
    """
    M3U account and stream management for Dispatcharr.

    Usage:
        manager = M3UManager("http://localhost:9191", "admin", "password")
        accounts = manager.list_m3u_accounts()
        groups = manager.list_channel_groups(search="NFL")
        streams = manager.list_streams(group_name="NFL Game Pass 🏈")
    """

    def __init__(self, url: str, username: str, password: str):
        self.auth = DispatcharrAuth(url, username, password)
        self._groups_cache: Optional[List[Dict]] = None

    def list_m3u_accounts(self) -> List[Dict]:
        """List all M3U accounts."""
        response = self.auth.get("/api/m3u/accounts/")
        if not response or response.status_code != 200:
            logger.error(f"Failed to list M3U accounts: {response.status_code if response else 'No response'}")
            return []
        return response.json()

    def list_channel_groups(self, search: Optional[str] = None) -> List[Dict]:
        """
        List channel groups, optionally filtered by name.

        Args:
            search: Filter by group name (case-insensitive substring match)

        Returns:
            List of group dicts with id, name, m3u_accounts
        """
        response = self.auth.get("/api/channels/groups/")
        if not response or response.status_code != 200:
            logger.error(f"Failed to list channel groups: {response.status_code if response else 'No response'}")
            return []

        groups = response.json()
        self._groups_cache = groups  # Cache for name lookups

        if search:
            search_lower = search.lower()
            groups = [g for g in groups if search_lower in g.get('name', '').lower()]

        return groups

    def get_group_name(self, group_id: int) -> Optional[str]:
        """Get exact group name by ID (needed for stream filtering)."""
        if self._groups_cache is None:
            self.list_channel_groups()

        group = next((g for g in (self._groups_cache or []) if g.get('id') == group_id), None)
        return group.get('name') if group else None

    def list_streams(
        self,
        group_name: Optional[str] = None,
        group_id: Optional[int] = None,
        account_id: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        List streams from Dispatcharr.

        Filter by group using exact group_name (preferred) or group_id (requires lookup).
        The API's channel_group_name filter requires exact match including emoji.

        Args:
            group_name: Exact group name (e.g., "NFL Game Pass 🏈")
            group_id: Group ID (will lookup name if group_name not provided)
            account_id: Filter by M3U account ID
            limit: Maximum streams to return

        Returns:
            List of stream dicts with id, name, url, channel_group, tvg_id, etc.
        """
        import urllib.parse

        # Resolve group_name from group_id if needed
        if group_name is None and group_id is not None:
            group_name = self.get_group_name(group_id)

        # Build query params
        params = ["page_size=1000"]
        if group_name:
            params.append(f"channel_group_name={urllib.parse.quote(group_name)}")
        if account_id is not None:
            params.append(f"m3u_account={account_id}")

        response = self.auth.get(f"/api/channels/streams/?{'&'.join(params)}")
        if not response or response.status_code != 200:
            logger.error(f"Failed to list streams: {response.status_code if response else 'No response'}")
            return []

        data = response.json()
        streams = data.get('results', []) if isinstance(data, dict) else data

        if limit:
            streams = streams[:limit]

        return streams

    def get_group_with_streams(self, group_id: int, stream_limit: int = 50) -> Optional[Dict]:
        """
        Get group info with its streams for UI preview.

        Returns:
            {"group": {...}, "streams": [...], "total_streams": int}
        """
        if self._groups_cache is None:
            self.list_channel_groups()

        group = next((g for g in (self._groups_cache or []) if g.get('id') == group_id), None)
        if not group:
            return None

        streams = self.list_streams(group_name=group.get('name'))

        return {
            "group": group,
            "streams": streams[:stream_limit],
            "total_streams": len(streams)
        }

    def refresh_m3u_account(self, account_id: int) -> Dict[str, Any]:
        """Trigger M3U refresh for an account (async, returns immediately)."""
        response = self.auth.post(f"/api/m3u/refresh/{account_id}/")

        if not response:
            return {"success": False, "message": "Request failed"}

        if response.status_code in (200, 202):
            return {"success": True, "message": "M3U refresh initiated"}
        return {"success": False, "message": f"HTTP {response.status_code}"}

    def get_account(self, account_id: int) -> Optional[Dict]:
        """Get a single M3U account by ID."""
        response = self.auth.get(f"/api/m3u/accounts/{account_id}/")
        if not response or response.status_code != 200:
            return None
        return response.json()

    def wait_for_refresh(
        self,
        account_id: int,
        timeout: int = 120,
        poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Trigger M3U refresh and wait for completion.

        This ensures streams are updated before we fetch them for EPG generation.
        Uses polling to detect when refresh completes by monitoring updated_at.

        Args:
            account_id: M3U account ID to refresh
            timeout: Maximum seconds to wait (default: 120)
            poll_interval: Seconds between status checks (default: 2)

        Returns:
            Result dict with:
            - success: bool
            - message: str
            - duration: float (seconds taken)
            - account: dict (final account state if successful)
        """
        import time

        # Get current state
        before = self.get_account(account_id)
        if not before:
            return {"success": False, "message": f"Account {account_id} not found"}

        before_updated = before.get('updated_at')

        # Trigger refresh
        trigger_result = self.refresh_m3u_account(account_id)
        if not trigger_result.get('success'):
            return trigger_result

        # Poll until updated_at changes or status indicates completion/error
        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(poll_interval)

            current = self.get_account(account_id)
            if not current:
                continue

            current_status = current.get('status', '')
            current_updated = current.get('updated_at')

            # Check if refresh completed (updated_at changed)
            if current_updated != before_updated:
                duration = time.time() - start_time
                if current_status == 'success':
                    return {
                        "success": True,
                        "message": current.get('last_message', 'Refresh completed'),
                        "duration": duration,
                        "account": current
                    }
                elif current_status == 'error':
                    return {
                        "success": False,
                        "message": current.get('last_message', 'Refresh failed'),
                        "duration": duration,
                        "account": current
                    }

            # Check for error status even if updated_at hasn't changed
            if current_status == 'error':
                return {
                    "success": False,
                    "message": current.get('last_message', 'Refresh failed'),
                    "duration": time.time() - start_time
                }

        # Timeout
        return {
            "success": False,
            "message": f"Refresh timed out after {timeout} seconds",
            "duration": timeout
        }

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Dispatcharr."""
        try:
            if not self.auth.get_token():
                return {"success": False, "message": "Authentication failed"}

            accounts = self.list_m3u_accounts()
            return {
                "success": True,
                "message": f"Connected. Found {len(accounts)} M3U account(s).",
                "accounts": accounts
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

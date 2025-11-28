"""
Shared League Configuration Module

Centralizes league configuration lookups used by both TeamMatcher and EventMatcher.
Eliminates duplicate code and provides a single source of truth for league mappings.
"""

from typing import Optional, Dict, Tuple, Callable

from utils.logger import get_logger

logger = get_logger(__name__)


# Fallback league configurations when database is not available
# Maps league_code -> {sport, api_path}
LEAGUE_FALLBACKS: Dict[str, Dict[str, str]] = {
    # Pro US leagues
    'nfl': {'sport': 'football', 'api_path': 'football/nfl'},
    'nba': {'sport': 'basketball', 'api_path': 'basketball/nba'},
    'nhl': {'sport': 'hockey', 'api_path': 'hockey/nhl'},
    'mlb': {'sport': 'baseball', 'api_path': 'baseball/mlb'},
    'mls': {'sport': 'soccer', 'api_path': 'soccer/usa.1'},

    # European soccer
    'epl': {'sport': 'soccer', 'api_path': 'soccer/eng.1'},
    'laliga': {'sport': 'soccer', 'api_path': 'soccer/esp.1'},
    'bundesliga': {'sport': 'soccer', 'api_path': 'soccer/ger.1'},
    'seriea': {'sport': 'soccer', 'api_path': 'soccer/ita.1'},
    'ligue1': {'sport': 'soccer', 'api_path': 'soccer/fra.1'},

    # College sports
    'ncaam': {'sport': 'basketball', 'api_path': 'basketball/mens-college-basketball'},
    'ncaaw': {'sport': 'basketball', 'api_path': 'basketball/womens-college-basketball'},
    'ncaaf': {'sport': 'football', 'api_path': 'football/college-football'},
}

# College leagues that need conference-based team fetching
COLLEGE_LEAGUES = {
    'ncaam', 'ncaaw', 'ncaaf',
    'mens-college-basketball', 'womens-college-basketball', 'college-football'
}


def get_league_config(
    league_code: str,
    db_connection_func: Optional[Callable] = None,
    cache: Optional[Dict[str, Dict]] = None
) -> Optional[Dict[str, str]]:
    """
    Get league configuration (sport, api_path) from database or fallback.

    Args:
        league_code: League code (e.g., 'nfl', 'epl', 'ncaam')
        db_connection_func: Function that returns a database connection.
                           If None, uses fallback mappings only.
        cache: Optional cache dict to store results. If provided, will
               check cache first and store results for future lookups.

    Returns:
        Dict with 'sport' and 'api_path' keys, or None if not found.
        Example: {'sport': 'football', 'api_path': 'football/nfl'}
    """
    league_lower = league_code.lower()

    # Check cache first
    if cache is not None and league_lower in cache:
        return cache[league_lower]

    # Try database lookup
    if db_connection_func:
        try:
            conn = db_connection_func()
            cursor = conn.cursor()
            result = cursor.execute(
                "SELECT sport, api_path FROM league_config WHERE league_code = ?",
                (league_lower,)
            ).fetchone()
            conn.close()

            if result:
                config = {'sport': result[0], 'api_path': result[1]}
                if cache is not None:
                    cache[league_lower] = config
                return config
        except Exception as e:
            logger.error(f"Error fetching league config for {league_code}: {e}")

    # Fall back to hardcoded mappings
    fallback = LEAGUE_FALLBACKS.get(league_lower)
    if fallback:
        if cache is not None:
            cache[league_lower] = fallback
        return fallback

    logger.warning(f"No league config found for {league_code}")
    return None


def parse_api_path(api_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse api_path into (sport, league) tuple.

    Args:
        api_path: API path string (e.g., 'football/nfl', 'basketball/mens-college-basketball')

    Returns:
        Tuple of (sport, league) or (None, None) if invalid format.
        Example: ('football', 'nfl')
    """
    if not api_path:
        return None, None

    parts = api_path.split('/')
    if len(parts) == 2:
        return parts[0], parts[1]

    logger.error(f"Invalid api_path format: {api_path}")
    return None, None


def is_college_league(league_code: str) -> bool:
    """
    Check if a league is a college league (requires conference-based team fetching).

    Args:
        league_code: League code to check

    Returns:
        True if college league, False otherwise
    """
    return league_code.lower() in COLLEGE_LEAGUES or 'college' in league_code.lower()

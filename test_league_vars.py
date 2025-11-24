"""
Test what league variables actually populate
"""
import sys
sys.path.insert(0, '/srv/dev-disk-by-uuid-c332869f-d034-472c-a641-ccf1f28e52d6/scratch/teamarr')

from epg.template_engine import TemplateEngine

engine = TemplateEngine()

print("Testing LEAGUE variables")
print("=" * 70)

# Test with typical team_config from database
test_configs = [
    {'league': 'nba', 'league_name': 'NBA', 'sport': 'basketball'},
    {'league': 'nhl', 'league_name': 'NHL', 'sport': 'hockey'},
    {'league': 'nfl', 'league_name': 'NFL', 'sport': 'football'},
]

for config in test_configs:
    # Mock game
    mock_game = {
        'home_team': {'id': '1', 'name': 'Test Team', 'abbrev': 'TST'},
        'away_team': {'id': '2', 'name': 'Opponent', 'abbrev': 'OPP'},
        'venue': {'name': 'Stadium', 'city': 'City', 'state': 'ST'},
        'status': {'name': 'Pre-Game'},
        'date': '2025-11-23T00:00:00Z'
    }
    
    # Build variables
    vars_dict = engine._build_variables_from_game_context(
        game=mock_game,
        team_config=config,
        team_stats={},
        opponent_stats={},
        h2h={},
        streaks={},
        head_coach='',
        player_leaders={},
        epg_timezone='America/New_York'
    )
    
    league = vars_dict.get('league', 'MISSING')
    league_id = vars_dict.get('league_id', 'MISSING')
    league_name = vars_dict.get('league_name', 'MISSING')
    
    print(f"\nteam_config.league = '{config['league']}'")
    print(f"team_config.league_name = '{config.get('league_name', 'N/A')}'")
    print(f"  → {{league}}      = '{league}'")
    print(f"  → {{league_id}}   = '{league_id}'")
    print(f"  → {{league_name}} = '{league_name}'")

print("\n" + "=" * 70)
print("EXPLANATION:")
print("{league} = uppercase (NBA, NHL, NFL) - uses league_name or league.upper()")
print("{league_id} = lowercase (nba, nhl, nfl) - uses league.lower()")
print("\nFor channel IDs use: {team_name_pascal}.{league_id}")

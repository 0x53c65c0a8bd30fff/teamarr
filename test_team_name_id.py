"""
Test team_name_id variable for channel IDs
"""
import sys
sys.path.insert(0, '/srv/dev-disk-by-uuid-c332869f-d034-472c-a641-ccf1f28e52d6/scratch/teamarr')

from epg.template_engine import TemplateEngine

engine = TemplateEngine()

print("Testing team_name_id variable (PascalCase for channel IDs)")
print("=" * 70)

# Test cases from user's request
test_teams = [
    ('Anaheim Ducks', 'nhl', 'AnaheimDucks.nhl'),
    ('Detroit Red Wings', 'nhl', 'DetroitRedWings.nhl'),
    ('Chicago Blackhawks', 'nhl', 'ChicagoBlackhawks.nhl'),
    ('Detroit Pistons', 'nba', 'DetroitPistons.nba'),
    ('Los Angeles Lakers', 'nba', 'LosAngelesLakers.nba'),
    ('New York Yankees', 'mlb', 'NewYorkYankees.mlb'),
    ('Tampa Bay Buccaneers', 'nfl', 'TampaBayBuccaneers.nfl')
]

all_passed = True

for team_name, league, expected_channel in test_teams:
    # Create mock game data
    mock_game = {
        'name': f'{team_name} vs Opponent',
        'home_team': {'id': '1', 'name': team_name, 'abbrev': 'XXX'},
        'away_team': {'id': '2', 'name': 'Opponent', 'abbrev': 'OPP'},
        'venue': {'name': 'Stadium', 'city': 'City', 'state': 'ST'},
        'status': {'name': 'Pre-Game'},
        'date': '2025-11-23T00:00:00Z'
    }
    
    # Build variables
    vars_dict = engine._build_variables_from_game_context(
        game=mock_game,
        team_config={'espn_team_id': '1', 'team_name': team_name, 'league': league},
        team_stats={},
        opponent_stats={},
        h2h={},
        streaks={},
        head_coach='',
        player_leaders={},
        epg_timezone='America/New_York'
    )
    
    team_name_id = vars_dict.get('team_name_id', 'MISSING')
    league_var = vars_dict.get('league', league)
    channel_id = f"{team_name_id}.{league_var}"
    
    passed = (channel_id == expected_channel)
    status = '✓' if passed else '✗'
    
    print(f"\n{status} {team_name}:")
    print(f"   team_name_id: {team_name_id}")
    print(f"   league:       {league_var}")
    print(f"   Channel ID:   {channel_id}")
    print(f"   Expected:     {expected_channel}")
    
    if not passed:
        all_passed = False
        print(f"   ERROR: Mismatch!")

print("\n" + "=" * 70)
if all_passed:
    print("✓ ALL TESTS PASSED")
    print("\nUsage in templates:")
    print("  Channel ID: {team_name_id}.{league}")
    print("  Example:    DetroitRedWings.nhl")
else:
    print("✗ SOME TESTS FAILED")

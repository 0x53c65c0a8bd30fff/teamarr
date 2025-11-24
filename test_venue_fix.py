"""
Test that venue variables work correctly for future games
"""
import sys
sys.path.insert(0, '/srv/dev-disk-by-uuid-c332869f-d034-472c-a641-ccf1f28e52d6/scratch/teamarr')

from epg.template_engine import TemplateEngine

engine = TemplateEngine()

print("Testing venue variable extraction with different ESPN API formats")
print("=" * 70)

# Test 1: Future game format (address nested)
print("\nTest 1: Future game format (from schedule API)")
print("-" * 70)
future_game = {
    'home_team': {'id': '22', 'name': 'Arizona Cardinals', 'abbrev': 'ARI'},
    'away_team': {'id': '27', 'name': 'Tampa Bay Buccaneers', 'abbrev': 'TB'},
    'venue': {
        'fullName': 'Raymond James Stadium',
        'address': {
            'city': 'Tampa',
            'state': 'FL',
            'zipCode': '33607',
            'country': 'USA'
        }
    },
    'status': {'name': 'Pre-Game'},
    'date': '2025-11-30T18:00Z'
}

vars_dict = engine._build_variables_from_game_context(
    game=future_game,
    team_config={'espn_team_id': '22', 'team_name': 'Arizona Cardinals', 'league': 'nfl'},
    team_stats={},
    opponent_stats={},
    h2h={},
    streaks={},
    head_coach='',
    player_leaders={},
    epg_timezone='America/New_York'
)

print(f"venue: '{vars_dict.get('venue')}'")
print(f"venue_city: '{vars_dict.get('venue_city')}'")
print(f"venue_state: '{vars_dict.get('venue_state')}'")
print(f"venue_full: '{vars_dict.get('venue_full')}'")

# Check if empty
if not vars_dict.get('venue_city') or not vars_dict.get('venue_state'):
    print("❌ FAIL: Venue city or state is empty!")
else:
    print("✅ PASS: Venue data extracted correctly")

# Test 2: Current game format (flat structure)
print("\n\nTest 2: Current/past game format (from scoreboard API)")
print("-" * 70)
current_game = {
    'home_team': {'id': '22', 'name': 'Arizona Cardinals', 'abbrev': 'ARI'},
    'away_team': {'id': '27', 'name': 'Tampa Bay Buccaneers', 'abbrev': 'TB'},
    'venue': {
        'name': 'Raymond James Stadium',
        'city': 'Tampa',
        'state': 'FL'
    },
    'status': {'name': 'In Progress'},
    'date': '2025-11-30T18:00Z'
}

vars_dict2 = engine._build_variables_from_game_context(
    game=current_game,
    team_config={'espn_team_id': '22', 'team_name': 'Arizona Cardinals', 'league': 'nfl'},
    team_stats={},
    opponent_stats={},
    h2h={},
    streaks={},
    head_coach='',
    player_leaders={},
    epg_timezone='America/New_York'
)

print(f"venue: '{vars_dict2.get('venue')}'")
print(f"venue_city: '{vars_dict2.get('venue_city')}'")
print(f"venue_state: '{vars_dict2.get('venue_state')}'")
print(f"venue_full: '{vars_dict2.get('venue_full')}'")

if not vars_dict2.get('venue_city') or not vars_dict2.get('venue_state'):
    print("❌ FAIL: Venue city or state is empty!")
else:
    print("✅ PASS: Venue data extracted correctly")

print("\n" + "=" * 70)
print("SUMMARY:")
print("Both formats (future and current games) should now work correctly")

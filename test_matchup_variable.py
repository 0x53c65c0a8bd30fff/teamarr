"""
Test new matchup variable (full team names) with real ESPN API data
"""
import sys
sys.path.insert(0, '/srv/dev-disk-by-uuid-c332869f-d034-472c-a641-ccf1f28e52d6/scratch/teamarr')

from api.espn_client import ESPNClient
from epg.template_engine import TemplateEngine

espn = ESPNClient()
engine = TemplateEngine()

team_id = '8'  # Detroit Pistons

print("Testing NEW matchup variable (full team names)")
print("=" * 70)

# Get schedule
schedule = espn.get_team_schedule('basketball', 'nba', team_id, days_ahead=30)

if not schedule or 'events' not in schedule:
    print("No schedule data")
    exit(1)

# Parse events
all_events = []
for event in schedule.get('events', []):
    try:
        parsed = espn._parse_event(event)
        if parsed:
            all_events.append(parsed)
    except:
        continue

if len(all_events) < 3:
    print(f"Not enough games ({len(all_events)})")
    exit(1)

# Build context
context = {
    'team_config': {'espn_team_id': team_id},
    'team_stats': {},
    'game': all_events[0],
    'opponent_stats': {},
    'h2h': {},
    'next_game': {
        'game': all_events[1],
        'opponent_stats': {},
        'h2h': {},
        'streaks': {},
        'head_coach': '',
        'player_leaders': {}
    },
    'last_game': {
        'game': all_events[2],
        'opponent_stats': {},
        'h2h': {},
        'streaks': {},
        'head_coach': '',
        'player_leaders': {}
    },
    'epg_timezone': 'America/Detroit'
}

# Build variables
all_vars = engine._build_variable_dict(context)

print("\nMATCHUP VARIABLES (from ESPN API):")
print("-" * 70)

# Full name matchup
matchup_base = all_vars.get('matchup', 'MISSING')
matchup_next = all_vars.get('matchup.next', 'MISSING')
matchup_last = all_vars.get('matchup.last', 'MISSING')

print(f"\nmatchup (NEW - full team names):")
print(f"  base:  '{matchup_base}'")
print(f"  .next: '{matchup_next}'")
print(f"  .last: '{matchup_last}'")

# Abbreviated matchup for comparison
matchup_abbrev_base = all_vars.get('matchup_abbrev', 'MISSING')
matchup_abbrev_next = all_vars.get('matchup_abbrev.next', 'MISSING')
matchup_abbrev_last = all_vars.get('matchup_abbrev.last', 'MISSING')

print(f"\nmatchup_abbrev (existing - abbreviations):")
print(f"  base:  '{matchup_abbrev_base}'")
print(f"  .next: '{matchup_abbrev_next}'")
print(f"  .last: '{matchup_abbrev_last}'")

# Verify
matchup_ok = (
    matchup_base not in ['MISSING', '', ' @ '] and
    matchup_next not in ['MISSING', '', ' @ '] and
    matchup_last not in ['MISSING', '', ' @ ']
)

print(f"\n{'✓ PASS - All contexts populated' if matchup_ok else '✗ FAIL - Missing data'}")

# Template test
print("\n\nTEMPLATE TEST:")
print("-" * 70)

templates = [
    ("Abbreviated", "{matchup_abbrev}"),
    ("Full names", "{matchup}"),
    ("Mixed", "{matchup} ({matchup_abbrev})")
]

for label, template in templates:
    resolved = engine.resolve(template, all_vars)
    print(f"\n{label}: {template}")
    print(f"  → {resolved}")

print("\n" + "=" * 70)
if matchup_ok:
    print("✓ SUCCESS: New matchup variable working with full team names")
else:
    print("✗ FAILURE: matchup variable not populated correctly")

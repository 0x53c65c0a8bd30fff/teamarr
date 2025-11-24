"""
Test venue and matchup variables with REAL ESPN API data in all three contexts
"""
import sys
sys.path.insert(0, '/srv/dev-disk-by-uuid-c332869f-d034-472c-a641-ccf1f28e52d6/scratch/teamarr')

from api.espn_client import ESPNClient
from epg.template_engine import TemplateEngine
from datetime import datetime
from zoneinfo import ZoneInfo

def test_venue_matchup_with_api():
    """Test venue and matchup variables with real API data"""
    
    espn = ESPNClient()
    engine = TemplateEngine()
    
    # Get Detroit Pistons schedule
    team_id = '8'  # Detroit Pistons
    
    print("Testing VENUE and MATCHUP variables with REAL ESPN API")
    print("=" * 70)
    
    # Get schedule
    schedule = espn.get_team_schedule('basketball', 'nba', team_id, days_ahead=30)
    
    if not schedule or 'events' not in schedule:
        print("No schedule data available")
        return
    
    # Get raw events
    all_events = []
    for event in schedule.get('events', []):
        try:
            parsed = espn._parse_event(event)
            if parsed:
                all_events.append(parsed)
        except Exception as e:
            continue
    
    if len(all_events) < 3:
        print(f"Not enough games found ({len(all_events)}). Need at least 3.")
        return
    
    print(f"Found {len(all_events)} games\n")
    
    # Pick 3 games for base, next, last
    base_game = all_events[0]
    next_game = all_events[1] if len(all_events) > 1 else None
    last_game = all_events[2] if len(all_events) > 2 else None
    
    # Build context with all three games
    context = {
        'team_config': {'espn_team_id': team_id, 'team_name': 'Detroit Pistons'},
        'team_stats': {},
        'game': base_game,
        'opponent_stats': {},
        'h2h': {},
        'next_game': {
            'game': next_game,
            'opponent_stats': {},
            'h2h': {},
            'streaks': {},
            'head_coach': '',
            'player_leaders': {}
        } if next_game else None,
        'last_game': {
            'game': last_game,
            'opponent_stats': {},
            'h2h': {},
            'streaks': {},
            'head_coach': '',
            'player_leaders': {}
        } if last_game else None,
        'epg_timezone': 'America/Detroit'
    }
    
    # Build all variables (base, .next, .last)
    all_vars = engine._build_variable_dict(context)
    
    # Test venue variables
    print("\nVENUE VARIABLES (from ESPN API):")
    print("-" * 70)
    
    venue_vars = ['venue', 'venue_city', 'venue_state', 'venue_full']
    
    for var in venue_vars:
        base_val = all_vars.get(var, 'MISSING')
        next_val = all_vars.get(f"{var}.next", 'MISSING')
        last_val = all_vars.get(f"{var}.last", 'MISSING')
        
        print(f"\n{var}:")
        print(f"  base:  '{base_val}'")
        print(f"  .next: '{next_val}'")
        print(f"  .last: '{last_val}'")
        
        # Verify all three are populated (not MISSING or empty)
        base_ok = base_val not in ['MISSING', '']
        next_ok = next_val not in ['MISSING', '']
        last_ok = last_val not in ['MISSING', '']
        
        if base_ok and next_ok and last_ok:
            print(f"  Status: ✓ All three contexts populated from API")
        else:
            print(f"  Status: ✗ Missing - base:{base_ok} next:{next_ok} last:{last_ok}")
    
    # Test matchup variables
    print("\n\nMATCHUP VARIABLES (from ESPN API):")
    print("-" * 70)
    
    matchup_base = all_vars.get('matchup_abbrev', 'MISSING')
    matchup_next = all_vars.get('matchup_abbrev.next', 'MISSING')
    matchup_last = all_vars.get('matchup_abbrev.last', 'MISSING')
    
    print(f"\nmatchup_abbrev:")
    print(f"  base:  '{matchup_base}'")
    print(f"  .next: '{matchup_next}'")
    print(f"  .last: '{matchup_last}'")
    
    matchup_base_ok = matchup_base not in ['MISSING', '', ' @ ']
    matchup_next_ok = matchup_next not in ['MISSING', '', ' @ ']
    matchup_last_ok = matchup_last not in ['MISSING', '', ' @ ']
    
    if matchup_base_ok and matchup_next_ok and matchup_last_ok:
        print(f"  Status: ✓ All three contexts populated from API")
    else:
        print(f"  Status: ✗ Missing - base:{matchup_base_ok} next:{matchup_next_ok} last:{matchup_last_ok}")
    
    # Template test
    print("\n\nTEMPLATE RESOLUTION TEST:")
    print("-" * 70)
    
    test_templates = [
        ("Base", "{matchup_abbrev} at {venue}"),
        ("Next", "{matchup_abbrev.next} at {venue.next}"),
        ("Last", "{matchup_abbrev.last} at {venue.last}")
    ]
    
    for label, template in test_templates:
        resolved = engine.resolve(template, all_vars)
        print(f"\n  {label}:")
        print(f"    Template: {template}")
        print(f"    Resolved: {resolved}")
    
    # Summary
    print("\n\n" + "=" * 70)
    print("FINAL SUMMARY:")
    print("=" * 70)
    
    all_venue_ok = all(
        all_vars.get(var) not in ['MISSING', ''] and
        all_vars.get(f"{var}.next") not in ['MISSING', ''] and
        all_vars.get(f"{var}.last") not in ['MISSING', '']
        for var in venue_vars
    )
    
    all_matchup_ok = matchup_base_ok and matchup_next_ok and matchup_last_ok
    
    print(f"\nVenue variables (venue, venue_city, venue_state, venue_full):")
    print(f"  {'✓ PASS - All populated in all three contexts from ESPN API' if all_venue_ok else '✗ FAIL - Some contexts missing'}")
    
    print(f"\nMatchup variable (matchup_abbrev):")
    print(f"  {'✓ PASS - Populated in all three contexts from ESPN API' if all_matchup_ok else '✗ FAIL - Some contexts missing'}")
    
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if (all_venue_ok and all_matchup_ok) else '✗ SOME TESTS FAILED'}")

if __name__ == '__main__':
    test_venue_matchup_with_api()

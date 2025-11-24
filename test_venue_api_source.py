"""
Check where venue data comes from in ESPN API - schedule vs scoreboard
"""
import sys
sys.path.insert(0, '/srv/dev-disk-by-uuid-c332869f-d034-472c-a641-ccf1f28e52d6/scratch/teamarr')

from api.espn_client import ESPNClient
import json

espn = ESPNClient()

# Get Detroit Pistons schedule
team_id = '8'

print("Checking VENUE data source in ESPN API")
print("=" * 70)

# Get schedule
schedule = espn.get_team_schedule('basketball', 'nba', team_id, days_ahead=30)

if schedule and 'events' in schedule:
    # Look at first few events
    for i, event in enumerate(schedule['events'][:3]):
        print(f"\n\nEvent {i+1}: {event.get('name', 'Unknown')}")
        print("-" * 70)
        
        # Check if venue data is in raw schedule response
        if 'competitions' in event and len(event['competitions']) > 0:
            comp = event['competitions'][0]
            
            if 'venue' in comp:
                venue = comp['venue']
                print(f"✓ VENUE DATA IN SCHEDULE API:")
                print(f"  Name: {venue.get('fullName', 'N/A')}")
                if 'address' in venue:
                    print(f"  City: {venue['address'].get('city', 'N/A')}")
                    print(f"  State: {venue['address'].get('state', 'N/A')}")
                else:
                    print(f"  Address: NOT IN SCHEDULE")
            else:
                print(f"✗ NO VENUE DATA IN SCHEDULE")
            
            # Check competitors (for matchup data)
            if 'competitors' in comp:
                competitors = comp['competitors']
                print(f"\n✓ COMPETITORS DATA:")
                for comp_team in competitors:
                    team = comp_team.get('team', {})
                    home_away = comp_team.get('homeAway', '?')
                    print(f"  {home_away}: {team.get('displayName', 'N/A')} ({team.get('abbreviation', 'N/A')})")

print("\n\n" + "=" * 70)
print("CONCLUSION:")
print("=" * 70)
print("If venue data appears above, it's in the schedule API (available for future games)")
print("If not, it only comes from scoreboard enhancement (TODAY's games only)")

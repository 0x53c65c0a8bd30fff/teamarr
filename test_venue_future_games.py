"""
Test venue data for future NFL games
"""
import sys
sys.path.insert(0, '/srv/dev-disk-by-uuid-c332869f-d034-472c-a641-ccf1f28e52d6/scratch/teamarr')

from api.espn_client import ESPNClient
import json

espn = ESPNClient()

print("Testing venue data for future NFL games")
print("=" * 70)

# Arizona Cardinals
team_id = '22'  # Arizona Cardinals
print(f"\nFetching schedule for Arizona Cardinals (team_id={team_id})...")

schedule = espn.get_team_schedule('football', 'nfl', team_id, days_ahead=14)

if schedule and 'events' in schedule:
    print(f"Found {len(schedule['events'])} events")

    for event in schedule['events']:
        name = event.get('name', 'Unknown')
        date = event.get('date', 'Unknown')

        print(f"\n{'-' * 70}")
        print(f"Event: {name}")
        print(f"Date: {date}")

        # Check competitions for venue
        if 'competitions' in event:
            competition = event['competitions'][0]

            if 'venue' in competition:
                venue = competition['venue']
                print(f"\nVenue data:")
                print(f"  Full name: {venue.get('fullName', 'N/A')}")
                print(f"  Name: {venue.get('name', 'N/A')}")
                print(f"  City: {venue.get('city', 'N/A')}")
                print(f"  State: {venue.get('state', 'N/A')}")
                print(f"\n  Raw venue keys: {list(venue.keys())}")
                print(f"\n  Full venue object:")
                print(json.dumps(venue, indent=2))
            else:
                print("  ⚠️ NO VENUE DATA IN COMPETITION")
        else:
            print("  ⚠️ NO COMPETITIONS DATA")

print("\n" + "=" * 70)

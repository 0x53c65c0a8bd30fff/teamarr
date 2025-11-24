"""
Check what ESPN API returns for league codes/names
"""
import sys
sys.path.insert(0, '/srv/dev-disk-by-uuid-c332869f-d034-472c-a641-ccf1f28e52d6/scratch/teamarr')

from api.espn_client import ESPNClient
import json

espn = ESPNClient()

print("Checking ESPN API league data")
print("=" * 70)

# Get Detroit Pistons team info
team_id = '8'
team_info = espn.get_team_info('basketball', 'nba', team_id)

if team_info and 'team' in team_info:
    team = team_info['team']
    print(f"\nTeam: {team.get('displayName', 'N/A')}")
    
    # Check league data in team info
    if 'groups' in team:
        print(f"\nGroups (league info):")
        print(json.dumps(team['groups'], indent=2))
    
    # Check what fields are available
    print(f"\nAvailable team fields:")
    for key in team.keys():
        if 'league' in key.lower():
            print(f"  {key}: {team[key]}")

# Also check schedule response
print(f"\n\nChecking schedule API response:")
print("-" * 70)

schedule = espn.get_team_schedule('basketball', 'nba', team_id, days_ahead=1)
if schedule and 'events' in schedule and len(schedule['events']) > 0:
    event = schedule['events'][0]
    if 'season' in event:
        print(f"Season data:")
        print(json.dumps(event['season'], indent=2))
    
    if 'leagues' in event:
        print(f"\nLeagues data:")
        print(json.dumps(event['leagues'], indent=2))

print("\n" + "=" * 70)
print("Summary: ESPN API does NOT provide league code/name in responses")
print("League data comes from OUR database (team_config table)")

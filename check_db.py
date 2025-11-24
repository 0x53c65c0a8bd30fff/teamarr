"""
Check what's actually in the database league field
"""
import sys
import sqlite3

db_path = '/mnt/docker/stacks/teamarr/data/teamarr.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Checking actual league values in database")
print("=" * 70)

# Get sample teams
cursor.execute("SELECT id, team_name, league FROM teams LIMIT 5")
teams = cursor.fetchall()

print("\nSample team data:")
print("-" * 70)
for team in teams:
    print(f"ID {team[0]}: {team[1]:<30} league='{team[2]}'")

# Also check league_config
print("\n\nLeague config table:")
print("-" * 70)
cursor.execute("SELECT code, name FROM league_config LIMIT 5")
leagues = cursor.fetchall()
for league in leagues:
    print(f"code='{league[0]}'  name='{league[1]}'")

conn.close()

print("\n" + "=" * 70)
print("ANSWER: league field in teams table contains LOWERCASE codes")
print("The code does: team_config.get('league', '').upper()")
print("So 'nba'.upper() → 'NBA'")
print("\nIf you're seeing lowercase, the .upper() isn't being called.")
print("This could mean league_name exists and has a value in team_config dict")

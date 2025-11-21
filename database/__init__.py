"""Database module for Teamarr"""
import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = '/app/data/teamarr.db'

def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database with schema"""
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')

    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    conn = get_connection()
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print(f"✅ Database initialized successfully at {DB_PATH}")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise
    finally:
        conn.close()

    # Run migrations after schema is initialized
    migrate_team_ids_to_numeric()

def migrate_team_ids_to_numeric():
    """
    Migrate existing teams from slug-based IDs to numeric IDs.

    This migration runs automatically on startup to fix the is_home logic.
    ESPN's schedule API returns numeric IDs, so we need numeric IDs in the database
    for proper home/away matching.
    """
    from api.espn_client import ESPNClient

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Find teams with non-numeric IDs (slugs)
        teams = cursor.execute("""
            SELECT id, espn_team_id, league, sport, team_name
            FROM teams
            WHERE espn_team_id NOT GLOB '[0-9]*'
        """).fetchall()

        if not teams:
            # No migration needed
            return

        print(f"\n🔄 Migrating {len(teams)} team(s) to numeric IDs...")

        espn = ESPNClient()
        updated_count = 0

        for team in teams:
            team_dict = dict(team)
            slug_id = team_dict['espn_team_id']

            # Fetch team info using the slug to get numeric ID
            team_data = espn.get_team_info(
                team_dict['sport'],
                team_dict['league'],
                slug_id
            )

            if team_data and 'team' in team_data:
                numeric_id = str(team_data['team'].get('id', ''))

                if numeric_id and numeric_id != slug_id:
                    cursor.execute("""
                        UPDATE teams
                        SET espn_team_id = ?
                        WHERE id = ?
                    """, (numeric_id, team_dict['id']))

                    print(f"  ✅ {team_dict['team_name']}: {slug_id} → {numeric_id}")
                    updated_count += 1

        conn.commit()

        if updated_count > 0:
            print(f"✅ Migrated {updated_count} team(s) to numeric IDs\n")

    except Exception as e:
        print(f"⚠️  Migration warning: {e}")
        # Don't fail startup if migration has issues
    finally:
        conn.close()

def reset_database():
    """Drop all tables and reinitialize"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"🗑️  Removed existing database at {DB_PATH}")
    init_database()

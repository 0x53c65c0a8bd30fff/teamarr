# Teamarr - Dynamic EPG Generator for Sports Team Channels

## Overview
Teamarr generates XMLTV EPG data for sports team channels with two modes:
1. **Team-based EPG** - One team per channel with pregame/game/postgame/idle programs
2. **Event-based EPG** - Dispatcharr channel groups with streams named by matchup (e.g., "Panthers @ 49ers")

**Tech Stack**: Python/Flask, SQLite, Jinja2/vanilla JS, ESPN API, Dispatcharr API

**Server**: `python3 app.py` (port 9195)

---

## Project Structure

```
teamarr/
├── app.py                 # Flask routes, EPG generation orchestration
├── config.py              # App configuration
├── database/
│   ├── __init__.py        # All DB functions (CRUD, migrations, helpers)
│   └── schema.sql         # SQLite schema
├── epg/
│   ├── orchestrator.py    # Team-based EPG orchestration
│   ├── xmltv_generator.py # XMLTV output for team-based
│   ├── template_engine.py # Team-based variable substitution
│   ├── team_matcher.py    # Extract teams from stream names
│   ├── event_matcher.py   # Find ESPN events by team matchup
│   ├── event_epg_generator.py    # XMLTV for event-based streams
│   ├── event_template_engine.py  # Event variable substitution
│   ├── epg_consolidator.py       # Merge team + event EPGs
│   └── channel_lifecycle.py      # Channel creation/deletion management
├── api/
│   ├── espn_client.py        # ESPN API wrapper
│   └── dispatcharr_client.py # Dispatcharr API client
├── utils/
│   ├── time_format.py     # Time/timezone formatting
│   ├── logger.py          # Logging setup
│   └── notifications.py   # Flash messages, JSON responses
├── templates/             # Jinja2 HTML templates
├── static/                # CSS, JS assets
└── config/
    └── variables.json     # Template variable definitions
```

---

## Key Classes & Functions

### app.py (Main Application)
| Function | Purpose |
|----------|---------|
| `generate_all_epg()` | **Single source of truth** for ALL EPG generation |
| `refresh_event_group_core()` | Core logic for refreshing a single event group |
| `run_scheduled_generation()` | Scheduler entry point |
| `inject_globals()` | Context processor for templates |

### epg/channel_lifecycle.py
| Item | Purpose |
|------|---------|
| `ChannelLifecycleManager` | Coordinates channel creation/deletion with Dispatcharr |
| `generate_event_tvg_id()` | Generates consistent tvg_id: `teamarr-event-{espn_event_id}` |
| `should_create_channel()` | Checks both create timing AND delete threshold (prevents create-then-delete cycles) |
| `calculate_delete_time()` | Scheduled deletion based on event END time (handles midnight crossings) |
| `get_sport_duration_hours()` | Sport-specific duration lookup |
| `start_lifecycle_scheduler()` | Background scheduler for auto-deletion |

### epg/epg_consolidator.py
| Function | Purpose |
|----------|---------|
| `merge_all_epgs()` | Merges teams.xml + event_epg_*.xml into final output |
| `after_team_epg_generation()` | Hook after team EPG completes |
| `after_event_epg_generation()` | Hook after event EPG completes |
| `get_epg_stats()` | Returns channel/program counts |

### epg/team_matcher.py
| Item | Purpose |
|------|---------|
| `TeamMatcher` | Extracts team names from stream names using ESPN DB + aliases |
| `extract_date_from_text()` | Parse dates from stream names |
| `create_matcher()` | Factory function |

### epg/event_matcher.py
| Item | Purpose |
|------|---------|
| `EventMatcher` | Finds upcoming/live ESPN events between detected teams |
| `enrich_with_team_stats()` | Adds records, logos, conference, division, rank, seed, streak from team endpoint |
| `find_and_enrich()` | Combined find + scoreboard + team stats enrichment |
| `create_event_matcher()` | Factory function |

### api/dispatcharr_client.py
| Class | Purpose |
|-------|---------|
| `DispatcharrAuth` | Authentication/session management |
| `EPGManager` | EPG source CRUD, refresh, EPGData lookup |
| `M3UManager` | M3U accounts, channel groups, streams |
| `ChannelManager` | Channel CRUD, EPG association |

### api/espn_client.py
| Class | Purpose |
|-------|---------|
| `ESPNClient` | ESPN API wrapper (leagues, teams, schedules) |

### database/__init__.py
Key functions:
- `db_fetch_one/all()`, `db_execute()`, `db_insert()` - Query helpers
- `get/create/update/delete_template()` - Template CRUD
- `get/create/update/delete_team()` - Team CRUD
- `get/create/update/delete_event_epg_group()` - Event group CRUD
- `get/create/update/delete_managed_channel()` - Managed channel CRUD
- `get_aliases_for_league()`, `create_alias()` - Team alias management
- `save_epg_generation_stats()`, `get_epg_history()` - EPG history

### utils/time_format.py
| Function | Purpose |
|----------|---------|
| `format_time()` | Format time with 12h/24h preference |
| `format_datetime()` | Format date+time in user's timezone |
| `format_game_time()` | Format game time for templates |

---

## EPG Generation Flow

All EPG generation uses `generate_all_epg()`:

```
generate_all_epg()
├── Phase 1: Team-based EPG → teams.xml
├── Phase 2: Event-based EPG → event_epg_*.xml, creates channels
├── Phase 3: Channel Lifecycle → process scheduled deletions
├── Phase 4: History & Stats → save to epg_history table
├── Phase 5: Dispatcharr Refresh → refresh EPG source
└── Phase 6: EPG Association → link channels to EPGData by tvg_id
```

**Entry Points**:
- UI button → `/generate/stream` (SSE)
- Scheduler → `run_scheduled_generation()`
- API → `/generate` POST

---

## Database Tables

| Table | Purpose |
|-------|---------|
| `templates` | EPG templates (team & event) |
| `teams` | Tracked teams with ESPN IDs |
| `team_aliases` | Custom team name aliases |
| `event_epg_groups` | Dispatcharr channel groups for event matching |
| `managed_channels` | Teamarr-created channels (lifecycle tracking) |
| `epg_history` | EPG generation history/stats |
| `settings` | Key-value app settings |

---

## Key Design Decisions

1. **UTC storage, local display** - All times stored UTC, converted for display
2. **Consistent tvg_id format** - `teamarr-event-{espn_event_id}` used everywhere
3. **Single EPG generation function** - `generate_all_epg()` is the only entry point
4. **Event matching skips completed games** - EPG is for upcoming/live only
5. **Sport-specific durations** - Football 4h, Basketball 3h, Hockey 3h, etc.
6. **Relative output paths** - `./data/teamarr.xml` works in Docker and local
7. **Team stats enrichment** - Event data enriched from team endpoint for reliable records/logos
8. **Stale stream handling** - Dangling provider streams silently ignored (no ESPN match = no channel)

---

## Lifecycle Timing

**Channel Creation** (`channel_create_timing`):
- `stream_available` - Create immediately when stream exists
- `same_day`, `day_before`, `2_days_before` - Time-based
- `manual` - Never auto-create

**Channel Deletion** (`channel_delete_timing`):
- `stream_removed` - Delete when stream no longer detected
- `same_day`, `day_after`, `2_days_after` - Time-based (at 23:59)
- `manual` - Never auto-delete

---

## UI Navigation

Dashboard → Templates → Teams → Events → EPG → Channels → Settings

---

## API Endpoints (Key)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/generate/stream` | GET | SSE EPG generation with progress |
| `/generate` | POST | API EPG generation |
| `/api/variables` | GET | Template variables with samples |
| `/api/channel-lifecycle/status` | GET | Managed channels status |
| `/api/channel-lifecycle/channels` | GET | List managed channels |
| `/api/managed-channels/bulk-delete` | POST | Bulk delete channels |

---

## Event Data Enrichment

Event-based EPG enriches data from multiple ESPN API sources:

1. **Schedule API** - Base event data (date, teams, venue)
2. **Scoreboard API** - Live data (odds, scores, broadcasts) - game day only
3. **Team Stats API** - Current records, logos, conference, division, rank, seed, streak

**Why team stats enrichment?** Schedule/scoreboard APIs don't have records for future games. Team endpoint always has current season stats.

### Home/Away Team Variables (16 total)
Conference/Division (10):
- `home_team_college_conference`, `home_team_college_conference_abbrev`
- `home_team_pro_conference`, `home_team_pro_conference_abbrev`, `home_team_pro_division`
- Same 5 for `away_team_*`

Rank/Seed/Streak (6):
- `home_team_rank`, `away_team_rank` - College ranking (#5), empty if unranked
- `home_team_seed`, `away_team_seed` - Pro playoff seed (1st, 2nd)
- `home_team_streak`, `away_team_streak` - Current streak (W5, L2)

---

## Stale Stream Handling

Provider streams that don't match ESPN events are silently ignored:

| Scenario | Result |
|----------|--------|
| Stream exists, no ESPN match | No channel created |
| ESPN game completed (previous day) | Skipped, no match |
| ESPN game completed (today) | Skipped by default |
| Past delete threshold | Channel NOT created |

Dangling streams (e.g., month-old World Series) cause no issues - they simply don't match.

---

## Future Work

### High Priority
- **Stream matching feedback** - UI indicators when streams fail to match teams/events
- **EPG preview** - Preview generated EPG before committing

### Medium Priority
- **UI help text** - Contextual documentation in the interface

### Low Priority
- **Backup/restore** - Export/import configuration and data

### Ideas (Unspecified)
- Better error recovery in EPG generation
- Bulk operations for event groups
- Template inheritance/variants

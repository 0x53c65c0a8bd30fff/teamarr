# Teamarr - Dynamic EPG Generator for Sports Team Channels

## Project Overview
Teamarr generates XMLTV EPG data for sports team channels. It supports two modes:
1. **Team-based EPG** - Traditional mode: one team per channel, generates pregame/game/postgame/idle programs
2. **Event-based EPG** - Dispatcharr channel groups with streams named by matchup (e.g., "Panthers @ 49ers")

## Tech Stack
- **Backend**: Python/Flask (app.py)
- **Database**: SQLite (teamarr.db)
- **Frontend**: Jinja2 templates with vanilla JS
- **External APIs**: ESPN API (schedules, teams), Dispatcharr API (M3U accounts, channel groups, channels)

## Key Directories
```
/srv/dev-disk-by-uuid-c332869f-d034-472c-a641-ccf1f28e52d6/scratch/teamarr/
├── app.py                    # Main Flask app, all routes
├── database/                 # SQLite schema, migrations, CRUD
├── epg/                      # EPG generation engines
│   ├── orchestrator.py       # Team-based EPG orchestration
│   ├── xmltv_generator.py    # XMLTV output for team-based
│   ├── template_engine.py    # Team-based variable substitution
│   ├── team_matcher.py       # Extract teams from stream names
│   ├── event_matcher.py      # Find ESPN events by team matchup
│   ├── event_epg_generator.py    # XMLTV for event-based streams
│   ├── event_template_engine.py  # Event variable substitution
│   ├── epg_consolidator.py   # Merge team + event EPGs
│   └── channel_lifecycle.py  # Channel creation/deletion management
├── api/
│   ├── espn_client.py        # ESPN API wrapper
│   └── dispatcharr_client.py # Dispatcharr API client (M3U + Channels)
├── utils/
│   └── time_format.py        # Time formatting utilities
├── templates/                # Jinja2 HTML templates
│   ├── base.html             # Base template with global JS helpers
│   ├── settings.html         # Settings page
│   ├── channels.html         # Managed channels table
│   └── ...
└── config/
    └── variables.json        # Template variable definitions
```

## Current Branch: `dev-withevents`

## Running the Server
```bash
cd /srv/dev-disk-by-uuid-c332869f-d034-472c-a641-ccf1f28e52d6/scratch/teamarr
python3 app.py
# Server runs on port 9195
```

---

## Feature Status

### Completed: Phases 1-7 (Event-based EPG)
- **Phase 1**: Database schema for event_epg_groups table
- **Phase 2**: TeamMatcher - extracts team names from stream names using ESPN team database + user aliases
- **Phase 3**: EventMatcher - finds upcoming/live ESPN events between detected teams
- **Phase 4**: EventEPGGenerator - generates XMLTV for matched streams
- **Phase 5**: EPG Consolidator - merges event EPGs with team EPGs into final output
- **Phase 6**: API endpoints for Dispatcharr integration (accounts, groups, streams)
- **Phase 7**: UI for event groups management

### Completed: Phases 8.1-8.4 (Channel Lifecycle Management)

**Phase 8.1: Database & API Foundation**
- Added columns to `event_epg_groups`: `channel_start`, `channel_create_timing`, `channel_delete_timing`
- Created `managed_channels` table to track Teamarr-created channels
- Added `ChannelManager` class to `dispatcharr_client.py` for channel CRUD
- Added `set_channel_epg()` for direct EPG injection

**Phase 8.2: Channel Creation Logic**
- Channel creation integrated into refresh endpoint
- Flow: Match streams → Generate EPG → Create channels → Inject EPG
- Channel number allocation from group's `channel_start`
- Tracks channels in `managed_channels` table

**Phase 8.3: Channel Lifecycle Scheduler**
- `should_create_channel()` - timing check based on event date
- `calculate_delete_time()` - scheduled deletion calculation with sport-specific durations
- Background scheduler thread for automatic deletion processing
- All timing uses user's configured timezone (no hardcoded defaults)

**Phase 8.4: UI Updates & Lifecycle Enhancements**
- Dashboard redesigned with compact tiles (50% smaller)
- Dashboard sections reordered to match tabs: Templates → Teams → Events → EPG Summary
- Added "Manage →" links to each section header
- Renamed "Event Groups" tab to "Events" for brevity
- Added dedicated "Channels" tab with managed channels table
- Bulk delete for channels table (matching teams/events pattern with shift-click)
- Edit modal for event groups with lifecycle settings
- `sync_group_settings()` ensures setting changes are honored on every EPG generation
- Sport-specific duration calculations for accurate event end times
- Delete times use 23:59:59 for clarity (not 00:00)

### Completed: Phase 9 (EPG Generation Consolidation)

**Single Source of Truth Architecture:**
- `generate_all_epg()` is the AUTHORITATIVE function for ALL EPG generation
- Scheduler, manual generation, and streaming endpoints all use this single function
- History saving and stats logging consolidated into single location

**EPG Generation Phases (in `generate_all_epg()`):**
1. **Phase 1: Team-based EPG** - Process teams via `epg_orchestrator.generate_epg()`
2. **Phase 2: Event-based EPG** - Refresh event groups via `refresh_event_group_core()`
3. **Phase 3: Channel Lifecycle** - Process scheduled deletions
4. **Phase 4: History & Stats** - Save to `epg_history` table (single source of truth)
5. **Phase 5: Dispatcharr Refresh** - Auto-trigger EPG refresh if configured

### Completed: Phase 10 (Time/Timezone Improvements)

**Global Time Format Settings:**
- User-configurable 12-hour or 24-hour time format
- Optional timezone abbreviation display (EST, PST, etc.)
- Settings stored in database: `time_format`, `show_timezone`

**Timezone Handling:**
- Docker TZ environment variable sync on startup (`sync_timezone_from_env()`)
- Fallback timezone: America/Detroit
- Timezone validation on save (case-sensitive, rejects invalid values)
- All dates/times stored as UTC, converted to user timezone for display

**Template Variables:**
- Consolidated to single `{game_time}` variable that honors user settings
- Removed redundant `{game_time_12h}` and `{game_time_24h}` variants
- Template previews (`/api/variables`) respect time format settings

**JavaScript Helpers (base.html):**
- `formatTime(dateInput, options)` - Format time with user's 12h/24h preference
- `formatDate(dateInput, format)` - Format date in user's timezone
- `formatDateTime(dateInput, options)` - Combined date and time
- All helpers read settings from `window.TEAMARR_SETTINGS`

**Managed Channels:**
- `event_date` stored as full UTC datetime (e.g., "2025-11-28T01:20Z")
- UI displays converted to user's local date/time
- Fixes issue where UTC date differed from local date

---

## Settings Page Organization

The settings page is organized into logical sections:

1. **System Settings** - Timezone, Time Format (12h/24h), Show Timezone option

2. **Team Based Streams**
   - Days to Generate (1-14)
   - Midnight Crossover Filler Type (idle/postgame)
   - Default Channel ID Format

3. **Event Based Streams**
   - Earliest Creation timing
   - Latest Deletion timing

4. **EPG Generation**
   - Output Path (relative path like `./data/teamarr.xml` works in both Docker and local)
   - Event Duration Defaults (per-sport hours)
   - Schedule (enable/frequency)

5. **Dispatcharr Integration** - URL, credentials, EPG source selection

6. **Advanced Settings** - XMLTV generator name/URL

---

## Key Files

### `epg/channel_lifecycle.py`
Channel lifecycle management module:
- `ChannelLifecycleManager` - coordinates channel creation/deletion with Dispatcharr
- `should_create_channel(event, timing, timezone)` - checks if channel should be created
- `calculate_delete_time(event, timing, timezone, sport)` - calculates deletion schedule
- `get_sport_duration_hours(sport)` - returns typical duration
- `generate_channel_name(event, template, timezone)` - generates channel name from template
- `sync_group_settings(group)` - updates ALL channels when group settings change
- `start_lifecycle_scheduler()` / `stop_lifecycle_scheduler()` - background scheduler

### `epg/epg_consolidator.py`
EPG file consolidation:
- `get_data_dir(from_output_path)` - derives data directory from output path
- `get_epg_paths(final_output_path)` - returns all EPG file paths
- `merge_all_epgs(final_output_path)` - merges teams.xml + event_epg_*.xml
- `after_team_epg_generation()` - saves teams.xml, triggers merge
- `after_event_epg_generation()` - triggers merge after event EPG
- `finalize_epg_generation()` - archives intermediate files

### `templates/base.html`
Global template with:
- CSS variables for theming
- JavaScript helpers: `formatTime()`, `formatDate()`, `formatDateTime()`
- `window.TEAMARR_SETTINGS` object with user preferences
- Context processor injects settings into all templates

### `templates/channels.html`
Managed channels UI:
- Active channels table with bulk delete (shift-click support)
- Recently Deleted section (always visible, even when empty)
- Event date/time displayed in user's timezone
- `formatChannelDateTime()` helper for SQLite timestamp conversion

---

## API Endpoints

### Channel Lifecycle
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/channel-lifecycle/status` | GET | Managed channels status, scheduler state |
| `/api/channel-lifecycle/channels` | GET | List managed channels |
| `/api/channel-lifecycle/channels/<id>` | DELETE | Manual channel deletion |
| `/api/channel-lifecycle/process-deletions` | POST | Process pending deletions |
| `/api/channel-lifecycle/scheduler` | POST | Start/stop background scheduler |
| `/api/managed-channels/bulk-delete` | POST | Bulk delete selected channels |

### EPG Generation
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/generate/stream` | GET | SSE endpoint for EPG generation with progress |
| `/generate` | POST | API endpoint for EPG generation |
| `/api/variables` | GET | Template variables with sample values |

---

## Database Schema (managed_channels)
```sql
CREATE TABLE managed_channels (
    id INTEGER PRIMARY KEY,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    event_epg_group_id INTEGER REFERENCES event_epg_groups(id),
    dispatcharr_channel_id INTEGER UNIQUE,
    dispatcharr_stream_id INTEGER,
    channel_number INTEGER,
    channel_name TEXT,
    tvg_id TEXT,
    espn_event_id TEXT,
    event_date TEXT,           -- Full UTC datetime (e.g., "2025-11-28T01:20Z")
    home_team TEXT,
    away_team TEXT,
    scheduled_delete_at TIMESTAMP,
    deleted_at TIMESTAMP,
    dispatcharr_logo_id INTEGER
);
```

---

## Important Design Decisions

1. **Event templates** use a single description field (not multi-fallback like team templates)
2. **Event matching** skips completed games - EPG is for upcoming/live events only
3. **EPG consolidation** merges all sources into a single XML file
4. **Direct EPG injection** via `set_channel_epg()` API - no tvg_id matching needed
5. **Timezone sensitivity** - all lifecycle timing uses user's configured timezone
6. **Channel creation flow**: Generate EPG first, then create channels and inject EPG
7. **Sport-specific durations** for calculating event end times (handles midnight crossings)
8. **Settings sync on every EPG generation** - ensures setting changes take effect immediately
9. **UTC storage, local display** - all dates stored as UTC, converted for display
10. **Relative output paths** - `./data/teamarr.xml` works in both Docker and local dev

## Lifecycle Timing Options

**Channel Creation (`channel_create_timing`):**
- `stream_available` - Create immediately when stream exists
- `same_day` - Create on event day
- `day_before` - Create 1 day before event
- `2_days_before` - Create 2 days before
- `manual` - Never auto-create

**Channel Deletion (`channel_delete_timing`):**
- `stream_removed` - Delete when stream no longer detected
- `same_day` - Delete at 23:59 of the day event ENDS
- `day_after` - Delete at 23:59 of the day after event ends
- `2_days_after` - Delete 2 days after event ends
- `manual` - Never auto-delete

**Sport Durations (for end time calculation):**
- Football: 4 hours
- Basketball: 3 hours
- Hockey: 3 hours
- Baseball: 4 hours
- Soccer: 2.5 hours
- Default: 3.5 hours

---

## EPG Generation Flow

All EPG generation uses `generate_all_epg()` as the single source of truth:

```
generate_all_epg(progress_callback, team_progress_callback, settings, save_history)
├── Phase 1: Team-based EPG
│   └── epg_orchestrator.generate_epg() → teams.xml via consolidator
├── Phase 2: Event-based EPG
│   └── For each enabled event group with template:
│       └── refresh_event_group_core() → events.xml via consolidator
├── Phase 3: Channel Lifecycle
│   └── get_lifecycle_manager().process_scheduled_deletions()
├── Phase 4: History & Stats
│   └── save_epg_generation_stats() → epg_history table
└── Phase 5: Dispatcharr Refresh
    └── EPGManager.refresh() if configured
```

**Entry Points (all use `generate_all_epg()`):**
- UI "Generate EPG" button → `/generate/stream` (SSE with progress)
- Scheduler → `run_scheduled_generation()` → `generate_all_epg()`
- API clients → `/generate` POST → `generate_all_epg()`

---

## UI Navigation

Dashboard → Templates → Teams → Events → EPG → Channels → Settings

- **Dashboard**: Overview stats, quick links
- **Templates**: Create/edit team and event EPG templates
- **Teams**: Manage tracked teams, team aliases
- **Events**: Configure event groups from Dispatcharr channel groups
- **EPG**: View/download generated EPG XML
- **Channels**: View/manage Teamarr-created channels (always shows Recently Deleted section)
- **Settings**: Organized into Team Based, Event Based, EPG Generation sections

---

## What's Next
- Better UI feedback for stream matching issues
- More event template variables (venue, broadcast network)
- Documentation/help text in UI
- EPG preview before generation
- Backup/restore functionality

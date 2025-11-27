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
├── templates/                # Jinja2 HTML templates
│   ├── template_form.html    # Template editor (team + event types)
│   ├── template_list.html    # Templates listing
│   ├── event_epg.html        # Event EPG groups management
│   ├── event_groups_import.html  # Import modal
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

### Completed: Phases 8.1-8.3 (Channel Lifecycle Management)

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
- `calculate_delete_time()` - scheduled deletion calculation
- Background scheduler thread for automatic deletion processing
- All timing uses user's configured timezone (no hardcoded defaults)

### Completed: Phase 8.4 (UI Updates)

- Dashboard redesigned with compact tiles (50% smaller)
- Dashboard sections reordered to match tabs: Templates → Teams → Events → EPG Summary
- Added "Manage →" links to each section header
- Dashboard stats now include event-based data
- Added `channel_name` field to event templates (template_form.html)
  - Variables: {home_team}, {away_team}, {league}, {sport}, {event_date}
  - Default: "{away_team} @ {home_team}"
- Added edit button (✏️) to event groups table for editing settings
- Edit modal with lifecycle settings:
  - Template selection
  - Channel start number
  - Channel create timing (day_of, day_before, 2_days_before, week_before)
  - Channel delete timing (stream_removed, end_of_day, end_of_next_day, manual)
- Channel Start column already in event groups table
- Smaller, more compact group tiles in import modal
- Managed channels section with 4x taller scrollable table
- Team aliases section with 4x taller scrollable table
- Simplified stream preview modal (removed Action column, cleaner status display)

---

## Key Files Added in Phase 8

### `epg/channel_lifecycle.py`
Channel lifecycle management module:
- `ChannelLifecycleManager` - coordinates channel creation/deletion with Dispatcharr
- `should_create_channel(event, timing, timezone)` - checks if channel should be created
- `calculate_delete_time(event, timing, timezone)` - calculates deletion schedule
- `generate_channel_name(event, template, timezone)` - generates channel name
- `start_lifecycle_scheduler()` / `stop_lifecycle_scheduler()` - background scheduler
- `get_lifecycle_manager()` - factory using settings from DB

### `api/dispatcharr_client.py` - ChannelManager class
```python
class ChannelManager:
    def create_channel(name, channel_number, stream_ids, ...) -> Dict
    def update_channel(channel_id, data) -> Dict
    def delete_channel(channel_id) -> Dict
    def set_channel_epg(channel_id, epg_data_id) -> Dict  # Direct EPG injection
    def get_channels() -> List[Dict]
    def find_channel_by_number(channel_number) -> Optional[Dict]
```

### New API Endpoints (app.py)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/channel-lifecycle/status` | GET | Managed channels status, scheduler state |
| `/api/channel-lifecycle/channels` | GET | List managed channels |
| `/api/channel-lifecycle/channels/<id>` | DELETE | Manual channel deletion |
| `/api/channel-lifecycle/process-deletions` | POST | Process pending deletions |
| `/api/channel-lifecycle/scheduler` | POST | Start/stop background scheduler |
| `/api/channel-lifecycle/cleanup-old` | POST | Hard delete old records |

### Database Schema (managed_channels)
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
    event_date TEXT,
    home_team TEXT,
    away_team TEXT,
    scheduled_delete_at TIMESTAMP,
    deleted_at TIMESTAMP
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

## Lifecycle Timing Options

**Channel Creation (`channel_create_timing`):**
- `day_of` - Create on event day
- `day_before` - Create day before event
- `2_days_before` - Create 2 days before
- `week_before` - Create week before

**Channel Deletion (`channel_delete_timing`):**
- `stream_removed` - Delete when stream no longer detected
- `end_of_day` - Delete at end of event day
- `end_of_next_day` - Delete at end of day after event
- `manual` - Never auto-delete

---

## Recent Fixes (This Session)

1. **Path mismatch fix**: Event EPG was saving to `./data/` but consolidator looked in `/app/data/`. Fixed by using `get_data_dir()` consistently.

2. **Game completed reason**: EventMatcher now returns "Game completed (previous day)" for streams where the game finished on a previous day.

3. **Double notification fix**: Removed success notification before `location.reload()` since it disappears immediately anyway.

4. **Scheduler handling**: Updated scheduler to handle both team and event EPG, doesn't treat "no teams" as error.

5. **Unified EPG Generation (Refactoring)**: Created shared core functions to eliminate code duplication:
   - `refresh_event_group_core()` - Core logic for refreshing a single event group (M3U, matching, EPG gen, channels)
   - `generate_all_epg()` - Unified function for both scheduled and manual EPG generation
   - `run_scheduled_generation()` now calls `generate_all_epg()` directly
   - `generate_epg_stream()` uses `refresh_event_group_core()` for event groups (no HTTP overhead)
   - `api_event_epg_refresh()` uses `refresh_event_group_core()` for consistency

6. **UX Simplification (Event Groups → Events, Channels tab)**:
   - Removed confusing "Refresh" button from Event Groups - all EPG generation now via "Generate EPG"
   - Renamed "Preview" button to "Test" - does lightweight matching without EPG generation
   - Renamed "Event Groups" tab to "Events" for brevity
   - Moved managed channels to new dedicated "Channels" tab
   - New navigation order: Dashboard → Templates → Teams → Events → EPG → Channels → Settings
   - Clearer mental model: Preview/Test = look, Generate EPG = build

---

## What's Next After Phase 8.4
- Test with live upcoming games
- Better UI feedback for stream matching issues
- Scheduled auto-refresh for event groups
- More event template variables (venue, broadcast network)
- Documentation/help text in UI

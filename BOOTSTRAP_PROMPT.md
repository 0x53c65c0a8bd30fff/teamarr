# Teamarr Bootstrap Prompt

Use this to quickly get a new Claude session up to speed.

---

## Quick Context

**Teamarr** is a Flask-based web app that generates XMLTV EPG data for sports channels. It integrates with:
- **ESPN API** - fetches team schedules and event data
- **Dispatcharr** - IPTV channel/stream management system

**Two EPG modes:**
1. **Team-based** - One team per channel, generates pregame/game/postgame/filler programs
2. **Event-based** - Parses stream names like "Panthers @ 49ers" to find matchups from Dispatcharr groups

**Server:** Python/Flask on port 9195

**Branch:** `dev-withevents`

---

## Running the App

```bash
cd /srv/dev-disk-by-uuid-c332869f-d034-472c-a641-ccf1f28e52d6/scratch/teamarr
python3 app.py
```

---

## Navigation Flow

Dashboard -> Templates -> Teams -> Events -> EPG -> Channels -> Settings

- **Dashboard**: Overview stats, quick links to each section
- **Templates**: EPG formatting (title, description, filler). Two types: "team" and "event"
- **Teams**: Add teams with assigned templates for team-based EPG
- **Events**: Import Dispatcharr channel groups, assign templates, configure lifecycle
- **EPG**: Generate all EPG (teams + events), view/download XML
- **Channels**: Managed channels created by Teamarr (lifecycle management)
- **Settings**: Organized into Team Based, Event Based, EPG Generation sections

---

## Key Architecture: Single Source of Truth

**`generate_all_epg()` is the AUTHORITATIVE function for ALL EPG generation.**

```
generate_all_epg(progress_callback, team_progress_callback, settings, save_history)
├── Phase 1: Team-based EPG → epg_orchestrator.generate_epg()
├── Phase 2: Event-based EPG → refresh_event_group_core() for each group
├── Phase 3: Channel Lifecycle → process_scheduled_deletions()
├── Phase 4: History & Stats → save_epg_generation_stats() (single source of truth)
└── Phase 5: Dispatcharr Refresh → EPGManager.refresh() if configured
```

**All entry points use this function:**
- UI "Generate EPG" → `/generate/stream` (SSE) → `generate_all_epg()`
- Scheduler → `run_scheduled_generation()` → `generate_all_epg()`
- API → `/generate` POST → `generate_all_epg()`

---

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main Flask app, `generate_all_epg()`, `refresh_event_group_core()`, all routes |
| `epg/orchestrator.py` | Team-based EPG orchestration |
| `epg/event_epg_generator.py` | Generates XMLTV for event-based streams |
| `epg/team_matcher.py` | Extracts team names from stream names |
| `epg/event_matcher.py` | Finds ESPN events for detected team matchups |
| `epg/epg_consolidator.py` | Merges team + event EPGs into final output |
| `epg/channel_lifecycle.py` | Channel creation/deletion scheduling |
| `api/dispatcharr_client.py` | Dispatcharr API client (M3U + ChannelManager + EPGManager) |
| `templates/base.html` | Global JS helpers: formatTime(), formatDate(), formatDateTime() |
| `database/__init__.py` | `save_epg_generation_stats()` - history saving |

---

## Time/Timezone System (Phase 10)

**User Settings:**
- `time_format` - "12h" or "24h"
- `show_timezone` - 1 or 0 (show EST, PST, etc.)
- `default_timezone` - e.g., "America/Detroit"

**Design Principle:** Store UTC, display local.
- All dates stored as UTC datetime (e.g., "2025-11-28T01:20Z")
- JavaScript helpers in base.html convert to user's timezone for display
- Docker syncs TZ env variable on startup

**JavaScript Helpers (base.html):**
```javascript
formatTime(dateInput, options)     // Time only with 12h/24h setting
formatDate(dateInput, format)      // Date in user's timezone
formatDateTime(dateInput, options) // Both date and time
```

---

## Channel Lifecycle System

Teamarr creates/deletes channels in Dispatcharr based on event timing.

**Per-group settings:**
- `channel_start` - Starting channel number for this group
- `channel_create_timing` - stream_available, same_day, day_before, 2_days_before, manual
- `channel_delete_timing` - stream_removed, same_day, day_after, 2_days_after, manual

**Key lifecycle methods in `epg/channel_lifecycle.py`:**
- `sync_group_settings(group)` - Ensures setting changes are honored (runs every EPG gen)
- `update_existing_channels(streams, group)` - Updates delete times with fresh event data
- `process_matched_streams(streams, group, template)` - Creates new channels
- `process_scheduled_deletions()` - Deletes channels past their scheduled time

**Sport durations (for calculating event end times):**
- Football: 4h, Basketball: 3h, Hockey: 3h, Baseball: 4h, Soccer: 2.5h

---

## Settings Page Organization

1. **System Settings** - Timezone, Time Format (12h/24h), Show Timezone
2. **Team Based Streams** - Days to Generate, Midnight Crossover Filler, Channel ID Format
3. **Event Based Streams** - Channel Create/Delete Timing
4. **EPG Generation** - Output Path, Event Duration Defaults, Schedule
5. **Dispatcharr Integration** - URL, credentials, EPG source
6. **Advanced Settings** - XMLTV generator name/URL

---

## Database Tables

- `templates` - EPG formatting templates (team or event type)
- `teams` - User's tracked teams with template assignment
- `event_epg_groups` - Imported Dispatcharr groups with lifecycle settings
- `managed_channels` - Channels created by Teamarr (tracks scheduled_delete_at, event_date as UTC)
- `team_aliases` - User-defined aliases for team name matching
- `epg_history` - Generation history (single source of truth for stats)

---

## EPG Output Files

All in `./data/` (resolves to `/app/data/` in Docker):
- `teams.xml` - Team-based EPG
- `event_epg_*.xml` - Per-group event EPG files
- `teamarr.xml` - Final consolidated EPG (all sources merged)

---

## Common Tasks

**Add new template variable:**
1. Add to `config/variables.json`
2. Implement in `epg/event_template_engine.py` (event) or `epg/template_engine.py` (team)
3. Add UI help text in `templates/template_form.html`

**Debug EPG generation:**
1. Check logs for progress messages
2. Query `epg_history` table for stats
3. Use `/api/epg-stats` endpoint for real-time EPG analysis

**Debug stream matching:**
1. Use "Test" button on Events page
2. Check logs for `team_matcher` and `event_matcher` debug messages
3. Add team aliases in Settings if names don't match

**Fix lifecycle issues:**
1. Check Channels tab for scheduled delete times
2. Verify group settings (delete_timing) in Events edit modal
3. Check `managed_channels` table for `scheduled_delete_at` values
4. Run EPG generation to trigger `sync_group_settings()`

---

## Recent Session Changes

- Fixed `event_date` storage: now stores full UTC datetime ("2025-11-28T01:20Z")
- Channels table shows date+time in user's timezone
- "Recently Deleted" section always visible
- Settings page reorganized into Team Based, Event Based, EPG Generation sections
- Consolidated time variables to single `{game_time}` that honors settings

---

*Read CLAUDE.md for complete technical documentation.*

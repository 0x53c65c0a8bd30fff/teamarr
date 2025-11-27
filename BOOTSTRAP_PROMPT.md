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

- **Templates**: EPG formatting (title, description, filler). Two types: "team" and "event"
- **Teams**: Add teams with assigned templates for team-based EPG
- **Events**: Import Dispatcharr channel groups, assign templates, test matching
- **EPG**: Generate all EPG (teams + events), view/download XML
- **Channels**: Managed channels created by Teamarr (lifecycle management)
- **Settings**: Dispatcharr URL, timezone, schedule

---

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main Flask app, all routes, core functions |
| `epg/event_epg_generator.py` | Generates XMLTV for event-based streams |
| `epg/team_matcher.py` | Extracts team names from stream names |
| `epg/event_matcher.py` | Finds ESPN events for detected team matchups |
| `epg/epg_consolidator.py` | Merges team + event EPGs into final output |
| `epg/channel_lifecycle.py` | Channel creation/deletion scheduling |
| `api/dispatcharr_client.py` | Dispatcharr API client (M3U + Channels) |
| `api/espn_client.py` | ESPN API wrapper |
| `templates/event_epg.html` | Events page (import groups, test matching) |
| `templates/channels.html` | Managed channels list |

---

## Core Functions in app.py

```python
# Refresh a single event group (M3U, matching, EPG gen, channels)
refresh_event_group_core(group, m3u_manager, wait_for_m3u=True)

# Unified EPG generation (both scheduled and manual)
generate_all_epg(progress_callback=None, settings=None)
```

---

## User Workflow

1. Create templates (team or event type)
2. Add teams and assign team templates (for team-based EPG)
3. Import Dispatcharr groups and assign event templates (for event-based EPG)
4. Click "Test" on event groups to verify stream matching
5. Go to EPG tab and click "Generate EPG" to build everything
6. Check Channels tab to see managed channels created

---

## Recent Architecture Decisions

- **No Refresh button** - Removed from Events page; all EPG generation happens via "Generate EPG"
- **Test vs Generate** - "Test" = lightweight matching preview, "Generate EPG" = full build
- **Unified generation** - `generate_all_epg()` handles both team and event EPG
- **Managed channels** live on dedicated Channels tab (not Events tab)
- **Channel lifecycle** - Channels auto-created/deleted based on event timing settings

---

## Database Tables

- `templates` - EPG formatting templates (team or event type)
- `teams` - User's tracked teams with template assignment
- `event_epg_groups` - Imported Dispatcharr groups with settings
- `managed_channels` - Channels created by Teamarr for lifecycle tracking

---

## EPG Output Files

All in `/app/data/`:
- `teams.xml` - Team-based EPG
- `events.xml` - Merged event-based EPG (all groups)
- `event_epg_*.xml` - Per-group event EPGs
- `teamarr.xml` - Final consolidated EPG (teams + events)

---

## Pending Work

See CLAUDE.md "What's Next" section for planned features.

---

## Common Tasks

**Add new template variable:**
1. Add to `config/variables.json`
2. Implement in `epg/event_template_engine.py` (for event) or `epg/template_engine.py` (for team)
3. Add UI help text in `templates/template_form.html`

**Add new API endpoint:**
1. Add route in `app.py`
2. Document in CLAUDE.md

**Debug stream matching:**
1. Use "Test" button on Events page
2. Check logs for `team_matcher` and `event_matcher` debug messages
3. Check team aliases in Settings

---

*Read CLAUDE.md for complete technical documentation.*

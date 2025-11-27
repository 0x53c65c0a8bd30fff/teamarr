# Teamarr

Dynamic EPG Generator for Sports Channels.

## Alpha Version (dev-withevents)

The `dev-withevents` tag is the current alpha with:
- Event-based EPG generation for Dispatcharr channel groups
- Automatic channel creation/deletion lifecycle management
- Team matching from stream names (e.g., "Panthers @ 49ers")
- ESPN event lookup for matched teams

All team-based EPG functions from main/dev are fully preserved.

### Docker Compose

```yaml
services:
  teamarr:
    image: ghcr.io/egyptiangio/teamarr:dev-withevents
    container_name: teamarr
    restart: unless-stopped
    ports:
      - 9195:9195
    volumes:
      - ./data:/app/data
    environment:
      - TZ=America/Detroit
```

### Access

Web interface: **http://localhost:9195**

---

## Upgrading from dev/main

Database migrations run automatically. Your existing teams and templates will be preserved.

## License

MIT

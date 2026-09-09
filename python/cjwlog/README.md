# cjwlog

## Dev

```
uv run uvicorn cjwlog.logger.main:app --host 0.0.0.0 --port 8000 --reload
```

`--reload` restarts the process on every file save — dev convenience only, drop
it for the real deployment (see below).

## Data

SQLite file at `data/cjwlog.db` (override with `CJWLOG_DB_PATH`), gitignored.
After every write it's copied into the SeaweedFS bucket mount
## GPS logging

`POST /owntracks` accepts OwnTracks-shaped location JSON (`_type: "location"`,
`lat`/`lon`/`tst`/...), writes to the `gps` table. Used by `swift/cjwlog-gps`.

Optional basic auth (leave both unset to skip):

```
CJWLOG_OWNTRACKS_USER=...
CJWLOG_OWNTRACKS_PASS=...
```

## Running as a systemd service

```
sudo cp cjwlog.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cjwlog.service

# To restart after changes
sudo systemctl restart cjwlog.service

# Check status / log
systemctl status cjwlog.service
journalctl -u cjwlog.service -f

# Kill
sudo systemctl disable --now cjwlog.service
```

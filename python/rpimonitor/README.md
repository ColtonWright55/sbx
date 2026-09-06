# pimonitor

## Dev workflow

Edit files here as normal on the Arch machine. In a separate terminal, run:

```
./sync-to-pi.sh
```

This mirrors this folder to `~/pimonitor` on the Pi every time you save a
file — no git push/pull needed. Leave it running while you work; Ctrl+C
to stop.

Then SSH into the Pi (`ssh cjw@pi1.lan`) and run scripts straight out of
`~/pimonitor`.


Pull logs from rpi to your machine:
```
rsync -avz cjw@pi1.lan:~/rpimonitor/logs/ ~/github/sbx/python/rpimonitor/logs/

ffmpeg -ss 00:00:03.5 -i logs/raw_20260906_XXXXXX.mp4 -frames:v 1 logs/frames/frame_at_3.5s.jpg
```

## See video (quick check, no code)

On the Pi:
```
rpicam-vid -t 0 --inline --listen --codec mjpeg -o tcp://0.0.0.0:8888
```

On the Arch machine:
```
# Live view
ffplay -f mjpeg tcp://pi1.lan:8888

# To record:
ffmpeg -f mjpeg -i tcp://pi1.lan:8888 ~/Videos/pimonitor.mp4
```

## Requirements

- `inotify-tools` on the Arch machine (`sudo pacman -S inotify-tools`)
- Passwordless SSH key to `cjw@pi1.lan`
- `python3-picamera2`, `python3-opencv` on the Pi

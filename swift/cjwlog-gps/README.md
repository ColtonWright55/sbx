# cjwlog-gps

Background iOS location logger. Posts to cjwlog's `/owntracks` endpoint every ~5 min.

## Build

Builds automatically on push to this dir:
https://github.com/ColtonWright55/sbx/actions/workflows/cjwlog-gps-ios.yml

Download the `CjwlogGPS-ipa` artifact from the latest run, unzip to get `CjwlogGPS.ipa`.

## Install (Sideloadly, Windows, free Apple ID)

1. Plug phone in, drag `.ipa` into Sideloadly, sign in with Apple ID, sideload.
2. Settings > Privacy > Location Services > CjwlogGPS > **Always**.
3. Trust profile: Settings > General > VPN & Device Management.

Free signing expires after 7 days — resideload to renew.

## Config

Edit `Sources/Config.swift` (server URL, tracker ID) before pushing.

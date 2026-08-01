import json, datetime, urllib.request, pathlib

# A few big interchange stations to start. IDs verified from the VBB API.
STATIONS = {
    "900013102": "U Kottbusser Tor",
    "900017101": "U Mehringdamm",
    "900058101": "S Suedkreuz",
    "900110005": "U Senefelderplatz",
    "900007102": "S+U Gesundbrunnen",
    "900120004": "S+U Warschauer Str.",
    "900120005": "S Ostbahnhof",
    "900068201": "S+U Tempelhof",
    "900079221": "S+U Hermannstr.",
    "900009202": "U Osloer Str.",
    "900096101": "S+U Wittenau",
    "900050201": "U Krumme Lanke",
    "900100001": "S+U Friedrichstr",
    "900120003": "S Ostkreuz",
}

def fetch(station_id):
    url = f"https://v6.vbb.transport.rest/stops/{station_id}/departures?duration=30"
    req = urllib.request.Request(url, headers={"User-Agent": "berlin-transit-collector"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

# The stamp we add ourselves — the exact moment we looked. UTC, sortable.
fetched_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
out = pathlib.Path("data"); out.mkdir(exist_ok=True)

for sid, name in STATIONS.items():
    try:
        raw = fetch(sid)
    except Exception as e:
        print(f"skip {name}: {e}"); continue
    record = {"fetched_at": fetched_at, "station_id": sid,
              "station_name": name, "response": raw}
    fname = f"{fetched_at.replace(':', '-')}__{sid}.json"
    (out / fname).write_text(json.dumps(record))
    print(f"saved {name}")
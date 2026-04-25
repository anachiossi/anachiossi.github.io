"""
build_films_json.py
Reads _data/ana_chiossi_data.xlsx and writes _output/films.json.
Run validate.py first. Double-click to run on Windows.
"""

import pandas as pd
import json
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
import sys
from datetime import datetime

DATA_FILE   = "_data/ana_chiossi_data_clean.xlsx"
OUTPUT_FILE = "_output/films.json"
HEROES_DIR  = "assets/images/heroes"
THUMBS_DIR  = "assets/images/thumbs"
PLACEHOLDER = "000x00"

def read(sheet):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet, header=1)
    return df.iloc[0:].reset_index(drop=True)

def split_semi(val):
    """Split a semicolon-separated string into a clean list. Returns [] if empty."""
    if pd.isna(val) or str(val).strip() == "" or str(val).strip() == "nan":
        return []
    return [x.strip() for x in str(val).split(";") if x.strip()]

def clean(val, fallback=None):
    """Return clean string or fallback if empty/nan."""
    if pd.isna(val) or str(val).strip() == "" or str(val).strip() == "nan":
        return fallback
    return str(val).strip()

def image_id(film_id, directory, suffix=""):
    path = os.path.join(directory, f"{film_id}{suffix}.avif")
    return film_id if os.path.exists(path) else PLACEHOLDER

print("\n" + "="*60)
print("  BUILD FILMS JSON")
print("="*60)

if not os.path.exists(DATA_FILE):
    print(f"\n❌  File not found: {DATA_FILE}")
    input("\nPress Enter to close...")
    sys.exit(1)

os.makedirs("_output", exist_ok=True)

print("\n  Reading sheets...")

fd   = read("film_details")
# Filter out films marked as hidden (if column exists)
if "show_on_site" in fd.columns:
    fd = fd[fd["show_on_site"].astype(str).str.upper() != "FALSE"]
aw   = read("all_awards")
ff   = read("film_festivals")
jt   = read("job_timeline")
desc = read("descriptions")

# ── Build lookup maps ────────────────────────────────────────

# awards by _id
awards_map = {}
for _, row in aw.iterrows():
    _id = clean(row.get("_id"))
    if not _id:
        continue
    awards_map.setdefault(_id, []).append({
        "event":          clean(row.get("award_event")),
        "year":           int(row["award_year"]) if pd.notna(row.get("award_year")) else None,
        "category":       clean(row.get("award_category")),
        "result":         clean(row.get("award_result")),
        "is_sound_award": bool(row["is_sound_award"]) if pd.notna(row.get("is_sound_award")) else False,
        "country":        clean(row.get("award_country")),
    })

# festivals by film_id
festivals_map = {}
for _, row in ff.iterrows():
    _id = clean(row.get("film_id"))
    if not _id:
        continue
    festivals_map.setdefault(_id, []).append({
        "name":    clean(row.get("festival_name")),
        "year":    int(row["festival_year"]) if pd.notna(row.get("festival_year")) else None,
        "country": clean(row.get("festival_country")),
    })

# job timeline by _id
timeline_map = {}
for _, row in jt.iterrows():
    _id = clean(row.get("_id"))
    if not _id:
        continue
    start = row.get("job_start_date")
    end   = row.get("job_end_date")
    timeline_map[_id] = {
        "job_start": start.strftime("%Y-%m-%d") if pd.notna(start) and hasattr(start, "strftime") else clean(start),
        "job_end":   end.strftime("%Y-%m-%d")   if pd.notna(end)   and hasattr(end,   "strftime") else clean(end),
    }

# descriptions by _id
desc_map = {}
for _, row in desc.iterrows():
    _id = clean(row.iloc[0])
    description = clean(row.iloc[4])
    if _id:
        desc_map[_id] = description

# ── Build film objects ───────────────────────────────────────
films = []
skipped = []

for _, row in fd.iterrows():
    _id = clean(row.get("_id"))
    if not _id:
        continue

    # roles
    r1 = clean(row.get("role_1"))
    r2 = clean(row.get("role_2"))
    roles = [r for r in [r1, r2] if r]
    role_display = roles[0] if len(roles) == 1 else "; ".join(roles) if roles else None

    # platforms = streaming + tv_channel combined
    platforms = split_semi(row.get("streaming")) + split_semi(row.get("tv_channel"))

    # release_year: keep as int, 0 means upcoming with no confirmed year
    ry = row.get("release_year")
    try:
        release_year = int(float(str(ry))) if pd.notna(ry) else 0
    except:
        release_year = 0

    awards_detail   = awards_map.get(_id, [])
    festivals_detail = festivals_map.get(_id, [])
    timeline        = timeline_map.get(_id, {})

    film = {
        "id":               _id,
        "title":            clean(row.get("title")),
        "type":             clean(row.get("type")),
        "director":         split_semi(row.get("director")),
        "prod_co":          split_semi(row.get("prod_co")),
        "department":       clean(row.get("department")),
        "role":             role_display,
        "release_year":     release_year,
        "release_status":   clean(row.get("release_status")),
        "platforms":        platforms,
        "film_language":    split_semi(row.get("film_language")),
        "prod_country":     split_semi(row.get("prod_country")),
        "imdb_link":        clean(row.get("imdb_link")),
        "image_id":         image_id(_id, HEROES_DIR),
        "thumb_id":         image_id(_id, THUMBS_DIR, "-thumb"),
        "awards_count":     len(awards_detail),
        "festivals_count":  len(festivals_detail),
        "awards_detail":    awards_detail,
        "festivals_detail": festivals_detail,
        "job_start":        timeline.get("job_start"),
        "job_end":          timeline.get("job_end"),
        "description":      desc_map.get(_id),
    }
    films.append(film)

# Sort: release_year=0 first (upcoming), then descending by year
films.sort(key=lambda f: (f["release_year"] != 0, -f["release_year"]))

# ── Write output ─────────────────────────────────────────────
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(films, f, ensure_ascii=False, indent=2)

# ── Summary ──────────────────────────────────────────────────
placeholders = [f["id"] for f in films if f["image_id"] == PLACEHOLDER]
no_desc      = [f["id"] for f in films if not f["description"]]
no_timeline  = [f["id"] for f in films if not f["job_start"]]

print(f"\n  ✅  {len(films)} films written to {OUTPUT_FILE}")
print(f"  🏆  {sum(f['awards_count'] for f in films)} award entries")
print(f"  🎬  {sum(f['festivals_count'] for f in films)} festival entries")

if placeholders:
    print(f"\n  ⚠️   {len(placeholders)} films using placeholder image:")
    for p in placeholders:
        title = next((f["title"] for f in films if f["id"] == p), p)
        print(f"       {p}  {title}")

if no_desc:
    print(f"\n  ⚠️   {len(no_desc)} films with no description:")
    for p in no_desc:
        title = next((f["title"] for f in films if f["id"] == p), p)
        print(f"       {p}  {title}")

if no_timeline:
    print(f"\n  ⚠️   {len(no_timeline)} films with no job timeline dates:")
    for p in no_timeline:
        title = next((f["title"] for f in films if f["id"] == p), p)
        print(f"       {p}  {title}")

print(f"\n  Check _output/films.json before copying to assets/")
print("="*60)
input("\nPress Enter to close...")

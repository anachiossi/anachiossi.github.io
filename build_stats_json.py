"""
build_stats_json.py
Reads _data/ana_chiossi_data.xlsx and writes _output/stats.json.
Used by cv.html and index.html for KPI numbers.
Double-click to run on Windows.
"""

import pandas as pd
import json
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
import sys
from datetime import datetime

DATA_FILE   = "_data/ana_chiossi_data_clean.xlsx"
OUTPUT_FILE = "_output/stats.json"

def read(sheet):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet, header=1)
    return df.iloc[0:].reset_index(drop=True)

def split_semi(val):
    if pd.isna(val) or str(val).strip() in ("", "nan"):
        return []
    return [x.strip() for x in str(val).split(";") if x.strip()]

print("\n" + "="*60)
print("  BUILD STATS JSON")
print("="*60)

if not os.path.exists(DATA_FILE):
    print(f"\n❌  File not found: {DATA_FILE}")
    input("\nPress Enter to close...")
    sys.exit(1)

os.makedirs("_output", exist_ok=True)

print("\n  Reading sheets...")

fd = read("film_details")
aw = read("all_awards")
ff = read("film_festivals")
jt = read("job_timeline")

# Stats count all work done — show_on_site only controls website display,
# not whether a project counts toward career numbers.
active = fd

# ── Project counts ───────────────────────────────────────────
total_projects = len(active[active["type"] != "Commercials"])

type_counts = active["type"].value_counts().to_dict()
features        = int(type_counts.get("Film", 0))
short_films     = int(type_counts.get("Short Film", 0))
tv_series       = int(type_counts.get("TV Series", 0))
doc_film        = int(type_counts.get("Documentary Film", 0))
doc_tv          = int(type_counts.get("Documentary TV", 0))
reality         = int(type_counts.get("Reality Show", 0))
commercials     = int(type_counts.get("Commercials", 0))
documentaries   = doc_film + doc_tv

# ── Department split ─────────────────────────────────────────
dept_counts     = active["department"].value_counts().to_dict()
sound_projects  = int(dept_counts.get("Sound", 0))
camera_projects = int(dept_counts.get("Cinematography", 0))

# ── Roles ────────────────────────────────────────────────────
role_counts = {}
for _, row in active.iterrows():
    for rf in ["role_1", "role_2"]:
        r = str(row.get(rf,"")).strip()
        if r and r != "nan":
            # Normalize role variants into primary roles
            if r == "Add. Prod. Sound Mixer":
                r = "Prod. Sound Mixer"
            elif r in ("2nd Boom Operator", "Dubbing Boom Operator"):
                r = "Boom Operator"
            role_counts[r] = role_counts.get(r, 0) + 1

# ── Countries (filming locations from geo.json) ──────────────
GEO_FILE = "_output/geo.json"
all_countries = set()
if os.path.exists(GEO_FILE):
    try:
        with open(GEO_FILE, encoding="utf-8") as _gf:
            for entry in json.load(_gf):
                c = entry.get("country")
                if c and str(c).strip() not in ("", "None", "nan"):
                    all_countries.add(str(c).strip())
    except Exception:
        pass

if not all_countries:
    # fallback: production countries if geo.json missing or has no country data
    for _, row in active.iterrows():
        for c in split_semi(row.get("prod_country")):
            all_countries.add(c)

countries_count = len(all_countries)
countries_list  = sorted(all_countries)

# ── Languages ────────────────────────────────────────────────
all_languages = set()
for _, row in active.iterrows():
    for l in split_semi(row.get("film_language")):
        all_languages.add(l)
languages_count = len(all_languages)
languages_list  = sorted(all_languages)

# ── Platforms (streaming + tv combined) ─────────────────────
all_platforms = set()
for _, row in active.iterrows():
    for p in split_semi(row.get("streaming")) + split_semi(row.get("tv_channel")):
        all_platforms.add(p)
platforms_count = len(all_platforms)
platforms_list  = sorted(all_platforms)

# ── Production companies ─────────────────────────────────────
all_companies = set()
for _, row in active.iterrows():
    for c in split_semi(row.get("prod_co")):
        all_companies.add(c)
companies_count = len(all_companies)

# ── Years active ─────────────────────────────────────────────
years = []
for _, row in jt.iterrows():
    start = row.get("job_start_date")
    if pd.notna(start):
        try:
            years.append(pd.to_datetime(start).year)
        except:
            pass

if years:
    first_year  = min(years)
    current_year = datetime.now().year
    years_active = current_year - first_year
else:
    first_year   = None
    years_active = None

# ── Awards ───────────────────────────────────────────────────
total_nominations = len(aw)
total_wins        = len(aw[aw["award_result"].astype(str).str.strip() == "Winner"])
sound_awards_wins = len(aw[(aw["award_result"].astype(str).str.strip() == "Winner") &
                            (aw["is_sound_award"].astype(str).str.upper() == "TRUE")])

# ── Festivals ────────────────────────────────────────────────
total_festival_entries = len(ff)
unique_festivals       = ff["festival_name"].nunique()

# ── Assemble stats.json ──────────────────────────────────────
stats = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),

    "career": {
        "total_projects":   total_projects,
        "years_active":     years_active,
        "first_year":       first_year,
        "countries_worked": countries_count,
        "countries_list":   countries_list,
        "languages_count":  languages_count,
        "languages_list":   languages_list,
    },

    "by_type": {
        "features":     features,
        "short_films":  short_films,
        "tv_series":    tv_series,
        "documentaries": documentaries,
        "reality":      reality,
        "commercials":  commercials,
    },

    "by_department": {
        "sound_projects":   sound_projects,
        "camera_projects":  camera_projects,
    },

    "roles": role_counts,

    "platforms": {
        "count": platforms_count,
        "list":  platforms_list,
    },

    "production": {
        "companies_count": companies_count,
    },

    "awards": {
        "total_nominations": total_nominations,
        "total_wins":        total_wins,
        "sound_award_wins":  sound_awards_wins,
    },

    "festivals": {
        "total_entries":   total_festival_entries,
        "unique_festivals": unique_festivals,
    },
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

# ── Summary ──────────────────────────────────────────────────
print(f"\n  ✅  stats.json written to {OUTPUT_FILE}")
print(f"\n  Career snapshot:")
print(f"    {total_projects} projects (excl. Commercials)  |  {years_active} years active  |  {countries_count} countries  |  {languages_count} languages")
print(f"    {sound_projects} sound  |  {camera_projects} camera")
print(f"    {total_wins}/{total_nominations} wins/nominations  |  {total_festival_entries} festival entries")
print(f"    {companies_count} production companies  |  {platforms_count} platforms")
print(f"\n  Check _output/stats.json before copying to assets/")
print("="*60)
input("\nPress Enter to close...")

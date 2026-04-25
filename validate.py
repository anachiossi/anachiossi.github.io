"""
validate.py
Reads _data/ana_chiossi_data.xlsx and checks for data quality issues.
Run this before any build script. Double-click to run on Windows.
"""

import pandas as pd
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

DATA_FILE = "_data/ana_chiossi_data_clean.xlsx"

VALID_TYPES     = {"Film","Short Film","TV Series","Documentary Film","Documentary TV","Reality Show","Commercials"}
VALID_STATUSES  = {"released","upcoming","canceled"}
VALID_DEPTS     = {"Sound","Cinematography"}
VALID_RESULTS   = {"Winner","Nominated"}
VALID_ROLES_SND = {"Prod. Sound Mixer","Add. Prod. Sound Mixer","Boom Operator","2nd Boom Operator","Dubbing Boom Operator","Sound Utility","Sound Trainee"}
VALID_ROLES_CAM = {"Focus Puller","2nd Camera Assistant","Loader","Still Photographer","Video Assistant"}
SEMI_FIELDS     = {"director","prod_co","streaming","tv_channel","film_language","prod_country"}

errors   = []
warnings = []

def err(sheet, row, col, msg):
    errors.append(f"  ❌  [{sheet}] row {row} | {col}: {msg}")

def warn(sheet, row, col, msg):
    warnings.append(f"  ⚠️   [{sheet}] row {row} | {col}: {msg}")

def read(sheet):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet, header=1)
    return df.iloc[0:].reset_index(drop=True)

print("\n" + "="*60)
print("  VALIDATE — ana_chiossi_data_clean.xlsx")
print("="*60)

if not os.path.exists(DATA_FILE):
    print(f"\n❌  File not found: {DATA_FILE}")
    input("\nPress Enter to close...")
    sys.exit(1)

# ── film_details ─────────────────────────────────────────────
fd = read("film_details")
fd_ids = set(fd["_id"].dropna().astype(str).str.strip().tolist())

for i, row in fd.iterrows():
    r = i + 3
    _id = str(row.get("_id","")).strip()

    if not _id or _id == "nan":
        err("film_details", r, "_id", "Missing _id")
        continue

    t = str(row.get("type","")).strip()
    if t not in VALID_TYPES:
        err("film_details", r, "type", f"'{t}' not in allowed types")

    # show_on_site
    sos = str(row.get("show_on_site","")).strip().upper()
    if sos not in ("TRUE", "FALSE", "NAN", ""):
        err("film_details", r, "show_on_site", f"'{sos}' must be TRUE or FALSE")

    rs = str(row.get("release_status",""))
    if rs != rs.strip():
        err("film_details", r, "release_status", "Trailing/leading space detected")
    if rs.strip() not in VALID_STATUSES:
        err("film_details", r, "release_status", f"'{rs.strip()}' not in allowed values")

    ry = row.get("release_year")
    if pd.notna(ry) and str(ry).strip() != "0":
        try:
            yr = int(float(str(ry)))
            if yr < 1990 or yr > 2030:
                warn("film_details", r, "release_year", f"Unusual year: {yr}")
        except:
            err("film_details", r, "release_year", f"Not a valid year: {ry}")

    dept = str(row.get("department","")).strip()
    if dept not in VALID_DEPTS:
        err("film_details", r, "department", f"'{dept}' not in allowed values")

    for role_field in ["role_1","role_2"]:
        rv = str(row.get(role_field,"")).strip()
        if rv and rv != "nan":
            valid_roles = VALID_ROLES_SND if dept == "Sound" else VALID_ROLES_CAM
            if ";" in rv:
                err("film_details", r, role_field, f"Contains ';' — split into role_1 and role_2")
            elif rv not in valid_roles:
                warn("film_details", r, role_field, f"'{rv}' not in {dept} vocabulary")

    for field in SEMI_FIELDS:
        val = str(row.get(field,""))
        if "," in val and ";" not in val and field in {"prod_co","director","film_language","prod_country"}:
            warn("film_details", r, field, f"Uses ',' as separator — should be '; '")

    for field in ["title","director","prod_co"]:
        val = str(row.get(field,""))
        if "\n" in val or "\t" in val:
            err("film_details", r, field, "Contains line break or tab")

print(f"\n  film_details:   {len(fd)} rows checked")

# ── all_awards ───────────────────────────────────────────────
aw = read("all_awards")
for i, row in aw.iterrows():
    r = i + 3
    _id = str(row.get("_id","")).strip()
    if _id not in fd_ids:
        err("all_awards", r, "_id", f"'{_id}' not found in film_details")
    result = str(row.get("award_result","")).strip()
    if result not in VALID_RESULTS:
        err("all_awards", r, "award_result", f"'{result}' not in allowed values")
    isa = row.get("is_sound_award")
    if pd.isna(isa):
        err("all_awards", r, "is_sound_award", "Empty — must be TRUE or FALSE")

print(f"  all_awards:     {len(aw)} rows checked")

# ── film_festivals ───────────────────────────────────────────
ff = read("film_festivals")
for i, row in ff.iterrows():
    r = i + 3
    _id = str(row.get("film_id","")).strip()
    if _id not in fd_ids:
        err("film_festivals", r, "film_id", f"'{_id}' not found in film_details")

print(f"  film_festivals: {len(ff)} rows checked")

# ── job_timeline ─────────────────────────────────────────────
jt = read("job_timeline")
for i, row in jt.iterrows():
    r = i + 3
    _id = str(row.get("_id","")).strip()
    if _id not in fd_ids:
        err("job_timeline", r, "_id", f"'{_id}' not found in film_details")
    for datecol in ["job_start_date","job_end_date"]:
        val = row.get(datecol)
        if pd.isna(val):
            warn("job_timeline", r, datecol, "Empty date")

print(f"  job_timeline:   {len(jt)} rows checked")

# ── film_geo ─────────────────────────────────────────────────
geo = read("film_geo")
geo_ids = set(geo["_id"].dropna().astype(str).str.strip().tolist())
for i, row in geo.iterrows():
    r = i + 3
    _id = str(row.get("_id","")).strip()
    if _id not in fd_ids:
        err("film_geo", r, "_id", f"'{_id}' not found in film_details")

print(f"  film_geo:       {len(geo)} rows checked")

# ── descriptions ─────────────────────────────────────────────
desc = read("descriptions")
desc_ids = set(desc.iloc[:,0].dropna().astype(str).str.strip().tolist())
missing_desc = fd_ids - desc_ids
for mid in sorted(missing_desc):
    warn("descriptions", "-", "_id", f"'{mid}' has no description entry")

print(f"  descriptions:   {len(desc)} rows checked")

# ── cross-check geo coverage ─────────────────────────────────
missing_geo = fd_ids - geo_ids
for mid in sorted(missing_geo):
    warn("film_geo", "-", "_id", f"'{mid}' missing from film_geo")

# ── Results ──────────────────────────────────────────────────
print("\n" + "="*60)

if errors:
    print(f"\n  {len(errors)} ERROR(S) — fix before building:\n")
    for e in errors:
        print(e)

if warnings:
    print(f"\n  {len(warnings)} WARNING(S):\n")
    for w in warnings:
        print(w)

if not errors and not warnings:
    print("\n  ✅  All checks passed. Safe to build.\n")
elif not errors:
    print(f"\n  ✅  No errors. {len(warnings)} warning(s) — review before pushing.\n")
else:
    print(f"\n  ❌  {len(errors)} error(s) must be fixed before building.\n")

print("="*60)
input("\nPress Enter to close...")

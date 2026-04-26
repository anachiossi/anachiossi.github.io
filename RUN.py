"""
RUN.py
Master launcher. Double-click this to run the full pipeline.
Runs: validate → build_films_json → build_geo_json → build_stats_json → deploy to assets/
"""

import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def run_script(name):
    print(f"\n{'='*60}")
    print(f"  RUNNING: {name}")
    print(f"{'='*60}\n")
    result = subprocess.run([sys.executable, name], capture_output=False)
    return result.returncode

print("\n" + "="*60)
print("  ANA CHIOSSI — DATA PIPELINE")
print("  validate → build_films_json → build_geo_json → build_stats_json → deploy")
print("="*60)

# ── Step 1: Validate ─────────────────────────────────────────
print("\n  Step 1 of 4: Validating data...")
code = run_script("validate.py")
if code != 0:
    print("\n  ❌  Validation failed. Fix errors before building.")
    input("\nPress Enter to close...")
    sys.exit(1)

# ── Step 2: Build films JSON ──────────────────────────────────
print("\n  Step 2 of 4: Building films.json...")
code = run_script("build_films_json.py")
if code != 0:
    print("\n  ❌  build_films_json.py failed.")
    input("\nPress Enter to close...")
    sys.exit(1)

# ── Step 3: Build geo JSON ────────────────────────────────────
print("\n  Step 3 of 4: Building geo.json...")
code = run_script("build_geo_json.py")
if code != 0:
    print("\n  ❌  build_geo_json.py failed.")
    input("\nPress Enter to close...")
    sys.exit(1)

# ── Step 4: Build stats JSON ──────────────────────────────────
print("\n  Step 4 of 4: Building stats.json...")
code = run_script("build_stats_json.py")
if code != 0:
    print("\n  ❌  build_stats_json.py failed.")
    input("\nPress Enter to close...")
    sys.exit(1)
    
# ── Step 5: Replace assets? ──────────────────────────────────
print("\n" + "="*60)
answer = input("\n  Replace assets/films.json, stats.json, geo.json with new outputs? (y/n): ").strip().lower()

if answer == "y":
    import shutil
    os.makedirs("_backup", exist_ok=True)
    
    for name in ["films.json", "stats.json", "geo.json"]:
        src = os.path.join("_output", name)
        dst = os.path.join("assets", name)
        bak = os.path.join("_backup", name)
        if os.path.exists(src):
            if os.path.exists(dst):
                shutil.copy2(dst, bak)
            shutil.copy2(src, dst)
            print(f"  ✅  {name} → assets/ (old version backed up to _backup/)")

    # ── Step 6: Git push? ────────────────────────────────────
    answer2 = input("\n  Push to GitHub? (y/n): ").strip().lower()
    if answer2 == "y":
        msg = input("  Commit message: ").strip()
        if not msg:
            msg = "Update data"
        os.system("git add .")
        os.system(f'git commit -m "{msg}"')
        os.system("git push")
        print("\n  ✅  Pushed. Site will update in ~2 minutes.")
else:
    print("\n  Skipped. Files remain in _output/ for review.")

print("\n" + "="*60)
print("  ✅  Pipeline complete.")
print("="*60)
input("\nPress Enter to close...")

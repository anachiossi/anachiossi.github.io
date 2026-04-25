"""
RUN.py
Master launcher. Double-click this to run the full pipeline.
Runs: validate → build_films_json → build_stats_json
Then asks if you want to run build_geo_json (slower, makes API calls).
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
print("  validate → build_films_json → build_stats_json")
print("="*60)

# ── Step 1: Validate ─────────────────────────────────────────
print("\n  Step 1 of 3: Validating data...")
code = run_script("validate.py")
if code != 0:
    print("\n  ❌  Validation failed. Fix errors before building.")
    input("\nPress Enter to close...")
    sys.exit(1)

# ── Step 2: Build films JSON ──────────────────────────────────
print("\n  Step 2 of 3: Building films.json...")
code = run_script("build_films_json.py")
if code != 0:
    print("\n  ❌  build_films_json.py failed.")
    input("\nPress Enter to close...")
    sys.exit(1)

# ── Step 3: Build stats JSON ──────────────────────────────────
print("\n  Step 3 of 3: Building stats.json...")
code = run_script("build_stats_json.py")
if code != 0:
    print("\n  ❌  build_stats_json.py failed.")
    input("\nPress Enter to close...")
    sys.exit(1)

# ── Optional: Geo ─────────────────────────────────────────────
print("\n" + "="*60)
print("\n  Optional: Run build_geo_json.py?")
print("  Only needed when you added a new filming location.")
answer = input("  Run geo script? (y/n): ").strip().lower()

if answer == "y":
    code = run_script("build_geo_json.py")
    if code != 0:
        print("\n  ⚠️   build_geo_json.py had issues. Check output above.")

# ── Done ──────────────────────────────────────────────────────
print("\n" + "="*60)
print("""
  ✅  Pipeline complete.

  Next steps:
  1. Check the _output/ folder
  2. Compare with assets/ if needed
  3. When happy, copy:
       _output/films.json  →  assets/films.json
       _output/stats.json  →  assets/stats.json
       _output/geo.json    →  assets/geo.json   (if you ran geo)

  Then push to GitHub:
       git add .
       git commit -m "Update data"
       git push
""")
print("="*60)
input("\nPress Enter to close...")

"""
RUN.py
Master launcher. Double-click this to run the full pipeline.
Runs: validate → build_films_json → build_geo_json → build_stats_json
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
print("  validate → build_films_json → build_geo_json → build_stats_json")
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

# ── Done ──────────────────────────────────────────────────────
print("\n" + "="*60)
print("""
  ✅  Pipeline complete.

  Next steps:
  1. Check the _output/ folder
  2. Compare with assets/ if needed
  3. When happy, copy:
       _output/films.json  →  assets/films.json
       _output/geo.json    →  assets/geo.json
       _output/stats.json  →  assets/stats.json

  Then push to GitHub:
       git add .
       git commit -m "Update data"
       git push
""")
print("="*60)
input("\nPress Enter to close...")

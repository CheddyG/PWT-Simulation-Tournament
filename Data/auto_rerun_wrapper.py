import os
import subprocess
import time
import sys







# Directory where this script lives (probably .../PWT-Simulation-Tournament/Data)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Output directory (will be created inside the same folder as this script)
OUTPUT_DIR = os.path.join(BASE_DIR, "Tour100")
os.makedirs(OUTPUT_DIR, exist_ok=True)

EXPECTED_BATTLES = 1  # or 2628 for full 73-trainer tournament
MAX_ITERATIONS = 100

def is_output_valid(path, min_battles):
    if not os.path.exists(path):
        return False
    with open(path, 'r', encoding="utf-8") as f:
        content = f.read()
    return content.count("]]]]]\n") >= min_battles

def run_simulation_script(output_path):
    print(f"🔁 Running tournament iteration, output -> {output_path}")

    # Path to runSimulations.py (assumes it's in the same folder as this script)
    run_sim_path = os.path.join(BASE_DIR, "runSimulations.py")

    # Use the SAME Python that is running this script
    subprocess.run(
        [sys.executable, run_sim_path, output_path],
        check=False  # set True if you want it to crash on error
    )

def main_loop():
    base_name = "output"
    extension = ".txt"

    current_iteration = 0
    while current_iteration < MAX_ITERATIONS:
        next_output_file = os.path.join(
            OUTPUT_DIR,
            f"{base_name}{current_iteration + 1}{extension}"
        )

        if not is_output_valid(next_output_file, EXPECTED_BATTLES):
            print(f"⛔ {next_output_file} missing or incomplete (< {EXPECTED_BATTLES} battles). Retrying simulation...")
            run_simulation_script(next_output_file)
            time.sleep(2)
        else:
            print(f"✅ {next_output_file} complete. Proceeding to next iteration.")
            current_iteration += 1

    print(f"🎉 All {MAX_ITERATIONS} iterations complete. Wrapper exiting.")

if __name__ == "__main__":
    main_loop()

import json
import subprocess
import threading
import time
import os
import sys
from timeit import default_timer as timer

# ============ New Helper Function to Get Next Output File ============
def get_next_output_filename(base_dir="Tour100", base_name="output", extension=".txt"):
    os.makedirs(base_dir, exist_ok=True)  # Make directory if it doesn't exist
    i = 1
    while os.path.exists(os.path.join(base_dir, f"{base_name}{i}{extension}")):
        i += 1
    return os.path.join(base_dir, f"{base_name}{i}{extension}")

def write_builds_to_file(lines, build_indices, file_path):
    with open(file_path, "w") as f:
        f.truncate(0)
        for build_index in build_indices:
            build_start = build_index[1]
            while build_start > 0 and not lines[build_start].startswith('|'):
                build_start -= 1
            f.write(lines[build_start].replace("|", "").strip() + "\n")
            for line in lines[build_start + 1:]:
                if line.startswith('|'):
                    break
                f.write(line)
            f.write("\n")

def runSimulation(matchup, threadNo, filename, teamNumbers):
    team1No = get_keys_from_value(teamNumbers, matchup[0])[0]
    team2No = get_keys_from_value(teamNumbers, matchup[1])[0]

    with open(filename) as f:
        lines = f.readlines()
        write_builds_to_file(lines, matchup[0], f"./WorkerFiles/{threadNo}1.txt")
        write_builds_to_file(lines, matchup[1], f"./WorkerFiles/{threadNo}2.txt")

        while True:
            mycommand = "cd ../pokemon-showdown && node ./dist/sim/examples/Simulation-test-1 " + threadNo + " " + str(team1No) + " " + str(team2No)
            result = subprocess.getoutput(mycommand)
            if not (result.startswith("node:internal") or result.startswith("TypeError") or result.startswith("runtime")) or result.endswith("Node.js v21.1.0"):
                try:
                    if not (result[:40].split("\n")[2].startswith("TypeError")):
                        break
                except:
                    break

        with open(f"./WorkerOutputs/{threadNo}.txt", "a") as o:
            o.write(result + "\n]]]]]\n")
        return result

def get_keys_from_value(d, val):
    return [k for k, v in d.items() if v == val]

# ============ Main Execution ============
filename = "Inputs/GymLeaderPokemon.txt"
noOfThreads = 6

with open('Inputs/tournament_battles.json', 'r') as infile:
    teams = json.load(infile)

with open('Inputs/GymLeaderTeams.json', 'r') as infile:
    teamNumbers = json.load(infile)

print(len(teams))
n = 100  # Number of battles to stop running after

noOfTeams = len(teamNumbers)

# ============ Get Output Filename from CLI Arg (Optional) ============
if len(sys.argv) > 1:
    output_filename = sys.argv[1]
else:
    output_filename = get_next_output_filename()

print(f"Writing to {output_filename}")

# Clear previous worker outputs
infiles = [str(i + 1) for i in range(noOfThreads)] + ["0"]
for i in infiles:
    with open(f"./WorkerOutputs/{i}.txt", "w") as output:
        output.truncate(0)

subprocess.getoutput("cd ../pokemon-showdown && node build")
threads = []
start = time.time()

# Parallel battle execution in chunks
while len(teams) >= noOfThreads:
    for i in range(noOfThreads):
        thread = threading.Thread(target=runSimulation, args=(teams[0], str(i+1), filename, teamNumbers))
        threads.append(thread)
        teams.pop(0)

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    threads.clear()
    print(len(teams))

while len(teams) >= 25:
    for i in range(25):
        thread = threading.Thread(target=runSimulation, args=(teams[0], str(i+1), filename, teamNumbers))
        threads.append(thread)
        teams.pop(0)

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    threads.clear()
    print(len(teams))

while len(teams) >= 10:
    for i in range(10):
        thread = threading.Thread(target=runSimulation, args=(teams[0], str(i+1), filename, teamNumbers))
        threads.append(thread)
        teams.pop(0)

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    threads.clear()
    print(len(teams))

# Final leftover battles
for battle in teams:
    runSimulation(battle, "0", filename, teamNumbers)

end = time.time()

# Write combined output
with open(output_filename, "a") as outfile:
    for i in infiles:
        with open(f"./WorkerOutputs/{i}.txt", "r") as output:
            outfile.writelines(output.readlines())

# Clear worker outputs again
for i in infiles:
    with open(f"./WorkerOutputs/{i}.txt", "w") as output:
        output.truncate(0)

print("ran in " + str(end - start) + " Seconds Overall")
print(str((end - start) / n) + " Seconds Per Sim On Average")


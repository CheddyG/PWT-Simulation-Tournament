# Ultimate Pokémon World Tournament Simulator

Built upon the foundation laid by [CRZShadows](https://github.com/cRz-Shadows/Pokemon_Trainer_Tournament_Simulator), this project expands and personalizes the tournament simulation concept with added parsing tools, and analytics.

This is my first project! Let me know if something doesn't add up!

This project extends [Pokémon Showdown](https://github.com/smogon/pokemon-showdown) with custom AI, ranking models, and powerful statistical analysis tools. It is designed to run, parse, and evaluate tens of thousands of battles programmatically.

---

## Core Features
-  Custom AI battle logic powered by Showdown
-  Multithreaded battle simulation for large datasets
-  Ranking models: Elo + Bradley-Terry
-  Animated trainer card generator
-  Heatmaps and statistical summaries
-  Battle rerun + error analysis tooling

---

## Quick Start

### 1. Clone and install
```bash
git clone --recursive https://github.com/poke-nerd/PWT-Simulation-Tournament.git
cd PWT-Simulation-Tournament
conda env create -f environment.yml
conda activate pwt-sim
```

### 2. Build Pokémon Showdown
```bash
cd pokemon-showdown
npm install
node build
```

---

## How It Works

### Simulation Pipeline
1. **Prepare trainer teams:** in `Data/Inputs/GymLeaderTeams.txt` + `GymLeaderPokemon.txt`
2. **Generate matchups:**
   ```bash
   python Data/BuildBattles.py
   ```
3. **Run simulations (multithreaded):**
   ```bash
   python Data/runSimulations.py
	(or yoiu can run auto_rerun_wrapper.py to run en masse)
   ```
4. **Handle errors (optional):**
   Use `get_battles_to_rerun.py`, `findErrors.py`, and `removeErrors.py`
5. **Parse + analyze results:**
   ```bash
   python Data/parseOutput.py           # heatmap (PNG)
   python Data/parseOutput_CSV.py       # CSV matrix
   python Data/ranking_elo.py           # Elo ranking
   python Data/ranking_bt.py            # Bradley-Terry
   ```(If you want all these ust use auto_parser.py)
6. **Visualize or animate results** with:
   ```bash
   python trainer_card_mkr.py
   python html_parser.py
   ```

---

## Key Utility Scripts
All scripts below are located in the `Data/` directory unless noted otherwise:

| Script/File                  | Description |
|-----------------------------|-------------|
| `BuildTour.py`              | Builds randomized tournament brackets |
| `auto_parser_csv.py`        | Automatically aggregates results into CSV format |
| `auto_rerun_wrapper.py`     | Reruns failed battles automatically |
| `check_count.py`            | Verifies completeness of output logs |
| `count_cheren_battles.py`   | Debug tool for per-trainer analysis |
| `graph.py`                  | Generates trainer winrate heatmaps |
| `trainer_winrate_heatmap.html` | HTML version of winrate heatmap |
| `master_battle_matrix.csv`  | Master winrate summary |
| `master_trainer_stats.csv`  | Aggregated trainer statistics |


---

## Modified Showdown Behavior

### Enhancements in Simulation Layer:
- `sim/pokemon.ts` → adds info like boost tables, trap status, species, and HP
- `sim/side.ts` → includes side condition states (e.g., Tailwind)
- `sim/dex-moves.ts` → improved multi-hit move handling

---

## Repo Overview
```
PWT-Simulation-Tournament/
├── Data/                       # All tournament logic and data
│   ├── Inputs/                # Trainer/Pokémon team definitions
│   ├── Output/                # Replays, stats, trainer cards
│   ├── UsefulDatasets/       # CSVs and winrate matrices
│   ├── Tour100/, WorkerFiles/  # Large simulation batches
│   ├── BuildBattles.py, runSimulations.py, ranking_elo.py, etc.
│   └── trainer_winrate_heatmap.html
├── pokemon-showdown/          # Forked + modified Showdown engine
├── trainer_card_mkr.py        # Generates trainer cards
├── html_parser.py             # Converts logs to replay format
├── environment.yml            # Conda environment
└── manual.md                  # Additional usage notes
```

---

## Credits
- Forked from [CRZShadow's Simulators](https://github.com/cRz-Shadows/Pokemon_Trainer_Tournament_Simulator)
- Built on top of [Pokémon Showdown](https://github.com/smogon/pokemon-showdown)

---


## Future Plans
- Make Youtube Video explaining how to run one yourelf
- Animated replays w/ trainer cards and battle stats
- Support for Multiple Generations
- Eventually battle bot



import os
import shutil
import pandas as pd

from parsing.parseOutput_CSV import parse_battles, save_to_csv, save_matrix_to_csv
from parsing.bradley_terry import run_bt_matrix
from parsing.rank_pipeline import run_full_ranking_pipeline

# Define folders
output_folder = "Tour100"
parsed_output_folder = "ParsedOutputs"
os.makedirs(parsed_output_folder, exist_ok=True)

# Initialize data
total_trainer_stats = {}
total_battle_matrix = {}
file_count = 0

# Process each simulation output file
for filename in sorted(os.listdir(output_folder)):
    if filename.startswith("output") and filename.endswith(".txt"):
        file_count += 1
        print(f"Processing {filename}")

        results, battle_matrix = parse_battles(os.path.join(output_folder, filename))

        # Save intermediate files
        save_to_csv(results, os.path.join(parsed_output_folder, f"trainer_stats_{filename}.csv"))
        save_matrix_to_csv(battle_matrix, os.path.join(parsed_output_folder, f"battle_matrix_{filename}.csv"))

        # Aggregate stats
        for trainer, record in results:
            if trainer not in total_trainer_stats:
                total_trainer_stats[trainer] = {'wins': 0, 'losses': 0, 'ties': 0}
            total_trainer_stats[trainer]['wins'] += record['wins']
            total_trainer_stats[trainer]['losses'] += record['losses']
            total_trainer_stats[trainer]['ties'] += record['ties']

        # Aggregate battle matrix
        for trainer1 in battle_matrix:
            if trainer1 not in total_battle_matrix:
                total_battle_matrix[trainer1] = {}
            for trainer2 in battle_matrix[trainer1]:
                if trainer2 not in total_battle_matrix[trainer1]:
                    total_battle_matrix[trainer1][trainer2] = {'wins': 0, 'losses': 0, 'ties': 0}
                total_battle_matrix[trainer1][trainer2]['wins'] += battle_matrix[trainer1][trainer2]['wins']
                total_battle_matrix[trainer1][trainer2]['losses'] += battle_matrix[trainer1][trainer2]['losses']
                total_battle_matrix[trainer1][trainer2]['ties'] += battle_matrix[trainer1][trainer2]['ties']

# Calculate win/loss ratios and toughest/easiest opponents
for trainer in total_trainer_stats:
    win_loss_ratios = {}
    
    # Calculate win/loss ratio for each matchup
    for opponent in total_battle_matrix[trainer]:
        wins = total_battle_matrix[trainer].get(opponent, {}).get('wins', 0)
        losses = total_battle_matrix[trainer].get(opponent, {}).get('losses', 0)
        
        # Avoid division by zero
        win_loss_ratio = wins / losses if losses != 0 else float('inf')
        win_loss_ratios[opponent] = win_loss_ratio

    # Sort opponents by win/loss ratio for hardest and easiest matchups
    sorted_opponents = sorted(win_loss_ratios.items(), key=lambda x: x[1], reverse=True)

    # Top 3 hardest matchups (highest win/loss ratio)
    total_trainer_stats[trainer]['easiest_opponent'] = [opponent for opponent, ratio in sorted_opponents[:1]]

    # Top 3 easiest matchups (lowest win/loss ratio)
    total_trainer_stats[trainer]['toughest_opponent'] = [opponent for opponent, ratio in sorted_opponents[-1:]]

# Compute win/loss ratios for all trainers
for trainer in total_trainer_stats:
    wins = total_trainer_stats[trainer]['wins']
    losses = total_trainer_stats[trainer]['losses']
    total_trainer_stats[trainer]['win_loss_ratio'] = wins / losses if losses != 0 else float('inf')

# Save the final aggregated results and battle matrix
pd.DataFrame.from_dict(total_trainer_stats, orient='index').reset_index().rename(columns={'index': 'Trainer'}).to_csv("master_trainer_stats.csv", index=False)
save_matrix_to_csv(total_battle_matrix, "master_battle_matrix.csv")
from parsing.parseOutput_CSV import save_win_matrix_to_csv
save_win_matrix_to_csv(total_battle_matrix, "master_battle_matrix_wins.csv")

# Sort trainer stats by Win/Loss Ratio
df = pd.read_csv('master_trainer_stats.csv')
df_sorted = df.sort_values(by='win_loss_ratio', ascending=False).reset_index(drop=True)

# Add Placement as 2nd column
df_sorted.insert(1, 'Placement', df_sorted.index + 1)

# Save updated master stats
df_sorted.to_csv('master_trainer_stats.csv', index=False)

# Run full ranking pipeline
print("\n🔧 Running Bradley-Terry matrix model...")
run_bt_matrix()

print("🧠 Running full ranking pipeline (tiers + Elo)...")
run_full_ranking_pipeline()

# Clean up intermediate CSVs
shutil.rmtree(parsed_output_folder)
cleanup_files = [
    "trainer_ranked_tiers.csv",
    "trainer_ranked_tiers_elo.csv",
    "master_trainer_stats_bt_matrix.csv"
]
for file in cleanup_files:
    if os.path.exists(file):
        os.remove(file)
        print(f"🗑️ Deleted temporary file: {file}")

print(f"\n✅ Processed {file_count} output files. Master trainer stats and battle matrix updated.")


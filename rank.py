import json
import random
import math
import os

def ranking_loss(order, games):
    """Compute the total ranking inconsistency loss for a given order."""
    index = {team: i for i, team in enumerate(order)}
    loss = 0
    for g in games:
        w = index[g["winner"]]
        l = index[g["loser"]]
        loss += max(0, 1 + w - l)
    return loss


def optimize_ranking(games, teams_file=None, max_iter=100000, seed=42):
    """Use simulated annealing to find a near-optimal ranking."""
    random.seed(seed)
    teams = list({g["winner"] for g in games} | {g["loser"] for g in games})
    random.shuffle(teams)
    
    best_order = teams[:]
    best_loss = ranking_loss(best_order, games)
    current_order = best_order[:]
    current_loss = best_loss

    temperature = 1.0

    for step in range(max_iter):
        # Randomly swap two teams
        i, j = random.sample(range(len(teams)), 2)
        new_order = current_order[:]
        new_order[i], new_order[j] = new_order[j], new_order[i]

        new_loss = ranking_loss(new_order, games)
        delta = new_loss - current_loss

        # Accept new order if better or probabilistically if worse
        if delta < 0 or random.random() < math.exp(-delta / temperature):
            current_order = new_order
            current_loss = new_loss
            if new_loss < best_loss:
                best_loss = new_loss
                best_order = new_order

        # Gradually cool temperature
        if step % 1000 == 0:
            temperature *= 0.98

    # Sliding optimization
    max_total_passes = 1000
    total_passes = 0
    max_slide_distance = 3
    
    while total_passes < max_total_passes:
        total_passes += 1
        improved = False
        
        for current_pos, team in enumerate(best_order):
            best_slide_pos = current_pos
            best_slide_loss = best_loss
            
            # Try sliding up (to lower rank numbers)
            for slide_up in range(1, max_slide_distance + 1):
                new_pos = current_pos - slide_up
                if new_pos < 0:
                    break
                
                new_order = best_order[:]
                # Remove team from current position and insert at new position
                new_order.pop(current_pos)
                new_order.insert(new_pos, team)
                
                new_loss = ranking_loss(new_order, games)
                if new_loss < best_slide_loss:
                    best_slide_loss = new_loss
                    best_slide_pos = new_pos
            
            # Try sliding down (to higher rank numbers)  
            for slide_down in range(1, max_slide_distance + 1):
                new_pos = current_pos + slide_down
                if new_pos >= len(best_order):
                    break
                
                new_order = best_order[:]
                new_order.pop(current_pos)
                new_order.insert(new_pos, team)
                
                new_loss = ranking_loss(new_order, games)
                if new_loss < best_slide_loss:
                    best_slide_loss = new_loss
                    best_slide_pos = new_pos
            
            # If we found a better position for this team
            if best_slide_pos != current_pos:
                new_order = best_order[:]
                new_order.pop(current_pos)
                new_order.insert(best_slide_pos, team)
                
                best_order = new_order
                best_loss = best_slide_loss
                improved = True
                break  # Restart from the beginning after any change
        
        if not improved:
            break
    
    print(f"Sliding optimization completed in {total_passes} passes")
    print(f"Final loss: {best_loss:.2f}")

    if teams_file:
        with open(teams_file, "r", encoding="utf-8") as f:
            specified_teams = json.load(f)
        best_order = [t for t in best_order if t in specified_teams]
    ranking = [{"rank": i + 1, "team": t} for i, t in enumerate(best_order)]

    return ranking, best_loss

if __name__ == "__main__":
    input_file = input("Enter input file with results: ")
    teams_file = input("Enter file with list of teams to rank (optional, press enter to skip): ")
    output_file = input("Enter output file name (default output.json): ")
    if not output_file:
        output_file = "output.json"
    output_file = "rankings/" + output_file

    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        exit(1)

    with open(input_file, "r", encoding="utf-8") as f:
        games = json.load(f)

    print(f"Loaded {len(games)} games...")
    ranking, loss = optimize_ranking(games, teams_file if teams_file else None)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(ranking, f, indent=2, ensure_ascii=False)

    print(f"Final loss: {loss:.2f}")
    print(f"Saved {len(ranking)} team rankings to {output_file}")
    print("\nTop 10:")
    for r in ranking[:10]:
        print(f"{r['rank']:>2}. {r['team']}")

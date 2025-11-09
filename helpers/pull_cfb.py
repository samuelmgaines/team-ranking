import requests
import json
import os
from dotenv import load_dotenv

def get_cfb_results_cfbd(year, output_file):
    load_dotenv()
    api_key = os.getenv("CFBD_API_KEY")
    if not api_key:
        raise ValueError("Please set CFBD_API_KEY in your .env file")

    url = f"https://api.collegefootballdata.com/games?year={year}"
    headers = {"Authorization": f"Bearer {api_key}"}

    print(f"Fetching data for {year} from CollegeFootballData API...")
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Error: received status code {resp.status_code}")
        return

    games = resp.json()
    results = []

    for g in games:
        # Only include completed games
        if not g.get("completed"):
            continue

        home_class = g.get("homeClassification")
        away_class = g.get("awayClassification")

        # Keep only games where BOTH are FBS or FCS
        valid_classes = {"fbs", "fcs"}
        if home_class not in valid_classes or away_class not in valid_classes:
            continue

        home_team = g.get("homeTeam")
        away_team = g.get("awayTeam")
        home_points = g.get("homePoints")
        away_points = g.get("awayPoints")

        # Skip games with missing scores
        if home_points is None or away_points is None:
            continue

        # Determine winner and loser
        if home_points > away_points:
            winner, loser = home_team, away_team
        else:
            winner, loser = away_team, home_team

        results.append({"winner": winner, "loser": loser})

    # Save results
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(results)} completed FBS/FCS games to {output_file}")
    
if __name__ == "__main__":
    year = input("Enter year: ")
    output_file = f"data/cfb_{year}_games.json"
    get_cfb_results_cfbd(year=int(year), output_file=output_file)

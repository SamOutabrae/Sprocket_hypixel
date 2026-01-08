import os
import requests
from datetime import datetime, timedelta
import json
import sys
import toml

from pathlib import Path

def get_key(path):
  with open(path + "/config.toml", "r") as f:
    data = toml.load(f)
    return data["api_key"].strip()
  

def main():
  # Have to go up one directory becuase this is in tracking, not root
  PATH = str(Path(__file__).parents[1].absolute())
  key = get_key(PATH)

  players = None
  with open(PATH + "/data/trackedplayers.txt", "r") as f:
    players = [player.strip() for player in f.readlines()]

  PATH = PATH + "/data/"
  DATE = datetime.now().strftime("%d-%m-%y")
  YESTERDAY_DATE = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%y")
  
  for player in players:
    url = f'https://api.hypixel.net/player?key={key}&uuid=' + player
    data = requests.get(url).json()

    FILEPATH = f"{PATH}/trackedplayers/{player}/{DATE}.json"
    YESTERDAY_FILEPATH = f"{PATH}/trackedplayers/{player}/{YESTERDAY_DATE}.json"
    MAPPING_FILEPATH = f"{PATH}/trackedplayers/{player}/mapping.json"
    
    if os.path.exists(YESTERDAY_FILEPATH):
      with open(YESTERDAY_FILEPATH, "r") as f:
        if json.load(f) == data:
          print(f"Data for {player} is the same as yesterday. Ignoring.")
        
          if os.path.exists(MAPPING_FILEPATH):
            with open(MAPPING_FILEPATH, "r") as map_file:
              mapping = json.load(map_file)
              mapping[DATE] = mapping[YESTERDAY_DATE] if YESTERDAY_DATE in mapping else YESTERDAY_DATE
          else:
            mapping = {}
            mapping[DATE] = YESTERDAY_DATE
          
          with open(MAPPING_FILEPATH, "w") as f:
            json.dump(mapping, f, indent=2)
          
          continue

    if(os.path.exists(PATH + "trackedplayers/" + player)):
      with open(FILEPATH, 'w') as f:
        f.write(json.dumps(data))
      print("Wrote data for " + player)
      continue

    with open(FILEPATH, "w") as f:
      f.write(json.dumps(data))
    print(f"Wrote data for {player} at {FILEPATH}.")
    continue

main()
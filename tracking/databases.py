import asyncio, os, json, logging
import datetime
import pandas as pd

from ..config import CONFIG
from .. import util

"""Player UUIDs are keys. Values are another dict which has
keys representing the different gamemodes
e.g. databases[uuid]['bedwars'] will give the bedwars database for the player uuid"""
databases = {}


def getJSON(date: datetime.datetime, uuid=None, username=None):
    PATH = CONFIG.PATH

    # Determine UUID
    if uuid is not None:
        real_uuid = uuid
    elif username is not None:
        real_uuid = util.getUUID(username)
        if real_uuid == 1:
            return None
    else:
        return None

    wkdir = os.path.join(PATH, "data", "trackedplayers", real_uuid)
    date_str = date.strftime("%d-%m-%y")
    filepath = os.path.join(wkdir, f"{date_str}.json")

    # If exact file doesn't exist, try mapping.json
    if not os.path.exists(filepath):
        mapping_path = os.path.join(wkdir, "mapping.json")
        if not os.path.exists(mapping_path):
            logging.error(f"Mapping file not found: {mapping_path}")
            return None

        with open(mapping_path, "r") as f:
            mapping = json.load(f)

        if date_str not in mapping:
            logging.error(f"No mapping for date {date_str}")
            return None

        mapped_date = mapping[date_str]
        if mapped_date is None:
            logging.error(f"No valid fallback for date {date_str}")
            return None

        filepath = os.path.join(wkdir, f"{mapped_date}.json")
        if not os.path.exists(filepath):
            logging.error(f"Mapped file {filepath} does not exist.")
            return None

    # Load and return JSON
    with open(filepath, "r") as f:
        return json.load(f)

# Helper to make adding new modes easier
def sum_stats(stats_dict, prefixes, suffix):
  total = 0
  for p in prefixes:
      key = f"{p}_{suffix}"
      val = stats_dict.get(key, 0)
      # Handle cases where the key exists but the value is None
      total += (val if val is not None else 0)
  return total

# TODO more elegant solution?
def normalizeJSON(datatype, json):
  if datatype == "bedwars":
    kills = json["player"]["stats"]["Bedwars"]["kills_bedwars"]
    deaths = json["player"]["stats"]["Bedwars"]["deaths_bedwars"]
    voidDeaths = json["player"]["stats"]["Bedwars"]["void_deaths_bedwars"]
    finalDeaths = json["player"]["stats"]["Bedwars"]["final_deaths_bedwars"]
    finalKills = json["player"]["stats"]["Bedwars"]["final_kills_bedwars"]
    bedwarsLevel = json["player"]["achievements"]["bedwars_level"]
    bedsBroken = json["player"]["stats"]["Bedwars"]["beds_broken_bedwars"]
    gamesplayed = json["player"]["stats"]["Bedwars"]["games_played_bedwars"]
    wins = json["player"]["stats"]["Bedwars"]["wins_bedwars"]
    losses = json["player"]["stats"]["Bedwars"]["losses_bedwars"]
    kdr = kills / deaths
    finalkdr = finalKills / finalDeaths
    
    return {
      "Date": json["date"],
      "Kills": kills,
      "Deaths": deaths,
      "Void Deaths": voidDeaths,
      "Final Deaths": finalDeaths,
      "Final Kills": finalKills,
      "Beds Broken": bedsBroken,
      "Bedwars Level": bedwarsLevel,
      "Games Played": gamesplayed,
      "Wins": wins,
      "Losses": losses,
      #"Win Streak": winstreak,
      "K/D Ratio": kdr,
      "Final K/D Ratio": finalkdr
    }
  
  elif datatype == "bridge":
    player_stats = json["player"]["stats"]["Duels"]
    username = json["player"]["displayname"]

    modes = ["bridge_duel", "bridge_doubles", "bridge_threes", "bridge_four", "bridge_3v3v3v3"]

    wins          = sum_stats(player_stats, modes, "wins")
    losses        = sum_stats(player_stats, modes, "losses")
    goals         = sum_stats(player_stats, modes, "goals")
    kills         = sum_stats(player_stats, modes, "bridge_kills")
    deaths        = sum_stats(player_stats, modes, "bridge_deaths")
    blocks_placed = sum_stats(player_stats, modes, "blocks_placed")

    games_played = wins + losses

    # TODO handle this better
    highest_winstreak = player_stats.get("best_bridge_winstreak", -1)
    winstreak = player_stats.get("current_bridge_winstreak", -1)


    return {
      'Date'             : json["date"],
      'Wins'             : wins,
      'Losses'           : losses,
      'Kills'            : kills,
      'Deaths'           : deaths,
      'Games Played'     : games_played,
      'Goals'            : goals,
      'Blocks Placed'    : blocks_placed,
      'Highest Winstreak': highest_winstreak,
      'Winstreak'        : winstreak,
    }


def rebuild_database_worker(player):
  path = CONFIG.PATH + "/data/"

  PLAYERPATH = f"{path}/trackedplayers/{player}"
  json_list = os.listdir(PLAYERPATH)
  json_list.remove("mapping.json")
  json_files = [f.replace(".json", "") for f in json_list if f.endswith(".json")]
  json_files.sort(key=lambda x : datetime.datetime.strptime(x, "%d-%m-%y"))
  json_files = [f + ".json" for f in json_files]

  data = {
     'bedwars': [],
     'bridge': []
  }
  failed = 0
  for filename in json_files:
    with open(os.path.join(PLAYERPATH, filename), "r") as file:
      json_data = json.load(file)
      json_data["date"] = filename.removesuffix(".json")

      if json_data["success"] != True:
        failed += 1
        continue
      
      for gamemode in data:
        dat = normalizeJSON(gamemode, json_data)
        data[gamemode].append(dat)

  for gamemode in data:
    data[gamemode] = pd.DataFrame(data[gamemode])
    # add _p{uuid} so it doesn't complain about invalid identifiers
    data[gamemode].to_hdf(CONFIG.PATH + f"/data/databases/{player}/{gamemode}.h5", key=f"p_{player}")
  return data


async def rebuild_db(player):
  result = await asyncio.to_thread(rebuild_database_worker, player)
  databases[player] = result

  logging.info(f"Sucessfully rebuilt database for {player}")

async def rebuild_dbs(PATH):
  logging.info("Rebuilding databeses.")
  players = [player.removesuffix("\n") for player in open(PATH + "/data/trackedplayers.txt").readlines()]
  PATH = PATH + "/data/trackedplayers"
  DATE = datetime.datetime.now().strftime("%d-%m-%y")

  tasks = [asyncio.create_task(rebuild_db(player)) for player in players]

  await asyncio.gather(*tasks)

def time_until_next_run(target_hour=0, target_minute=0):
  now = datetime.datetime.now()
  next_run = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

  if next_run <= now:  # If the target time today has already passed, schedule for tomorrow
    next_run += datetime.timedelta(days=1)

  return (next_run - now).total_seconds()

async def daily_scheduler():
  while True:
    seconds_until_next_run = time_until_next_run(target_hour=6, target_minute=0)  # Adjust time as needed
    await asyncio.sleep(seconds_until_next_run)  
    await initialize_dbs() 

async def initialize_dbs(directory):
  PATH = f"{directory}/data/"
  players = [player.strip() for player in open(PATH + "trackedplayers.txt").readlines()]

  now = datetime.datetime.now().strftime('%d-%m-%y')

  for player in players:
    databases[player] = {}

    player_dir = PATH + f"/databases/{player}"

    if not os.path.exists(player_dir):
      os.mkdir(player_dir)

    datatypes = {
       'bedwars': 'bedwars.h5',
       'bridge':  'bridge.h5'
    }
    for datatype, datapath in datatypes.items():
      datapath = f"{player_dir}/{datapath}"
      if not os.path.isfile(datapath):
        asyncio.create_task(rebuild_db(player))
        break

      df = pd.read_hdf(datapath)

      if df["Date"].iloc[-1] != now:
        json_path = f"{player_dir}/{now}.json"

        if os.path.isfile(json_path):
          with open(json_path, "r") as file:
            json_data = json.load(file)
            json_data["date"] = json_path.removesuffix(".json")

            if json_data.get("success") is True:
              dat = dat.normalizeJSON(datatype, json_data)
              df = pd.concat([df, dat], ignore_index=True)

              df.to_hdf(datapath)

      databases[player][datatype] = df
    logging.info(f"Loaded database for {player}")
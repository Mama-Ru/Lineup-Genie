from lg_classes import PlayerJSON
from datetime import datetime, timedelta
import json
import apa_client

apa = apa_client.APA()

class Cacher():
    def __init__(self):
        with open("cache/players.json", "r") as f:
            self.players: list[PlayerJSON] = json.load(f)

        self.AGE_THRESHOLD = timedelta(weeks=1.5)

    def can_upd_player(self, id: int) -> bool:
        """Returns a boolean that reflects if a player's cache should be added or updated via existence and age.'"""
        current_time = datetime.now()

        player_found = False

        for player in self.players:
            if id == player['id']:
                player_found = True
                player_date = datetime.fromisoformat(
                    player['date']
                )

                if current_time - player_date >= self.AGE_THRESHOLD:
                    return True
                
                break

        if not player_found:
            return True
                
        return False

    def write(self, name: str, id: int, sl: str, date: str) -> None:
        self.players.append({
            "name": name.title(),
            "id": id,
            "sl": sl,
            "date": date # ISO Format
        })

        with open("cache/players.json", "w") as f:
            json.dump(self.players, f, indent=4)

    def update_player(self, name: str) -> bool:
        """Checks if a player can update or not and proceeds to update the player within the cache."""

        players = apa.search_player(name)
        player = players[0]

        id: int = player['id']
        
        if self.can_upd_player(id):
            try:
                alias_id = player['aliases'][-1]['id']

                name = f"{player['firstName']} {player['lastName']}"

                team_data = apa.get_teams(alias_id)
                current_teams = team_data['alias'].get("currentTeams", [])

                player_level = next(
                    record['skillLevel']
                    for record in current_teams
                    if record['__typename'] == "EightBallPlayer"
                )

                matches = apa.get_player_matches(
                    alias_id=alias_id,
                    days=365,
                    same_sl_only=True,
                    target_sl=player_level
                )

                self.write(
                    name,
                    id,
                    apa.get_skill_level(matches, player_level),
                    datetime.isoformat(datetime.now())
                )

                return True
            
            except:
                return False
        
        return False

    def get(self, name: str) -> list[PlayerJSON]:
        """Returns all player's w/name. Specificity to narrow it down."""
        return [
            player
            for player in self.players
            if name.lower() in player['name'].lower()
        ]

    def format_players(self) -> str:
        """Returns all the players in one string. This is meant to be used"""
        final = [] # \n joined

        for player in self.players:
            final.append(f"{player['name']}: {player['sl']}")

        return "\n".join(final)
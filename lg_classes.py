from typing import Literal, TypedDict, Self

class Player:
    """A class that stores a player's name, level, and additional skill within their level."""
    PLUS_OR_MINUS_OPTIONS = {"-", "", "+"}

    def __init__(self, name: str, level: int, plus_or_minus: Literal["-", "", "+"] = ""):
        if plus_or_minus not in Player.PLUS_OR_MINUS_OPTIONS:
            raise ValueError(f"plus_or_minus must be in {Player.PLUS_OR_MINUS_OPTIONS}")
        
        self.name: str = name.title()
        self.level: int = level
        self.plus_or_minus = plus_or_minus

class Lineup:
    """A class that stores a list of the 5 Players in a lineup.

    The lineup is enforced with rules to prevent invalid lineups. It
    involves adding players to the lineup, raising an error if it pushes the
    limits, and removing players if necessary. Also includes a Player object
    search by name.
    """
    LINEUP_PLAYER_CAP: int = 5
    LINEUP_VALUE_CAP: int = 23

    def __init__(self):
        self.lineup: list[Player] = []

    def get_lineup_points(self) -> int:
        """Returns the sum of the lineup's points/level."""
        return sum(player.level for player in self.lineup)

    def add_player(self, player: Player) -> None:
        """Adds a player to a lineup if it doesn't exceed the rules.
        
        Args:
            player: The player to add to the lineup.
        """
        if len(self.lineup) >= Lineup.LINEUP_PLAYER_CAP:
            raise ValueError(f"Failed to add {player.name} to lineup due to exceeding player cap.")
        
        if self.get_lineup_points() + player.level > Lineup.LINEUP_VALUE_CAP:
            raise ValueError(f"Failed to add {player.name} to lineup due to exceeding value cap.")
        
        self.lineup.append(player)
    
    def add_players(self, players: list[Player]) -> list[Player] | None:
        """Adds multiple players to the lineup at once.
        
        Args:
            players: The players to add to the lineup.
        """
        for player in players:
            self.add_player(player)
            return self.lineup

    def del_player(self, player: Player, return_lineup: bool = False) -> list[Player] | None:
        """Removes a player from the lineup.

        Args:
            player: The player to remove from the lineup.
        """
        if player in self.lineup:
            if return_lineup:
                lineup = self.lineup.copy()
            else:
                lineup = self.lineup

            lineup.remove(player)

            if return_lineup:
                return lineup

    def clear_lineup(self) -> None:
        """Clears the lineup from players."""
        self.lineup.clear()

    def get_player_by_name(self, player_name: str) -> Player | None:
        """Searches the lineup for a player.
        
        Args:
            player_name: The Player's name.
            
        Returns:
            The Player Object or None if it is not found.
        """
        for player in self.lineup:
            if player.name == player_name.title():
                return player
    
class LineupResult(TypedDict):
    total_points: float
    """The total PPM that the specific lineup is expected to achieve."""
    lineup: tuple[tuple[Player, Player, float], ...]
    """The lineup containing the matchups, and that matchup PPM expectancy."""

class PGHResult(TypedDict):
    """Percent Greater than Half Result"""

    percentage: float
    """The percentage of games out of the reduced lineups that are above 50% mark of all lineups."""
    match_count: int
    """The amount of matches that are above the 50% mark of all lineups."""
    half_point: int
    """The point at which is half of the length of lineups."""
    cutoff_score: float
    """The score to which it can go past the 50% mark due to duplicate/same result lineups."""
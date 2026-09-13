from itertools import permutations
from ppm_tables import PPM_TABLE
from lg_classes import Player, Lineup, LineupResult, PGHResult

class Predictor:
    """A class for predicting lineup performance and evaluating player matchups.

    This class provides static methods to calculate expected points per match (PPM)
    between players, evaluate all permutations of all matchup possibilities, and generate
    the optimal player to put up and respond with.
    """

    @staticmethod
    def expected_ppm(player: Player, opponent: Player) -> float:
        """Calculates the expected points per match (PPM) for a player against an opponent.

        Looks up the base performance value using a combination of both players' 
        skill levels and plus/minus modifiers against the pre-defined PPM matrix.

        Args:
            player: Our player.
            opponent: Their player.

        Returns:
            The expected PPM float value from the PPM lookup table. Meant to show the
            advantage of our player to their player.
        """

        player_sl = f"{player.level}{player.plus_or_minus}"
        opponent_sl = f"{opponent.level}{opponent.plus_or_minus}"

        return PPM_TABLE[player_sl][opponent_sl]
    
    @staticmethod
    def generate_lineup_perms(our_lineup: Lineup, their_lineup: Lineup) -> list[LineupResult]:
        """Evaluates all possible permutations of all matchup possibilities.

        Iterates through every permuation of 5 players and 5 opponents.
        The final list is sorted from highest expected total points to lowest.

        Args:
            our_lineup: The lineup of our team.
            their_lineup: The lineup of our opponents.

        Returns:
            A list of dictionaries containing the calculated total points of 
            the player pairings, sorted descending by performance.
        """
        their_lineup_permutations = permutations(their_lineup.lineup)

        lineups: list[LineupResult] = []

        for lineup in their_lineup_permutations:
            lineup_expected_points = 0.0
            recorded_lineup: list[tuple[Player, Player, float]] = []

            for us, them in zip(our_lineup.lineup, lineup):
                matchup_expected_points = Predictor.expected_ppm(us, them)
                lineup_expected_points += matchup_expected_points

                recorded_lineup.append((us, them, matchup_expected_points))

            lineups.append({
                'total_points': lineup_expected_points,
                'lineup': tuple(recorded_lineup),
            })

        lineups.sort(key=lambda x: x['total_points'], reverse=True)
        return lineups

    @staticmethod
    def all_matchups(our_lineup: Lineup, their_lineup: Lineup) -> dict[Player, list[tuple[Player, float]]]:
        """Generates a matrix of all possible individual head-to-head matchups.

        Maps every player in our lineup to every possible opponent in their lineup, 
        providing the expected PPM score for each pairing.

        Args:
            our_lineup: The lineup of our team.
            their_lineup: The lineup of our opponents.

        Returns:
            A dictionary where keys are our players' names, and values are lists
            of tuples containing the opponent's name and the corresponding
            expected PPM.

            Example:
            {
                Player: [
                    (Opponent, 1.23),
                    ...
                ],
                ...
            }
        """
        matchups: dict[Player, list[tuple[Player, float]]] = {}

        for player in our_lineup.lineup:
            matchups[player] = []

            for opponent in their_lineup.lineup:
                matchups[player].append((opponent, Predictor.expected_ppm(player, opponent)))

        return matchups

    @staticmethod
    def calculate_PGH(lineups: list[LineupResult], reduced_lineups: list[LineupResult]) -> PGHResult:
        """Gets the Percentage Greater than Half (PGH) of the reduced lineups.
        
        Args:
            lineups: The lineup permutations (all of it).
            reduced_lineups: The reduced lineups (specific matchup removed)
            
        Returns:
            A dictionary containing percentage of matches of the reduced matches exceeding
            the halfway mark, match count, halfway mark, and the cutoff score to which
            it allowed duplicate scores past the halfway mark to be counted.
        """

        half_point = len(lineups) // 2
        cutoff_score = lineups[half_point - 1]["total_points"]

        counter = sum(
            lineup["total_points"] >= cutoff_score
            for lineup in reduced_lineups
        )

        return {
            'percentage': counter / len(reduced_lineups),
            'match_count': counter,
            'half_point': half_point,
            'cutoff_score': cutoff_score,
        }

    @staticmethod
    def reduced_lineups(lineups: list[LineupResult], player: Player, opponent: Player) -> list[LineupResult]:
        """Returns the reduced_lineups. A helper function
        
        Args:
            lineups: The lineup permutations. Can be cut or uncut (reduced after previous plays).
            player: Our player.
            opponent: Their player.
        
        Returns:
            The reduced lineups.
        """

        return [
            l for l in lineups 
            if any(us == player and them == opponent for us, them, _ in l['lineup'])
        ]

    @staticmethod
    def deploy_options(lineups: list[LineupResult], matchups: dict[Player, list[tuple[Player, float]]]) -> list[tuple[float, str]]:
        """Evaluates each possible put-up by determining what percentage
        of the resulting permutations fall within the upper half of the
        current lineup rankings.
        Use min() to choose the safest option.

        Args:
            lineups: The lineup permutations. Can be cut or uncut (reduced after previous plays).
        
        Returns:
            All of the options required to determine the safest and most advantagous
            player to put up.
        """

        pgh_options: list = []

        for player, matchup in matchups.items():
            percentages = []

            for opponent, _ in matchup:
                reduced_lineups = Predictor.reduced_lineups(lineups, player, opponent)

                pgh = Predictor.calculate_PGH(lineups, reduced_lineups)
                percentages.append(pgh['percentage'])

            pgh_options.append((min(percentages), player.name))
        
        return pgh_options

    @staticmethod
    def response_options(lineups: list[LineupResult], matchups: dict[Player, list[tuple[Player, float]]], opponent: Player) -> list[tuple[float, str]]:
        """Generates the optimal response to the opponent's player that they put up.
        Use max() to choose the best option.
        
        Args:
            lineups: The lineup permutations. Can be cut or uncut (reduced after previous plays).
            opponent: The player that they put up.
        
        Returns:
            All of the options required to determine the safest and most advantagous
            player to respond with.
        """

        pgh_options: list = []
        
        for player in matchups:
            reduced_lineups = Predictor.reduced_lineups(lineups, player, opponent)

            pgh = Predictor.calculate_PGH(lineups, reduced_lineups)
            pgh_options.append((pgh['percentage'], player.name))
        
        return pgh_options
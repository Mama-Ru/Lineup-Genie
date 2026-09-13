from lg_classes import Lineup, Player
from predictor import Predictor

our_lineup = Lineup()
their_lineup = Lineup()

our_players = [
    Player("Mason", 7, "+"),
    Player("Ethan", 6, "-"),
    Player("Michaela", 5),
    Player("Andie", 2),
    Player("Luke", 2, "-"),
]
their_players = [
    Player("Opponent1", 2, "-"),
    Player("Opponent2", 6, "+"),
    Player("Opponent3", 4),
    Player("Opponent4", 3),
    Player("Opponent5", 2, "-"),
]
our_lineup.add_players(our_players)
their_lineup.add_players(their_players)

lineups = Predictor.generate_lineup_perms(our_lineup, their_lineup)

# Put Up Example
result = max(
    Predictor.deploy_options(
        lineups,
        Predictor.all_matchups(our_lineup, their_lineup)
    )
)
print(result)

# Respond Example
oplayer = our_lineup.get_player_by_name(result[1])
tplayer = their_lineup.get_player_by_name("Opponent3")
tput_up = their_lineup.get_player_by_name("Opponent1")

if oplayer and tplayer and tput_up:
    our_lineup.del_player(oplayer)
    their_lineup.del_player(tplayer)

    result = max(
        Predictor.response_options(
            Predictor.reduced_lineups(lineups, oplayer, tplayer),
            Predictor.all_matchups(our_lineup, their_lineup),
            tput_up,
        )
    )

    print(result)
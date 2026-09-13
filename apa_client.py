from ppm_tables import BASIC_PPM_TABLE, PPM_SD_SIGMA, PPM_PEER_MEAN
from typing import Any
from datetime import datetime, timedelta, timezone
import requests
import os

from dotenv import load_dotenv
load_dotenv()

URL = "https://gql.poolplayers.com/graphql"

class APA:
    def __init__(self):
        self.REFRESH_TOKEN = (
            os.environ.get("APA_REFRESH_TOKEN")
        )

        self.access_token: str | None = None

        self.http = requests.Session()

        self.http.headers.update({
            "Accept": "*/*",
            "Content-Type": "application/json",

            "Origin": "https://league.poolplayers.com",
            "Referer": "https://league.poolplayers.com/",

            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/150.0.0.0 Safari/537.36"
            ),

            "Accept-Language": "en-US,en;q=0.9",

            "apollographql-client-name": "MemberServices",
            "apollographql-client-version": "3.18.53-3856",
        })

        self.REFRESH_QUERY = """
        mutation GenerateAccessTokenMutation($refreshToken: String!) {
            generateAccessToken(refreshToken: $refreshToken) {
                accessToken
            }
        }
        """

        self.SEARCH_QUERY = """
        query Search($query: String!) {
            search(query: $query) {
                suggestions

                hits {
                    __typename

                    ... on Member {
                        id
                        firstName
                        lastName
                        city

                        aliases {
                            id
                            nickname
                            memberNumber
                        }

                        stateProvince {
                            id
                            name
                        }
                    }

                    ... on Team {
                        id
                        name
                        number

                        session {
                            id
                            name
                        }

                        division {
                            id
                            name
                            type
                            format
                        }

                        league {
                            id
                            name
                            slug
                        }
                    }
                }
            }
        }
        """

        self.TEAM_STAT_QUERY = """
        query TeamStat($id: Int!, $limit: Int!, $offset: Int!) {
            alias(id: $id) {
                id

                pastTeams: players(
                    current: false
                    active: null
                    limit: $limit
                    offset: $offset
                ) {
                    id
                    ...EightBallTeam
                    ...NineBallTeam
                    ...MastersTeam
                }

                currentTeams: players(
                    current: true
                    active: null
                ) {
                    id
                    ...EightBallTeam
                    ...NineBallTeam
                    ...MastersTeam
                }
            }
        }


        fragment NineBallTeam on NineBallPlayer {
            id
            isActive
            role
            rosterPosition
            nickName
            matchesPlayed
            matchesWon

            session {
                id
                name
            }

            skillLevel
            rank

            team {
                id
                name

                division {
                    id
                    isTournament
                }
            }

            __typename
        }


        fragment EightBallTeam on EightBallPlayer {
            id
            isActive
            role
            rosterPosition
            nickName
            matchesPlayed
            matchesWon

            session {
                id
                name
            }

            skillLevel
            rank

            team {
                id
                name

                division {
                    id
                    isTournament
                }
            }

            __typename
        }


        fragment MastersTeam on MastersPlayer {
            id
            isActive
            role
            rosterPosition
            nickName
            matchesPlayed
            matchesWon

            session {
                id
                name
            }

            team {
                id
                name

                division {
                    id
                    isTournament
                }
            }

            __typename
        }
        """

        self.DIVISION_MATCHES_QUERY = """
        query DivisionMatches($id: Int!) {
            division(id: $id) {
                id

                matches(
                    filter: {
                        excludeReplayMatches: true
                    }
                ) {
                    id
                    state
                    startTime

                    home {
                        id
                        name
                        number
                    }

                    away {
                        id
                        name
                        number
                    }

                    preferredScoresheet {
                        id
                        state

                        playerMatches {
                            id
                            state
                            innings

                            home {
                                __typename

                                ... on EightMatchPlayer {
                                    id
                                    skillLevel
                                    points
                                    racksWon
                                    defensiveShots

                                    player {
                                        id
                                        nickName
                                        memberNumber

                                        member {
                                            id
                                        }

                                        alias {
                                            id
                                        }
                                    }

                                    team {
                                        id
                                        name
                                        number
                                    }
                                }
                            }

                            away {
                                __typename

                                ... on EightMatchPlayer {
                                    id
                                    skillLevel
                                    points
                                    racksWon
                                    defensiveShots

                                    player {
                                        id
                                        nickName
                                        memberNumber

                                        member {
                                            id
                                        }

                                        alias {
                                            id
                                        }
                                    }

                                    team {
                                        id
                                        name
                                        number
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def get_access_token(self) -> str | None:
        """Gets the access token used for making requests."""

        payload = [
            {
                "operationName": "GenerateAccessTokenMutation",
                "variables": {
                    "refreshToken": self.REFRESH_TOKEN,
                },
                "query": self.REFRESH_QUERY,
            }
        ]

        response = self.http.post(
            URL,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        result: dict[str, Any] = response.json()[0]

        if result.get("errors"):
            raise RuntimeError(result["errors"])

        self.access_token = (
            result["data"]
            ["generateAccessToken"]
            ["accessToken"]
        )

        return self.access_token

    # ------------------------------------------------------------------
    # Generic GraphQL request
    # ------------------------------------------------------------------

    def request(self, operation_name: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        """Makes the request using the operation names, queries, and variables."""

        if not self.access_token:
            self.get_access_token()

        payload = [
            {
                "operationName": operation_name,
                "variables": variables,
                "query": query,
            }
        ]

        result = self._send_authenticated_request(payload)

        if self._token_expired(result):
            self.get_access_token()
            result = self._send_authenticated_request(payload)

        if result.get("errors"):
            raise RuntimeError(result["errors"])

        return result["data"]

    def _send_authenticated_request(self, payload: list[Any]) -> dict[str, Any]:
        """Sends an authorized request."""

        response = self.http.post(
            URL,
            headers={
                "Authorization": self.access_token,
            },
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()[0]

    def _token_expired(self, result: dict[str, Any]) -> bool:
        """Checks if the auth token expired."""

        errors = result.get("errors", [])

        for error in errors:
            code = (
                error
                .get("extensions", {})
                .get("code")
            )

            if code == "TOKEN_EXPIRED":
                return True

        return False

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _search(self, search_text: str) -> list[dict[str, Any]]:
        """Searches using a query."""

        data = self.request(
            operation_name="Search",
            query=self.SEARCH_QUERY,
            variables={
                "query": search_text,
            },
        )

        return data["search"]["hits"]

    def search_player(self, name: str) -> list[Any]:
        """Searches for a player using _search()."""

        hits = self._search(name)

        return [
            hit for hit in hits
            if hit.get("__typename") == "Member"
        ]

    def search_team(self, name: str) -> list[dict[str, Any]]:
        """Searches for a team using _search()."""

        hits = self._search(name)

        return [
            hit for hit in hits
            if hit.get("__typename") == "Team"
        ]
    
    def find_team(self, name: str) -> dict[str, Any] | None:
        """Searches for a team using search_team."""

        teams = self.search_team(name)

        if not teams:
            return None

        return teams[0]
    
    def get_division_matches(self, division_id: int) -> list[dict[str, Any]]:
        """Gets all matches within a division."""

        data = self.request(
            operation_name="DivisionMatches",
            query=self.DIVISION_MATCHES_QUERY,
            variables={
                "id": division_id,
            },
        )

        return data["division"]["matches"]

    def get_teams(self, alias_id: int) -> dict[str, Any]:
        """Gets more data from a team."""

        return self.request(
            operation_name="TeamStat",
            query=self.TEAM_STAT_QUERY,
            variables={
                "id": alias_id,
                "limit": 50,
                "offset": 0,
            },
        )
    
    def get_player_matches(self, alias_id: int, days: int = 90, same_sl_only: bool = False, target_sl: int | None = None) -> list[dict[str, Any]]:
        """Gets the matches from a player."""

        team_data = self.get_teams(alias_id)

        records = (
            team_data["alias"].get("currentTeams", [])
            + team_data["alias"].get("pastTeams", [])
        )

        # Keep only the player's current format.
        current_type = None

        current_teams = (
            team_data["alias"]
            .get("currentTeams", [])
        )

        if current_teams:
            current_type = (
                current_teams[0]
                .get("__typename")
            )

        if current_type:
            records = [
                record for record in records
                if record.get("__typename") == current_type
            ]

        # Keep the most recent N sessions.
        session_ids: list[int] = []

        for record in records:
            session = record.get("session") or {}
            session_id = session.get("id")

            if session_id is not None and session_id not in session_ids:
                session_ids.append(session_id)

            # 98 = 14 weeks which is how long a session is
            max_sessions = (days + 97) // 98
            if len(session_ids) >= max_sessions:
                break

        recent_records = [
            record for record in records
            if (record.get("session") or {}).get("id") in session_ids
        ]

        # Include every division the player was in during those sessions.
        division_ids: list[int] = []

        for record in recent_records:
            division_id = (
                record
                .get("team", {})
                .get("division", {})
                .get("id")
            )

            if division_id is not None and division_id not in division_ids:
                division_ids.append(division_id)

        print("Sessions being searched:")
        for record in recent_records:
            print(
                " ",
                (record.get("session") or {}).get("name"),
                "|",
                (record.get("team") or {}).get("name"),
                "| Division:",
                (
                    record
                    .get("team", {})
                    .get("division", {})
                    .get("id")
                ),
            )

        all_matches: list[dict[str, Any]] = []

        for division_id in division_ids:
            print(f"Loading division {division_id}...")

            division_matches = (self.get_division_matches(division_id))

            print(f"  {len(division_matches)} matches returned")

            all_matches.extend(division_matches)

        # The same team match could theoretically appear
        # more than once, so deduplicate.
        unique_matches = {
            str(match["id"]): match
            for match in all_matches
        }

        return self.filter_player_matches(
            matches=list(unique_matches.values()),
            alias_id=alias_id,
            days=days,
            same_sl_only=same_sl_only,
            target_sl=target_sl
        )
    
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def filter_player_matches(self, matches: list[Any], alias_id: int, days: int = 365, same_sl_only: bool = False, target_sl: int | None = None) -> list[dict[str, Any]]:
        """Filters the players matches according to age and SL."""

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        results: list[dict[str, Any]] = []

        for team_match in matches:
            if team_match.get("state") != "SCORED":
                continue

            start_time = team_match.get("startTime")

            if not start_time:
                continue

            played_at = datetime.fromisoformat(
                start_time.replace("Z", "+00:00")
            )

            if played_at < cutoff:
                continue

            scoresheet = (
                team_match.get("preferredScoresheet")
                or {}
            )

            for player_match in scoresheet.get("playerMatches", []):
                home = player_match.get("home") or {}
                away = player_match.get("away") or {}

                home_alias_id = str(
                    ((home.get("player") or {}).get("alias") or {}).get("id")
                )

                away_alias_id = str(
                    ((away.get("player") or {}).get("alias") or {}).get("id")
                )

                if home_alias_id == str(alias_id):
                    player_side = home
                    opponent_side = away
                elif away_alias_id == str(alias_id):
                    player_side = away
                    opponent_side = home
                else:
                    continue

                player_sl = player_side.get("skillLevel")
                opponent_sl = opponent_side.get("skillLevel")

                if target_sl is not None and player_sl != target_sl:
                    continue

                if same_sl_only and player_sl != opponent_sl:
                    continue

                results.append({
                    "date": team_match["startTime"],
                    "player_sl": player_sl,
                    "opponent_sl": opponent_sl,
                    "points": player_side.get("points"),
                    "opponent_points": opponent_side.get("points"),
                    "innings": player_match.get("innings"),
                })

        return results
    
    def get_skill_level(self, matches: list[Any], player_level: int) -> str:
        """Gets a player's SL using ±1 SIG."""
        if len(matches) < 5:
            return str(player_level)

        average_ppm = sum(match['points'] for match in matches) / len(matches)
        
        mean = PPM_PEER_MEAN[player_level]
        sigma = PPM_SD_SIGMA[player_level]

        z_score = (average_ppm - mean) / sigma

        if z_score >= 1:
            return f"{player_level}+"

        if z_score <= -1:
            return f"{player_level}-"

        return str(player_level)

# ======================================================================
# Example
# ======================================================================

if __name__ == "__main__":
    apa = APA()

    player_name = "justin rustad"
    players = apa.search_player(player_name)

    if not players:
        raise LookupError(f"Player not found: {player_name}")

    player = players[0]
    alias_id = player["aliases"][-1]["id"]

    team_data = apa.get_teams(alias_id)

    current_teams = team_data["alias"].get("currentTeams", [])

    player_level = next(
        record["skillLevel"]
        for record in current_teams
        if record["__typename"] == "EightBallPlayer"
    )

    matches = apa.get_player_matches(
        alias_id=alias_id,
        days=365,
        same_sl_only=True,
        target_sl=player_level
    )

    print(
        f"{player['firstName']} {player['lastName']}"
        f"\nSame-SL matches: {len(matches)}"
    )

    for match in matches:
        print(
            f"\n{match['date']}"
            f"\nPoints: {match['points']}-{match['opponent_points']}"
            f"\nInnings: {match['innings']}"
        )

    print(apa.get_skill_level(matches, player_level))
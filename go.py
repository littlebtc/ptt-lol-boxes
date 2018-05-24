import sys
import re
import datetime
import requests

VICTORY_MSG = u"\x1b[1;37;42m  \u52dd\u5229  \x1b[m"
DEFEAT_MSG = u"\x1b[1;37;45m  \u843d\u6557  \x1b[m"


def bar_chart(i):
    """
    Given a int from 0 to 48, output a 6 full-width characters
    that reprecents the value.
    """
    i = int(i)
    if i < 0 or i > 48:
        return ""
    result = ""
    while i >= 8:
        result += u"\u2588"
        i -= 8
    graphs = ["", u"\u258F", u"\u258E", u"\u258D",
              u"\u258C", u"\u258B", u"\u258A", u"\u2589"]
    result += graphs[i]
    return result


def main():
    if len(sys.argv) != 2:
        print 'Usage: python go.py MATCH-HISTORY-URL'
        return
    output = ""
    # Check the URL from argv, get ID, normalize it.
    url = sys.argv[1]
    url_prefix = ('https://matchhistory.na.leagueoflegends.com/'
                  'en/#match-details/')
    if not url.startswith(url_prefix):
        raise Exception('Expect a valid match history URL.')

    re_id = re.compile(r'(TR[0-9A-Z]+\/[0-9]+)\?gameHash=([0-9a-z]+)')
    match = re_id.search(url)
    if not match:
        raise Exception('Expect a valid match history URL.')
    match_part = match.group(0)
    match_id = match.group(1)
    game_hash = match.group(2)
    normalized_url = "{0}{1}".format(url_prefix, match_part)

    # Get the latest ddragon version and get champion data.
    print "* Getting champion data..."
    res = requests.get('https://ddragon.leagueoflegends.com'
                       '/api/versions.json')
    ddragon_patch = res.json()[0]
    champion_url = ('https://ddragon.leagueoflegends.com/cdn/'
                    '{0}/data/zh_TW/champion.json').format(
                        ddragon_patch)
    res = requests.get(champion_url)
    champions_dict = res.json()["data"]
    champions = dict([
        (int(detail["key"]), detail["name"])
        for _, detail in champions_dict.iteritems()
    ])

    ##########################################
    # Fetch the match history and analyze it.
    print "* Fetching matching history..."
    json_url = ('https://acs.leagueoflegends.com'
                '/v1/stats/game/{0}?gameHash={1}').format(
                    match_id, game_hash)
    res = requests.get(json_url)
    match_history = res.json()

    # Get timeline history. Maybe we can add graph at future.
    # It is the only way we can get the dragon types :(
    print "* Getting timeline data..."
    json_timeline_url = ('https://acs.leagueoflegends.com'
                         '/v1/stats/game/{0}/timeline?gameHash={1}').format(
                         match_id, game_hash)
    res = requests.get(json_timeline_url)
    timeline = res.json()

    ##########################################
    # Output!

    print "* Preparing output..."

    # Some data that needs to be prepared.
    patch_ver = re.search(
        r'^[0-9]+\.[0-9]+', match_history["gameVersion"]).group(0)
    m, s = divmod(match_history["gameDuration"], 60)
    duration = "{0:02d}:{1:02d}".format(m, s)
    game_date = datetime.datetime.fromtimestamp(
        match_history["gameCreation"] / 1000).strftime("%Y-%m-%d")
    players = [
        identity["player"]["summonerName"]
        for identity in match_history["participantIdentities"]
    ]
    blue_kills = 0
    blue_golds = 0
    red_kills = 0
    red_golds = 0
    for i in range(0, 5):
        blue_kills += match_history["participants"][i]["stats"]["kills"]
        blue_golds += match_history["participants"][i]["stats"]["goldEarned"]
    for i in range(5, 10):
        red_kills += match_history["participants"][i]["stats"]["kills"]
        red_golds += match_history["participants"][i]["stats"]["goldEarned"]
    blue_kills = u"\x1b[1;34;40m{:>2}\x1b[m".format(blue_kills)
    red_kills = u"\x1b[1;31;40m{:>2}\x1b[m".format(red_kills)
    blue_golds = "{}k".format(round(blue_golds / 100.00) / 10)
    red_golds = "{}k".format(round(red_golds / 100.00) / 10)
    blue_result = (
        VICTORY_MSG
        if match_history["teams"][0]["win"] == "Win"
        else DEFEAT_MSG
    )
    red_result = (
        VICTORY_MSG
        if match_history["teams"][1]["win"] == "Win"
        else DEFEAT_MSG
    )

    # Output the result line-by-line.
    output += ((u"\u2500" * 19) + u"\u252c" + (u"\u2500" * 13) +
               " " + game_date + "\n")
    output += u"{0}{1:>6}    {2}  \u2502  {3}    {4:<6}\n".format(
        " " * 24, blue_golds, blue_kills, red_kills, red_golds)
    output += u"{0}{1}{2}PATCH{3:>6}  \u2502  {4}{5}{6}\n".format(
        " " * 6, blue_result, " " * 11, patch_ver,
        duration, " " * 16, red_result)
    output += (u"\u2500" * 19) + u"\u253c" + (u"\u2500" * 19) + "\n"

    # Iterrate through all players in the game.
    for i in range(0, 5):
        pass

    print output


if __name__ == "__main__":
    main()
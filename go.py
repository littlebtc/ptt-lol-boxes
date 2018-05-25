import sys
import re
import datetime
import requests
import pyperclip
from kitchen.text.display import textual_width_fill

VICTORY_MSG = u'\x1b[1;37;42m  \u52dd\u5229  \x1b[m'
DEFEAT_MSG = u'\x1b[1;37;45m  \u843d\u6557  \x1b[m'


def bar_chart(i):
    '''
    Given a int from 0 to 48, output a 6 full-width characters
    that reprecents the value.
    '''
    i = int(i)
    if i < 0 or i > 48:
        return ''
    result = ''
    while i >= 8:
        result += u'\u2588'
        i -= 8
    graphs = ['', u'\u258F', u'\u258E', u'\u258D',
              u'\u258C', u'\u258B', u'\u258A', u'\u2589']
    result += graphs[i]
    return result + '  ' * (6 - len(result))


def stats_first(stats, player):
    return u'{0:<16} {1:>2}/{2:>2}/{3:>2} {4:>4} {5:>5}k'.format(
        player, stats['kills'], stats['deaths'], stats['assists'],
        stats['totalMinionsKilled'],
        round(stats['goldEarned'] / 100.00) / 10)


def stats_second(participant, champions, max_damage):
    damage = participant['stats']['totalDamageDealtToChampions']
    return u'{0} {1}  {2:>6}'.format(
        textual_width_fill(champions[participant['championId']], 16),
        bar_chart(round(damage * 48.00 / max_damage)),
        damage
    )


def color_dragon(name):
    return {
        'FIRE_DRAGON': u'\x1b[1;31;40m\u706b\x1b[m',
        'WATER_DRAGON': u'\x1b[1;36;40m\u6c34\x1b[m',
        'AIR_DRAGON': u'\x1b[1;37;40m\u98a8\x1b[m',
        'EARTH_DRAGON': u'\x1b[0;33;40m\u5730\x1b[m',
        'ELDER_DRAGON': u'\x1b[1;37;46m\u53e4\x1b[m',
    }[name]


def main():
    if len(sys.argv) != 2:
        print 'Usage: python go.py MATCH-HISTORY-URL'
        return
    output = ''
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
    normalized_url = '{0}{1}'.format(url_prefix, match_part)

    # Get the latest ddragon version and get champion data.
    print '* Getting champion data...'
    res = requests.get('https://ddragon.leagueoflegends.com'
                       '/api/versions.json')
    ddragon_patch = res.json()[0]
    champion_url = ('https://ddragon.leagueoflegends.com/cdn/'
                    '{0}/data/zh_TW/champion.json').format(
                        ddragon_patch)
    res = requests.get(champion_url)
    champions_dict = res.json()['data']
    champions = dict([
        (int(detail['key']), detail['name'])
        for _, detail in champions_dict.iteritems()
    ])

    ##########################################
    # Fetch the match history and analyze it.
    print '* Fetching matching history...'
    json_url = ('https://acs.leagueoflegends.com'
                '/v1/stats/game/{0}?gameHash={1}').format(
                    match_id, game_hash)
    res = requests.get(json_url)
    match_history = res.json()

    # Get timeline history. Maybe we can add graph at future.
    # It is the only way we can get the dragon types :(
    print '* Getting timeline data...'
    json_timeline_url = ('https://acs.leagueoflegends.com'
                         '/v1/stats/game/{0}/timeline?gameHash={1}').format(
                         match_id, game_hash)
    res = requests.get(json_timeline_url)
    timeline = res.json()

    ##########################################
    # Output!

    print '* Preparing output...'

    # Some data that needs to be prepared.
    patch_ver = re.search(
        r'^[0-9]+\.[0-9]+', match_history['gameVersion']).group(0)
    m, s = divmod(match_history['gameDuration'], 60)
    duration = '{0:02d}:{1:02d}'.format(m, s)
    game_date = datetime.datetime.fromtimestamp(
        match_history['gameCreation'] / 1000).strftime('%Y-%m-%d')
    players = [
        identity['player']['summonerName']
        for identity in match_history['participantIdentities']
    ]
    blue_kills = 0
    blue_golds = 0
    red_kills = 0
    red_golds = 0
    max_damage = 0
    for i in range(0, 5):
        stats = match_history['participants'][i]['stats']
        blue_kills += stats['kills']
        blue_golds += stats['goldEarned']
        max_damage = max(
            max_damage,
            stats['totalDamageDealtToChampions'])
    for i in range(5, 10):
        stats = match_history['participants'][i]['stats']
        red_kills += stats['kills']
        red_golds += stats['goldEarned']
        max_damage = max(
            max_damage,
            stats['totalDamageDealtToChampions'])
    blue_kills = u'\x1b[1;36;40m{:>2}\x1b[m'.format(blue_kills)
    red_kills = u'\x1b[1;31;40m{:>2}\x1b[m'.format(red_kills)
    blue_golds = '{}k'.format(round(blue_golds / 100.00) / 10)
    red_golds = '{}k'.format(round(red_golds / 100.00) / 10)
    blue_result = (
        VICTORY_MSG
        if match_history['teams'][0]['win'] == 'Win'
        else DEFEAT_MSG
    )
    red_result = (
        VICTORY_MSG
        if match_history['teams'][1]['win'] == 'Win'
        else DEFEAT_MSG
    )
    blue_bans = [
        champions[ban['championId']]
        for ban in match_history['teams'][0]['bans']]
    red_bans = [
        champions[ban['championId']]
        for ban in match_history['teams'][1]['bans']]

    blue_dragons = ''
    blue_dragon_count = 0
    red_dragons = ''
    red_dragon_count = 0
    # Get the dragon slain from the timeline.
    for frame in timeline['frames']:
        for event in frame['events']:
            if (event.get('monsterType', '') == 'DRAGON' and
                    event['killerId'] < 5):
                blue_dragons += color_dragon(
                    event['monsterSubType']
                )
                blue_dragon_count += 1
            elif event.get('monsterType', '') == 'DRAGON':
                red_dragons += color_dragon(
                    event['monsterSubType']
                )
                red_dragon_count += 1
    blue_dragons += ' ' * (32 - blue_dragon_count * 2)

    # Output the result line-by-line.
    output += ((u'\u2500' * 19) + u'\u252c' + (u'\u2500' * 13) +
               ' ' + game_date + '\n')
    output += u'{0}{1:>6}    {2}  \u2502  {3}    {4:<6}\n'.format(
        ' ' * 24, blue_golds, blue_kills, red_kills, red_golds)
    output += u'{0}{1}{2}PATCH{3:>6}  \u2502  {4}{5}{6}\n'.format(
        ' ' * 6, blue_result, ' ' * 11, patch_ver,
        duration, ' ' * 16, red_result)
    output += (u'\u2500' * 19) + u'\u253c' + (u'\u2500' * 19) + '\n'
    output += u'{0} \u2502 {0}\n'.format(
        ' ' * 18 + '\x1b[1;37;40mK  D  A   CS   Gold\x1b[m')
    output += u'{0} \u2502 {0}\n'.format(
        ' ' * 27 + u'\x1b[1;37;40m\u5c0d\u82f1\u96c4\u50b7\u5bb3\x1b[m')

    # Iterrate through all players in the game.
    for i in range(0, 5):
        j = i + 5
        output += (u'\x1b[1;36;40m{0}\x1b[m \u2502 '
                   u'\x1b[1;31;40m{1}\x1b[m\n').format(
            stats_first(match_history['participants'][i]['stats'], players[i]),
            stats_first(match_history['participants'][j]['stats'], players[j]),
        )
        output += (u'{0} \u2502 {1}\n').format(
            stats_second(match_history['participants'][i],
                         champions, max_damage),
            stats_second(match_history['participants'][j],
                         champions, max_damage),
        )

    output += (u'\u2500' * 19) + u'\u253c' + (u'\u2500' * 19) + '\n'

    # Stats like Bans, picks, dragons, barons.
    output += u'{0} {1} {2} {3} \u2502 {0} {4} {5} {6}\n'.format(
        u'\u7981\u7528',
        textual_width_fill(blue_bans[0], 10),
        textual_width_fill(blue_bans[1], 10),
        textual_width_fill(blue_bans[2], 10),
        textual_width_fill(red_bans[0], 10),
        textual_width_fill(red_bans[1], 10),
        textual_width_fill(red_bans[2], 10),
        )
    output += u'{0} {1} {2} {3} \u2502 {0} {4} {5}\n'.format(
        ' ' * 4,
        textual_width_fill(blue_bans[3], 10),
        textual_width_fill(blue_bans[4], 10),
        ' ' * 10,
        textual_width_fill(red_bans[3], 10),
        textual_width_fill(red_bans[4], 10),
        )
    output += u'{0} {1} \u2502 {0} {2}\n'.format(
        u'\u5c0f\u9f8d', blue_dragons, red_dragons
    )
    output += (u'{0:>2} \u5854 / {1} \u5175\u71df / '
               u'{2} \u9810\u793a\u8005 / {3:>2} \u5df4\u9f8d  ').format(
        match_history['teams'][0]['towerKills'],
        match_history['teams'][0]['inhibitorKills'],
        match_history['teams'][0]['riftHeraldKills'],
        match_history['teams'][0]['baronKills'],
    )
    output += u' \u2502 '
    output += (u'{0:>2} \u5854 / {1} \u5175\u71df / '
               u'{2} \u9810\u793a\u8005 / {3:>2} \u5df4\u9f8d\n').format(
        match_history['teams'][1]['towerKills'],
        match_history['teams'][1]['inhibitorKills'],
        match_history['teams'][1]['riftHeraldKills'],
        match_history['teams'][1]['baronKills'],
    )
    output += (u'\u2500' * 19) + u'\u2534' + (u'\u2500' * 19) + '\n'

    # Print and copy to clipboard.
    print output
    pyperclip.copy(output)
    print 'Copied to clipboard!'


if __name__ == '__main__':
    main()

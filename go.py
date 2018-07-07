from __future__ import absolute_import
from __future__ import print_function
import re
import datetime
import requests
import click
import pyperclip
import bitly_api
import json
from kitchen.text.display import textual_width_fill
import six
from six.moves import range

VICTORY_MSG = u'\x1b[1;37;42m  \u52dd\u5229  \x1b[m'
DEFEAT_MSG = u'\x1b[1;37;45m  \u6230\u6557  \x1b[m'


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
    return u'{0} {1:>2}/{2:>2}/{3:>2} {4:>4} {5:>5}k'.format(
        textual_width_fill(player, 16),
        stats['kills'], stats['deaths'], stats['assists'],
        stats['totalMinionsKilled'] + stats['neutralMinionsKilled'],
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


def get_champions():
    # Get the latest ddragon version and get champion data.
    print('* Getting champion data...')
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
        for _, detail in six.iteritems(champions_dict)
    ])
    # Deal with empty bans in ranked games.
    champions[-1] = u'(\u7121)'
    return champions


def output_match_result(data, game_number, short_url, champions, lpl=False):
    print('* Preparing output...')

    output = ''

    # Output the result line-by-line.
    output += (u'\x1b[1;37;46mGame {0:>2}\x1b[m ' +
               (u'\u2500' * 15) + u'\u252c' + (u'\u2500' * 13) +
               ' {1}\n').format(game_number, data['game_date'])

    blue_team_spaces = 12 - len(data['blue_team_name']) / 2
    red_team_spaces = 12 - len(data['red_team_name']) / 2

    output += (u'{0}\x1b[1;37;44m{1}\x1b[m{2}{3:>6}    '
               u'\x1b[1;36;40m{4:>2}\x1b[m'
               u'  \u2502  \x1b[1;31;40m{5:>2}\x1b[m    '
               u'{6:<6}{7}\x1b[1;37;41m{8}\x1b[m\n').format(
        ' ' * blue_team_spaces, data['blue_team_name'],
        ' ' * (24 - blue_team_spaces - len(data['blue_team_name'])),
        data['blue_golds'], data['blue_kills'],
        data['red_kills'], data['red_golds'],
        ' ' * red_team_spaces, data['red_team_name'])
    if lpl:
        output += u'{0}{1}{2}{3}  \u2502  {4}{5}{6}\n'.format(
            ' ' * 8, data['blue_result'], ' ' * 9, ' ' * 11,
            data['duration'], ' ' * 15, data['red_result'])
    else:
        output += u'{0}{1}{2}PATCH{3:>6}  \u2502  {4}{5}{6}\n'.format(
            ' ' * 8, data['blue_result'], ' ' * 9, data['patch_ver'],
            data['duration'], ' ' * 15, data['red_result'])
    output += (u'\u2500' * 19) + u'\u253c' + (u'\u2500' * 19) + '\n'
    output += u'{0} \u2502 {0}\n'.format(
        ' ' * 18 + '\x1b[1;37;40mK  D  A   CS  $/Dmg\x1b[m')

    # Iterrate through all players in the game.
    for i in range(0, 5):
        j = i + 5
        output += (u'\x1b[1;36;40m{0}\x1b[m \u2502 '
                   u'\x1b[1;31;40m{1}\x1b[m\n').format(
            stats_first(data['participants'][i]['stats'], data['players'][i]),
            stats_first(data['participants'][j]['stats'], data['players'][j]),
        )
        output += (u'{0} \u2502 {1}\n').format(
            stats_second(data['participants'][i],
                         champions, data['max_damage']),
            stats_second(data['participants'][j],
                         champions, data['max_damage']),
        )

    output += (u'\u2500' * 19) + u'\u253c' + (u'\u2500' * 19) + '\n'

    # Stats like Bans, picks, dragons, barons.
    output += u'{0} {1} {2} {3} \u2502 {0} {4} {5} {6}\n'.format(
        u'\u7981\u7528',
        textual_width_fill(data['blue_bans'][0], 10),
        textual_width_fill(data['blue_bans'][1], 10),
        textual_width_fill(data['blue_bans'][2], 10),
        textual_width_fill(data['red_bans'][0], 10),
        textual_width_fill(data['red_bans'][1], 10),
        textual_width_fill(data['red_bans'][2], 10),
        )
    output += u'{0} {1} {2} {3} \u2502 {0} {4} {5}\n'.format(
        ' ' * 4,
        textual_width_fill(data['blue_bans'][3], 10),
        textual_width_fill(data['blue_bans'][4], 10),
        ' ' * 10,
        textual_width_fill(data['red_bans'][3], 10),
        textual_width_fill(data['red_bans'][4], 10),
        )
    output += u'{0} {1} \u2502 {0} {2}\n'.format(
        u'\u5c0f\u9f8d', data['blue_dragons'], data['red_dragons']
    )
    if lpl:
        output += (u'{0:>2} \u5854 / {1:>2} \u5df4\u9f8d{2}').format(
            data['team_blue']['towerKills'],
            data['team_blue']['baronKills'],
            ' ' * 22
        )
        output += u' \u2502 '
        output += (u'{0:>2} \u5854 / {1:>2} \u5df4\u9f8d\n').format(
            data['team_red']['towerKills'],
            data['team_red']['baronKills'],
        )
    else:
        output += (u'{0:>2} \u5854 / {1} \u5175\u71df / '
                   u'{2} \u9810\u793a\u8005 / {3:>2} \u5df4\u9f8d  ').format(
            data['team_blue']['towerKills'],
            data['team_blue']['inhibitorKills'],
            data['team_blue']['riftHeraldKills'],
            data['team_blue']['baronKills'],
        )
        output += u' \u2502 '
        output += (u'{0:>2} \u5854 / {1} \u5175\u71df / '
                   u'{2} \u9810\u793a\u8005 / {3:>2} \u5df4\u9f8d\n').format(
            data['team_red']['towerKills'],
            data['team_red']['inhibitorKills'],
            data['team_red']['riftHeraldKills'],
            data['team_red']['baronKills'],
        )
    if short_url:
        output += ((u'\u2500' * 19) + u'\u2534' +
                   (u'\u2500' * 6) + '{0:>26}\n\n').format(
            short_url)
    else:
        output += (u'\u2500' * 19) + u'\u2534' + (u'\u2500' * 19) + '\n\n'
    return output


def get_match_result(url_match, champions, game_number, teams, bitly):

    game_hash = url_match.group('hash')
    garena = url_match.group('site').startswith(
        ('id', 'ph', 'sg', 'tw', 'th', 'vn')
    )
    normalized_url = ('https://matchhistory.{0}/{1}/#match-details/'
                      '{2}/{3}{4}').format(
        url_match.group('site'), url_match.group('lang'),
        url_match.group('server'), url_match.group('id1'),
        url_match.group('id2'))

    short_url = ''
    if bitly:
        print('* Shorten URL...')
        shorten_data = bitly.shorten(normalized_url)
        short_url = shorten_data['url']

    ##########################################
    # Fetch the match history and analyze it.
    print('* Fetching matching history...')
    json_url = ('https://{0}.leagueoflegends.com'
                '/v1/stats/game/{1}/{2}{3}').format(
                    'acs-garena' if garena else 'acs',
                    url_match.group('server'),
                    url_match.group('id1'),
                    '?gameHash={0}'.format(game_hash) if game_hash else '')
    print(json_url)
    res = requests.get(json_url)
    match_history = res.json()

    # Get timeline history. Maybe we can add graph at future.
    # It is the only way we can get the dragon types :(
    print('* Getting timeline data...')
    json_timeline_url = ('https://{0}.leagueoflegends.com'
                         '/v1/stats/game/{1}/{2}/timeline{3}').format(
                            'acs-garena' if garena else 'acs',
                            url_match.group('server'),
                            url_match.group('id1'),
                            '?gameHash={0}'.format(
                                game_hash) if game_hash else '')
    res = requests.get(json_timeline_url)
    timeline = res.json()

    ##########################################
    # Output!

    data = dict()
    # Some data that needs to be prepared.
    data['patch_ver'] = re.search(
        r'^[0-9]+\.[0-9]+', match_history['gameVersion']).group(0)
    m, s = divmod(match_history['gameDuration'], 60)
    data['duration'] = '{0:02d}:{1:02d}'.format(m, s)
    data['game_date'] = datetime.datetime.fromtimestamp(
        match_history['gameCreation'] / 1000).strftime('%Y-%m-%d')
    data['players'] = [
        identity['player']['summonerName']
        for identity in match_history['participantIdentities']
    ]
    team_dict = dict(teams)
    data['blue_team_name'] = team_dict.get(
        data['players'][0].split(' ')[0], '')
    data['red_team_name'] = team_dict.get(
        data['players'][5].split(' ')[0], '')
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
    data['max_damage'] = max_damage
    data['blue_kills'] = blue_kills
    data['red_kills'] = red_kills
    data['blue_golds'] = blue_golds
    data['red_golds'] = red_golds
    data['blue_golds'] = '{}k'.format(round(blue_golds / 100.00) / 10)
    data['red_golds'] = '{}k'.format(round(red_golds / 100.00) / 10)
    data['blue_result'] = (
        VICTORY_MSG
        if match_history['teams'][0]['win'] == 'Win'
        else DEFEAT_MSG
    )
    data['red_result'] = (
        VICTORY_MSG
        if match_history['teams'][1]['win'] == 'Win'
        else DEFEAT_MSG
    )
    data['blue_bans'] = [
        champions[ban['championId']]
        for ban in match_history['teams'][0]['bans']]
    data['blue_bans'] += [''] * (5 - len(data['blue_bans']))
    data['red_bans'] = [
        champions[ban['championId']]
        for ban in match_history['teams'][1]['bans']]
    data['red_bans'] += [''] * (5 - len(data['red_bans']))

    blue_dragons = ''
    blue_dragon_count = 0
    red_dragons = ''
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
    blue_dragons += ' ' * (32 - blue_dragon_count * 2)
    data['blue_dragons'] = blue_dragons
    data['red_dragons'] = red_dragons
    data['participants'] = match_history['participants']
    data['team_blue'] = match_history['teams'][0]
    data['team_red'] = match_history['teams'][1]

    return output_match_result(data, game_number, short_url, champions)


def get_lpl_teams():
    print("* Get LPL teams...")
    res = requests.get(
        'http://lpl.qq.com/web201612'
        '/data/LOL_MATCH2_TEAM_LIST.js'
    )
    data = json.loads(res.text.split('=', 1)[1][:-1])
    return dict(
        (team['TeamId'], team['TeamName'])
        for team in six.itervalues(data['msg']))


def get_lpl_matches(group_id, bitly):
    short_url = ''
    if bitly:
        normalized_url = (
            'http://lpl.qq.com/es/stats.shtml?bmid={0}').format(group_id)
        print('* Shorten URL...')
        shorten_data = bitly.shorten(normalized_url)
        short_url = shorten_data['url']

    res = requests.get(
        ('http://apps.game.qq.com/lol/match/apis/'
         'searchSMatchList.php?p0={0}&r1=SMatchListArr').format(group_id)
    )
    # Dirty way to convert JSONP to json.
    data = json.loads(res.text.split('=', 1)[1][:-1])
    return short_url, (msg['sMatchId'] for msg in data['msg'])


def get_match_result_lpl(match_id, champions,
                         game_number, teams, short_url):
    lpl_teams = get_lpl_teams()

    print('* Getting LPL data...')
    res = requests.get(
        ('http://apps.game.qq.com/lol/match/apis/'
         'searchMatchInfo_s.php?p0={0}&r1=MatchInfo').format(match_id)
    )
    # Dirty way to convert JSONP to json.
    msg_data = json.loads(res.text.split('=', 1)[1][:-1])['msg']
    battle_data = json.loads(msg_data['battleInfo']['BattleData'])

    data = dict()
    # Some data that needs to be prepared.
    data['patch_ver'] = ''
    m, s = divmod(int(battle_data['game-period']), 60)
    data['duration'] = '{0:02d}:{1:02d}'.format(m, s)
    data['game_date'] = battle_data['game-date']
    data['players'] = [
        p['name'] for p in battle_data['left']['players']
    ] + [
        p['name'] for p in battle_data['right']['players']
    ]
    match_info = msg_data['sMatchInfo']
    blue_team = match_info['BlueTeam']
    red_team = (
        match_info['TeamB']
        if match_info['BlueTeam'] == match_info['TeamA']
        else match_info['TeamA']
    )
    team_dict = dict(teams)
    data['blue_team_name'] = team_dict.get(
        lpl_teams[blue_team], lpl_teams[blue_team])
    data['red_team_name'] = team_dict.get(
        lpl_teams[red_team], lpl_teams[red_team])

    blue_kills = 0
    blue_golds = 0
    red_kills = 0
    red_golds = 0
    max_damage = 0
    for player in battle_data['left']['players']:
        blue_kills += int(player['kill'])
        blue_golds += int(player['gold'])
        max_damage = max(
            max_damage,
            int(player['totalDamageToChamp']))
    for player in battle_data['right']['players']:
        red_kills += int(player['kill'])
        red_golds += int(player['gold'])
        max_damage = max(
            max_damage,
            int(player['totalDamageToChamp']))

    data['max_damage'] = max_damage
    data['blue_kills'] = blue_kills
    data['red_kills'] = red_kills
    data['blue_golds'] = blue_golds
    data['red_golds'] = red_golds
    data['blue_golds'] = '{}k'.format(round(blue_golds / 100.00) / 10)
    data['red_golds'] = '{}k'.format(round(red_golds / 100.00) / 10)
    data['blue_result'] = (
        VICTORY_MSG
        if battle_data['game-win'] == 'left'
        else DEFEAT_MSG
    )
    data['red_result'] = (
        VICTORY_MSG
        if battle_data['game-win'] == 'right'
        else DEFEAT_MSG
    )
    # For LPL match history, empty ban is presented as champion id zero.
    blue_bans = [
        int(battle_data['left']['ban-hero-{0}'.format(i)])
        for i in range(1, 6)]
    red_bans = [
        int(battle_data['right']['ban-hero-{0}'.format(i)])
        for i in range(1, 6)]
    data['blue_bans'] = [
        champions[b] if b != 0 else ''
        for b in blue_bans
    ]
    data['red_bans'] = [
        champions[b] if b != 0 else ''
        for b in red_bans
    ]
    data['blue_dragons'] = '{0:<32}'.format(battle_data['left']['s-dragon'])
    data['red_dragons'] = battle_data['right']['s-dragon']

    data['participants'] = []
    for player in (battle_data['left']['players'] +
                   battle_data['right']['players']):
        participant = {
             'championId': int(player['hero']),
             'stats': {
                 'totalDamageDealtToChampions': int(
                     player['totalDamageToChamp']),
                 'kills': int(player['kill']),
                 'deaths': int(player['death']),
                 'assists': int(player['assist']),
                 'totalMinionsKilled': int(player['lasthit']),
                 'neutralMinionsKilled': 0,
                 'goldEarned': int(player['gold'])
             }
        }
        data['participants'].append(participant)

    data['team_blue'] = {
        'towerKills': battle_data['left']['tower'],
        'inhibitorKills': 0,
        'riftHeraldKills': 0,
        'baronKills': battle_data['left']['b-dragon']
    }
    data['team_red'] = {
        'towerKills': battle_data['right']['tower'],
        'inhibitorKills': 0,
        'riftHeraldKills': 0,
        'baronKills': battle_data['right']['b-dragon']
    }
    return output_match_result(data, game_number, short_url, champions, True)


@click.command()
@click.option('--number', '-n', type=int, default=1,
              help='The game number of the first match. Default: 1')
@click.option('--teams', '-t', type=(six.text_type, six.text_type), multiple=True,
              help='The team names. e.g. -t FW "Flash Wolves"')
@click.option('--bitly_token', '-b', type=six.text_type, default=u'',
              help='The bitly generic access token to generate short URLs.')
@click.argument('urls', nargs=-1)
def main(number, teams, bitly_token, urls):
    champions = get_champions()
    # Print and copy to clipboard.
    output = ''
    i = number
    bitly = None
    if bitly_token:
        bitly = bitly_api.Connection(access_token=bitly_token)
    for url in urls:
        url_regex = (
            r'^https?://matchhistory\.(?P<site>[a-z]+\.leagueoflegends\.com|'
            r'leagueoflegends\.co\.kr)\/(?P<lang>[a-z]+)\/#match-details\/'
            r'(?P<server>[0-9A-Z]+)\/(?P<id1>[0-9]+)'
            r'(?P<id2>\/[0-9]+|\?gameHash=(?P<hash>[0-9a-z]+))'
        )
        url_match = re.match(url_regex, url)
        if url_match:
            output += get_match_result(url_match, champions, i, teams, bitly)
            i += 1
        else:
            lpl_url_regex = (
                r'^http://lpl\.qq\.com\/es\/stats\.shtml'
                r'\?bmid=(?P<id>[0-9]+)$'
            )
            lpl_old_url_regex = (
                r'^http://lol\.qq\.com\/match\/match_data\.shtml'
                r'\?bmid=(?P<id>[0-9]+)$'
            )
            lpl_url_match = re.match(lpl_url_regex, url)
            lpl_old_url_match = re.match(lpl_old_url_regex, url)
            # For LPL, we should fetch every matches in the group.
            if lpl_url_match:
                short_url, matches = get_lpl_matches(lpl_url_match.group('id'), bitly)
                for match_id in matches:
                    output += get_match_result_lpl(
                        match_id, champions, i, teams, short_url)
                    i += 1
            elif lpl_old_url_match:
                short_url, matches = get_lpl_matches(lpl_old_url_match.group('id'), bitly)
                for match_id in matches:
                    output += get_match_result_lpl(
                        match_id, champions, i, teams, short_url)
                    i += 1
    print(output)
    pyperclip.copy(output)
    print('Copied to clipboard!')


if __name__ == '__main__':
    main()

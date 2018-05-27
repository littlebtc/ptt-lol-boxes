![Screenshot](https://i.imgur.com/Ny8UaTb.png)

### ptt-lol-boxes

An open-sourced Python script to generate ready-to-use box article from LoL match history to PTT.

The result will be copied to your clipboard :)

#### Getting started

`virtualenv` is recommended.

Install the requirements first:

    pip install -r requirements.txt

Usage can be checked by using `--help` option.

    $ python go.py --help
    Usage: go.py [OPTIONS] [URLS]...

    Options:
      -n, --number INTEGER        The game number of the first match. Default: 1
      -t, --teams <TEXT TEXT>...  The team names. e.g. -t FW "Flash Wolves"
      -b, --bitly_token TEXT      The bitly generic access token to generate short
                                  URLs.
      --help                      Show this message and exit.

For example, get the match result from the [final match](https://matchhistory.na.leagueoflegends.com/en/#match-details/TRLH1/1002570098?gameHash=0fb783d881dfa330&tab=stats) of the MSI 2018:

    python go.py https://matchhistory.na.leagueoflegends.com/en/#match-details/TRLH1/1002570098?gameHash=0fb783d881dfa330


Get the whole BO5 matches at one time, with correct team names and short URLs:

    python go.py -t RNG "Royal Never Give Up" -t KZ "Kingzone DragonX" -b xxxxxx https://matchhistory.na.leagueoflegends.com/en/#match-details/TRLH1/1002570087?gameHash=e506fdec16a5629d https://matchhistory.na.leagueoflegends.com/en/#match-details/TRLH1/1002570096?gameHash=6c652054b242d072 https://matchhistory.na.leagueoflegends.com/en/#match-details/TRLH1/1002570097?gameHash=96b0da282b905451 https://matchhistory.na.leagueoflegends.com/en/#match-details/TRLH1/1002570098?gameHash=0fb783d881dfa330


Change `xxxxxx` to the generic access token you generated on the bitly website.

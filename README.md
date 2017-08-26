# qldsmash-parser
Under construction!

This uses BeautifulSoup to scrape [QLDSmash](https://qldsmash.com/Online) (a website for Super Smash Bros. competitive play in Australia). It can then generate various information otherwise not available on the site directly, such as showing win/loss ratios for one player against another/one player against several other players/a table of several players against each other, list of which characters a player most frequently loses to, a list of upsets that occured during a certain time based on Elo, or which players out of a list have attended the most tournaments. It uses dateutil to constrain all this information to a certain time period, and can use openpyxl or Pillow to export tables to an Excel workbook or an image respectively.

There's not really a CLI or GUI for now, other than a barebones command line interface which only exposes the most basic functionality so far. For now, you'll have to edit main.py to call the function you want.
"""
It might be cool at some point to get rankings, ranking of a player at a tournament, and
any sets played at a tournament
Also this means you can determine that L R5 is loser's finals etc
"""

from bs4 import BeautifulSoup
from datetime import date
import qldsmashparser
from qldsmashparser import parse_int
import re
from urllib.parse import quote

class Bracket():
	"""
	This represents each individual bracket at a tournament, like
	how you might have both Melee and Smash 4 at a tournament
	"""
	def __init__(self, bracket_id, name, game, tournament):
		self.bracket_id = bracket_id
		self.name = name
		self.game = game
		self.tournament = tournament
		
	def __repr__(self):
		return repr({'id': self.bracket_id, 'name': self.name, 'game': self.game})
	
	def get_sets(self):
		#bracket_id = next(bracket.bracket_id for bracket in self._get_brackets() 
		#				  if bracket.name == bracket_name)
		sets = self.tournament.page(lambda tag: tag.find('th') is None and
						   tag.find('td') is not None and
						   tag.has_attr('data-match-event-id') and
						   tag['data-match-event-id'] == self.bracket_id)
		return [create_set_from_tournament_match(s, self) for s in sets]
	
	def get_losers_finals(self, bracket):
		#TODO
		pass

GET_TOURNAMENT_PAGE_CACHE = {}
HEADING_DATE_REGEX = re.compile(r'\[.+\]\s+.+\s+-\s+\((\d+)/(\d+)/(\d+)\)')
class Tournament():
	"""
	Doc McString
	"""

	@staticmethod
	def __get_tournament_page(region, name):
		"""
		Returns the actual tournament page from QLDSmash, parsed with BeautifulSoup
		"""
		if (region, name) not in GET_TOURNAMENT_PAGE_CACHE:
			print('Retrieving tournament page for {0} from {1}'.format(name, region))
			url = 'http://qldsmash.com/Results/{0}?t={1}'.format(region, quote(name))
			page = BeautifulSoup(qldsmashparser.get_http(url), 'lxml')
			print('Finished retrieving tournament page for {0} from {1}'.format(name, region))
			GET_TOURNAMENT_PAGE_CACHE[(region, name)] = page
		return GET_TOURNAMENT_PAGE_CACHE[(region, name)]

	@property
	def page(self):
		if not hasattr(self, '__page'):
			self.__page = Tournament.__get_tournament_page(self.region, self.name)
		return self.__page


	def __init__(self, region, name):
		#self.page = Tournament.__get_tournament_page(region, name)
		self.region = region
		self.name = name
		self._brackets = self._get_brackets()
		
	@property
	def date(self):
		header = self.page.find(class_='col-sm-12').get_text().strip()
		match = HEADING_DATE_REGEX.match(header)
		return date(parse_int(match.group(3)), parse_int(match.group(2)), parse_int(match.group(1)))
		
	def _get_brackets(self):
		js_filters = self.page.find_all(class_='js-filter-results')
		#The data-ga-label property seems to be a bit broken on QLDSmash at the time
		#of writing, it looks like it's supposed to say something like
		#"SSBU - Smash 4 Singles" but instead says "SSBU" and then there are
		#empty attributes after it named -, smash, 4, and singles
		return [Bracket(js_filter['data-ga-value'],
						js_filter.get_text().strip(),
						js_filter['data-ga-label'],
						self)
			for js_filter in js_filters]
	
	@property
	def brackets(self):
		return self._brackets
	
	def __getitem__(self, key):
		return next(bracket for bracket in self._brackets if bracket.name == key)
	
	#TODO Should probably implement __iter__ and maybe __missing__ and maybe __len__
	
	
PLAYER_URL_REGEX = re.compile(r'/Players/(.+)\?p=(.+)')
	
def create_set_from_tournament_match(s, bracket):
	if s.find(class_='nowrap') is None:
		return str(s) #why
	the_round = s.find(class_='nowrap').string.strip()
	#construct winner and loser PlayerOfSet objects from URL and characters
	#Forfeit can probably be determined from score (it looks to be always ' - ')
	#And then there you have it a SmashSet object
	#Move this to bracket class
	score = s.find(lambda tag: tag.name == 'td' and not tag.has_attr('class')).string.strip()
	tournament = bracket.tournament
	forfeit = score == '-'
	winner_url_matches = PLAYER_URL_REGEX.match(s.select_one('.link-block.success > a')['href'])
	winner = qldsmashparser.PlayerOfSet(winner_url_matches.group(2),
										list(map(lambda img: img['alt'], s.select('.text-right.success > img'))),
										winner_url_matches.group(1))
	loser_url_matches = PLAYER_URL_REGEX.match(s.select_one('.link-block.danger > a')['href'])
	loser = qldsmashparser.PlayerOfSet(loser_url_matches.group(2),
									   list(map(lambda img: img['alt'], s.select('.text-right.danger > img'))),
									   loser_url_matches.group(1))
	return qldsmashparser.SmashSet(tournament.name, tournament.region, bracket.game, bracket.name, winner, loser, forfeit, score, the_round, tournament.date)

print(Tournament('ACT', 'Capital Smash 22').date)
print(Tournament('ACT', 'Capital Smash 22')['Smash 4 Singles']) 
print(Tournament('ACT', 'Capital Smash 22')['Smash 4 Singles'].get_sets())


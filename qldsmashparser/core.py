"""
Copyright (c) 2017 Megan Leet (Zowayix)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

This one is where all the magic happens, where it parses the pages and all
that kinda crap
"""

import atexit
import dateutil.relativedelta
import gzip
import json
import re
from bs4 import BeautifulSoup
from datetime import date
from functools import reduce
from urllib.parse import quote, unquote
from urllib.request import urlopen
	
def write_cache_to_json():
	"""
	Called at exit, this means I can load the cache later and not 
	have to download pages again next time I run the script
	This will overwrite the cache if it already exists
	"""
	with gzip.open('player_cache.gz', 'wt') as player_cache:
		json.dump({'/'.join(key): 
				  str(value) for key, value in GET_PLAYER_PAGE_CACHE.items()}, player_cache)
	with gzip.open('tournament_cache.gz', 'wt') as tournament_cache:
		json.dump({'/'.join(key): 
				  str(value) for key, value in GET_TOURNAMENT_PAGE_CACHE.items()}, tournament_cache)

def load_cache():
	"""
	Yeah I kinda want to load the cache when I run the thing too
	It won't load anything if there is no cache to load, but the cache will be
	generated at the end
	"""
	try:
		with gzip.open('player_cache.gz', 'rt') as player_cache:
			#json.load does not return a bool you fucking dumb piece of shit
			#pylint: disable=no-member
			for key, value in json.load(player_cache).items():
				GET_PLAYER_PAGE_CACHE[tuple(key.split('/'))] = BeautifulSoup(value, 'lxml')
	except (FileNotFoundError, ValueError):
		pass
	try:
		with gzip.open('tournament_cache.gz', 'rt') as tournament_cache:
			#pylint: disable=no-member
			for key, value in json.load(tournament_cache).items():
				GET_TOURNAMENT_PAGE_CACHE[tuple(key.split('/'))] = BeautifulSoup(value, 'lxml')
	except (FileNotFoundError, ValueError):
		pass

GET_PLAYER_PAGE_CACHE = {}
GET_TOURNAMENT_PAGE_CACHE = {}
load_cache()
atexit.register(write_cache_to_json)

class Generic:
	#pylint: disable=too-few-public-methods
	"""
	This just lets you create a custom object with any old attributes
	easily, because object() doesn't let you do that e.g. you can do
	a = Generic(x=1, y=2) and then a.x == 1
	Also repr() gives it a dictionary representation of the attributes
	"""
	def __init__(self, ** params):
		self.__dict__.update(params)
	def __repr__(self):
		return repr(self.__dict__)
	
def get_alt(img):
	"""
	cbf lambdas all the time to do this one thing
	"""
	return img['alt'] if img.has_attr('alt') else None

def get_img_alts(image_list):
	"""zzzz"""
	return [get_alt(img) for img in image_list]
	
PLAYER_URL_REGEX = re.compile(r'/Players/(.+)\?p=(.+)')
class Player():
	"""
	I can't be fucked writing docstrings anymore. This does what I say it does
	"""
	@staticmethod
	def __get_player_page(region, name):
		"""
		Returns the actual player page from QLDSmash, parsed with BeautifulSoup
		"""
		if (region, name) not in GET_PLAYER_PAGE_CACHE:
			print('Retrieving player page for {0} from {1}'.format(name, region))
			url = 'http://qldsmash.com/Players/{0}?p={1}'.format(region, quote(name))
			page = BeautifulSoup(get_http(url), 'lxml')
			print('Finished retrieving player page for {0} from {1}'.format(name, region))
			GET_PLAYER_PAGE_CACHE[(region, name)] = page
		return GET_PLAYER_PAGE_CACHE[(region, name)]
	
	@classmethod
	def from_url(cls, url):
		"""
		You put a URL in and you get a player y'know whatever
		"""
		matches = PLAYER_URL_REGEX.match(url)
		region = unquote(matches.group(1))
		name = unquote(matches.group(2))
		return cls(region, name)
	
	def __init__(self, region, name):
		self.__page_internal = None
		self.region = region
		self.name = name
		
	def __eq__(self, other):
		return self.region == other.region and self.name.casefold() == other.name.casefold()
	
	def __ne__(self, other):
		return not self == other
	
	def __hash__(self):
		return hash((self.region, self.name))
	
	@property
	def __page(self):
		if self.region is None:
			print('Warning in Player.__page: {0} has no region'.format(self.name))
			return None
		if self.__page_internal is None:
			self.__page_internal = Player.__get_player_page(self.region, self.name)
		return self.__page_internal
	
	def get_games_played(self):
		"""Returns list of games this player has attended tournaments for, e.g. SSBU/SSBM"""
		def __is_stat_element(tag):
			if not tag.has_attr('data-slide'):
				return False
			return tag['data-slide'].startswith('#stats')
		stats_elements = self.__page.find_all(__is_stat_element)
		return [element['data-slide'][len('#stats'):] for element in stats_elements]
		
	def get_elo(self, game):
		"""
		Returns the Elo (as an int) this player has for a given Smash game.
		"""
		if self.__page is None:
			return None
		stats_element = self.__page.find(attrs={'data-slide': '#stats' + game})
		if stats_element is None:
			return None
		if stats_element.strong is None:
			#This person doesn't have Elo, perhaps they've just been added to the
			#database and it's not Thursday morning yet
			return None
		return parse_int(stats_element.strong.string)
	
	def get_mains(self, game):
		"""
		docstring docstring docstring
		"""
		stats_element = self.__page.find(attrs={'data-slide': '#stats{0}'.format(game)})
		#Drop the first element, as that is the logo of the game
		return get_img_alts(stats_element('img'))[1:]
	
	@property
	def true_name(self):
		"""
		The name but with the capitalisation corrected to how it appears on the site, etc
		This probably doesn't matter too much now that I started using casefold() everywhere
		"""
		if self.__page is None:
			print('{0} from {1} doesn\'t actually exist or something'.format(self.name, self.region))
			return None
		page_header = self.__page.find(id='dHero')
		if page_header is None:
			return None
		return page_header.h1.string.strip()
		
	def get_sets(self):
		"""
		Gets the player page from QLDSmash, and returns a list of SmashSet objects for
		all the sets they've played in history
		"""
		if self.true_name is None:
			print('Attempted to call get_sets on {0}/{1}'.format(self.region, self.name))
			return []
		return [SmashSet.from_match_history(element) for element
			in self.__page.find_all(class_='match-history')]
	
	def get_opponent_data(self, game, opponent, date_limit=None, include_forfeits=False, 
						  additional_filter=None):
		"""
		No this doesn't have too many arguments fuck off
		Anyway this gets a summary of information about one player versus another, and
		lists of all the sets that they have won or lost
		"""

		if self == opponent:
			#No point trying to find sets for someone against themselves, return empty data
			return OpponentMatchupData()

		def __set_filter(the_set):
			if the_set.game != game:
				return False
			if not (the_set.involves_player(self) and the_set.involves_player(opponent)):
				return False
				
			if the_set.forfeit and not include_forfeits:
				return False
			if date_limit is not None and the_set.date < date_limit:
				return False
			return additional_filter(the_set) if additional_filter is not None else True

		filtered_sets = list(filter(__set_filter, self.get_sets()))

		return OpponentMatchupData.create(self, filtered_sets)
	

TOURNAMENT_URL_REGEX = re.compile(r'/Results/(.+)\?t=(.+)')
class SmashSet():
	"""
	Holds a bunch of information about a specific set, I'm shit at
	documentation okay
	This is probably messy
	"""
	def __init__(self, tournament_name, tournament_region, game, bracket,
				 winner, loser, forfeit, score, the_round, the_date):
		#pylint: disable=too-many-arguments
		#Seems like it needs all these arguments for what it does
		self.tournament = Tournament(tournament_region, tournament_name)
		self.game = game
		self.bracket_name = bracket
		self.winner = winner
		self.loser = loser
		self.forfeit = forfeit
		self.score = '0 - F' if forfeit else score
		self.round = the_round
		self.date = the_date
		
	def __repr__(self):
		return repr(self.__dict__)
	
	@property
	def bracket(self):
		"""Gets the bracket object for the bracket this set was part of, not just the name"""
		return self.tournament[self.bracket_name]
	
	def get_formatted_round(self, lookup_bracket):
		"""See format_round I guess"""
		if lookup_bracket:
			return format_round(self.round, self.bracket)
		return format_round(self.round)
		
	def involves_player(self, player):
		"""Is either player in this set a certain player? (used for filtering)"""
		return self.winner == player or self.loser == player
	
	def won_by_player(self, player):
		"""Is this player the winner of this set? (also used for filtering)"""
		return self.winner == player

	@classmethod
	def from_match_history(cls, match_history_element):
		"""
		Gets actual useful info out of a HTML element for a set in the
		history section of a QLDSmash player page
		"""
		if match_history_element in FROM_MATCH_HISTORY_CACHE:
			return FROM_MATCH_HISTORY_CACHE[match_history_element]
				
		heading = match_history_element.find(class_='panel-heading')
		body = match_history_element.find(class_='panel-body')
		footer = match_history_element.find(class_='panel-footer').findAll(class_='col-xs-6')
		
		score = body.find(class_='col-xs-2').string.strip()
		forfeit = body.find(class_='col-md-12') is not None or score == '-'
		if forfeit:
			games_to_winner = None
			games_to_loser = None
		else:
			split_score = score.split(' - ')
			#TODO This shouldn't assume bigger number goes first, and should detect that
			games_to_winner = parse_int(split_score[0])
			games_to_loser = parse_int(split_score[1])
		
		
		player_elements = body(class_='col-xs-5')
		def __convert_player_element(element, is_winner):
			return PlayerOfSet(element.get_text().strip(), get_img_alts(element('img')), 
							   get_player_region_from_page(element),
							   games_to_winner if is_winner else games_to_loser)
							 
		#Seems to always be the case that winner is first, I suppose you could
		#do something like
		#win = match_history_element['data-filter-win'] == 'True'
		#winner_first = (player[0] == me) if win else (player[0] == opponent)
		#to make sure
		winner = __convert_player_element(player_elements[0], True)
		loser = __convert_player_element(player_elements[1], False)


		#It's not always reliable to look at the actual text in the <a>
		#element in the heading, because of a certain tournament with a name
		#starting with Buys of the AC3 16 having a space at the beginning
		tournament_url_matches = TOURNAMENT_URL_REGEX.match(heading.a['href'])
		tournament_name = unquote(tournament_url_matches.group(2))
		tournament_region = unquote(tournament_url_matches.group(1))
		
		
		bracket = heading.find(class_='pull-right').small.string.strip()
		if bracket[-1] == ')':
			bracket = bracket[:-1]
		if bracket[0] == '(':
			bracket = bracket[1:]
				
		this_set = cls(tournament_name, tournament_region, match_history_element['data-filter-game'],
					   bracket, winner, loser, forfeit, score, footer[0].string.strip(),
					   date(*[int(x) for x in footer[1].string.strip().split('/')[::-1]]))
							
		FROM_MATCH_HISTORY_CACHE[match_history_element] = this_set
		return this_set
FROM_MATCH_HISTORY_CACHE = {} #Why does this take so long it needs memoization?
	
class PlayerOfSet(Player):
	"""
	Represents a single instance of a player in some particular match, so
	you have things specific to each set like which character they used
	as well as all the normal Player methods
	"""
	def __init__(self, name, characters, region, games_won):
		super().__init__(region, name)
		self.characters = characters
		self.games_won = games_won
		
	def __repr__(self):
		return repr({'name': self.name, 'region': self.region,
					'characters': self.characters, 'games_won': self.games_won})
		

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
	
	def __eq__(self, other):
		return self.tournament == other.tournament and self.bracket_id == other.bracket_id
	
	def __ne__(self, other):
		return not self == other
	
	def __hash__(self):
		return hash((self.tournament, self.bracket_id))
	
	def get_sets(self):
		"""Returns a list of SmashSet objects for all the sets played in this bracket"""
		def __create_set_from_tournament_match(the_set):
			the_round = the_set.find(class_='nowrap').string.strip()
			def __is_score_element(tag):
				if tag.name != 'td':
					return False
				return not tag.has_attr('class')
			
			score = the_set.find(__is_score_element).string.strip()
			forfeit = score == '-'
			if forfeit:
				games_to_winner = None
				games_to_loser = None
			else:
				split_score = score.split(' - ')
				games_to_winner = parse_int(split_score[0])
				games_to_loser = parse_int(split_score[1])					 
			
			tournament = self.tournament
			
			def __create_player_object(is_winner):
				css_class = 'success' if is_winner else 'danger'
				element = the_set.select_one('.link-block.{0} > a'.format(css_class))
				image_elements = the_set.select('.text-right.{0} > a'.format(css_class))
				games_won = games_to_winner if is_winner else games_to_loser
				if element is None:
					#Not in the database
					name = the_set.select_one('.link-block.{0}'.format(css_class)).get_text().strip()
					return PlayerOfSet(name, get_img_alts(image_elements), None, games_won)
				
				url_matches = PLAYER_URL_REGEX.match(element['href'])
				return PlayerOfSet(unquote(url_matches.group(2)),
								   get_img_alts(image_elements),
								   unquote(url_matches.group(1)), games_won)
									   
			winner = __create_player_object(True)
			loser = __create_player_object(False)
			return SmashSet(tournament.name, tournament.region, self.game, self.name,
							winner, loser, forfeit, score, the_round, tournament.date)
		
		def __is_set_element(tag):
			if tag.find('th') is not None:
				return False
			if tag.find('td') is None:
				return False
			if not tag.has_attr('data-match-event-id'):
				return False
			return tag['data-match-event-id'] == self.bracket_id
		
		sets = self.tournament.page(__is_set_element)
		return [__create_set_from_tournament_match(s) for s in sets]
	
	def get_max_rounds(self):
		"""
		Returns the round number (where you have W R4 etc) which is the last one, so
		you can figure out which is winner's finals/winner's semis etc
		Returned as tuple (winners max, losers max)
		"""
		my_sets = self.get_sets()
		winners_sets = [_set for _set in my_sets if _set.round.startswith('W')]
		losers_sets = [_set for _set in my_sets if _set.round.startswith('L')]
		if not winners_sets:
			winners_max = None
		else:
			winners_max = max(parse_int(FORMAT_ROUND_REGEX.match(each_set.round).group(2))
							  for each_set in winners_sets)
		if not losers_sets:
			losers_max = None
		else:
			losers_max = max(parse_int(FORMAT_ROUND_REGEX.match(each_set.round).group(2))
							 for each_set in losers_sets)
		
		return (winners_max, losers_max)
		
HEADING_DATE_REGEX = re.compile(r'\[.+\]\s+.+\s+-\s+\((\d+)/(\d+)/(\d+)\)')
class Tournament():
	"""
	Doc McString write later
	"""

	@staticmethod
	def __get_tournament_page(region, name):
		if (region, name) not in GET_TOURNAMENT_PAGE_CACHE:
			print('Retrieving tournament page for {0} from {1}'.format(name, region))
			url = 'http://qldsmash.com/Results/{0}?t={1}'.format(region, quote(name))
			page = BeautifulSoup(get_http(url), 'lxml')
			print('Finished retrieving tournament page for {0} from {1}'.format(name, region))
			GET_TOURNAMENT_PAGE_CACHE[(region, name)] = page
		return GET_TOURNAMENT_PAGE_CACHE[(region, name)]

	@property
	def page(self):
		"""
		Returns the actual tournament page from QLDSmash, parsed with BeautifulSoup (lazy loaded)
		"""
		if self.__page is None:
			self.__page = Tournament.__get_tournament_page(self.region, self.name)
		return self.__page


	def __init__(self, region, name):
		self.__page = None
		self.region = region
		self.name = name
		self.__brackets = None
			
	def __repr__(self):
		return repr({'name': self.name, 'region': self.region})
	
	def __eq__(self, other):
		return self.region == other.region and self.name == other.name
	
	def __ne__(self, other):
		return not self == other
		
	def __hash__(self):
		return hash((self.region, self.name))
		
	@property
	def date(self):
		"""
		The date that this tournament took place. This is the first day for events (e.g. majors)
		that took place across multiple days, because that's just how QLDSmash does it
		"""
		header = self.page.find(class_='col-sm-12').get_text().strip()
		match = HEADING_DATE_REGEX.match(header)
		return date(parse_int(match.group(3)), parse_int(match.group(2)), parse_int(match.group(1)))
		
	def __get_brackets(self):
		js_filters = self.page.find_all(class_='js-filter-results')
		#The data-ga-label property seems to be a bit broken on QLDSmash at the time
		#of writing, it looks like it's supposed to say something like
		#"SSBU - Smash 4 Singles" but instead says "SSBU" and then there are
		#empty attributes after it named -, smash, 4, and singles
		
		def __create_bracket(js_filter):
			game = js_filter['data-ga-label']
			if game.startswith('data-ga-value='):
				#WHOOPS someone forgot to put the game in hey (or it's doubles or just weird)
				game = None
			return Bracket(js_filter['data-filter-event'], js_filter.get_text().strip(),
						   game, self)
						   
		return [__create_bracket(js_filter) for js_filter in js_filters]
	
	@property
	def brackets(self):
		"""List of Bracket objects for this tournament (see Bracket class)"""
		if self.__brackets is None:
			self.__brackets = self.__get_brackets()
		return self.__brackets
	
	def __getitem__(self, key):
		return next(bracket for bracket in self.brackets if bracket.name.casefold() == key.casefold())
	
		
class OpponentMatchupData(Generic):
	"""
	Used with Player().get_opponent_data, sorta stores aggregated data
	against an opponent I guess but also wins and stuff, I dunno
	as I say in the docstring for create() I could do something more with this
	"""
	
	def __init__(self, ** args):
		self.total_set_count = '-'
		self.win_count = '-'
		self.loss_count = '-'
		self.game_win_count = '-'
		self.game_loss_count = '-'
		self.total_game_count = '-'
		self.set_win_rate = '-'
		self.game_win_rate = '-'
		self.wins = []
		self.losses = []
		super().__init__( ** args)
	
	@classmethod
	def create(cls, player, filtered_sets):
		"""
		Aggregates the data in filtered_sets, basically
		Hmm... if I think about it, this could be genericized to be some
		kind of aggregation of multiple sets class rather than opponent
		matchup data specifically, but I'll burn that bridge when I get to it
		"""
		
		def __did_win_set(the_set):
			return the_set.winner == player
		
		def __did_lose_set(the_set):
			return the_set.loser == player
		
		def __sum_games_won(total, the_set):
			return total + (the_set.winner.games_won if __did_win_set(the_set) else the_set.loser.games_won)
		
		def __sum_games_lost(total, the_set):
			return total + (the_set.winner.games_won if __did_lose_set(the_set) else the_set.loser.games_won)
		
		wins = list(filter(__did_win_set, filtered_sets))
		losses = list(filter(__did_lose_set, filtered_sets))
	
		total_set_count = len(filtered_sets)
		win_count = len(wins)
		loss_count = len(losses)
		game_win_count = reduce(__sum_games_won, filtered_sets, 0)
		game_loss_count = reduce(__sum_games_lost, filtered_sets, 0)
		total_game_count = game_win_count + game_loss_count
		has_sets = total_set_count > 0
		has_games = total_game_count > 0
		return cls(
				   total_set_count=total_set_count,
				   win_count=win_count,
				   loss_count=loss_count,
				   total_game_count=total_game_count,
				   game_win_count=game_win_count,
				   game_loss_count=game_loss_count,
				   set_win_rate=(win_count / total_set_count) * 100 if has_sets else 'N/A',
				   game_win_rate=(game_win_count / total_game_count) * 100 if has_games else 'N/A',
				   wins=wins,
				   losses=losses
				   )
				   	
def parse_int(string):
	"""
	Like int(), but just returns None if it doesn't parse properly
	"""
	try:
		return int(string)
	except ValueError:
		pass

def get_http(url):
	"""
	Stops me having to mess around with closing objects, I just want the content of the page
	"""
	with urlopen(url) as response:
		return response.read()

FORMAT_ROUND_REGEX = re.compile(r'^(W|L|P\d+)\s+(?:R|M)?(.*)$')
def format_round(round_code, bracket=None):
	"""
	Parses that little thing at the bottom of the QLDSmash match history element
	that says something like "W R2" or "P3 M7" into something much nicer
	like "Winners Bracket Round 2" or "Pool #3 Match #7"
	To do something like "Winner's Semis" or "Loser's Finals" requires looking at
	the Bracket object
	"""
	if bracket is not None:
		winners_max, losers_max = bracket.get_max_rounds()
	
	if round_code == '[F]':
		return 'Grand Finals'
	if round_code == '[GF]':
		return 'Grand Finals Bracket Reset'
	
	matches = FORMAT_ROUND_REGEX.match(round_code)
	bracket_side = matches.group(1)
	round_number = matches.group(2)
	if bracket_side == 'W':
		#Is it Winners or Winner's? I can never be quite sure
		prefix = 'Winners'
		max_round = winners_max
	elif bracket_side == 'L':
		prefix = 'Losers'
		max_round = losers_max
	else:
		return 'Pool #{0} Match #{1}'.format(bracket_side.lstrip('P'), round_number) 
	
	if bracket is not None:
		if parse_int(round_number) == max_round:
			return prefix + ' Finals'
		elif parse_int(round_number) == max_round - 1:
			return prefix + ' Semis'
		elif parse_int(round_number) == max_round - 2:
			return prefix + ' Quarters'
	
	return '{0} Bracket Round {1}'.format(prefix, round_number)
		

def get_player_region_from_page(player_element_in_match_history):
	"""
	This just gets the region of some player in the match history by
	looking at the URL. Some players aren't in the QLDSmash database at
	all though and don't have links, so we return None for those, and that
	means elsewhere in the code I should be checking for region is None, or
	maybe having some kind of is_in_database property
	"""
	player_link = player_element_in_match_history.div.find('a')
	if player_link is None:
		return None

	return unquote(PLAYER_URL_REGEX.match(player_link['href']).group(1))

def get_all_headers_in_table(table):
	"""
	This is just here if I decide to mess with CSV again really, or otherwise
	need to get all the inner keys out of a dict of dicts, which I will
	inevitably forget how to do otherwise
	"""
	return list({key for row in table.values() for key in row.keys()})

def past_date_from_delta(** args):
	"""
	Intended for use with date_limit parameters, returns something like
	3 months ago for past_date_from_delta(months=3)
	"""
	return date.today() - dateutil.relativedelta.relativedelta( ** args)

def write_table_to_json(table, filename):	
	"""Well it actually just writes anything to a file as JSON"""
	with open(filename, 'w') as the_file:
		json.dump(table, the_file)
		
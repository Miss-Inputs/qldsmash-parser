#Crappy CLI which sucks but at least it's an interface

import argparse

arg_parser = argparse.ArgumentParser()
subparsers = arg_parser.add_subparsers(dest='cmd')

get_player = subparsers.add_parser('get_player')
get_player.add_argument('region')
get_player.add_argument('player_name')

get_tournament = subparsers.add_parser('get_tournament')
get_tournament.add_argument('region')
get_tournament.add_argument('tournament_name')

get_all_players = subparsers.add_parser('get_all_players')
get_all_players.add_argument('region')

get_attendance = subparsers.add_parser('get_attendance')
get_attendance.add_argument('--all-players-from-region', action='store_true')
get_attendance.add_argument('player_list')
get_attendance.add_argument('game')
#TODO Allow time deltas for these arguments (maybe put that into parse_date)
#Also allow for referencing date of a tournament perhaps
get_attendance.add_argument('start_date')
get_attendance.add_argument('end_date')

args = arg_parser.parse_args()

import core
import main
from dateutil.parser import parse

def parse_date(stringy):
	return parse(stringy, dayfirst=True).date()

def check_for_args(args):
	#This code probably sucks too but if you think about it isn't it still
	#premature optimization if you're optimizing for readability before readability is
	#determined to definitely be a problem and you've isolated this function as the cause
	#of lack of readability? Checkmate atheists
	if args.cmd == 'get_player':
		return core.Player(args.region, args.player_name)
	if args.cmd == 'get_tournament':
		return core.Tournament(args.region, args.tournament_name)
	if args.cmd == 'get_all_players':
		return main.get_all_players(args.region)
	if args.cmd == 'get_attendance':
		start_date = parse_date(args.start_date)
		end_date = parse_date(args.end_date)
		if args.all_players_from_region:
			player_list = main.get_all_players(args.player_list)
		else:
			print('Borf borf borf unimplemented')
			player_list = []
		return main.get_tournament_attendance(player_list, args.game, start_date, end_date)
	
	return "I've done something horribly wrong  with " + repr(args)

def get_short_format(obj):
	if isinstance(obj, core.Player):
		return '{0}/{1}'.format(obj.region, obj.name)
	else:
		return repr(obj)
	
def print_output(obj):
	#This is probably the wrong way to code this, but my iced coffee hasn't kicked in yet
	#Now I'm drunk and I'm just gonna let myself realise some other time what the best way
	#to do this is, and for now just go with this because I guess it works? Until it doesn't
	#TODO: Exit with error message if something doesn't exist
	if isinstance(obj, list):
		for item in obj:
			print_output(item)
			print('-' * 10)
	elif isinstance(obj, dict):
		formatted_dict = {get_short_format(k): get_short_format(v) for k, v in obj.items()}
		max_len = max(len(k) for k in formatted_dict.keys())
		for k, v in formatted_dict.items():
			print('{0:<{2}}\t{1}'.format(k, v, max_len))
	elif isinstance(obj, core.Player):
		print('Information for player {0} from {1}:'.format(obj.name, obj.region))
		print('-' * 10)
		
		games_played = obj.get_games_played()
		print('Games played: {0}'.format(games_played))
		for game_played in games_played:
			print('Elo for {0}: {1}'.format(game_played, obj.get_elo(game_played)))
			print('Tournament mains for {0}: {1}'.format(game_played, obj.get_mains(game_played)))
	elif isinstance(obj, core.Tournament):
		print('Information for tournament {0} in {1}:'.format(obj.name, obj.region))
		print('-' * 10)
		print('Date of tournament: {0}'.format(obj.date))
		
		print('-' * 4)
		brackets = obj.brackets
		for bracket in brackets:
			print_output(bracket)
			print('-' * 4)
	elif isinstance(obj, core.Bracket):
		print('Bracket: {0}'.format(obj.name))
		print('Game: {0}'.format(obj.game))
	else:
		print(repr(obj))
	
output = check_for_args(args)
print_output(output)
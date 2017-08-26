"""
Ignore this
"""

if __name__ == "__main__":
    print "Hello World"

def get_data_against_act_opponents(region, player):
    """
    For each player, gets some information about how they go against
    each of the ACT players who actually show up these days
    """
    
    def did_pazx_sandbag(this_set):
        """Pazx sandbagged at these events, except against Maple
        Because I'm nice, I'm treating this sandbagging as a separate
        player entirely to not mess with Pazx's stats
        """ 
        if region == 'ACT' and player == 'MapleMage':
            return False
        if this_set.event_region == 'ACT' and this_set.event == 'Capital Smash 20':
            return True
        if this_set.event_region == 'ACT' and this_set.event == 'Rise of the ACT 18':
            return True
        return False
    
    def did_pazx_play_properly(this_set):
        return not did_pazx_sandbag(this_set)
    
    data = {}
    for opponent in RELEVANT_ACT_PLAYERS:
        if opponent == 'Pazx':
            data[opponent] = get_opponent_data('SSBU', region, player,
                                               'ACT', opponent, False, did_pazx_play_properly)
        elif opponent == 'Sandbag!Pazx':
            data[opponent] = get_opponent_data('SSBU', region, player,
                                               'ACT', 'Pazx', False, did_pazx_sandbag)
        else:
            data[opponent] = get_opponent_data('SSBU', region, player, 'ACT', opponent)
    return data

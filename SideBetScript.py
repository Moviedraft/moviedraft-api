# =============================================================================
# Script requires two arguments to be passed when running:
#     The connection string to MongoDB
#     The database name
# =============================================================================

from pymongo import MongoClient
from bson.objectid import ObjectId
from enum import Enum
import sys

class SideBetStatus(Enum):
    current = 1
    previous = 2
    old = 3

client = MongoClient(sys.argv[1])
db = client.get_database(sys.argv[2])

previous_side_bets = db.sidebets.find({'status': SideBetStatus.previous.value})
previous_side_bets_list = [side_bet for side_bet in previous_side_bets]

for previous_side_bet in previous_side_bets_list:
    db.sidebets.update_one({'_id': previous_side_bet['_id']},
                           {'$set': {'status': SideBetStatus.old.value}})

    print('Updated status of previous side bet ID: \'{}\' to \'old\''.format(previous_side_bet['_id']))
    
side_bets = db.sidebets.find({'status': SideBetStatus.current.value})
side_bets_list = [side_bet for side_bet in side_bets]

for side_bet in side_bets_list:
    movie = db.movies.find_one({'_id': side_bet['movie_id']})

    if len(side_bet['bets']) < 1:
        print('No bets made for side bet ID: \'{}\''.format(side_bet['_id']))
        continue
    elif len(side_bet['bets']) == 1:
        winning_bet = side_bet['bets'][0] if side_bet['bets'][0]['bet'] < movie['domesticGross'] else {'user_id': None, 'bet': None}
    else:
        winning_bet = max((side_bet for side_bet in side_bet['bets'] if movie['domesticGross'] - side_bet['bet'] > 0), key= lambda x: x['bet'])

    print('Updating side bet ID: \'{}\' with winner \'{}\'. Bet was $\'{}\'. Weekend gross was $\'{}\''
          .format(side_bet['_id'],
                  winning_bet['user_id'] or None,
                  winning_bet['bet'],
                  movie['domesticGross']))

    db.sidebets.update_one({'_id': side_bet['_id']},
                           {'$set': {'winner': ObjectId(winning_bet['user_id']),
                                     'status': SideBetStatus.previous.value,
                                     'weekend_gross': movie['domesticGross']}})

    print('Updated side bet ID: \'{}\''.format((side_bet['_id'])))
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

side_bets = db.sidebets.find({'status': SideBetStatus.current.value})
side_bets_list = [side_bet for side_bet in side_bets]

for side_bet in side_bets_list:
    if len(side_bet['bets']) < 1:
        print('No bets made for side bet ID: \'{}\''.format(side_bet['_id']))
        continue

    movie = db.movies.find_one({'_id': side_bet['movie_id']})
    winning_bet = max((side_bet for side_bet in side_bet['bets'] if movie['domesticGross'] - side_bet['bet'] > 0), key= lambda x: x['bet'])

    print('Updating side bet ID: \'{}\' with winner \'{}\'. Bet was $\'{}\'. Weekend gross was $\'{}\''
          .format(side_bet['_id'],
                  winning_bet['user_id'],
                  winning_bet['bet'],
                  movie['domesticGross']))

    db.sidebets.update_one({'_id': side_bet['_id']},
                           {'$set': {'winner': ObjectId(winning_bet['user_id']),
                                     'status': SideBetStatus.previous.value }})

    print('Updated side bet ID: \'{}\''.format((side_bet['_id'])))
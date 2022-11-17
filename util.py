from hanabi import *

# Is this card definitely playable
def is_playable(knowledge, board):
    possible = get_possible(knowledge)
    return all(map(playable(board), possible))

# Is this card possibly playable
def maybe_playable(knowledge, board):
    possible = get_possible(knowledge)
    return any(map(playable(board), possible))

# Is this card definitely not playable
def is_useless(knowledge, board):
    possible = get_possible(knowledge)
    return all(map(useless(board), possible))
    
def maybe_useless(knowledge, board):
    possible = get_possible(knowledge)
    return any(map(useless(board), possible))
    
def has_property(predicate, knowledge):
    possible = get_possible(knowledge)
    return all(map(predicate, possible))

def may_have_property(predicate, knowledge):
    possible = get_possible(knowledge)
    return any(map(predicate, possible))

# Predicate can be playable(board), useless(board), rank(rank), color(color)
def probability(predicate, knowledge):
    num = 0.0
    denom = 0.0
    for col in ALL_COLORS:
        for i,cnt in enumerate(knowledge[col]):
            if predicate(Card(col,i+1)):
                num += cnt 
            denom += cnt
    return num/denom

def playable(board):
    def playable_inner(card):
        return card.is_playable(board)
    return playable_inner
     
def useless(board):
    def useless_inner(card):
        return card.is_useless(board)
    return useless_inner
    
def has_rank(rank):
    def has_rank_inner(card):
        return card.rank == rank
    return has_rank_inner
    
def has_color(color):
    def has_color_inner(card):
        return card.color == color
    return has_color_inner
    
def get_possible(knowledge):
    result = []
    for col in ALL_COLORS:
        for i,cnt in enumerate(knowledge[col]):
            if cnt > 0:
                result.append(Card(col,i+1))
    return result
    
def filter_actions(type, actions):
    return [act for act in actions if act.type == type]

def probability_is_card(knowledge, card):
    num = knowledge[card.color][card.rank - 1]
    denom = sum(sum(knowledge, []))
    return num / denom
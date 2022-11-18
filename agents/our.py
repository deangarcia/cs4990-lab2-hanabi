from hanabi import *
import util
import agent
import random
import copy
        
def format_hint(h):
    if h == HINT_COLOR:
        return "color"
    return "rank"
        
class OurPlayer(agent.Agent):
    def __init__(self, name, pnr):
        self.name = name
        self.hints = {}
        self.pnr = pnr
        self.explanation = []
    def get_action(self, nr, hands, knowledge, trash, played, board, valid_actions, hints, hits, cards_left):
        for player,hand in enumerate(hands):
            for card_index,_ in enumerate(hand):
                if (player,card_index) not in self.hints:
                    self.hints[(player,card_index)] = set()
        known = [""]*5
        for h in self.hints:
            pnr, card_index = h 
            if pnr != nr:
                known[card_index] = str(list(map(format_hint, self.hints[h])))
        self.explanation = [["hints received:"] + known]

        # Figure out what cards we want and don't want
        playable_cards = [Card(color, curr_rank+1) for color, curr_rank in board if curr_rank+1 <= 5] # Cards that are currently playable on the board
        unplayable_cards = []                                                                          # Cards that are not playable on the board
        for card in board:
            card_color, card_rank = card
            for rank in range(card_rank):
                unplayable_cards.append(Card(card_color, rank+1))

        my_knowledge = knowledge[nr]

        my_informed_knowledge = copy.deepcopy(my_knowledge) # Knowledge informed by discard pile and other players hands
        # Adjust my_knowledge based on other knowledge
        for i,k in enumerate(my_informed_knowledge):
            # Discount stuff we've discarded
            for discarded_card in trash:
                if k[discarded_card[0]][discarded_card[1] - 1] > 0:
                    k[discarded_card[0]][discarded_card[1] - 1] -= 1

            # Discount stuff we can see in hands
            for player_hand in hands:
                for player_card in player_hand:
                    if k[player_card[0]][player_card[1] - 1] > 0:
                        k[player_card[0]][player_card[1] - 1] -= 1
            
            # Discount stuff we can see on the board
            for played_card in unplayable_cards:
                if k[played_card.color][played_card.rank - 1] > 0:
                    k[played_card.color][played_card.rank - 1] -= 1
            
            # Save adjusted
            my_informed_knowledge[i] = k


        probably_playable = []
        potential_discards = []
        for i,k in enumerate(my_informed_knowledge):
            if util.is_playable(k, board):
                self.explanation.append("dead set on this card")
                return Action(PLAY, card_index=i) # Step 1
            if util.is_useless(k, board):    
                potential_discards.append(i)

            for wanted_card in playable_cards:
                # If this current card is likely a card we want, add it to probably_playable
                if util.probability_is_card(k, wanted_card) > 0.55: # PARAMETER we can mess with
                    probably_playable.append((util.probability_is_card(k, wanted_card), i, wanted_card))
        
        # If there are any cards in our hand we are reasonably certain are playable, play the best one
        if len(probably_playable) > 0:
            probably_playable.sort(key=lambda x: x[0], reverse=True) # Sort by most probable to least
            most_likely = probably_playable[0]
            return Action(PLAY, card_index=most_likely[1])

        # Step 2
        if potential_discards:
            return Action(DISCARD, card_index=random.choice(potential_discards))

        # Step 3
        playables = []        
        for player,hand in enumerate(hands):
            if player != nr:
                for card_index,card in enumerate(hand):
                    if card.is_playable(board):                              
                        playables.append((player,card_index))
        
        playables.sort(key=lambda which: -hands[which[0]][which[1]].rank)
        while playables and hints > 0:
            player,card_index = playables[0]
            knows_rank = True
            real_color = hands[player][card_index].color
            real_rank = hands[player][card_index].rank
            k = knowledge[player][card_index]
            
            hinttype = [HINT_COLOR, HINT_RANK]
            
            for h in self.hints[(player,card_index)]:
                hinttype.remove(h)
            
            t = None
            if hinttype:
                if len(hinttype) == 2:
                    color_count = [0,0,0,0,0]
                    max_color_count = 0
                    max_color = 0

                    same_rank = 0

                    for i,card in enumerate(hands[player]):
                        color_count[card.color] = color_count[card.color] + 1
                        if card.rank == real_rank:
                            same_rank = same_rank + 1
                        if color_count[card.color] > max_color_count:
                            max_color_count = color_count[card.color]
                            max_color = card.color

                    if max_color == real_color:
                        if same_rank > 1:
                            t = hinttype[HINT_COLOR]
                        else:
                            t = hinttype[HINT_RANK]
                    else: 
                        t = hinttype[HINT_COLOR]
                else:
                    t = random.choice(hinttype)
            
            if t == HINT_RANK:
                for i,card in enumerate(hands[player]):
                    if card.rank == hands[player][card_index].rank:
                        self.hints[(player,i)].add(HINT_RANK)
                return Action(HINT_RANK, player=player, rank=hands[player][card_index].rank)
            if t == HINT_COLOR:
                for i,card in enumerate(hands[player]):
                    if card.color == hands[player][card_index].color:
                        self.hints[(player,i)].add(HINT_COLOR)
                return Action(HINT_COLOR, player=player, color=hands[player][card_index].color)
            
            playables = playables[1:]

        # Step 4
        if hints > 0:
            hints = util.filter_actions(HINT_COLOR, valid_actions) + util.filter_actions(HINT_RANK, valid_actions)

            hintgiven = random.choice(hints)

            rank_count = [0,0,0,0,0]
            max_rank_count = 0
            max_rank = 0
            min_rank = 0
            min_rank_count = 5
            
            for i,card in enumerate(hands[hintgiven.player]):
                rank_count[card.rank - 1] = rank_count[card.rank - 1] + 1
                if rank_count[card.rank - 1] > max_rank_count:
                    max_rank_count = rank_count[card.rank - 1]
                    max_rank = card.rank
                if rank_count[card.rank - 1] < min_rank_count:
                    min_rank_count = rank_count[card.rank - 1]
                    min_rank = card.rank


            for hint in hints:
                if hint.rank is not None:
                    if hint.rank == max_rank:
                        hintgiven = hint
                    

            if hintgiven.type == HINT_COLOR:
                for i,card in enumerate(hands[hintgiven.player]):
                    if card.color == hintgiven.color:
                        self.hints[(hintgiven.player,i)].add(HINT_COLOR)
            else:
                for i,card in enumerate(hands[hintgiven.player]):
                    if card.rank == hintgiven.rank:
                        self.hints[(hintgiven.player,i)].add(HINT_RANK)
                
            return hintgiven

        # Step 5
          
        probably_discardable = []
        # This part isn't actually helping, might have to investigate more later
        # for i,k in enumerate(my_informed_knowledge):
        #     for unwanted_card in unplayable_cards:
        #         # if util.probability_is_card(k, unwanted_card) > 0.01: # PARAMETER we can mess with
        #         #     print(f'DISCARD: card {i} is {unwanted_card} with {util.probability_is_card(k, unwanted_card)} probability.')
        #         if util.probability_is_card(k, unwanted_card) > 0.95: # PARAMETER we can mess with
        #             # print(f'DISCARD: card {i} is {unwanted_card} with {util.probability_is_card(k, unwanted_card)} probability.')
        #             probably_discardable.append((util.probability_is_card(k, unwanted_card), i))
        
        # if len(probably_discardable) > 0:
        #     probably_discardable.sort(key=lambda x: x[0], reverse=True) # Sort by most probable to least
        #     return Action(DISCARD, card_index=probably_discardable[0][1])
            

        return random.choice(util.filter_actions(DISCARD, valid_actions))

    def inform(self, action, player):
        if action.type in [PLAY, DISCARD]:
            if (player,action.card_index) in self.hints:
                self.hints[(player,action.card_index)] = set()
            for i in range(5):
                if (player,action.card_index+i+1) in self.hints:
                    self.hints[(player,action.card_index+i)] = self.hints[(player,action.card_index+i+1)]
                    self.hints[(player,action.card_index+i+1)] = set()

agent.register("our", "Our", OurPlayer)
from hanabi import *
import util
import agent
import random

class InnerStatePlayer(agent.Agent):
    def __init__(self, name, pnr):
        self.name = name
        self.explanation = []
    def get_action(self, nr, hands, knowledge, trash, played, board, valid_actions, hints, hits, cards_left):
        my_knowledge = knowledge[nr]
        
        potential_discards = []
        for i,k in enumerate(my_knowledge):
            if util.is_playable(k, board):
                return Action(PLAY, card_index=i)
            if util.is_useless(k, board):    
                potential_discards.append(i)
                
        if potential_discards:
            return Action(DISCARD, card_index=random.choice(potential_discards))

        if hints > 0:
            for player,hand in enumerate(hands):
                if player != nr:
                    for card_index,card in enumerate(hand):
                        if card.is_playable(board):                              
                            if random.random() < 0.5:
                                return Action(HINT_COLOR, player=player, color=card.color)
                            return Action(HINT_RANK, player=player, rank=card.rank)

            hints = util.filter_actions(HINT_COLOR, valid_actions) + util.filter_actions(HINT_RANK, valid_actions)
            return random.choice(hints)

        return random.choice(util.filter_actions(DISCARD, valid_actions))
        
def format_hint(h):
    if h == HINT_COLOR:
        return "color"
    return "rank"
        
class OuterStatePlayer(agent.Agent):
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

        my_knowledge = knowledge[nr]
        
        potential_discards = []

        for i,k in enumerate(my_knowledge):
            # maybe proritize what should be played
            if util.is_playable(k, board):
                # Step 1
                return Action(PLAY, card_index=i)
            if util.is_useless(k, board):    
                #Step 2
                potential_discards.append(i)
                
        if potential_discards:
            return Action(DISCARD, card_index=random.choice(potential_discards))
         
        playables = []        
        for player,hand in enumerate(hands):
            if player != nr:
                for card_index,card in enumerate(hand):
                    if card.is_playable(board):                              
                        playables.append((player,card_index))
        
        playables.sort(key=lambda which: -hands[which[0]][which[1]].rank)
        
        # if we have hints to give and there are actually playable cards I guess this prevents us from 
        # from just giving random hints this could mean it makes more sense to discard than to give a hint
        # that will lead to more confusion 
        while playables and hints > 0:
            player,card_index = playables[0]
            knows_rank = True
            real_color = hands[player][card_index].color
            real_rank = hands[player][card_index].rank

            # what is k
            k = knowledge[player][card_index]
            
            hinttype = [HINT_COLOR, HINT_RANK]
            
            # we iterate through our playable cards what makes it playable though?
            # than we check to see if it already has a hint if it does we remove whatever
            # hint type it was
            for h in self.hints[(player,card_index)]:
                hinttype.remove(h)
            
            t = None
            # hinttype will be false if both hints for a card have been given 
            # already if none has been given then it probably makes sense to give a hint based off what you want
            # the player to do but remeber we have to look at it from both angle so the player has to interpret the 
            # hint the way you intended it too it could get sloppy here because it wont always be the same but 
            # rather than let it get sloppy we could defer to discarding

            # you also want to give hints based of what is discardable so if there is a blue two but blue already has a blue
            # two than you should hint the two if it is isolated and doesnt make sense for it to be played anywhere else
            # dont give hints that will confuse the AI so if there is a blue and its on 2 dont hints any numbers that proceed it so 3
            # also if the hint isnt to infer someone to play something than make sure you are revealing information about the most cards

            # TODO create a function to look for isolated cards that are playable if only 1 more hint was given
            # if there is no one hint that will make a card playable than just give a hint that reveals the most information as long as it 
            # does not confuse the player like if its the next number that can be played somewhere if it will confuse tehe player defer to this random logic

            # TODO KEVIN If there are two of the same cards in a persons hands and they can see it based off the hint they should discard one of them

            # TODO KEVIN IF there is a card already on the board discard it

            # TODO 1st is there anything that we want the player to infer? If not give hint that will let the player know boths things about
            # any one card or the most cards. Than if we cant do that give hint that will let the player know a attribute about the most cards
            # if not that then just random

            # if there rank is already on the board and you hint it it wont play it it will discard it so by default it assumes 
            # if you give a hint about a rank that is already on the board you want to discard it TODO work with kevin to invert this 
            # behavior or since the odds that it isnt of the same color is in our favor maybe only for 1 and not for any other rank and only
            # the odss in our favor would have to match up with how many ones have been played already so work with KEVIN to select this an

            # also give hints based off what has been discarded 
            if hinttype:
                t = random.choice(hinttype)
            
            if t == HINT_RANK:
                for i,card in enumerate(hands[player]):
                    # or we could do random and then based off of what is know hint a specific rank
                    # like if it is 1 hint that cards rank 
                    # iterate through our hand and if there is a playable card than hint it
                    if card.rank == hands[player][card_index].rank:
                        self.hints[(player,i)].add(HINT_RANK)
                return Action(HINT_RANK, player=player, rank=hands[player][card_index].rank)
            if t == HINT_COLOR:
                for i,card in enumerate(hands[player]):
                    if card.color == hands[player][card_index].color:
                        self.hints[(player,i)].add(HINT_COLOR)
                return Action(HINT_COLOR, player=player, color=hands[player][card_index].color)
            
            playables = playables[1:]
 
        if hints > 0:
            hints = util.filter_actions(HINT_COLOR, valid_actions) + util.filter_actions(HINT_RANK, valid_actions)
 
            hintgiven = random.choice(hints)

            color_count = [0,0,0,0,0]
            max_color_count = 0
            max_color = 0
            for i,card in enumerate(hands[hintgiven.player]):
                color_count[card.color] = color_count[card.color] + 1
                if color_count[card.color] > max_color_count:
                    max_color_count = color_count[card.color]
                    max_color = card.color

            for hint in hints:
                if hint.rank is not None:
                    if hint.rank == 1:
                        hintgiven = hint
                elif hint.color is not None:
                    if hint.color == max_color:
                        hintgiven = hint
                    
                print(hint.type, hint.player, hint.color, hint.rank, hint.card_index)

            if hintgiven.type == HINT_COLOR:
                for i,card in enumerate(hands[hintgiven.player]):
                    if card.color == hintgiven.color:
                        self.hints[(hintgiven.player,i)].add(HINT_COLOR)
            else:
                for i,card in enumerate(hands[hintgiven.player]):
                    if card.rank == hintgiven.rank:
                        self.hints[(hintgiven.player,i)].add(HINT_RANK)
                
            return hintgiven

        return random.choice(util.filter_actions(DISCARD, valid_actions))


    # After performing a play or a discard action update the hints data structure so that it 
    # no longer has the hint of the card that was discarded or played
    def inform(self, action, player):
        if action.type in [PLAY, DISCARD]:
            if (player,action.card_index) in self.hints:
                self.hints[(player,action.card_index)] = set()
            for i in range(5):
                if (player,action.card_index+i+1) in self.hints:
                    self.hints[(player,action.card_index+i)] = self.hints[(player,action.card_index+i+1)]
                    self.hints[(player,action.card_index+i+1)] = set()

agent.register("inner", "Inner State Player", InnerStatePlayer)
agent.register("outer", "Outer State Player", OuterStatePlayer)
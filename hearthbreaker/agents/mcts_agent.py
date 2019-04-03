from hearthbreaker.agents.basic_agents import DoNothingAgent
from itertools import combinations 
import functools
import operator
import random
import math

def play_move(game, move):
    game._start_turn()
    cards, attacks = move

    if len(cards)>0:
        for card in cards:
            game.play_card(card)
    if len(attacks)>0: 
        for (minion, target) in attacks:
            game.attack_target(minion, target)

    # end round 
    game._end_turn()


def get_minions_to_use(game):
    minions_to_use = []
    print(game.current_player.minions)
    for minion in game.current_player.minions:
        if minion.can_attack():
            minions_to_use.append(minion)
    return minions_to_use

def get_inner_tree(game):
    attack_sequences = []
    minions_use = get_minions_to_use(game)
    print("MINIONS TO USE")
    print(minions_use)
    for minion in minions_use:
        targets = minion.get_targets()
        
        for target in targets:
            attack = (minion, target)
            attack_sequences.append([attack]) 
            game_copy = game.copy()
            game_copy.attack_target(minion,target)
            a = get_inner_tree(game_copy)
            new_a = list(map(lambda x: [attack]+x,a))
            attack_sequences += new_a
    
    return attack_sequences

class GameState:
    """ A state of the game, i.e. the game board. These are the only functions which are
        absolutely necessary to implement UCT in any 2-player complete information deterministic 
        zero-sum game, although they can be enhanced and made quicker, for example by using a 
        GetRandomMove() function to generate a random move during rollout.
        By convention the players are numbered 1 and 2.
    """
    def __init__(self, game):
        self.game = game
        # changed from game.current_player to game.other_player
        self.playerJustMoved = game.other_player # At the root pretend the player just moved is player 2 - player 1 has the first move
        # self.playerJustMoved = game.current_player

    def Clone(self):
        return GameState(self.game.copy())

    def DoMove(self, move):
        """ Update a state by carrying out the given move.
            Must update playerJustMoved.
        """
        play_move(self.game, move)
        self.playerJustMoved = self.game.current_player

        
    def GetMoves(self):
        """ Get all possible moves from this state.
        """
        player = self.game.current_player
        opponent = self.game.other_player
        if player.hero.dead or opponent.hero.dead:
            return []

        cards = player.hand
        # get all combinations of cards play (order doesn't matter): 
        a = list(filter(lambda x: x.mana < player.mana, cards))
        # print("CARDS TO PLAY")
        # print(a)
        cards_combinations = []
        for r in range(0, len(a) + 1):
	        cards_combinations += list(combinations(a, r))
        # print("CARDS COMB BEF")
        # print(cards_combinations)
        # print("MANA", player.mana)
        cards_combinations = list(filter(lambda xs: sum([x.mana_cost() for x in xs]) <= player.mana, cards_combinations))
        # print("CARDS COMB AF")
        # print(cards_combinations)
        # print(list(filter(lambda xs: sum([x.mana_cost() for x in xs]) > player.mana, cards_combinations)) + [[]])
        
        print("-------------------")
        # get all combinations of attacks (order matters):
        attack_sequences = get_inner_tree(self.game) + [[]]
        

        seq = map(lambda cc: list(map(lambda aseq: (cc,aseq), attack_sequences)), cards_combinations)
        # [[(), ()],[(), ()]] => [(), (), (), ()]
        all_possible_moves = functools.reduce(operator.add, seq, [])
        print("ATT COMB")
        print(all_possible_moves)
        return all_possible_moves

    def GetResult(self, playerjm):
        """ Get the game result from the viewpoint of playerjm. 
        """
        return 0 if playerjm.hero.dead else 1

    def __repr__(self):
        pass

class MCTSAgent(DoNothingAgent):
    def __init__(self, depth=100):
        super().__init__()
        self.depth = depth

    def do_turn(self, player):
        print('---\nTurn of', player)
        state = GameState(player.game)
        move = UCT(rootstate = state, itermax = self.depth, verbose = False)
        print(move)
        play_move(player.game,move)

class Node:
    """ A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
    Crashes if state not specified.
    """
    def __init__(self, move = None, parent = None, state = None):
        self.move = move # the move that got us to this node - "None" for the root node
        self.parentNode = parent # "None" for the root node
        self.childNodes = []
        self.wins = 0
        self.visits = 0
        self.untriedMoves = state.GetMoves() # future child nodes
        self.playerJustMoved = state.playerJustMoved # the only part of the state that the Node needs later
        
    def UCTSelectChild(self):
        """ Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
            lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
            exploration versus exploitation.
        """
        s = sorted(self.childNodes, key = lambda c: c.wins/c.visits + math.sqrt(2*math.log(self.visits)/c.visits))[-1]
        return s
    
    def AddChild(self, m, s):
        """ Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
        n = Node(move = m, parent = self, state = s)
        self.untriedMoves.remove(m)
        self.childNodes.append(n)
        return n
    
    def Update(self, result):
        """ Update this node - one additional visit and result additional wins. result must be from the viewpoint of playerJustmoved.
        """
        self.visits += 1
        self.wins += result

    def __repr__(self):
        return "[M:" + str(self.move) + " W/V:" + str(self.wins) + "/" + str(self.visits) + " U:" + str(self.untriedMoves) + "]"

    def TreeToString(self, indent):
        s = self.IndentString(indent) + str(self)
        for c in self.childNodes:
             s += c.TreeToString(indent+1)
        return s

    def IndentString(self,indent):
        s = "\n"
        for i in range (1,indent+1):
            s += "| "
        return s

    def ChildrenToString(self):
        s = ""
        for c in self.childNodes:
             s += str(c) + "\n"
        return s

def UCT(rootstate, itermax, verbose=False):
    rootnode = Node(state=rootstate)

    for i in range(itermax):
        node = rootnode
        state = rootstate.Clone()

        # Select
        while node.untriedMoves == [] and node.childNodes != []:  # node is fully expanded and non-terminal
            # print('SELECT')
            node = node.UCTSelectChild()
            state.DoMove(node.move)

        # Expand
        if node.untriedMoves != []:  # if we can expand (i.e. state/node is non-terminal)
            # print('EXPAND')

            m = random.choice(node.untriedMoves)
            state.DoMove(m)
            node = node.AddChild(m, state)  # add child and descend tree

        # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
        while state.GetMoves() != []:  # while state is non-terminal
            # print('PLAYOUT')
            state.DoMove(random.choice(state.GetMoves()))

        # Backpropagate
        while node != None:  # backpropagate from the expanded node and work back to the root node
            # print('BACKPROPAGATE')
            node.Update(state.GetResult(
                node.playerJustMoved))  # state is terminal. Update node with result from POV of node.playerJustMoved
            node = node.parentNode

    # Output some information about the tree - can be omitted
    if (verbose): print(rootnode.TreeToString(0))
    else: print(rootnode.ChildrenToString())

    return sorted(rootnode.childNodes, key=lambda c: c.visits)[-1].move  # return the move that was most visited
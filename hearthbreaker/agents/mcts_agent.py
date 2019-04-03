from hearthbreaker.agents.basic_agents import Agent, DoNothingAgent
from itertools import combinations 
import functools
import operator
import random
import math
from hearthbreaker.agents.basic_agents import RandomAgent, DoNothingAgent

def play_move(game, chosen_move):
    cards, attacks = chosen_move

    if len(cards) > 0:
        for card in cards:
            game.play_card(card)
    if len(attacks) > 0:
        for (minion, target) in attacks:
            game.attack_target(minion, target)

    game._end_turn()


def get_minions_to_use(game):
    minions_to_use = []
    for minion in game.current_player.minions:
        if minion.can_attack():
            minions_to_use.append(minion)
    return minions_to_use

def get_inner_tree(game):
    attack_sequences = []
    minions_use = get_minions_to_use(game)
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
        absolutely necessary to implement uct in any 2-player complete information deterministic
        zero-sum game, although they can be enhanced and made quicker, for example by using a 
        GetRandomMove() function to generate a random move during rollout.
        By convention the players are numbered 1 and 2.
    """
    def __init__(self, game):
        self.game = game
        self.playerJustMoved = game.current_player # At the root pretend the player just moved is player 2 - player 1 has the first move
        
    def clone(self):
        return GameState(self.game.copy())

    def do_move(self, move):
        """ update a state by carrying out the given move.
            Must update playerJustMoved.
        """
        play_move(self.game, move)
        self.playerJustMoved = self.game.current_player

        
    def get_moves(self):
        """ Get all possible moves from this state.
        """
        player = self.game.current_player
        opponent = self.game.other_player
        if player.hero.dead or opponent.hero.dead:
            return []
        cards = player.hand

        # get all combinations of cards play (order doesn't matter): 
        a = list(filter(lambda x: cards.mana_cost() <= mana, cards))
        cards_combinations = []
        for r in range(len(possible_cards_to_play)+1):
	        cards_combinations.extend(list(combinations(possible_cards_to_play, r)))

        # print("CARDS COMB BEF")
        # print(cards_combinations)
        # print("MANA", player.mana)
        cards_combinations = list(
            filter(lambda xs: sum([x.mana_cost() for x in xs]) <= player.mana, cards_combinations))  # + [[]]
        # print("CARDS COMB AF")
        # print(cards_combinations)
        # print(list(filter(lambda xs: sum([x.mana_cost() for x in xs]) > player.mana, cards_combinations)) + [[]])
        print("-------------------")

        # get all combinations of attacks (order matters):
        attack_sequences = get_inner_tree(self.game) + [[]]

        seq = map(lambda cc: list(map(lambda aseq: (cc,aseq), attack_sequences)), cards_combinations)
        # [[(), ()],[(), ()]] => [(), (), (), ()]
        all_possible_moves = functools.reduce(operator.add, seq, [])

        ##### printing informations
        # print("---\n", player, "'s mana:", player.mana)
        # print("Possible cards to play:", possible_cards_to_play)
        # print("Cards combinations:", cards_combinations)
        #print("Attack sequences:", attack_sequences)
        print("All possible moves:",all_possible_moves)

        return all_possible_moves

    def get_result(self, playerjm):
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
        self.untriedMoves = state.get_moves() # future child nodes
        self.playerJustMoved = state.playerJustMoved # the only part of the state that the Node needs later
        
    def uct_select_child(self):
        """ Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
            lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
            exploration versus exploitation.
        """
        s = sorted(self.childNodes, key = lambda c: c.wins/c.visits + math.sqrt(2*math.log(self.visits)/c.visits))[-1]
        return s
    
    def add_child(self, m, s):
        """ Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
        n = Node(move = m, parent = self, state = s)
        self.untriedMoves.remove(m)
        self.childNodes.append(n)
        return n
    
    def update(self, result):
        """ update this node - one additional visit and result additional wins. result must be from the viewpoint of playerJustmoved.
        """
        self.visits += 1
        self.wins += result

    def __repr__(self):
        # return "[M:" + str(self.move) + " W/V:" + str(self.wins) + "/" + str(self.visits) + " U:" + str(self.untriedMoves) + "]"
        return "[M:" + str(self.move) + " W/V:" + str(self.wins) + "/" + str(self.visits) + "]"

    def tree_to_string(self, indent):
        s = self.indent_string(indent) + str(self)
        for c in self.childNodes:
             s += c.tree_to_string(indent + 1)
        return s

    def indent_string(self, indent):
        s = "\n"
        for i in range (1,indent+1):
            s += "| "
        return s

    def children_to_string(self):
        s = ""
        for c in self.childNodes:
             s += str(c) + "\n"
        return s

def uct(rootstate, itermax, verbose=False):
    rootnode = Node(state=rootstate)

    for i in range(itermax):
        node = rootnode
        state = rootstate.clone()

        print("Turn:", state.game._turns_passed, ", iteration:", i)
        # Select
        while node.untriedMoves == [] and node.childNodes != []:  # node is fully expanded and non-terminal
            node = node.uct_select_child()
            print("==========\nSelect - chosen move:", node.move)
            state.do_move(node.move)
            print("Select - finished selecting for move:", node.move, "\n==========")

        # Expand
        if node.untriedMoves != []:  # if we can expand (i.e. state/node is non-terminal)
            m = random.choice(node.untriedMoves)
            print("==========\nExpand - chosen move:", m)
            state.do_move(m)
            node = node.add_child(m, state)  # add child and descend tree
            print("Expand - finished expanding for move:", m, "\n==========")

        # My rollout
        curr_player_won = 0
        if not state.game.current_player.hero.dead and not state.game.other_player.hero.dead:
            game_copy = state.game.copy()
            game_copy.players[0].change_agent(RandomAgent())
            game_copy.players[1].change_agent(RandomAgent())

            while not game_copy.current_player.hero.dead and not game_copy.other_player.hero.dead:
                game_copy._start_turn()
                game_copy.current_player.agent.do_turn(game_copy.current_player)
                game_copy._end_turn()
            if game_copy.current_player.hero.dead:
                print("current player DEAD")
            elif game_copy.other_player.hero.dead:
                print("other player DEAD")
            else:
                print("ERROR: no one won")
            curr_player_won = 0 if game_copy.current_player.hero.dead else 1

        # My Backpropagate
        while node != None:  # backpropagate from the expanded node and work back to the root node
            print("==========\nBackpropagation - updating node:", node)
            node.update(curr_player_won)  # state is terminal. update node with result from POV of node.playerJustMoved
            print("Backpropagation - finished updating node:", node, "\n==========")
            node = node.parentNode

    # Output some information about the tree - can be omitted
    if (verbose): print (rootnode.TreeToString(0))
    else: print (rootnode.ChildrenToString())

    return sorted(rootnode.childNodes, key = lambda c: c.visits)[-1].move # return the move that was most visited
                
def UCTPlayGame():
    """ Play a sample game between two UCT players where each player gets a different number 
        of UCT iterations (= simulations = tree nodes).
    """
    # state = OthelloState(4) # uncomment to play Othello on a square board of the given size
    # state = OXOState() # uncomment to play OXO
    state = NimState(15) # uncomment to play Nim with the given number of starting chips
    
    while (state.GetMoves() != []):
        print (str(state))
        if state.playerJustMoved == 1:
            m = UCT(rootstate = state, itermax = 1000, verbose = False) # play with values for itermax and verbose = True
        else:
            m = UCT(rootstate = state, itermax = 100, verbose = False)
        print ("Best Move: " + str(m) + "\n")
        state.DoMove(m)
    if state.GetResult(state.playerJustMoved) == 1.0:
        print ("Player " + str(state.playerJustMoved) + " wins!")
    elif state.GetResult(state.playerJustMoved) == 0.0:
        print ("Player " + str(3 - state.playerJustMoved) + " wins!")
    else: print ("Nobody wins!")

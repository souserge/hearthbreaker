from hearthbreaker.agents.basic_agents import Agent
from itertools import combinations 

def get_minions_to_use(game):
    minions_to_use = []
    for minion in game.curr_player.minions:
        if minion.can_attack():
            minions_to_use.append(minion)
    return minions_to_use

def get_inner_tree(node):
    attack_sequences = node
    game_sim = node.game
    minions_use = get_minions_to_use(game_sim)
    for minion in minions_use:
        targets = minion.get_targets()
        # for all minions we can use:
            # for all targets we can attack:
                attack_sequences.addChild((minion, target)) 
                # copy game
                # attack in copy
                # goto $THERE   

class GameState:
    """ A state of the game, i.e. the game board. These are the only functions which are
        absolutely necessary to implement UCT in any 2-player complete information deterministic 
        zero-sum game, although they can be enhanced and made quicker, for example by using a 
        GetRandomMove() function to generate a random move during rollout.
        By convention the players are numbered 1 and 2.
    """
    def __init__(self, game):
            self.game = game
            self.playerJustMoved = game.current_player # At the root pretend the player just moved is player 2 - player 1 has the first move
        
    def Clone(self):
        return GameState(self.game.copy())

    def DoMove(self, move):
        """ Update a state by carrying out the given move.
            Must update playerJustMoved.
        """
        # game.do_move(move)
        for step in move:
            # apply step
            pass

        # end round 

        self.playerJustMoved = game.other_player
        
    def GetMoves(self):
        """ Get all possible moves from this state.
        """
        player = self.game.current_player
        # get all combinations of cards play (order doesn't matter): 
        a = list(filter(lambda x: cards.mana_cost() < mana, cards))
        cards_combinations = []
        for r in range(0, len(a) + 1):
	        cards_combinations + list(combinations(a, r))

        cards_combinations = list(filter(lambda xs: sum([x.mana_cost() for x in xs]) > player.mana, cards_combinations))
        
        attack_sequences = Node()

        # $THERE
        game_sim = self.game
        # for all minions we can use:
            # for all targets we can attack:
                attack_sequences.addChild((minion, target)) 
                # copy game
                # attack in copy
                # goto $THERE   

        
    
    def GetResult(self, playerjm):
        """ Get the game result from the viewpoint of playerjm. 
        """

    def __repr__(self):
        pass

class MCTSAgent(Agent):

    def get_minions_to_use(game, curr_player):
        minions_to_use = []
        for minion in curr_player.minions:
            if minion.can_attack():
                minions_to_use.append(minion)
        return minions_to_use

    def generate_possible_moves(game):
        player = game.current_player
        possible_cards_to_use = [ card for card in player.hand if (card.can_use(player, player.game))]
        get_minions_to_attack(game,player)

    def choose_target(self, targets):
        return targets[0]

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
        s = sorted(self.childNodes, key = lambda c: c.wins/c.visits + sqrt(2*log(self.visits)/c.visits))[-1]
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
    
                
    # zakładamy że granie kart i atakowanie minionami jest niezależne, obojetna kolejność

def UCT(rootstate, itermax, verbose = False):

    rootnode = Node(state = rootstate)

    for i in range(itermax):
        node = rootnode
        state = rootstate.Clone()

        # Select
        while node.untriedMoves == [] and node.childNodes != []: # node is fully expanded and non-terminal
            node = node.UCTSelectChild()
            state.DoMove(node.move)

        # Expand
        if node.untriedMoves != []: # if we can expand (i.e. state/node is non-terminal)
            m = random.choice(node.untriedMoves) 
            state.DoMove(m)
            node = node.AddChild(m,state) # add child and descend tree

        # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
        while state.GetMoves() != []: # while state is non-terminal
            state.DoMove(random.choice(state.GetMoves()))

        # Backpropagate
        while node != None: # backpropagate from the expanded node and work back to the root node
            node.Update(state.GetResult(node.playerJustMoved)) # state is terminal. Update node with result from POV of node.playerJustMoved
            node = node.parentNode

    # Output some information about the tree - can be omitted
    if (verbose): print rootnode.TreeToString(0)
    else: print rootnode.ChildrenToString()

    return sorted(rootnode.childNodes, key = lambda c: c.visits)[-1].move # return the move that was most visited
                
def UCTPlayGame():
    """ Play a sample game between two UCT players where each player gets a different number 
        of UCT iterations (= simulations = tree nodes).
    """
    # state = OthelloState(4) # uncomment to play Othello on a square board of the given size
    # state = OXOState() # uncomment to play OXO
    state = NimState(15) # uncomment to play Nim with the given number of starting chips
    while (state.GetMoves() != []):
        print str(state)
        if state.playerJustMoved == 1:
            m = UCT(rootstate = state, itermax = 1000, verbose = False) # play with values for itermax and verbose = True
        else:
            m = UCT(rootstate = state, itermax = 100, verbose = False)
        print "Best Move: " + str(m) + "\n"
        state.DoMove(m)
    if state.GetResult(state.playerJustMoved) == 1.0:
        print "Player " + str(state.playerJustMoved) + " wins!"
    elif state.GetResult(state.playerJustMoved) == 0.0:
        print "Player " + str(3 - state.playerJustMoved) + " wins!"
    else: print "Nobody wins!"

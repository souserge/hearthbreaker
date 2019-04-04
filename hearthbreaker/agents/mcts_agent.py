from hearthbreaker.agents.basic_agents import Agent, DoNothingAgent
from itertools import combinations
import functools
import operator
import random
import math
from hearthbreaker.agents.basic_agents import RandomAgent, DoNothingAgent


def find_minion(m, ms):
    filtered_minions = list(filter(lambda x: x.key == m.key, ms))
    if len(filtered_minions) < 1:
        raise Exception('No minion: {}\n found in: {}\n key: {}, keys: {}\n\n'.format(
            m, ms, m.key, list(map(lambda x: x.key, ms))))
    return filtered_minions[0]


def find_target(t, ts, hero):
    if t.is_hero():
        return hero
    else:
        return find_minion(t, ts)


def attack_target(minion, target, game):
    m = find_minion(minion, game.current_player.minions)
    t = find_target(target, game.other_player.minions, game.other_player.hero)
    m.attack(t)


def play_move(game, chosen_move):
    cards, attacks = chosen_move
    for card in cards:
        game.play_card(card)

    for (minion, target) in attacks:
        attack_target(minion, target, game)


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
            attack_target(minion, target, game_copy)
            a = get_inner_tree(game_copy)
            new_a = list(map(lambda x: [attack] + x, a))
            attack_sequences += new_a

    return attack_sequences


class GameState:
    """ A state of the game, i.e. the game board. These are the only functions which are
        absolutely necessary to implement uct in any 2-player complete information deterministic
        zero-sum game, although they can be enhanced and made quicker, for example by using a 
        GetRandomMove() function to generate a random move during rollout.
        By convention the players are numbered 1 and 2.
    """

    def __init__(self, game, playerjm=None):
        self.game = game
        self.playerJustMoved = playerjm  # At the root pretend the player just moved is player 2 - player 1 has the first move

    def clone(self):
        return GameState(self.game.copy(), self.playerJustMoved)

    def do_move(self, move):
        """ update a state by carrying out the given move.
            Must update playerJustMoved.
        """
        play_move(self.game, move)
        self.playerJustMoved = self.game.current_player
        self.game._start_turn()

    def get_moves(self):
        """ Get all possible moves from this state.
        """
        player = self.game.current_player
        opponent = self.game.other_player

        if player.hero.dead or opponent.hero.dead:
            return []

        cards = player.hand
        possible_cards_to_play = list(filter(lambda x: x.mana <= player.mana, cards))
        # get all combinations of cards play (order doesn't matter):
        cards_combinations = []
        for r in range(len(possible_cards_to_play) + 1):
            combs = list(map(lambda x: list(x), combinations(possible_cards_to_play, r)))
            cards_combinations.extend(combs)

        cards_combinations = list(
            filter(lambda xs: sum([x.mana_cost() for x in xs]) <= player.mana, cards_combinations))  # + [[]]

        # get all combinations of attacks (order matters):
        attack_sequences = get_inner_tree(self.game) + [[]]

        seq = map(lambda cc: list(map(lambda aseq: (cc, aseq), attack_sequences)), cards_combinations)
        # [[(), ()],[(), ()]] => [(), (), (), ()]
        all_possible_moves = functools.reduce(operator.add, seq, [])

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
        self.independent = True

    def do_turn(self, player):
        state = GameState(player.game.copy())
        move = UCT(rootstate=state, itermax=self.depth, verbose=False)
        play_move(player.game, move)


class Node:
    """ A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
        Crashes if state not specified.
    """

    def __init__(self, move=None, parent=None, state=None):
        self.move = move  # the move that got us to this node - "None" for the root node
        self.parentNode = parent  # "None" for the root node
        self.childNodes = []
        self.wins = 0
        self.visits = 0
        self.untriedMoves = state.get_moves()  # future child nodes
        self.playerJustMoved = state.playerJustMoved  # the only part of the state that the Node needs later

    def uct_select_child(self):
        """ Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
            lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
            exploration versus exploitation.
        """
        s = sorted(self.childNodes, key=lambda c: c.wins / c.visits +
                   math.sqrt(2 * math.log(self.visits) / c.visits))[-1]
        return s

    def add_child(self, m, s):
        """ Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
        n = Node(move=m, parent=self, state=s)
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
        for i in range(1, indent + 1):
            s += "| "
        return s

    def children_to_string(self):
        s = ""
        for c in self.childNodes:
            s += str(c) + "\n"
        return s


def UCT(rootstate, itermax, verbose=False):
    rootnode = Node(state=rootstate)

    for i in range(itermax):
        node = rootnode
        state = rootstate.clone()

        # Select
        while node.untriedMoves == [] and node.childNodes != []:  # node is fully expanded and non-terminal
            node = node.uct_select_child()
            state.do_move(node.move)

        # Expand
        if node.untriedMoves != []:  # if we can expand (i.e. state/node is non-terminal)
            m = random.choice(node.untriedMoves)
            state.do_move(m)
            node = node.add_child(m, state)  # add child and descend tree

        # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
        while state.get_moves() != []:  # while state is non-terminal
            move = random.choice(state.get_moves())
            state.do_move(move)

        # Backpropagate
        while node != None:  # backpropagate from the expanded node and work back to the root node
            node.update(state.get_result(
                node.playerJustMoved))  # state is terminal. Update node with result from POV of node.playerJustMoved
            node = node.parentNode

    # Output some information about the tree - can be omitted
    if (verbose):
        print(rootnode.tree_to_string(0))
        print(rootnode.children_to_string())

    return sorted(rootnode.childNodes, key=lambda c: c.visits)[-1].move  # return the move that was most visited

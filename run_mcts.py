import json
from hearthbreaker.agents.basic_agents import RandomAgent
from hearthbreaker.agents.test_agent import TalkativeAgent
from hearthbreaker.agents.aggressive_agent import AggressiveAgent
from hearthbreaker.agents.controlling_agent import ControllingAgent
from hearthbreaker.cards.heroes import Jaina, Malfurion, hero_for_class
from hearthbreaker.constants import CHARACTER_CLASS
from hearthbreaker.engine import Game, Deck, card_lookup
from hearthbreaker.cards import *
import timeit
import functools
from hearthbreaker.agents.mcts_agent import GameState, MCTSAgent, Node


def UCTPlayGame():
    """ Play a sample game between two UCT players where each player gets a different number
        of UCT iterations (= simulations = tree nodes).
    """

    cards = load_deck("mage3.hsdeck")
    deck1 = Deck(cards, Jaina())
    deck2 = Deck(cards, Malfurion())
    game = Game([deck1, deck2], [MCTSAgent(), RandomAgent()])
    game.pre_game()
    state = GameState(game) # uncomment to play Nim with the given number of starting chips
    print(state.GetMoves())
    while (state.GetMoves() != []):
        print(str(state))
        if state.playerJustMoved == 1:
            m = UCT(rootstate = state, itermax = 1000, verbose = False) # play with values for itermax and verbose = True
        else:
            m = UCT(rootstate = state, itermax = 100, verbose = False)
        print("Best Move: " + str(m) + "\n")
        state.DoMove(m)
    if state.GetResult(state.playerJustMoved) == 1.0:
        print("Player " + str(state.playerJustMoved) + " wins!")
    elif state.GetResult(state.playerJustMoved) == 0.0:
        print("Player " + str(3 - state.playerJustMoved) + " wins!")
    else: print("Nobody wins!")


if __name__ == "__main__":
    """ Play a single game to the end using UCT for both players. 
    """
    UCTPlayGame()
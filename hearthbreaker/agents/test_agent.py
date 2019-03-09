from hearthbreaker.agents.basic_agents import PredictableAgent


class TalkativeAgent(PredictableAgent):
    def __init__(self):
        print('Initialising...')
        print()
        super().__init__()

    def do_card_check(self, cards):
        print('Checking cards')
        print(cards)
        print()
        return super().do_card_check(cards)

    def do_turn(self, player):
        print('Doing turn')
        print(player)
        print()
        return super().do_turn(player)

    def choose_target(self, targets):
        print('Choosing target')
        print(targets)
        print()
        return super().choose_target(targets)

    def choose_index(self, card, player):
        print('Choosing index')
        print(card)
        print(player)
        print()
        return super().choose_index(card, player)

    def choose_option(self, options, player):
        print('Choosing option')
        print(options)
        print(player)
        print()
        return super().choose_option(options, player)
from hearthbreaker.agents.basic_agents import Agent

class MCTSAgent(Agent):

    def get_minions_to_attack(game,curr_player):
        minions_to_attack = []
        for minion in curr_player.minions:
            if minion.can_attack():
                minions_to_attack.append(minion)
        return minions_to_attack

    def generate_possible_moves(game):
        player = game.current_player
        possible_cards_to_use = [ card for card in player.hand if (card.can_use(player, player.game))]
        get_minions_to_attack(game,player)

    def choose_target(self, targets):
        return targets[0]    
                
    # zakładamy że granie kart i atakowanie minionami jest niezależne, obojetna kolejność

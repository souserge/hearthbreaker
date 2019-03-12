from hearthbreaker.agents.basic_agents import Agent

# Agresive
# atakuje
# sprawdza inne mozliwości
# wybrać wszytskie karty ktorymi można zadac obrazenia w tej rundzie
# użyć tej ktora da najwieksze obrazenie
 
# atakuje albo stronnikiem albo karta 

# 1) najpierw po wszyst. kartach, jakie można użyć, to je użyć
# 2) zaatakować wszystkimi możliwymi stronnikami

class AggressiveAgent(Agent):
    def do_card_check(self, cards):
        return [True, True, True, True]

    def check_opponent_life(self, player):
        print (player.game.other_player.hero.health)

    def attack_with_all_possible_minions(self,player):
        for minion in player.minions:
            if minion.can_attack():
                print('BEFORE ATTACK')
                self.check_opponent_life(player)
                minion.attack()
                self.check_opponent_life(player)
                print('AFTER ATTACK')
    
    def use_all_possible_cards(self, player):
        card_costs = [card.mana for card in player.hand]
        # player używa wszystkie karty jakie może użyć
        done_something = True
        while done_something:
            print("Current mana: {}".format(player.mana))
            print("Card costs: {}".format(card_costs))
            done_something = False
            for card in player.hand:
                if card.can_use(player, player.game):
                    player.game.play_card(card)
                    print("used card",card)
                    done_something = True
                    break

    def do_turn(self, player):
        print("START TURN")
        self.use_all_possible_cards(player)
        self.attack_with_all_possible_minions(player)
        
        
        print("END TURN")
           

    def choose_target(self, targets):
        print("CHOOSING")
        print(targets)
        return targets[-1]

    def choose_index(self, card, player):
        return 0

    def choose_option(self, options, player):
        return self.filter_options(options, player)[0]


            


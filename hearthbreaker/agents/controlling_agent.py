from hearthbreaker.agents.basic_agents import Agent


class ControllingAgent(Agent):
    def do_card_check(self, cards):
        return [True, True, True, True]

    def check_opponent_life(self, player):
        print("Health of opponent's hero: {}".format(player.game.other_player.hero.health))

    def attack_with_hero(self, player):
        if player.hero.can_attack():
            print('BEFORE ATTACK WITH HERO')
            self.check_opponent_life(player)
            player.hero.attack()
            self.check_opponent_life(player)
            print('AFTER ATTACK WITH HERO')
        print('HERO CANNOT ATTACK')

    # player atakuje wszystkimi swoimi stronnikami, zaczyna od ataku na other_player.hero
    def attack_with_all_possible_minions(self, player):
        attack_done = False
        for minion in player.minions:
            if minion.can_attack():
                attack_done = True
                print('BEFORE ATTACK WITH MINIONS')
                self.check_opponent_life(player)
                print(">>> Attacking with minion:\n\tlife:", minion)#.card.__str__() +""+ str(minion.health), "\n\tattack:", str(minion.base_attack))
                minion.attack()
                self.check_opponent_life(player)
                print('AFTER ATTACK WITH MINIONS')
        if not attack_done:
            print('NONE MINION CAN ATTACK')

    def print_info_about_turn(self, player):
        print("--> info -->")
        print("My hero's health:", player.hero.health)
        print("Opponent's health:", player.game.other_player.hero.health)
        print("My current mana:", player.mana)

        print("Cards on hand:\n\t", end='')
        if player.hand:
            cards_details = [str(card.name) + " (" + str(card.mana) + " mana)" for card in player.hand]
            print(*cards_details, sep='\n\t')
        else:
            print('[]')

        print("<-- info <--")

    # player używa wszystkie karty jakie może użyć, czyli dopóki starczy mu many
    def use_all_possible_cards(self, player):
        print(">>>>>>>>>>>>>>>\nPlayer hand: ",player.hand)
        possible_cards_to_use = [ (card, card.mana) for card in player.hand if (card.can_use(player, player.game))]
        #print("Possible cards to use: ", possible_cards_to_use)
        possible_cards_to_use_sorted = self.Sort(possible_cards_to_use)
        print("Possible cards to use (sorted by mana): ", possible_cards_to_use_sorted)

        # for card_tuple in possible_cards_to_use_sorted:
        #     card = card_tuple[0]
        #     if card.can_use(player, player.game):
        #         print(card)
        #         player.game.play_card(card)

        # print(type(card[0]) for card in possible_cards_to_use_sorted)
        # print(type(card) for card in player.hand)

        cards_fin = False
        for card_tuple in possible_cards_to_use_sorted: #player.hand:
            if not cards_fin:
                print(">>> next")
                print(card_tuple)
                card = card_tuple[0]
                if card.can_use(player, player.game):
                    player.game.play_card(card)
                    print("USING CARD FROM HAND:\n\t", card)
            else:
                cards_fin = True
                break

                print("<<< fin")



    def Sort(self, sub_li):

        # reverse = None (Sorts in Ascending order)
        # key is set to sort using second element of
        # sublist lambda has been used
        sub_li.sort(key=lambda x: x[1])
        return sub_li

        # player używa power swojego hero
    def use_hero_power(self, player):
        if player.hero.power.can_use():
            player.hero.power.use()

    def do_turn(self, player):
        print("\nSTART TURN OF", player)
        self.print_info_about_turn(player)

        self.use_all_possible_cards(player)
        self.attack_with_all_possible_minions(player)
        self.attack_with_hero(player)
        self.use_hero_power(player)
        print("END TURN OF",player,"\n")

    def choose_target(self, targets):
        print("CHOOSING TARGET FROM LIST:\n\t", end='')
        print(*targets, sep='\n\t')

        chose_target = targets[0]

        print("CHOSE TARGET:\n\t", chose_target)
        return chose_target

    def choose_index(self, card, player):
        return 0

    def choose_option(self, options, player):
        return self.filter_options(options, player)[0]





from chessboard import display
import chess
from chess.engine import Score
import random

from blackjack21 import Table, Dealer

class ChessGame:
    def __init__(self, starting_fen=None) -> None:
        self.engine = chess.engine.SimpleEngine.popen_uci(
            r"/opt/homebrew/bin/stockfish"
        )

        if starting_fen:
            self.board = chess.Board(starting_fen)
        else:
            self.board = chess.Board()

    def get_board(self) -> chess.Board:
        return self.board

    def get_score(self) -> int:
        analyze_board = chess.Board(self.board.fen())
        info = self.engine.analyse(analyze_board, chess.engine.Limit(time=0.2))

        return info["score"].pov(not analyze_board.turn).score(mate_score=5000)
    
    def get_best_move(self) -> str:
        analyze_board = chess.Board(self.board.fen())
        result = self.engine.play(analyze_board, chess.engine.Limit(time=0.2))

        return self.board.san(result.move)

    def is_valid(self, move_str, san=False) -> bool:
        if san:
            try:
                move = self.board.parse_san(move_str)
            except:
                return False
        else:
            move = chess.Move.from_uci(move_str)

        return move in self.board.legal_moves

    def play_move(self, move_str, show=False, san=False) -> None:
        if san:
            move = self.board.parse_san(move_str)
        else:
            move = chess.Move.from_uci(move_str)

        self.board.push(move)

        if show:
            display.start(self.board.fen())

            while True:
                for event in display.pygame.event.get():
                    if (
                        event.type == display.pygame.KEYDOWN
                        and event.key == display.pygame.K_RIGHT
                    ):
                        display.pygame.quit()
                        return

# https://github.com/alessiomeloni/blackjack-strategy-calculator/blob/main/blackjack_strategy.py
class BlackjackStrategy:
    def __init__(self):
        self.HI_LO_COUNT = 0

    def count_cards(self, hand):
        """Updates the HI_LO_COUNT based on the given hand."""
        for card in hand:
            if card in ["T", "J", "Q", "K", "A"]:
                self.HI_LO_COUNT -= 1
            elif card in ["2", "3", "4", "5", "6"]:
                self.HI_LO_COUNT += 1

    def calculate_bet(self, current_bet):
        """Calculates the optimal bet for the next hand based on the HI_LO_COUNT."""
        if self.HI_LO_COUNT > 5:
            return current_bet * 2
        elif self.HI_LO_COUNT < -5:
            return current_bet / 2
        return current_bet

    # def should_split(self, dealer_hand, player_hand):
    #     """Determines if the player should split their hand based on the cards in the dealer's hand and the player's hand."""
    #     if (len(player_hand) != 2) or (player_hand[0] != player_hand[1]):
    #         return False
    #     if player_hand[0] in ["A"]:
    #         return True
    #     elif player_hand[0] in ["8"]:
    #         return True
    #     elif player_hand[0] in ["9"]:
    #         if dealer_hand[0] in ["7", "T", "J", "Q", "K", "A"]:
    #             return False
    #         else:
    #             return True
    #     elif player_hand[0] in ["2", "3", "4", "5", "6"]:
    #         return True
    #     return False

    def calculate_points(self, hand):
        """Calculates the total points in the given hand."""
        points = 0
        num_aces = 0
        for card in hand:
            if card in ["T", "J", "Q", "K"]:
                points += 10
            elif card == "A":
                points += 11
                num_aces += 1
            else:
                points += int(card)
        while (points > 21) and (num_aces > 0):
            points -= 10
            num_aces -= 1
        return points
    
    def get_optimal_move(self, current_bet, dealer_hand, player_hand, no_split=False):
        """
        Returns the optimal mathematical perfect move and bet for the current hand, based on the Hi-Lo system, Betting Deviations, and Playing Deviations strategies.

        Parameters:
            current_bet (int): The current bet of the player.
            dealer_hand (list): A list of strings representing the cards in the 
                dealer's hand. Each string is a single character representing the rank of the card, with T representing 10, J representing Jack, Q representing Queen, K representing King, and A representing Ace.
            player_hand (list): A list of strings representing the cards in the 
                player's hand. Each string is a single character representing the rank of the card, with T representing 10, J representing Jack, Q representing Queen, K representing King, and A representing Ace.

        Returns:
            tuple: A tuple containing the optimal move as a string and the optimal
            bet for the next hand as an integer. The possible values for the move are 'hit', 'stand', and 'split'.
        """
        dealer_hand = [card.upper() for card in dealer_hand]
        player_hand =  [card.upper() for card in player_hand]
        self.count_cards(dealer_hand)
        self.count_cards(player_hand)
        next_hand_bet = self.calculate_bet(current_bet)
        if (no_split is False) and self.should_split(dealer_hand, player_hand):
            return "split", next_hand_bet
        points = self.calculate_points(player_hand)
        if points < 17:
            return "hit", next_hand_bet
        elif points > 21:
            return "stand", next_hand_bet
        return "stand", next_hand_bet

class Blackjack:
    def __init__(self, player) -> None:
        players = (player, )

        self.table = Table(players)

        # dealer_first_card = table.dealer.hand[0]
        # print(f"Dealer: {dealer_first_card.rank} of {dealer_first_card.suit} and ?")

    def get_table(self):
        return self.table

    def print_cards(self, player):
        return_str = f"\n{player.name}\n"
        # print(f"\n{player.name}")
        for i, card in enumerate(player.hand):
            if (type(player) != Dealer) or (type(player) == Dealer and i == 0):
                return_str += f"{card.rank} of {card.suit}\n"
                # print(f"{card.rank} of {card.suit}")
        if type(player) != Dealer:
            return_str += f"Total: {player.total}\n"
            # print(player.total)

        return return_str


    def play_round(self, table, player, action):
        # self.print_cards(table.dealer)
        # self.print_cards(player)
        
        # action = int(input("\nHit(1), Stand(2): "))
        if action == "hit":
            player.play_hit()
        elif action == "stand":
            player.play_stand()


    def show_result(self, table):
        # print("--------------------")
        # print(f"\nDealer has {table.dealer.total}")
        # for player in table:
        #     print(f"{self.print_cards(player)}")

        for player in table:
            # result = player.result
            # if result > 0:
            #     print(f"{player.name} wins ${player.bet} ({player.total})")
            # elif result == 0:
            #     print(f"Hand tied ({player.total})")
            # else:
            #     print(f"{player.name} loses ${player.bet} ({player.total})")

            if player.bust:
                return -player.bet
            elif table.dealer.bust:
                return player.bet
            elif player.total > table.dealer.total:
                return player.bet
            else:
                return -player.bet

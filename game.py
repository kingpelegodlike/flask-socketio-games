#
# Contains all of the game logic regarding guesser and chooser
# and ways to guess
# This is the interface that the sockets can call to manipulate the
# control flow
#
import math
import logging
import logging.config
from generation import GENERATION_TO_YEAR
logger = logging.getLogger(__name__)

def configure_logging():
    # logger = logging.getLogger("my logger")
    logger.setLevel(logging.DEBUG)
    # Format for our loglines
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # Setup console logging
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    # Setup file logging as well
    fh = logging.FileHandler("game.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger

import random

from player import Player
from suite import Suite

# These are the different screens that the users can be seeing
class GameState:
  TITLE_SCREEN = 'titlescreen'
  LOADING_SCREEN = 'loadingscreen'
  GAME_SCREEN = 'gamescreen'
  NOT_STARTED = 'not started'
  QUESTIONS_SELECTION = 'questions selection'
  PLAYER_SELECTION = 'player selection'
  PLAYERS_SELECTED = 'players selected'
  DISPLAY_QUESTION = 'display question'
  ASK_QUESTION = 'ask question'
  WAITING_PLAYERS = 'waiting players'
  CHOOSE_TOPIC = 'choose topic'


class Game:

  def __init__(self):
    self.players = {} # Dictionary of [session_id:Player] currently connected
    self.removed_players = {}
    self.player_names = []
    self.questions = []
    self.state = GameState.NOT_STARTED # Screen that the users are on
    self.round = 0
    self.letters_guessed = []
    self.phrase_misses = 0
    self.nb_suites_played = 0
    self.suite_index_to_choose = 0
    self.is_players_report_presence = True
    self.is_score_per_time_range = False
    self.data_path = "."
    self.ranks_history = {}

  def set_data_path(self, a_path):
    self.data_path = a_path

  def __str__(self):
    return_str = ""
    for player_name in self.players:
      return_str = "{}{}\n".format(return_str, str(self.players[player_name]))
    return "<GAME:\tstate:{}\n{}>".format(self.state, return_str)

  # Reset the whole state
  def reset(self):
    # Don't reset players since people are still connected as spectators
    self.players = {} # Dictionary of [session_id:Player] currently connected
    self.removed_players = {}
    self.player_names = []
    self.questions = []
    self.state = GameState.NOT_STARTED
    self.round = 0
    self.letters_guessed = []
    self.phrase_misses = 0
    self.nb_suites_played = 0
    self.suite_index_to_choose = 0

  # Keep track of a new player in the game
  def add_player(self, name, generation = "Elders", buzzer=0):
    result = "None"
    if name is None:
      result = "NO_NAME"
      return result
    if name == "":
      result = "NO_NAME"
      return result
    if name in self.players:
      result = "ALLREADY_ADD"
      return result
    if name in self.removed_players:
      logger.info("Add former player with name {}".format(name))
      self.players[name] = self.removed_players[name]
      self.removed_players.pop(name, None)
    else:
      logger.info("Add player with name {}".format(name))
      self.players[name] = Player(name, generation, buzzer)
    self.player_names.append(name)
    result = "ADDED"
    return result

  # Remove a player from the game when they disconnect
  def remove_player(self, name):
    result = "None"
    removed_player_index = -1
    if name is None:
      result = "NO_NAME"
      return result
    if name not in self.players:
      result = "NOT_A_PLAYER"
      return result
    removed_player = self.players.pop(name, None)
    self.removed_players[name] = removed_player
    removed_player_index = self.player_names.index(name)
    self.player_names.pop(removed_player_index)
    result = "REMOVED"
    return result, removed_player_index

  # Get the number of players currently connected
  def count_players(self):
    return len(self.players)

  def get_player_score(self, name):
    if name not in self.players:
      return 0
    return self.players[name].get_score()

  def get_leader(self):
    top_score = -1;
    play_time = -1;
    leader = "No one"
    for a_player in self.players:
      player_score = self.players[a_player].get_score()
      player_name = self.players[a_player].name
      player_play_time = self.players[a_player].play_time
      logger.debug("check Player {} with {} pts and {} secondes".format(player_name, player_score, player_play_time))
      if player_score > top_score:
        logger.debug("player score is higher")
        leader = player_name
        play_time = player_play_time
        top_score = player_score
      elif player_score == top_score:
        logger.debug("player score is equal")
        if player_play_time < play_time:
          logger.debug("player play time is lower")
          leader = player_name
          play_time = player_play_time
      else:
        logger.debug("player score is not enough")
        pass 
    return leader, play_time, top_score

  def set_state(self, a_state):
    self.state = a_state

  def set_answer_button(self, a_button):
    self.answer_button = a_button

  def set_nb_suites(self, nb):
    self.nb_suites = nb

  def set_nb_questions_per_suite(self, nb):
    self.nb_questions_per_suite = nb

  def set_suites_list(self, suites_list):
    self.suites_list = suites_list

  def set_questions(self, suites=None, suites_path="suites"):
    # suite = Suite("suite1.json")
    if suites is not None:
        # suite = Suite("suites/"+suites+".json")
        # suite = Suite("suites_link/"+suites+".json")
        suite = Suite(f"{suites_path}/{suites}.json")
        self.questions = suite.questions

  def set_youtube_questions(self, youtube_questions=None):
    # suite = Suite("suite1.json")
    if youtube_questions is not None:
        self.questions = youtube_questions

  def add_questions(self, suites, max_questions_nbr=5, question_nbr_list=[], suites_path="suites"):
    # suite = Suite("suites/"+suites+".json", max_questions_nbr, question_nbr_list)
    suite = Suite(f"{suites_path}/{suites}.json", max_questions_nbr, question_nbr_list)
    self.questions.extend(suite.questions)

  def set_max_questions_number(self, max_questions_nbr=20):
    random.shuffle(self.questions)
    self.questions = self.questions[:max_questions_nbr]

  def is_next_question(self):
    if not self.questions:
        return False
    else:
        return True

  def set_next_question(self):
    if not self.questions:
        self.question = None
        return False
    self.question = self.questions.pop(0)
    return True

  def get_next_question(self):
    if not self.questions:
        self.question = None
        return False
    self.question = self.questions[0]
    return True

  def get_current_question(self):
    if not self.question:
        return None
    return self.question

  def increase_score(self, a_player, increment = 1, time = 0):
    if increment == 0:
      time_max = float(self.question.waiting_answer_timeout)
      time_left = time_max - float(time)
      slice_size = int(time_max) / 5
      score = int(math.floor(time_left / slice_size)) + 1
      self.players[a_player].increase_score(score)
    else:
      self.players[a_player].increase_score(increment)

  def increase_time(self, a_player, a_time):
    self.players[a_player].increase_time(a_time)

  def increase_timeout(self, a_player):
    if a_player in self.players:
      self.players[a_player].increase_timeout(self.question.waiting_answer_timeout)
    if a_player in self.removed_players:
      self.removed_players[a_player].increase_timeout(self.question.waiting_answer_timeout)

  def set_round_not_played(self, a_player):
    self.players[a_player].round_played = False
    self.players[a_player].good_time = 0

  def set_round_played(self, a_player, good_time=0):
    self.players[a_player].round_played = True
    self.players[a_player].good_time = good_time

  def is_round_played_by_player(self, a_player_name):
    is_round_played_by_player = False
    if a_player_name in self.players:
        is_round_played_by_player = self.players[a_player_name].round_played
    return is_round_played_by_player

  def set_players_round_not_played(self):
    for a_player in self.players:
        self.players[a_player].round_played = False
        self.players[a_player].round_ready = False
        self.players[a_player].round_guess = False
        self.players[a_player].good_time = 0

  def is_round_played(self):
    round_played = True
    if len(self.players) == 0:
        round_played = False
    for a_player in self.players:
        if self.players[a_player].round_played == False:
            round_played = False
            break
    return round_played

  def get_player_name_list_not_played(self):
    player_name_list = []
    for a_player in self.players:
        if self.players[a_player].round_played == False:
            player_name_list.append(a_player)
    return player_name_list

  def set_not_ready_for_round(self, a_player):
    self.players[a_player].round_ready = False

  def set_ready_for_round(self, a_player):
    if a_player in self.players:
      self.players[a_player].round_ready = True

  def is_players_ready_for_round(self):
    ready_for_round = True
    for a_player in self.players:
        if self.players[a_player].round_ready == False:
            ready_for_round = False
            break
    return ready_for_round

  def has_suite_played_left(self):
    if self.nb_suites == self.nb_suites_played:
      return False
    else:
      return True

  def get_suites_list_to_choose(self):
    suites_list_to_choose = []
    self.suite_index_to_choose_list = []
    for a_player in self.players:
      self.players[a_player].chosen_topic = None
    if self.suite_index_to_choose >= len(self.suites_list):
      self.suite_index_to_choose = 0
    self.suite_index_to_choose_list.append(self.suite_index_to_choose)
    suites_list_to_choose.append(self.suites_list[self.suite_index_to_choose])
    self.suite_index_to_choose += 1
    if self.suite_index_to_choose >= len(self.suites_list):
      self.suite_index_to_choose = 0
    self.suite_index_to_choose_list.append(self.suite_index_to_choose)
    suites_list_to_choose.append(self.suites_list[self.suite_index_to_choose])
    self.suite_index_to_choose += 1
    if self.suite_index_to_choose >= len(self.suites_list):
      self.suite_index_to_choose = 0
    self.suite_index_to_choose_list.append(self.suite_index_to_choose)
    suites_list_to_choose.append(self.suites_list[self.suite_index_to_choose])
    self.suite_index_to_choose += 1
    if self.suite_index_to_choose >= len(self.suites_list):
      self.suite_index_to_choose = 0
    self.suite_index_to_choose_list.append(self.suite_index_to_choose)
    suites_list_to_choose.append(self.suites_list[self.suite_index_to_choose])
    self.suite_index_to_choose += 1
    return suites_list_to_choose
  
  def is_topic_chosen_by_player(self, player_name):
    res = False
    for a_player in self.players:
      if self.players[a_player].name == player_name:
        if self.players[a_player].chosen_topic is not None:
          res = True
          break
    return res

  def is_topic_chosen_by_all_players(self):
    res = True
    for a_player in self.players:
      if self.players[a_player].chosen_topic is None:
        res = False
        break
    return res

  def set_chosen_topic_by_player(self, player_name, topic_index):
    self.players[player_name].chosen_topic = topic_index
    logger.info("Suite topic index to choose is {}".format(self.suite_index_to_choose_list))
    vote_list = [ 0, 0, 0, 0 ]
    for a_player in self.players:
      for index, value in enumerate(self.suite_index_to_choose_list):
        if self.players[a_player].chosen_topic == value:
          logger.info("Player {} chose topic index {}".format(self.players[a_player].name, value))
          vote_list[index] = vote_list[index] + 1
    # vote_list_sorted = sorted(vote_list, key=int, reverse=True)
    logger.info("Vote list is {}".format(vote_list))
    vote_index = 0
    nb_votes = -1
    for index, value in enumerate(vote_list):
      if value > nb_votes:
        vote_index = index
        nb_votes = value
    self.chosen_topic_index = self.suite_index_to_choose_list[vote_index]

  def add_questions_from_chosen_topic(self, suites_path="suites"):
    chosen_suite = self.suites_list[self.chosen_topic_index]
    suite_path = f"{suites_path}/{chosen_suite['name']}.json"
    logger.info("Add questions from suite %s", suite_path)
    # suite = Suite("suites/"+chosen_suite["name"]+".json", self.nb_questions_per_suite)
    # suite = Suite("suites_link/"+chosen_suite["name"]+".json", self.nb_questions_per_suite)
    suite = Suite(f"{suites_path}/{chosen_suite['name']}.json", self.nb_questions_per_suite)
    self.questions.extend(suite.questions)

  def get_players_name_list_from_buzz_number(self):
    player_list = [ None, None, None, None]
    for a_player in self.players:
      buzz_nb = self.players[a_player].buzzer
      player_list[buzz_nb-1] = self.players[a_player].name
    return player_list

  def get_player_name_from_buzz_number(self, buzzer_nb):
    player_name = None
    for a_player in self.players:
      if str(buzzer_nb) == str(self.players[a_player].buzzer):
        player_name = self.players[a_player].name
    return player_name

  def get_buzzer_number_list(self):
    buzzer_number_list = []
    for a_player in self.players:
      buzzer_number_list.append(str(self.players[a_player].buzzer))
    return buzzer_number_list
  
  def set_ranking(self):
    sorted_players = sorted(
      self.players.items(), 
      key=lambda p: (-p[1].score, p[1].play_time)
    )

    # Préparation du payload pour le socket
    payload = []
    new_ranks_history = {}

    for index, (p_id, p_obj) in enumerate(sorted_players):
      new_rank = index + 1
      
      # 2. Récupérer l'ancien rang depuis la mémoire
      # Si le joueur n'existait pas, on considère qu'il n'a pas bougé (0)
      old_rank = self.ranks_history.get(p_id, new_rank)
      
      # Calcul de la progression (Ancien - Nouveau)
      # Exemple : Place 5 -> Place 2 = +3
      progression = old_rank - new_rank
      
      # 3. Préparer les données pour le socket
      payload.append({
          "id": p_id,
          "name": p_obj.name,
          "points": p_obj.score,
          "play_time": p_obj.play_time,
          "rank": new_rank,
          "progression": progression
      })
      
      # Stocker le nouveau rang pour le prochain cycle
      new_ranks_history[p_id] = new_rank

    # Mettre à jour la mémoire globale
    self.ranks_history = new_ranks_history
    return payload

  def get_generation_range(self):
    min_generation_value = GENERATION_TO_YEAR["Youngers"]
    max_generation_value = GENERATION_TO_YEAR["Elders"]
    for a_player in self.players:
      player_generation_value = GENERATION_TO_YEAR[self.players[a_player].generation]
      if player_generation_value < min_generation_value:
        min_generation_value = player_generation_value
      if player_generation_value > max_generation_value:
        max_generation_value = player_generation_value
    return min_generation_value, max_generation_value



if __name__ == '__main__':
    logger = configure_logging
    game = Game()
    game.add_player("toto")

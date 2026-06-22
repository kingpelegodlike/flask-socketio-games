#
# Used to represent a player connected to the game
#

NO_NAME = 'Anonymous'


# Different roles that the players can have
class PlayerType:
  GUESSER_TYPE = 'guesser'
  CHOOSER_TYPE = 'chooser'
  SPECTATOR_TYPE = 'spectator'
  NO_TYPE = 'none'


class Player:

  def __init__(self, name, generation="Elders", buzzer=0):
    # Keep record of the session id of the player
    # self.sid = sid
    # self.player_type = PlayerType.SPECTATOR_TYPE
    self.name = name
    self.generation = generation
    self.buzzer = buzzer
    self.succed_guesses = 0
    self.missed_guesses = 0
    self.score = 0
    self.play_time = 0
    self.good_time = 0 # good answer time
    self.round_played = False
    self.round_ready = False
    self.round_guess = False
    self.chosen_topic = None

  def __repr__(self):
    is_round_played = "NOT play this round"
    if self.round_played:
        is_round_played = "Play this round"
    is_round_ready = "NOT ready this round"
    if self.round_ready:
        is_round_ready = "Ready this round"
    player_repr = \
      f"<Player name:{self.name} generation:{self.generation} score:{self.score} play time:{self.play_time} " \
      f"good answers:{self.succed_guesses} wrong answers:{self.missed_guesses} {is_round_played}, {is_round_ready}>"
    return player_repr

  def __str__(self):
    is_round_played = "NOT play this round"
    if self.round_played:
        is_round_played = "Play this round"
    is_round_ready = "NOT ready this round"
    if self.round_ready:
        is_round_ready = "Ready this round"
    player_str = \
      f"Player: name is {self.name}, generation is {self.generation}, score is {self.score}, " \
      f"play time is {self.play_time}s, {self.succed_guesses} good answers, {self.missed_guesses} wrong answers, " \
      f"{is_round_played}, {is_round_ready}"
    return player_str

  def __eq__(self, other): 
    if not isinstance(other, Player):
        # don't attempt to compare against unrelated types
        return False

    return self.name == other.name and self.score == other.score and self.play_time == other.play_time

  # Checks if the player is a guesser
  # def is_guesser(self):
    # return self.player_type == PlayerType.GUESSER_TYPE

  # Checks if the player is a chooser
  # def is_chooser(self):
    # return self.player_type == PlayerType.CHOOSER_TYPE

  # Checks if the player is a spectator
  # def is_spectator(self):
    # return self.player_type == PlayerType.SPECTATOR_TYPE

  # Returns the type of the player
  # def get_player_type(self):
    # return self.player_type

  # Makes the player a guesser
  # def make_guesser(self):
    # self.player_type = PlayerType.GUESSER_TYPE

  # Makes the player a chooser
  # def make_chooser(self):
    # self.player_type = PlayerType.CHOOSER_TYPE

  # Makes the player a spectator
  # def make_spectator(self):
    # self.player_type = PlayerType.SPECTATOR_TYPE

  # Sets the name of the player
  def set_name(self, name):
    assert name is not None
    self.name = name

  # Returns the name of the player
  def get_name(self):
    assert self.name is not None
    return self.name

  # Resets the name of the player
  # def reset_name(self):
    # self.name = NO_NAME

  # Sets the generation of the player
  def set_generation(self, generation):
    assert generation is not None
    self.generation = generation

  # Returns the generation of the player
  def get_generation(self):
    assert self.generation is not None
    return self.generation

  # Returns the score of the player
  def get_score(self):
    return self.score

  # Returns the number of phrase misses the player has
  def get_succes(self):
    return self.succed_guesses

  # Returns the number of phrase misses the player has
  def get_misses(self):
    return self.missed_guesses

  # Resets the round after a results_screen completes
  def round_reset(self):
    self.missed_guesses = 0

  # Fully resets the player
  # def full_reset(self):
    # self.make_spectator()
    # self.reset_name()

  # Returns the score of the player
  def increase_score(self, increment = 1):
    self.score = self.score + increment
    self.round_guess = True

  # Returns the score of the player
  def increase_time(self, a_time):
    self.play_time = round(self.play_time + float(a_time), 3)
    self.round_played = True

  # Returns the score of the player
  def increase_timeout(self, timeout):
    self.play_time = round(self.play_time + timeout, 3)
    self.round_played = True

  

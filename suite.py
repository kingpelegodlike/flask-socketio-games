#
# Used to represent a question suite
#
#
# Contains all of the game logic regarding guesser and chooser
# and ways to guess
# This is the interface that the sockets can call to manipulate the
# control flow
#
import logging
import logging.config
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
    fh = logging.FileHandler("suite.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger

import json
from collections import OrderedDict
import random
import ntpath

from question import Question

class Suite:
  def __init__(self, suite_file_name, max_questions_nbr=5, question_nbr_list=[]):
    topic = ""
    category = "All"
    try:
        with open(suite_file_name, encoding='utf-8') as json_file:
            data = json.load(json_file, object_pairs_hook=OrderedDict)
        question_list = data['questions']
        topic = ntpath.basename(suite_file_name)
        topic = topic.replace(".json", "")
        if "topic" in data:
            topic = data['topic']
    except FileNotFoundError as e:
        question_list = []
    self.questions = []
    if question_nbr_list == []:
        for question in question_list:
            question = Question(question, topic)
            self.questions.append(question)
            # logger.debug("Add question {}".format(question.question))
    else:
        nb_questions = len(question_list)
        for i, number in enumerate(question_nbr_list):
            if number < 0:
                question_nbr_list[i] = nb_questions + number
        for i, question in enumerate(question_list):
            if i in question_nbr_list:
                question = Question(question, topic)
                self.questions.append(question)
                # logger.debug("Add question {}".format(question.question))
    random.shuffle(self.questions)
    self.questions = self.questions[:max_questions_nbr]

  

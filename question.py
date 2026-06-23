#
# Used to represent a Question
#

import json


class Question:

  def __init__(self, question_type, topic=""):
    if isinstance(question_type, dict):
        self.topic = topic
        self.question = question_type['question']
        self.good_answer = question_type['good_answer']
        self.wrong_answers = question_type['wrong_answers']
        self.question_timeout = question_type['question_timeout']
        self.question_start_time = 0.0
        if "question_start_time" in question_type:
            self.question_start_time = round(float(question_type['question_start_time']), 2)
        self.waiting_answer_timeout = question_type['waiting_answer_timeout']
        self.waiting_answer_start_time = 0.0
        if "waiting_answer_start_time" in question_type:
            self.waiting_answer_start_time = round(float(question_type['waiting_answer_start_time']), 2)
        self.answer_timeout = question_type['answer_timeout']
        self.answer_start_time = 0.0
        if "answer_start_time" in question_type:
            self.answer_start_time = round(float(question_type['answer_start_time']), 2)
        self.question_media = question_type['question_media']
        self.waiting_answer_media = question_type['waiting_answer_media']
        self.answer_media = question_type['answer_media']
    else:
        self.topic = topic
        self.question = ""
        self.good_answer = ""
        self.wrong_answers = ["", "", ""]
        self.question_timeout = 0
        self.question_start_time = 0.0
        self.waiting_answer_timeout = 0
        self.waiting_answer_start_time = 0.0
        self.answer_timeout = 0
        self.answer_start_time = 0.0
        self.question_media = ""
        self.waiting_answer_media = ""
        self.answer_media = ""

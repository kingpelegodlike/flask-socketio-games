from os import listdir
from os.path import isfile, join
import json
import logging
import logging.config
from generation import GENERATION_TO_YEAR

# create logger
logger = logging.getLogger('app')
logging.config.fileConfig('logging.conf')

CATEGORIES = [ "All", "Elders", "Adults", "Teenagers", "Children" ]
mypath = "suites"
onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
# print(onlyfiles)
logger.debug(onlyfiles)
for sfile in onlyfiles:
    data = []
    data_loaded = False
    try:
        # print("Try to load suites/{} file.".format(sfile))
        logger.info("Load suites/%s file.", sfile)
        data = json.load(open("suites/{}".format(sfile)))
        data_loaded = True
    except Exception as e:
        # print("suites/{} is not a good JSON. {}".format(sfile, e))
        logger.error("suites/%s is not a good JSON. %s", sfile, e)
    if not data_loaded:
        continue
    if "generation_min" in data:
        generation_min = data["generation_min"]
        if generation_min not in GENERATION_TO_YEAR.keys():
            logger.debug(\
            "'generation_min' field value %s is NOT a part of GENERATION_TO_YEAR dictionary",
            generation_min)
    else:
        logger.debug("'generation_min' field is missing")
    if "generation_max" in data:
        generation_max = data["generation_max"]
        if generation_max not in GENERATION_TO_YEAR.keys():
            logger.debug(\
            "'generation_max' field value %s is NOT a part of GENERATION_TO_YEAR dictionary",
            generation_max)
    else:
        logger.debug("'generation_max' field is missing")
    if "categories" in data:
        categories = data["categories"]
        for category in categories:
            if not category in CATEGORIES:
                # print("Category field is '{}' not a part of categories '{}'" \
                #     .format(category, CATEGORIES))
                logger.debug(\
                    "Category field is '%s' not a part of categories '%s'", \
                    category, CATEGORIES)
    else:
        # print("'categories' field is missing")
        logger.debug("'categories' field is missing")
    if not "topic" in data:
        # print("Topic field is missing")
        logger.debug("Topic field is missing")
    for question_nbr, question in enumerate(data["questions"]):
        question_field = "Unknow"
        if "question" in question:
            question_field = question["question"]
        else:
            # print("question field is missing in question number {} for file '{}'" \
            #       .format(question_nbr+1, sfile))
            logger.error(\
                "question field is missing in question number %s for file '%s'", \
                question_nbr+1, sfile)

        question_timeout = "Unknow"
        if "question_timeout" in question:
            question_timeout = question["question_timeout"]
            if not isinstance(question_timeout,int):
                # print("question_timeout '{}' is not an integer in question number {}: '{}' for file '{}'" \
                #       .format(question_timeout, question_nbr+1, question_field, sfile))
                logger.error(\
                    "question_timeout '%s' is not an integer in question number %s: '%s' for file '%s'", \
                    question_timeout, question_nbr+1, question_field, sfile)
        else:
            # print("question_timeout field is missing in question number {}: '{}' for file '{}'" \
            #           .format(question_nbr+1, question_field, sfile))
            logger.debug(\
                "question_timeout field is missing in question number %s: '%s' for file '%s'", \
                question_nbr+1, question_field, sfile)

        waiting_answer_timeout = "Unknow"
        if "waiting_answer_timeout" in question:
            waiting_answer_timeout = question["waiting_answer_timeout"]
            if not isinstance(waiting_answer_timeout,int):
                # print("waiting_answer_timeout '{}' is not an integer in question number {}: '{}' for file '{}'" \
                #       .format(waiting_answer_timeout, question_nbr+1, question_field, sfile))
                logger.error(\
                    "waiting_answer_timeout '%s' is not an integer in question number %s: '%s' for file '%s'", \
                    waiting_answer_timeout, question_nbr+1, question_field, sfile)
        else:
            # print("waiting_answer_timeout field is missing in question number {}: '{}' for file '{}'" \
            #       .format(question_nbr+1, question_field, sfile))
            logger.debug(\
                "waiting_answer_timeout field is missing in question number %s: '%s' for file '%s'", \
                question_nbr+1, question_field, sfile)

        answer_timeout = "Unknow"
        if "answer_timeout" in question:
            answer_timeout = question["answer_timeout"]
            if not isinstance(answer_timeout,int):
                # print("answer_timeout '{}' is not an integer in question number {}: '{}' for file '{}'" \
                #       .format(answer_timeout, question_nbr+1, question_field, sfile))
                logger.error(\
                    "answer_timeout '%s' is not an integer in question number %s: '%s' for file '%s'", \
                    answer_timeout, question_nbr+1, question_field, sfile)
        else:
            # print("answer_timeout field is missing in question number {}: '{}' for file '{}'" \
            #       .format(question_nbr+1, question_field, sfile))
            logger.debug(\
                "answer_timeout field is missing in question number %s: '%s' for file '%s'", \
                question_nbr+1, question_field, sfile)

        if "question_media" in question:
            question_media_list = question["question_media"]
            for question_media_nbr, question_media in enumerate(question_media_list):
                if not isfile(question_media[1:]):
                    # print("Unknow question_media '{}' in question number {}: '{}' for file '{}'" \
                    #       .format(question_media, question_nbr+1, question_field, sfile))
                    logger.error(\
                        "Unknow question_media '%s' in question number %s: '%s' for file '%s'", \
                        question_media, question_nbr+1, question_field, sfile)
        else:
            # print("question_media field is missing in question number {}: '{}' for file '{}'" \
            #       .format(question_nbr+1, question_field, sfile))
            logger.debug(\
                "question_media field is missing in question number %s: '%s' for file '%s'", \
                question_nbr+1, question_field, sfile)

        if "waiting_answer_media" in question:
            waiting_answer_media_list = question["waiting_answer_media"]
            for waiting_answer_media_nbr, waiting_answer_media in enumerate(waiting_answer_media_list):
                if not isfile(waiting_answer_media[1:]) and not waiting_answer_media.endswith((".yt", ".yta")):
                    # print("Unknow waiting_answer_media '{}' in question number {}: '{}' for file '{}'" \
                    #       .format(waiting_answer_media, question_nbr+1, question_field, sfile))
                    logger.error(\
                        "Unknow waiting_answer_media '%s' in question number %s: '%s' for file '%s'", \
                        waiting_answer_media, question_nbr+1, question_field, sfile)
        else:
            # print("waiting_answer_media field is missing in question number {}: '{}' for file '{}'" \
            #       .format(question_nbr+1, question_field, sfile))
            logger.debug(\
                "waiting_answer_media field is missing in question number %s: '%s' for file '%s'", \
                question_nbr+1, question_field, sfile)

        if "answer_media" in question:
            answer_media_list = question["answer_media"]
            for answer_media_nbr, answer_media in enumerate(answer_media_list):
                if not isfile(answer_media[1:]) and not answer_media.endswith((".yt",".yta")):
                    # print("Unknow answer_media '{}' in question number {}: '{}' for file '{}'" \
                    #       .format(answer_media, question_nbr+1, question_field, sfile))
                    logger.error(\
                        "Unknow answer_media '%s' in question number %s: '%s' for file '%s'", \
                        answer_media, question_nbr+1, question_field, sfile)
        else:
            # print("answer_media field is missing in question number {}: '{}' for file '{}'" \
            #       .format(question_nbr+1, question_field, sfile))
            logger.debug(\
                "answer_media field is missing in question number %s: '%s' for file '%s'", \
                question_nbr+1, question_field, sfile)

        if "wrong_answers" in question:
            wrong_answers_list = question["wrong_answers"]
            if not isinstance(wrong_answers_list,list):
                # print("wrong_answers '{}' is not a list in question number {}: '{}' for file '{}'" \
                #       .format(wrong_answers_list, question_nbr+1, question_field, sfile))
                logger.error(\
                    "wrong_answers '%s' is NOT a list in question number %s: '%s' for file '%s'", \
                    wrong_answers_list, question_nbr+1, question_field, sfile)
            else:
                if len(wrong_answers_list) != 3:
                    # print("wrong_answers '{}' list length is {} instead of 3 in question number {}: '{}' for file '{}'" \
                    #       .format(wrong_answers_list, len(wrong_answers_list), question_nbr+1, question_field, sfile))
                    logger.error(\
                        "wrong_answers '%s' list length is %s instead of 3 in question number %s: '%s' for file '%s'", \
                        wrong_answers_list, len(wrong_answers_list), question_nbr+1, question_field, sfile)
        else:
            # print("wrong_answers field is missing in question number {}: '{}' for file '{}'" \
            #       .format(question_nbr+1, question_field, sfile))
            logger.debug(\
                "wrong_answers field is missing in question number %s: '%s' for file '%s'", \
                question_nbr+1, question_field, sfile)

        if "good_answer" in question:
            good_answer = question["good_answer"]
            if not isinstance(good_answer,str):
                # print("good_answer field is not a string in question number {}: '{}' for file '{}'" \
                #           .format(question_nbr+1, question_field, sfile))
                logger.error(\
                    "good_answer field is not a string in question number %s: '%s' for file '%s'", \
                    question_nbr+1, question_field, sfile)
        else:
            # print("good_answer field is missing in question number {}: '{}' for file '{}'" \
            #       .format(question_nbr+1, question_field, sfile))
            logger.error(\
                "good_answer field is missing in question number %s: '%s' for file '%s'", \
                question_nbr+1, question_field, sfile)
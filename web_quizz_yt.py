#!/usr/bin/env python
import argparse
import socket
import os
import fnmatch
import qrcode
import json
import logging
import logging.config

logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

# create logger
logger = logging.getLogger('app')

logging.config.fileConfig('logging.conf')

from threading import Lock
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
# from engineio.async_drivers import threading
# from engineio.async_drivers import gevent
from game import Game, GameState
from generation import GENERATION_TO_YEAR
import random

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None
# async_mode = 'threading'
# async_mode = 'engineio.async_drivers.threading'
# async_mode = 'eventlet'
# async_mode = 'gevent'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# socketio = SocketIO(app, async_mode=async_mode)
socketio = SocketIO(app, cors_allowed_origins="*")
game = Game()
thread = None
thread_lock = Lock()
PLAYERS_CATEGORY = ["All"]
NBR_SUITES = [ 2 ]
NBR_QUESTIONS_PER_SUITE = [ 2 ]
suites_list = []
nb_times_color_choosed = [0, 0, 0, 0]


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    # while True:
        # socketio.sleep(10)
        # count += 1
        # socketio.emit('my_response',
                      # {'data': 'Server generated event', 'count': count},
                      # namespace='/test')

def countdown_thread(counter):
    """Example of how to send server generated events to clients."""
    count = 0
    buzz_clear_timeout = False
    while count < counter:
        socketio.sleep(1)
        count += 1
        if game.is_round_played():
            count = counter
            buzz_clear_timeout = True
        # print("Counter is {}".format(count))
    return buzz_clear_timeout

def countdown_ready_thread(counter):
    """Example of how to send server generated events to clients."""
    count = 0
    is_timeout = False
    while count < counter:
        socketio.sleep(1)
        count += 1
        if game.is_players_ready_for_round():
            count = counter
            is_timeout = True
        # print("Counter is {}".format(count))
    return is_timeout


@app.route('/')
def index():
    # if 'username' in session:
      # username = session['username']
      # if username == "admin":
    logger.info("render_template 'index.html'")
    return render_template('index.html', async_mode=socketio.async_mode)
      # else:
        # return render_template('buzzer.html', async_mode=socketio.async_mode)
    # return render_template('logout.html', async_mode=socketio.async_mode)


@app.route('/web_quizz')
def web_quizz():
    game.reset()
    hostname = socket.gethostbyname(socket.gethostname())
    logger.info("render_template 'web_quizz.html' with hostname=%s", hostname)
    return render_template('web_quizz.html', async_mode=socketio.async_mode, hostname=hostname)

@app.route('/web_quizz_login', methods = ['GET', 'POST'])
def web_quizz_login():
   if request.method == 'POST':
      return render_template('web_quizz_buzzer.html', async_mode=socketio.async_mode)
   return render_template('web_quizz_login.html', async_mode=socketio.async_mode)


@app.route('/web_quizz_buzzer')
def web_quizz_buzzer():
    return render_template('web_quizz_buzzer.html', async_mode=socketio.async_mode)


@app.route('/quizz_settings')
def quizz_settings():
    game.reset()
    logger.info("render_template 'quizz_settings.html'")
    return render_template('quizz_settings.html', async_mode=socketio.async_mode)

@app.route('/login', methods = ['GET', 'POST'])
def login():
   if request.method == 'POST':
      session['username'] = request.form['username']
      if session['username'] == "admin":
        logger.info("admin session render_template 'index.html'")
        return render_template('index.html', async_mode=socketio.async_mode)
      else:
        logger.info("render_template 'buzzer.html'")
        return render_template('buzzer.html', async_mode=socketio.async_mode)
   logger.info("render_template 'login.html'")
   return render_template('login.html', async_mode=socketio.async_mode)
   
@app.route('/logout')
def logout():
   # remove the username from the session if it is there
   session.pop('username', None)
   return render_template('logout.html', async_mode=socketio.async_mode)


@app.route('/buzzer')
def buzzer():
    return render_template('buzzer.html', async_mode=socketio.async_mode)


@app.route('/test_question')
def test_question():
    return render_template('test_question.html', async_mode=socketio.async_mode)

@socketio.on('my_event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my_broadcast_event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('join', namespace='/test')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close_room', namespace='/test')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


@socketio.on('my_room_event', namespace='/test')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])


@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('my_ping', namespace='/test')
def ping_pong():
    emit('my_pong')


@socketio.on('connect', namespace='/test')
def test_connect():
    logger.debug("Receive from '/test' namespace 'connect' event")
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    # print("remove {} handlers".format(len(logger.handlers)))
    # handlers = logger.handlers[:]
    # for handler in handlers:
        # handler.close()
        # logger.removeHandler(handler)
    # print("set new handler")
    # logger = logging.getLogger('app')
    emit_data_to_test = {'data': 'Connected', 'count': 0}
    logger.info("emit to '/test' namespace 'my_response' event with data %s", emit_data_to_test)
    emit('my_response', emit_data_to_test, namespace='/test')

@socketio.on('connect', namespace='/buz')
def test_connect():
    emit_data_to_test = {'data': 'Connected', 'action': 'connect'}
    logger.info("emit to '/buz' namespace 'my_response' event with data %s", emit_data_to_test)
    emit('my_response', emit_data_to_test, namespace='/buz')

@socketio.on('connect', namespace='/test_question')
def test_connect():
    logger.debug("Receive from '/test_question' namespace 'connect' event")
    # global thread
    # with thread_lock:
    #     if thread is None:
    #         thread = socketio.start_background_task(background_thread)
    # emit_data_to_test = {'data': 'Connected', 'count': 0}
    # logger.info("emit to '/test_question' namespace 'my_response' event with data %s", emit_data_to_test)
    # emit('my_response', emit_data_to_test, namespace='/test_question')

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


@socketio.on('set_questions', namespace='/test')
def set_questions(data):
    logger.info("set_questions")
    session['status'] = "set_questions"
    game.set_state(GameState.QUESTIONS_SELECTION)
    game.set_questions(suites_path=suites_path)
    # print("with data {}\n and ID {}".format(data, data["data"][0]["id"]))
    # suite_name = data["data"][0]["id"]
    # game.set_questions(suite_name)
    question_nbr_per_suite = int(data["question_nbr_per_suite"])
    for i in range(len(data["data"])):
        logger.debug("with data {}\n and ID {}".format(data, data["data"][i]["id"]))
        suite_name = data["data"][i]["id"]
        game.add_questions(suite_name, question_nbr_per_suite, suites_path=suites_path)
    question_nbr = int(data["question_nbr"])
    session['nb_questions'] = question_nbr
    game.set_max_questions_number(question_nbr)


@socketio.on('quiz_set', namespace='/test')
def quiz_set(data):
    global game
    logger.info("Receive from '/test' namespace 'quiz_set' event with data %s", data)
    session['status'] = "quiz_set"
    game = Game()
    game.is_players_report_presence = data['is_players_report_presence']
    # logger.debug("With players report presence set to '%s'", game.is_players_report_presence)
    game.set_state(GameState.QUESTIONS_SELECTION)
    game.set_questions(suites_path=suites_path)
    PLAYERS_CATEGORY[0] = data["players_category"]
    logger.debug("With '%s' category", PLAYERS_CATEGORY[0])
    NBR_SUITES[0] = int(data["topic_nbr"])
    logger.debug("With '%s' suites", NBR_SUITES[0])
    NBR_QUESTIONS_PER_SUITE[0] = int(data["question_nbr_per_topic"])
    logger.debug("With '%s' question per suites", NBR_QUESTIONS_PER_SUITE[0])
    players_generation_max, players_generation_min = game.get_generation_range()
    logger.debug("With players generation min '%s' and max '%s'", players_generation_min, players_generation_max)
    for path, folders, files in os.walk(os.path.join(os.getcwd(), suites_path)):
    # for path, folders, files in os.walk(os.path.join(os.getcwd(), "suites_link")):
    # for path, folders, files in os.walk(os.path.join(os.getcwd(), "suites")):
        for file in files:
            if fnmatch.fnmatch(file, '*.json'):
                filename = os.path.join(path, file)
                basename = os.path.basename(filename)
                suitename = os.path.splitext(basename)[0]
                # print("suite file {} and path:{}".format(suitename, filename))
                json_data = json.load(open(filename, encoding='utf-8'))
                categories = json_data["categories"]
                suite_generation_min = GENERATION_TO_YEAR[json_data.get("generation_min", "Youngers")]
                suite_generation_max = GENERATION_TO_YEAR[json_data.get("generation_max", "Elders")]
                logger.debug("suite generation min '%s' and max '%s'", suite_generation_min, suite_generation_max)
                topic = json_data["topic"]
                # if ( (PLAYERS_CATEGORY[0] == "All") or (PLAYERS_CATEGORY[0] in categories) or (categories == ["All"]) ):
                if suite_generation_max <= players_generation_max and suite_generation_min >= players_generation_min:
                    if suitename != "test_suite":
                        logger.debug("Add suite file '%s' and topic '%s' and path:'%s'", suitename, topic, filename)
                        suite_dict = {"name": suitename, "topic": topic}
                        suites_list.append(suite_dict)
                    else:
                        logger.debug("Skip suite file '%s' and topic '%s' and path:'%s'", suitename, topic, filename)
                else:
                    logger.debug("Skip suite file '%s' and topic '%s' and path:'%s' due to generation range",
                                 suitename, topic, filename)


@app.route('/quizz_players')
def quizz_players():
    logger.info("render_template 'quizz_players.html'")
    return render_template('quizz_players.html', async_mode=socketio.async_mode)


@app.route('/quizz')
def quizz():
    logger.info("render_template 'quizz.html'")
    return render_template('quizz.html', async_mode=socketio.async_mode)


@socketio.on('set_test_question', namespace='/test')
def set_test_question(data):
    logger.info("set_test_question")
    session['status'] = "set_test_question"
    game.set_state(GameState.QUESTIONS_SELECTION)
    game.set_questions(suites_path=suites_path)
    question_nbr = int(data["question_nbr"])
    question_nbr_list = [question_nbr]
    suite_name = data["suite_file_name"]
    game.add_questions(suite_name, 1, question_nbr_list, suites_path)
    session['nb_questions'] = 1
    game.set_max_questions_number(1)
     


@socketio.on('activ_all_buttons', namespace='/test')
def activ_all_buttons():
    print("activ_buttons")
    session['status'] = "activ_all_buttons"
    socketio.emit('my_response',
         {'action': "activ_buttons"},
         namespace='/buz')


@socketio.on('activ_buttons', namespace='/test')
def activ_buttons():
    print("activ_buttons")
    session['status'] = "activ_buttons"
    print("\nemit my_response to buz with action {} b1 {} b2 {} b3 {} b4 {} b5 {}\n".format("activ_buttons", "ROUGE", "REPONSE BLEU", "REPONSE ORANGE", "REPONSE VERT", "REPONSE JAUNE"))
    socketio.emit('my_response',
         {'action': "activ_buttons", 'b1': "ROUGE", 'b2': "REPONSE BLEU", 'b3': "REPONSE ORANGE", 'b4': "REPONSE VERT", 'b5': "REPONSE JAUNE"},
         namespace='/buz')

def get_medias(media_list):
    sound = ""
    media_type = ""
    media = ""
    for file_name in media_list:
        if file_name.endswith(".mp3"):
            sound = file_name
        elif ( file_name.endswith(".png") or file_name.endswith(".jpg") ):
            if media_type == "youtube":
                media = f"{media}&{file_name}"
            else:
                media_type = "image"
                media = file_name
        elif ( file_name.endswith((".mp4", ".avi", ".mkv", ".flv", ".3gp")) ):
            media_type = "video"
            media = file_name
        elif ( file_name.endswith(".yt") ):
            media_type = "youtube"
            media = file_name.replace(".yt", "")
        elif ( file_name.endswith(".yta") ):
            media_type = "youtube_animated"
            media = file_name.replace(".yta", "")
        else:
            continue
    return sound, media_type, media

@socketio.on('launch_quiz', namespace='/test')
def launch_quiz(data):
    global game
    logger.info("launch_quiz")
    session['status'] = "quiz_set"
    # game = Game()
    game.is_players_report_presence = data['is_players_report_presence']
    # logger.debug("With players report presence set to '%s'", game.is_players_report_presence)
    game.is_score_per_time_range = data['is_score_per_time_range']
    # logger.debug("With score pert time range set to '%s'", game.is_score_per_time_range)
    game.set_state(GameState.QUESTIONS_SELECTION)
    game.set_questions(suites_path=suites_path)
    PLAYERS_CATEGORY[0] = data["players_category"]
    logger.debug("With '%s' category", PLAYERS_CATEGORY[0])
    NBR_SUITES[0] = int(data["topic_nbr"])
    logger.debug("With '%s' suites", NBR_SUITES[0])
    NBR_QUESTIONS_PER_SUITE[0] = int(data["question_nbr_per_topic"])
    logger.debug("With '%s' question per suites", NBR_QUESTIONS_PER_SUITE[0])
    players_generation_max, players_generation_min = game.get_generation_range()
    logger.debug("With players generation min '%s' and max '%s'", players_generation_min, players_generation_max)
    for path, folders, files in os.walk(os.path.join(os.getcwd(), suites_path)):
    # for path, folders, files in os.walk(os.path.join(os.getcwd(), "suites_link")):
    # for path, folders, files in os.walk(os.path.join(os.getcwd(), "suites")):
        for file in files:
            if fnmatch.fnmatch(file, '*.json'):
                filename = os.path.join(path, file)
                basename = os.path.basename(filename)
                suitename = os.path.splitext(basename)[0]
                # print("suite file {} and path:{}".format(suitename, filename))
                json_data = json.load(open(filename, encoding='utf-8'))
                categories = json_data["categories"]
                suite_generation_min = GENERATION_TO_YEAR[json_data.get("generation_min", "Youngers")]
                suite_generation_max = GENERATION_TO_YEAR[json_data.get("generation_max", "Elders")]
                logger.debug("suite generation min '%s' and max '%s'", suite_generation_min, suite_generation_max)
                topic = json_data["topic"]
                # if ( (PLAYERS_CATEGORY[0] == "All") or (PLAYERS_CATEGORY[0] in categories) or (categories == ["All"]) ):
                if suite_generation_max <= players_generation_max and suite_generation_min >= players_generation_min:
                    if suitename != "test_suite":
                        logger.debug("Add suite file '%s' and topic '%s' and path:'%s'", suitename, topic, filename)
                        suite_dict = {"name": suitename, "topic": topic}
                        suites_list.append(suite_dict)
                    else:
                        logger.debug("Skip suite file '%s' and topic '%s' and path:'%s'", suitename, topic, filename)
                else:
                    logger.debug("Skip suite file '%s' and topic '%s' and path:'%s' due to generation range",
                                 suitename, topic, filename)
    session['status'] = "launch_quiz"
    random.shuffle(suites_list)
    for suite_nb in range(NBR_SUITES[0]):
        suite_choosen = display_suite_selection(game)
        if suite_choosen == -1:
            break
        game.add_questions(suite_choosen, NBR_QUESTIONS_PER_SUITE[0], suites_path=suites_path)
        session['nb_questions'] = NBR_QUESTIONS_PER_SUITE[0]
        while game.is_next_question():
            is_next_question = game.set_next_question()
            question_obj = game.get_current_question()
            buttons = ['b2', 'b3', 'b4', 'b5']
            answers = [question_obj.good_answer, question_obj.wrong_answers[0], question_obj.wrong_answers[1], question_obj.wrong_answers[2]]
            random.shuffle(buttons)
            random.shuffle(answers)
            good_answer_question_index = answers.index(question_obj.good_answer)
            good_answer_button = buttons[good_answer_question_index]
            good_answer_button = good_answer_button[0] + "outon" + good_answer_button[1]
            game.set_answer_button(good_answer_button)
            players_score_list = []
            for player_name in game.player_names:
                players_score_list.append(game.players[player_name].score)
            players_play_time_list = []
            for player_name in game.player_names:
                players_play_time_list.append(game.players[player_name].play_time)
            continue_game = display_question(game, game.player_names, players_score_list, players_play_time_list)
            if not continue_game:
                break
            game.set_players_round_not_played()
            display_answer_question(game, answers, good_answer_button, buttons, game.player_names)
            display_answer(game, answers, good_answer_question_index, buttons, good_answer_button)
    leader, top_score, play_time = game.get_leader()
    print("Winner {} ({}s)".format(leader, play_time))
    players_score_list = []
    for player_name in game.player_names:
        players_score_list.append(game.players[player_name].score)
    players_play_time_list = []
    for player_name in game.player_names:
        players_play_time_list.append("{0:.3f}".format(round(game.players[player_name].play_time,3)))
    display_winner(leader, top_score, "{0:.3f}".format(round(play_time,3)), game.player_names, players_score_list, players_play_time_list)
    return

@socketio.on('display_suite_selection', namespace='/test')
def display_suite_selection(game):
    global nb_times_color_choosed
    logger.info("display_suite_selection from /test namespace")
    game.set_state(GameState.WAITING_PLAYERS)
    media_type = "image"
    media = "/static/images/are_you_ready.jpg"
    sound = "/static/sounds/lets_get_ready_to_rumble.mp3"
    is_timeout = False
    is_players_report_presence = game.is_players_report_presence
    logger.debug("is_players_report_presence %s with type %s", is_players_report_presence, type(is_players_report_presence))
    if (not is_players_report_presence):
        is_timeout = True
        for player_name in game.players:
            game.set_ready_for_round(player_name)
    while not is_timeout:
        players = game.players
        game.set_players_round_not_played()
        waiting_players = ""
        for player_name in players:
            if not game.players[player_name].round_ready:
                waiting_players = "{} {}".format(waiting_players, player_name)
            game.set_not_ready_for_round(player_name)

        emit_data_to_test =  {
            'name': "GAME", 'time': 0,
            'media_type': media_type, 'media': media, 'sound': sound,
            'players': game.player_names, 'comment': f" WAITING FOR PLAYERS{waiting_players}"
        }
        logger.info("emit to '/test' namespace 'add_players_console' event with data %s", emit_data_to_test)
        socketio.emit('add_players_console', emit_data_to_test, namespace='/test')

        emit_data_to_buz = {
            'action': "player_ready",
            'b1': "PRET A JOUER", 'b2': "", 'b3': "", 'b4': "", 'b5': ""
        }
        logger.info("emit to '/buz' namespace 'my_response' event with data %s", emit_data_to_buz)
        socketio.emit('my_response', emit_data_to_buz, namespace='/buz')

        is_timeout = countdown_ready_thread(10)

    if game.players == {}:
        logger.info("No more players connected. End Game")
        return ""

    game.set_state(GameState.CHOOSE_TOPIC)
    colors = ['darkblue', 'darkorange', 'darkgreen', 'gold']
    topic1 = suites_list[0]["topic"]
    topic2 = suites_list[1]["topic"]
    topic3 = suites_list[2]["topic"]
    topic4 = suites_list[3]["topic"]
    good_answer_button = ""
    sound = "/static/sounds/countdown.mp3"
    media_type = "image"
    media = "/static/images/choose_topic.jpg"
    waiting_answer_timeout = 60
    for player_name in game.players:
        game.set_round_not_played(player_name)
    nb_times_color_choosed = [0, 0, 0, 0]

    emit_data_to_test = {
        'action': "display_topic",
        'b1': "CHOISIR LE SUJET", "b2": topic1, "b3": topic2, "b4": topic3, "b5": topic4,
        'topic': '', 'question': "CHOISIR LE SUJET",
        'sound': sound, 'media_type': media_type, 'media': media,
        'timeout': waiting_answer_timeout
    }
    logger.info("emit to '/test' namespace 'display_topic' event with data %s", emit_data_to_test)
    socketio.emit('display_topic', emit_data_to_test, namespace='/test')

    emit_data_to_buz = {
        'action': "display_topic",
        'b1': "CHOISIR LE SUJET", "b2": topic1, "b3": topic2, "b4": topic3, "b5": topic4,
        'answer': good_answer_button,
        'timeout': waiting_answer_timeout*1000
    }
    logger.info("emit to '/buz' namespace 'my_response' event with data %s", emit_data_to_buz)
    socketio.emit('my_response', emit_data_to_buz, namespace='/buz')

    # socketio.sleep(10)
    buzz_clear_timeout = countdown_thread(waiting_answer_timeout)

    logger.debug("Nb times color choosed list is %s", nb_times_color_choosed)
    best_choose = -1
    for index in range(len(nb_times_color_choosed)):
        print(f"check index {index}")
        if nb_times_color_choosed[index] > best_choose:
            print(f"index {index} choosen {nb_times_color_choosed[index]} times")
            color_index_choosed = index
            best_choose = nb_times_color_choosed[index]
    print("Choose color {}".format(colors[color_index_choosed]))
    suite_choosen = suites_list[color_index_choosed]["name"]
    print("\nSUITE CHOOSEN is {}\n".format(suite_choosen))
    del[suites_list[color_index_choosed]]
    suites_list.append(suites_list.pop(0))
    suites_list.append(suites_list.pop(0))
    suites_list.append(suites_list.pop(0))
    # TODO : to remove perhaprs
    emit_data_to_buz = {'action': "clear_timeout", 'b1': suite_choosen, "b2": "", "b3": "", "b4": "", "b5": ""}
    logger.info("to remove perhaps '/buz' namespace 'my_response' event with data %s", emit_data_to_buz)
    socketio.emit('my_response', emit_data_to_buz, namespace='/buz')
    return suite_choosen

@socketio.on('display_question', namespace='/test')
def display_question(game, players_name_list, players_score_list, players_play_time_list):
    logger.info("display_question")
    session['status'] = "display_question"
    
    game.set_state(GameState.WAITING_PLAYERS)
    media_type = "image"
    media = "/static/images/are_you_ready.jpg"
    is_timeout = False
    is_players_report_presence = game.is_players_report_presence
    # logger.debug("is_players_report_presence %s with type %s", is_players_report_presence, type(is_players_report_presence))
    if (not is_players_report_presence):
        is_timeout = True
        for player_name in game.players:
            game.set_ready_for_round(player_name)
    while not is_timeout:
        players = game.players
        game.set_players_round_not_played()
        waiting_players = ""
        for player_name in players:
            if not game.players[player_name].round_ready:
                waiting_players = "{} {}".format(waiting_players, player_name)
            game.set_not_ready_for_round(player_name)

        emit_data_to_test = {
            'name': "GAME", 'time': 0,
            'media_type': media_type, 'media': media,
            'players': game.player_names, 'comment': f" WAITING FOR PLAYERS{waiting_players}"
        }
        logger.info("emit to '/test' namespace 'add_players_console' event with data %s", emit_data_to_test)
        socketio.emit('add_players_console', emit_data_to_test, namespace='/test')

        emit_data_to_buz = {
            'action': "player_ready",
            'b1': "PRET A JOUER", 'b2': "", 'b3': "", 'b4': "", 'b5': ""
        }
        logger.info("emit to '/buz' namespace 'my_response' event with data %s", emit_data_to_buz)
        socketio.emit('my_response', emit_data_to_buz, namespace='/buz')

        is_timeout = countdown_ready_thread(10)

    if game.players == {}:
        logger.info("No more players connected. End Game")
        return False

    question = game.question
    sound, media_type, media = get_medias(question.question_media)
    game.set_state(GameState.DISPLAY_QUESTION)
    topic = "({}/{}) : {}".format(session['nb_questions']-len(game.questions), session['nb_questions'], question.topic)
    emit_data_to_test = {
        'action': "display_question",
        'b1': question.question, 'b2': "&nbsp;", 'b3': "&nbsp;", 'b4': "&nbsp;", 'b5': "&nbsp;",
        'topic': topic, 'question': question.question,
        'sound': sound, 'media_type': media_type, 'media': media,
        'timeout': question.question_timeout, 'start_time': question.question_start_time
    }
    logger.info("emit to '/test' namespace 'display_question' event with data %s", emit_data_to_test)
    socketio.emit('display_question', emit_data_to_test, namespace='/test')

    logger.info("emit to '/buz' namespace 'deactiv_buttons' event")
    socketio.emit('my_response', {'action': "deactiv_buttons"}, namespace='/buz')

    socketio.sleep(question.question_timeout)
    return True

@socketio.on('test_display_question', namespace='/test_question')
def test_display_question(data):
    logger.info("test_display_question")
    session['status'] = "test_display_question"
    suite_file_name = data["suite_file_name"]
    question_nbr = int(data["question_nbr"])
    try:
        json_data = json.load(open(f"suites/{suite_file_name}.json", encoding='utf-8'))
    except Exception as e:
        error_msg = f"Error loading suite file 'suites/{suite_file_name}.json'"
        logger.error("%s: %s", error_msg, e)
        emit_data_to_test = {'error_msg': error_msg}
        logger.info("emit to '/test_question' namespace 'popup_error_msg' event with data %s", emit_data_to_test)
        socketio.emit('popup_error_msg', emit_data_to_test, namespace='/test_question')
        return
    from question import Question
    nb_questions = len(json_data["questions"])
    if question_nbr < -nb_questions or question_nbr > nb_questions or question_nbr == 0:
        error_msg = f"Question number '{question_nbr}' is out of range (1-{len(json_data['questions'])}) in suite file '{suite_file_name}.json'"
        logger.error("%s", error_msg)
        emit_data_to_test = {'error_msg': error_msg}
        logger.info("emit to '/test_question' namespace 'popup_error_msg' event with data %s", emit_data_to_test)
        socketio.emit('popup_error_msg', emit_data_to_test, namespace='/test_question')
        return
    question_index = question_nbr -1 if question_nbr > 0 else nb_questions + question_nbr
    question = Question(json_data["questions"][question_index], json_data["topic"])
    sound, media_type, media = get_medias(question.question_media)
    topic = f"({question_index+1}/{nb_questions}) : {question.topic}"
    emit_data_to_test = {
        'action': "display_question",
        'b1': question.question, 'b2': "&nbsp;", 'b3': "&nbsp;", 'b4': "&nbsp;", 'b5': "&nbsp;",
        'topic': topic, 'question': question.question,
        'sound': sound, 'media_type': media_type, 'media': media,
        'timeout': question.question_timeout, 'start_time': question.question_start_time
    }
    logger.info("emit to '/test_question' namespace 'display_question' event with data %s", emit_data_to_test)
    socketio.emit('display_question', emit_data_to_test, namespace='/test_question')
    socketio.sleep(question.question_timeout)
    emit_data_to_test = { 'action': "end_game", 'leader': "leader"}
    logger.info("emit to '/test_question' namespace 'end_game' event with data %s", emit_data_to_test)
    socketio.emit('end_game', emit_data_to_test, namespace='/test_question')



@socketio.on('display_answer_question', namespace='/test')
def display_answer_question(game, answers, good_answer_button, buttons, players_name_list):
    logger.info("display_answer_question")
    session['status'] = "display_answer_question"
    question = game.question
    topic = "({}/{}) : {}".format(session['nb_questions']-len(game.questions), session['nb_questions'], question.topic)
    sound, media_type, media = get_medias(question.waiting_answer_media)
    game.set_state(GameState.ASK_QUESTION)
    emit_data_to_test = {
        'action': "display_answer_question",
        'b1': "ROUGE", buttons[0]: answers[0], buttons[1]: answers[1], buttons[2]: answers[2], buttons[3]: answers[3],
        'topic': topic, 'question': question.question,
        'sound': sound, 'media_type': media_type, 'media': media,
        'timeout': question.waiting_answer_timeout,
        'start_time': question.waiting_answer_start_time
    }
    logger.info("emit to '/test' namespace 'display_answer_question' event with data %s", emit_data_to_test)
    socketio.emit('display_answer_question', emit_data_to_test, namespace='/test')

    emit_data_to_buz = {
        'action': "next_question",
        'b1': question.question, buttons[0]: answers[0], buttons[1]: answers[1], buttons[2]: answers[2], buttons[3]: answers[3],
        'answer': good_answer_button,
        'timeout': question.waiting_answer_timeout*1000
    }
    logger.info("emit to '/buz' namespace 'my_response' event with data %s", emit_data_to_buz)
    socketio.emit('my_response', emit_data_to_buz, namespace='/buz')

    players = game.players
    for player_name in players:
        game.set_round_not_played(player_name)
    # socketio.sleep(question.waiting_answer_timeout)
    buzz_clear_timeout = countdown_thread(question.waiting_answer_timeout)



@socketio.on('test_display_answer_question', namespace='/test_question')
def test_display_answer_question(data):
    logger.info("test_display_answer_question")
    session['status'] = "display_answer_question"
    suite_file_name = data["suite_file_name"]
    question_nbr = int(data["question_nbr"])
    try:
        json_data = json.load(open(f"suites/{suite_file_name}.json", encoding='utf-8'))
    except Exception as e:
        error_msg = f"Error loading suite file 'suites/{suite_file_name}.json'"
        logger.error("%s: %s", error_msg, e)
        emit_data_to_test = {'error_msg': error_msg}
        logger.info("emit to '/test_question' namespace 'popup_error_msg' event with data %s", emit_data_to_test)
        socketio.emit('popup_error_msg', emit_data_to_test, namespace='/test_question')
        return
    from question import Question
    nb_questions = len(json_data["questions"])
    if question_nbr < -nb_questions or question_nbr > nb_questions or question_nbr == 0:
        error_msg = f"Question number '{question_nbr}' is out of range (1-{len(json_data['questions'])}) in suite file '{suite_file_name}.json'"
        logger.error("%s", error_msg)
        emit_data_to_test = {'error_msg': error_msg}
        logger.info("emit to '/test_question' namespace 'popup_error_msg' event with data %s", emit_data_to_test)
        socketio.emit('popup_error_msg', emit_data_to_test, namespace='/test_question')
        return
    question_index = question_nbr -1 if question_nbr > 0 else nb_questions + question_nbr
    question = Question(json_data["questions"][question_index], json_data["topic"])
    topic = f"({question_index+1}/{nb_questions}) : {question.topic}"
    sound, media_type, media = get_medias(question.waiting_answer_media)
    emit_data_to_test = {
        'action': "display_answer_question",
        'b1': "ROUGE", 'b2': question.wrong_answers[0], 'b3': question.wrong_answers[1], 'b4': question.wrong_answers[2], 'b5': question.good_answer,
        'topic': topic, 'question': question.question,
        'sound': sound, 'media_type': media_type, 'media': media,
        'timeout': question.waiting_answer_timeout,
        'start_time': question.waiting_answer_start_time
    }
    logger.info("emit to '/test_question' namespace 'display_answer_question' event with data %s", emit_data_to_test)
    socketio.emit('display_answer_question', emit_data_to_test, namespace='/test_question')
    socketio.sleep(question.waiting_answer_timeout)
    # buzz_clear_timeout = countdown_thread(question.waiting_answer_timeout)
    
    emit_data_to_test = { 'action': "end_game", 'leader': "leader"}
    logger.info("emit to '/test_question' namespace 'end_game' event with data %s", emit_data_to_test)
    socketio.emit('end_game', emit_data_to_test, namespace='/test_question')



@socketio.on('display_answer', namespace='/test')
def display_answer(game, answers, good_answer_question_index, buttons, good_answer_button):
    print("display_answer")
    logger.info("display_answer")
    session['status'] = "display_answer"
    question = game.question
    topic = "({}/{}) : {}".format(session['nb_questions']-len(game.questions), session['nb_questions'], question.topic)

    emit_data_to_buz = {
        'action': "clear_timeout",
        'b1': question.question, buttons[0]: answers[0], buttons[1]: answers[1], buttons[2]: answers[2], buttons[3]: answers[3]
    }
    logger.info("emit to '/buz' namespace 'my_response' event with data %s", emit_data_to_buz)
    socketio.emit('my_response', emit_data_to_buz, namespace='/buz')

    players = game.players
    players_that_not_play = ""
    for player_name in players:
        if not players[player_name].round_played:
            logger.info("Player %s has not play this round. Check his connection", player_name)
            game.increase_timeout(player_name)
            players_that_not_play += f"{player_name} "

        # game.set_round_not_played(player_name)
    if players_that_not_play != "":
        emit_data_to_test = {
            'name': players_that_not_play, 'time': 0,
            'media_type': '', 'media': '', 'sound': '',
            'players': [], 'comment': "DID NOT PLAY THIS ROUND"
        }
        logger.info("emit to '/test' namespace 'add_players_console' event with data %s", emit_data_to_test)
        socketio.emit('add_players_console', emit_data_to_test, namespace='/test')
    for player_name in game.removed_players:
        game.increase_timeout(player_name)
    players = game.players
    players_name = []
    players_score = []
    players_play_time = []
    for player_name in players:
        players_name.append(player_name)
        player_score = players[player_name].score
        players_score.append(player_score)
        player_play_time = players[player_name].play_time
        players_play_time.append("{0:.3f}".format(round(player_play_time,3)))

    
    ranking = game.set_ranking()
    emit_data_to_test = {'leaderboard_update': ranking}
    logger.info("emit to '/test' namespace 'update_players' event with data %s", emit_data_to_test)
    socketio.emit('update_players', emit_data_to_test, namespace='/test')

    sound, media_type, media = get_medias(question.answer_media)
    emit_data_to_test = {
        'action': "display_answer",
        'b1': "ROUGE", buttons[0]: answers[0], buttons[1]: answers[1], buttons[2]: answers[2], buttons[3]: answers[3],
        'topic': topic, 'question': question.question, 'answer': good_answer_button,
        'sound': sound, 'media_type': media_type, 'media': media,
        'timeout': question.answer_timeout, 'start_time': question.answer_start_time}
    logger.info("emit to '/test' namespace 'display_answer' event with data %s", emit_data_to_test)
    socketio.emit('display_answer', emit_data_to_test, namespace='/test')
    socketio.sleep(question.answer_timeout)
    # logger.info("\nemit enabled_next_question to test\n")
    # socketio.emit('enabled_next_question', {'action': "enabled_next_question"}, namespace='/test')
    logger.info("emit to '/buz' namespace 'deactiv_buttons' event")
    socketio.emit('my_response', {'action': "deactiv_buttons"}, namespace='/buz')

@socketio.on('test_display_answer', namespace='/test_question')
def test_display_answer(data):
    logger.info("test_display_answer")
    game = Game()
    game.add_player("player1")
    game.add_player("player2")
    game.add_player("player3")
    ranking = game.set_ranking()
    emit_data_to_test = {'leaderboard_update': ranking}
    logger.info("emit to '/test_question' namespace 'update_players' event with data %s", emit_data_to_test)
    socketio.emit('update_players', emit_data_to_test, namespace='/test_question')
    game.set_round_played("player1", 10)
    game.increase_score("player1")
    game.increase_time("player1", 10)
    game.set_round_not_played("player2")
    game.set_round_played("player3", 5)
    game.increase_score("player3")
    game.increase_time("player3", 5)
    session['status'] = "display_answer"
    suite_file_name = data["suite_file_name"]
    question_nbr = int(data["question_nbr"])
    try:
        json_data = json.load(open(f"suites/{suite_file_name}.json", encoding='utf-8'))
    except Exception as e:
        error_msg = f"Error loading suite file 'suites/{suite_file_name}.json'"
        logger.error("%s: %s", error_msg, e)
        emit_data_to_test = {'error_msg': error_msg}
        logger.info("emit to '/test_question' namespace 'popup_error_msg' event with data %s", emit_data_to_test)
        socketio.emit('popup_error_msg', emit_data_to_test, namespace='/test_question')
        return
    from question import Question
    nb_questions = len(json_data["questions"])
    if question_nbr < -nb_questions or question_nbr > nb_questions or question_nbr == 0:
        error_msg = f"Question number '{question_nbr}' is out of range (1-{len(json_data['questions'])}) in suite file '{suite_file_name}.json'"
        logger.error("%s", error_msg)
        emit_data_to_test = {'error_msg': error_msg}
        logger.info("emit to '/test_question' namespace 'popup_error_msg' event with data %s", emit_data_to_test)
        socketio.emit('popup_error_msg', emit_data_to_test, namespace='/test_question')
        return
    question_index = question_nbr -1 if question_nbr > 0 else nb_questions + question_nbr
    question = Question(json_data["questions"][question_index], json_data["topic"])
    game.question = question
    game.increase_timeout("player2")
    ranking = game.set_ranking()
    emit_data_to_test = {'leaderboard_update': ranking}
    logger.info("emit to '/test_question' namespace 'update_players' event with data %s", emit_data_to_test)
    socketio.emit('update_players', emit_data_to_test, namespace='/test_question')
    topic = f"({question_index+1}/{nb_questions}) : {question.topic}"
    sound, media_type, media = get_medias(question.answer_media)
    emit_data_to_test = {
        'action': "display_answer",
        'b1': "ROUGE", 'b2': question.wrong_answers[0], 'b3': question.wrong_answers[1], 'b4': question.wrong_answers[2], 'b5': question.good_answer,
        'topic': topic, 'question': question.question, 'answer': 'bouton5',
        'sound': sound, 'media_type': media_type, 'media': media,
        'timeout': question.answer_timeout, 'start_time': question.answer_start_time}
    logger.info("emit to '/test_question' namespace 'display_answer' event with data %s", emit_data_to_test)
    socketio.emit('display_answer', emit_data_to_test, namespace='/test_question')
    socketio.sleep(question.answer_timeout)
    emit_data_to_test = { 'action': "end_game", 'leader': "leader"}
    logger.info("emit to '/test_question' namespace 'end_game' event with data %s", emit_data_to_test)
    socketio.emit('end_game', emit_data_to_test, namespace='/test_question')


@socketio.on('display_winner', namespace='/test')
def display_winner(leader, top_score, play_time, players_name_list, players_score_list, players_play_time_list):
    global game
    global suites_list
    sound = "/static/sounds/correct_answer.wav"
    media_type = "image"
    media = "/static/images/winner.jpg"
    emit_data_to_test = {
        'action': "end_game", 'leader': leader,
        'names': players_name_list, 'scores': players_score_list, 'play_times': players_play_time_list,
        'sound': sound, 'media_type': media_type, 'media': media
    }
    logger.info("emit to '/test' namespace 'end_game' event with data %s", emit_data_to_test)
    socketio.emit('end_game', emit_data_to_test, namespace='/test')

    emit_data_to_buz = {'action': "end_game"}
    logger.info("emit to '/buz' namespace 'my_response' event with data %s", emit_data_to_buz)
    socketio.emit('my_response', emit_data_to_buz, namespace='/buz')

    logger.debug("Game reset")
    game.reset()
    suites_list = []
    socketio.sleep(10)

    emit_data_to_test = {'action': "new_game"}
    logger.info("emit to '/test' namespace 'new_game' event with data %s", emit_data_to_test)
    socketio.emit('new_game', emit_data_to_test, namespace='/test')


@socketio.on('new_game', namespace='/test')
def new_game():
    global game
    logger.info("new_game")
    game.questions = []
    game.state = GameState.NOT_STARTED
    game.round = 0
    game.letters_guessed = []
    game.phrase_misses = 0
    game.nb_suites_played = 0
    game.suite_index_to_choose = 0
    session['status'] = "deactiv_buttons"
    socketio.emit('my_response',
         {'action': "new_game"},
         namespace='/buz')


@socketio.on('deactiv_buttons', namespace='/test')
def deactiv_buttons():
    print("deactiv_buttons")
    session['status'] = "deactiv_buttons"
    socketio.emit('my_response',
         {'action': "deactiv_buttons"},
         namespace='/buz')


@socketio.on('add_player', namespace='/buz')
def add_player(message):
    global game
    message_items = ""
    for key, value in message.items():
        message_items = "{}, {} = {}".format(message_items, key, value)
    logger.info("Receive from '/buz' namespace 'add_player' event with data %s", message_items[1:])
    logger.info("Add player '%s' from '%s' generation in game", message['name'], message['generation'])
    res = game.add_player(message['name'], message['generation'])
    logger.debug("GAME is now:%s", game)
    logger.info("result: {}".format(res))
    if res == "ADDED":
        ranking = game.set_ranking()
        emit_data_to_test = {'name': message['name'], 'number': len(game.players), 'leaderboard_update': ranking}
        # emit_data_to_test = {'name': message['name']}
        logger.info("emit to '/test' namespace 'add_player' event with data %s", emit_data_to_test)
        socketio.emit('add_player', emit_data_to_test, namespace='/test')

@socketio.on('add_buzz_player', namespace='/test')
def add_buzz_player(message):
    global game
    message_items = ""
    for key, value in message.items():
        message_items = "{}, {} = {}".format(message_items, key, value)
    logger.info("Receive from '/test' namespace 'add_buzz_player' event with data %s", message_items[1:])
    logger.info("Add buzzer '%s' player '%s' from '%s' generation in game", message['buzz_nb'], message['name'], message['generation'])
    res = game.add_player(message['name'], message['generation'], buzzer=message['buzz_nb'])
    logger.debug("GAME is now:%s", game)
    logger.info("result: {}".format(res))
    if res == "ADDED":
        ranking = game.set_ranking()
        emit_data_to_test = {'name': message['name'], 'number': len(game.players), 'leaderboard_update': ranking}
        # emit_data_to_test = {'name': message['name']}
        logger.info("emit to '/test' namespace 'add_player' event with data %s", emit_data_to_test)
        socketio.emit('add_player', emit_data_to_test, namespace='/test')


@socketio.on('del_player', namespace='/test')
def del_player(message):
    message_items = ""
    logger.info("Receive from '/test' namespace 'del_player' event with data %s", message_items[1:])
    logger.info("Del player {} in game".format(message['name']))
    res, index = game.remove_player(message['name'])
    logger.info("result: %s, index: %s", res, index)
    if res == "REMOVED":
        ranking = game.set_ranking()
        emit_data_to_test = {'name': message['name'], 'index': index, 'leaderboard_update': ranking}
        logger.info("emit to 'test' namespace 'del_player' event with data %s", emit_data_to_test)
        socketio.emit('del_player', emit_data_to_test, namespace='/test')


@socketio.on('bouton_click_event', namespace='/buz')
def bouton_click_event(message):
    global nb_times_color_choosed
    global game
    game_state = game.state
    message_items = ""
    for key, value in message.items():
        message_items = "{}, {} = {}".format(message_items, key, value)
    logger.debug("Receive from '/buz' namespace 'bouton_click_event' event with data %s", message_items[1:])
    if game_state == GameState.WAITING_PLAYERS :
        try:
            media_type = "image"
            media = "/static/images/are_you_ready.jpg"
            game.set_ready_for_round(message['name'])
            logger.info("Player %s is ready for round", message['name'])
            logger.debug("GAME is %s:", game)
            emit_data_to_test = {
                'name': message['name'], 'time': 0,
                'media_type': media_type, 'media': media, 'sound': '',
                'players': game.player_names, 'comment': "READY TO PLAY"
            }
            logger.info("emit to '/test' namespace 'add_players_console' event with data %s", emit_data_to_test)
            socketio.emit('add_players_console',
                        emit_data_to_test,
                        namespace='/test')
        except KeyError:
            logger.info("Player {} not in game".format(message['name']))
    if game_state == GameState.ASK_QUESTION :
        answer_button = game.answer_button
        emit_data_to_test = {
            'name': message['name'], 'time': message['time'],
            'media_type': '', 'media': '', 'sound': '',
            'players': []
        }
        logger.info("emit to '/test' namespace 'add_players_console' event with data %s", emit_data_to_test)
        socketio.emit('add_players_console', emit_data_to_test, namespace='/test')
        if message['data'] == answer_button:
            if game.is_score_per_time_range:
                game.increase_score(message['name'], 0, message['time'])
            else:
                game.increase_score(message['name'])
            game.increase_time(message['name'], message['time'])
            game.set_round_played(message['name'])
        else:
            game.increase_timeout(message['name'])
    if game.state == GameState.CHOOSE_TOPIC:
        player_name = message['name']
        # play_time = message['time']
        answer_button = message['data']
        if not game.is_round_played_by_player(player_name):
            try:
                game.set_round_played(player_name)
                emit_data_to_test = {'name': player_name, 'button': answer_button}
                logger.info("emit to '/test' namespace 'player_choose_category' event with data %s", emit_data_to_test)
                socketio.emit('player_choose_category', emit_data_to_test, namespace='/test')
            except KeyError:
                print("Player {} not in game".format(player_name))
                logger.info("Player {} not in game".format(player_name))
                answer_button = ""
            if answer_button == "bouton2":
                nb_times_color_choosed[0] = nb_times_color_choosed[0] + 1
            if answer_button == "bouton3":
                nb_times_color_choosed[1] = nb_times_color_choosed[1] + 1
            if answer_button == "bouton4":
                nb_times_color_choosed[2] = nb_times_color_choosed[2] + 1
            if answer_button == "bouton5":
                nb_times_color_choosed[3] = nb_times_color_choosed[3] + 1
            logger.debug("Nb times color choosed list is %s", nb_times_color_choosed)
        else:
            logger.debug("%s has already choose a topic", player_name)

@socketio.on('gamepad_press_button', namespace='/test')
def gamepad_press_button_event(message):
    global nb_times_color_choosed
    global game
    game_state = game.state
    message_items = ""
    for key, value in message.items():
        message_items = "{}, {} = {}".format(message_items, key, value)
    logger.debug(\
        "Receive from '/test' namespace 'gamepad_press_button' event with data %s for game state %s", \
        message_items[1:], game_state)
    button_idx = message["button_index"]
    button_name = "bouton0"
    buzzer_number = 0
    if button_idx in [0, 5, 10, 15]: # red
        button_name = "bouton1"
        buzzer_number = button_idx // 5 + 1
        if game_state != GameState.WAITING_PLAYERS:
            return
    if button_idx in [1, 2, 3, 4]:
        buzzer_number = 1
    elif button_idx in [6, 7, 8, 9]:
        buzzer_number = 2
    elif button_idx in [11, 12, 13, 14]:
        buzzer_number = 3
    elif button_idx in [16, 17, 18, 19]:
        buzzer_number = 4
    else:
        if buzzer_number == 0:
            return
    if button_idx in [4, 9, 14, 19]: # Blue
        button_name = "bouton2"
    elif button_idx in [3, 8, 13, 18]: # Orange
        button_name = "bouton3"
    elif button_idx in [2, 7, 12, 17]: # green
        button_name = "bouton4"
    elif button_idx in [1, 6, 11, 16]: # yellow
        button_name = "bouton5"
    else:
        if button_name == "bouton0":
            return
    buzzer_player_name = game.get_player_name_from_buzz_number(buzzer_number)
    if game_state == GameState.WAITING_PLAYERS :
        try:
            media_type = "image"
            media = "/static/images/are_you_ready.jpg"
            game.set_ready_for_round(buzzer_player_name)
            logger.info("Player %s is ready for round", buzzer_player_name)
            logger.debug("GAME is %s:", game)
            emit_data_to_test = {
                'name': buzzer_player_name, 'time': 0,
                'media_type': media_type, 'media': media, 'sound': '',
                'players': game.player_names, 'comment': "READY TO PLAY"
            }
            logger.info("emit to '/test' namespace 'add_players_console' event with data %s", emit_data_to_test)
            socketio.emit('add_players_console',
                        emit_data_to_test,
                        namespace='/test')
        except KeyError:
            logger.info("Player {} not in game".format(buzzer_player_name))
    if game_state == GameState.ASK_QUESTION :
        answer_button = game.answer_button
        emit_data_to_test = {
            'name': buzzer_player_name, 'time': message['time'],
            'media_type': '', 'media': '', 'sound': '',
            'players': []
        }
        logger.info("emit to '/test' namespace 'add_players_console' event with data %s", emit_data_to_test)
        socketio.emit('add_players_console', emit_data_to_test, namespace='/test')
        if button_name == answer_button:
            if game.is_score_per_time_range:
                game.increase_score(buzzer_player_name, 0, message['time'])
            else:
                game.increase_score(buzzer_player_name)
            game.increase_time(buzzer_player_name, message['time'])
            game.set_round_played(buzzer_player_name)
        else:
            game.increase_timeout(buzzer_player_name)
    if game.state == GameState.CHOOSE_TOPIC:
        player_name = buzzer_player_name
        # play_time = message['time']
        answer_button = button_name
        if not game.is_round_played_by_player(player_name):
            try:
                game.set_round_played(player_name)
                emit_data_to_test = {'name': player_name, 'button': answer_button}
                logger.info("emit to '/test' namespace 'player_choose_category' event with data %s", emit_data_to_test)
                socketio.emit('player_choose_category', emit_data_to_test, namespace='/test')
            except KeyError:
                print("Player {} not in game".format(player_name))
                logger.info("Player {} not in game".format(player_name))
                answer_button = ""
            if answer_button == "bouton2":
                nb_times_color_choosed[0] = nb_times_color_choosed[0] + 1
            if answer_button == "bouton3":
                nb_times_color_choosed[1] = nb_times_color_choosed[1] + 1
            if answer_button == "bouton4":
                nb_times_color_choosed[2] = nb_times_color_choosed[2] + 1
            if answer_button == "bouton5":
                nb_times_color_choosed[3] = nb_times_color_choosed[3] + 1
            logger.debug("Nb times color choosed list is %s", nb_times_color_choosed)
        else:
            logger.debug("%s has already choose a topic", player_name)

@socketio.on('gamepad_press', namespace='/test')
def gamepad_press_event(message):
    gamepad_id = message["gamepad_id"]
    if gamepad_id != "Buzz (Vendor: 054c Product: 1000)":
        return
    button_index = message["button_index"]
    if button_index == 0:
        emit_data_to_test = {"buzz_nb": 1}
        logger.info("emit to '/test' namespace 'add_buzz_player' event with data %s", emit_data_to_test)
        socketio.emit('add_buzz_player', emit_data_to_test, namespace='/test')
    if button_index == 5:
        emit_data_to_test = {"buzz_nb": 2}
        logger.info("emit to '/test' namespace 'add_buzz_player' event with data %s", emit_data_to_test)
        socketio.emit('add_buzz_player', emit_data_to_test, namespace='/test')
    if button_index == 10:
        emit_data_to_test = {"buzz_nb": 3}
        logger.info("emit to '/test' namespace 'add_buzz_player' event with data %s", emit_data_to_test)
        socketio.emit('add_buzz_player', emit_data_to_test, namespace='/test')
    if button_index == 15:
        emit_data_to_test = {"buzz_nb": 4}
        logger.info("emit to '/test' namespace 'add_buzz_player' event with data %s", emit_data_to_test)
        socketio.emit('add_buzz_player', emit_data_to_test, namespace='/test')

if __name__ == '__main__':
    # Initialize parser
    description = "Web Quiz"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-s", "--suites", help = "Set Suites path")
    # Read arguments from command line
    args = parser.parse_args()
    suites_path = "suites"
    if args.suites:
        suites_path = args.suites
    hostname = socket.gethostname()
    # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # s.connect(("8.8.8.8", 80))
    # hostname = s.getsockname()[0]
    # s.close()
    host_ip = socket.gethostbyname(hostname)
    qr = qrcode.make(f"http://{host_ip}:5000/web_quizz_login")
    qr.save("static/qrcode.png")
    logger.info('launch http://%s:5000/web_quizz', hostname)
    logger.info('launch http://%s:5000/web_quizz_login', hostname)
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
    # socketio.run(app, host=hostname, port=5000, debug=True)
    # socketio.run(app, host="127.0.0.1", port=5000, debug=True)

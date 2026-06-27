#!/usr/bin/env python
import os
import socket
import re
import random
import qrcode
import logging
import logging.config

logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

# create logger
logger = logging.getLogger('app')
# if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
logging.config.fileConfig('logging.conf')

from threading import Lock
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from tinydb import TinyDB, Query
from game import Game, GameState
import random

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
# socketio = SocketIO(app, cors_allowed_origins="*")
game = Game()
question_format = ""
# game.add_player("toto")
thread = None
thread_lock = Lock()


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


@app.route('/blind_test_admin_ui_yt')
def blind_test_admin_ui_yt():
    return render_template('blind_test_admin_ui_yt.html', async_mode=socketio.async_mode)

@app.route('/blind_test_ui_yt')
def blind_test_ui_yt():
    return render_template('blind_test_ui_yt.html', async_mode=socketio.async_mode)

@app.route('/blind_test_login', methods = ['GET', 'POST'])
def blind_test_login():
   if request.method == 'POST':
      return render_template('blind_test_buzzer.html', async_mode=socketio.async_mode)
   return render_template('blind_test_login.html', async_mode=socketio.async_mode)

@app.route('/blind_test_buzzer')
def blind_test_buzzer():
    return render_template('blind_test_buzzer.html', async_mode=socketio.async_mode)

@socketio.on('get_players', namespace='/blind_test_admin_ui_yt')
def get_players():
    logger.info("Receive get_players event from blind_test_admin_ui_yt")
    for player_name, player in game.players.items():
        logger.info("emit add_player event to blind_test_admin_ui_yt with player name {} and score {} points".format(player_name, player.score))
        socketio.emit('add_player',
                      {'player_name': player_name, 'player_score': player.score},
                      namespace='/blind_test_admin_ui_yt')
    
@socketio.on('get_players', namespace='/blind_test_ui_yt')
def get_players():
    logger.info("Receive get_players event from blind_test_ui_yt")
    for player_name, player in game.players.items():
        logger.info("emit add_player event to blind_test_ui_yt with player name {} and score {} points".format(player_name, player.score))
        socketio.emit('add_player',
                      {'player_name': player_name, 'player_score': player.score},
                      namespace='/blind_test_ui_yt')

@socketio.on('update_score_player', namespace='/blind_test_admin_ui_yt')
def update_score_player(message):
    logger.info("Receive update_score_player event from blind_test_admin_ui_yt with player name '{}' and {} points to update from score".format(message['player_name'], message['update_score']))
    logger.info("Add '{}' increment to '{}' player in game".format(message['update_score'], message['player_name']))
    increment = int(message['update_score'])
    game.increase_score(message['player_name'], increment)
    new_score = game.get_player_score(message['player_name'])
    logger.info("emit 'update_score_player' event to 'blind_test_admin_ui_yt' namespace with player name {} and score {} points ".format(message['player_name'], new_score))
    socketio.emit('update_score_player',
                  {'player_name': message['player_name'], 'score': new_score},
                  namespace='/blind_test_admin_ui_yt')
    logger.info("emit 'update_score_player' event to 'blind_test_ui_yt' namespace with player name {} and score {} points ".format(message['player_name'], new_score))
    socketio.emit('update_score_player',
                  {'player_name': message['player_name'], 'score': new_score},
                  namespace='/blind_test_ui_yt')

@socketio.on('del_player', namespace='/blind_test_admin_ui_yt')
def del_player(message):
    logger.info("Receive del_player event from blind_test_admin_ui_yt with player name {}".format(message['player_name']))
    logger.info("Del player {} in game".format(message['player_name']))
    res = game.remove_player(message['player_name'])
    logger.info("result: {}".format(res))
    if res == "REMOVED":
        logger.info("emit 'del_player' event to 'blind_test_admin_ui_yt' namespace with player name {}".format(message['player_name']))
        socketio.emit('del_player',
                      {'player_name': message['player_name']},
                      namespace='/blind_test_admin_ui_yt')
        logger.info("emit 'del_player' event to 'blind_test_ui_yt' namespace with player name {}".format(message['player_name']))
        socketio.emit('del_player',
                      {'player_name': message['player_name']},
                      namespace='/blind_test_ui_yt')

@socketio.on('new_question', namespace='/blind_test_admin_ui_yt')
def new_question(message):
    logger.info("Receive new_question event from blind_test_admin_ui_yt")
    question_format = message['format']
    question_value = message['value']
    # logger.debug("question_value is:%s", question_value)
    answer_str = ""
    youtube_answer_id = ""
    start_time = "0"
    if question_format == "youtube":
        # db = TinyDB('db.json', indent=4)
        db = TinyDB('database/default.json', indent=4)
        table = db.table('yt')
        song = Query()
        result = table.search(song.id == question_value)
        logger.info("Result: %s with %s type", result, type(result))
        if result:
            for key, value in result[0].items():
                # logger.debug("key: %s, value: %s", key, value)
                if key not in ['start_time']:
                    answer_str = f'{answer_str}{key}="{value}" '
                if key == 'start_time':
                    start_time = value
        youtube_answer_id = question_value
    elif question_format == "youtube_suite":
        db_name = f"database/{message['db']}.json"
        # db = TinyDB('db.json', indent=4)
        db = TinyDB(db_name, indent=4)
        table = db.table('yt')
        all_yt_fields = table.all()
        # logger.debug("all_yt_fields is:\n%s", all_yt_fields)
        random.shuffle(all_yt_fields)
        # logger.debug("Random all_yt_fields is:\n%s", all_yt_fields)
        youtube_suite = all_yt_fields[:int(question_value)]
        # logger.debug("youtube_suite is:\n%s", youtube_suite)
        game.question = youtube_suite.pop()
        # logger.debug("Game question is: %s with type %s", game.question, type(game.question))
        for key, value in game.question.items():
            # logger.debug("key: %s, value: %s", key, value)
            if key not in ['start_time']:
                answer_str = f'{answer_str}{key}="{value}" '
        youtube_answer_id = game.question['id']
        message['topic'] = game.question.get('topic', "Donnez l'artiste de la chanson")
        start_time = game.question.get('start_time', "0")
        # logger.debug("Set Youtube questions left: %s", youtube_suite)
        game.set_youtube_questions(youtube_suite)
    else:
        answer_str = question_value
    emit_data_to_namespace_blind_test_admin_ui_yt = {'answer': answer_str, 'youtube_answer_id': youtube_answer_id}
    logger.info("emit to '/blind_test_admin_ui_yt' namespace 'set_answer' event with data %s", emit_data_to_namespace_blind_test_admin_ui_yt)
    socketio.emit('set_answer', emit_data_to_namespace_blind_test_admin_ui_yt, namespace='/blind_test_admin_ui_yt')
    emit_set_answer_to_namespace_blind_test_ui_yt = {'youtube_answer_id': youtube_answer_id, 'question_type': question_format}
    logger.info("emit to '/blind_test_ui_yt' namespace 'set_answer' event with data %s", emit_set_answer_to_namespace_blind_test_ui_yt)
    socketio.emit('set_answer', emit_set_answer_to_namespace_blind_test_ui_yt, namespace='/blind_test_ui_yt')
    game.set_state(GameState.WAITING_PLAYERS)
    game.set_players_round_not_played()
    is_timeout = False
    is_players_report_presence = message['is_players_report_presence']
    # logger.debug("is_players_report_presence %s with type %s", is_players_report_presence, type(is_players_report_presence))
    if (not is_players_report_presence):
        is_timeout = True
        game.is_players_report_presence = False
        for player_name in game.players:
            game.set_ready_for_round(player_name)
    else:
        game.is_players_report_presence = True
    while not is_timeout:
        players = game.players
        waiting_players = ""
        for player_name in players:
            if not game.players[player_name].round_ready:
                waiting_players = "{} {}".format(waiting_players, player_name)
            game.set_not_ready_for_round(player_name)
        socketio.emit('add_players_console',
                      {'name': "GAME", 'time': 0, 'comment': " WAITING FOR PLAYERS{}".format(waiting_players)},
                      namespace='/blind_test_admin_ui_yt')
        emit_data_to_namespace_blind_test_buz = {'action': "player_ready", 'b1': "PRET A JOUER", 'b2': "", 'b3': "", 'b4': "", 'b5': ""}
        logger.info("emit to '/blind_test_buz' namespace 'ready_to_play' event with data %s", emit_data_to_namespace_blind_test_buz)
        socketio.emit('ready_to_play', emit_data_to_namespace_blind_test_buz, namespace='/blind_test_buz')
        emit_data_to_namespace_blind_test_ui_yt = {'display': "is_players_ready"}
        logger.info("emit to '/blind_test_ui_yt' namespace 'is_players_ready' event with data %s", emit_data_to_namespace_blind_test_ui_yt)
        socketio.emit('is_players_ready', emit_data_to_namespace_blind_test_ui_yt, namespace='/blind_test_ui_yt')
        is_timeout = countdown_ready_thread(10)

    game.set_state(GameState.DISPLAY_QUESTION)
    logger.info("All players are ready to play question")
    emit_data_to_namespace_blind_test_admin_ui_yt = {'start_time': start_time}
    logger.info("emit to '/blind_test_admin_ui_yt' namespace 'play_question' event with data %s", emit_data_to_namespace_blind_test_admin_ui_yt)
    socketio.emit('play_question', emit_data_to_namespace_blind_test_admin_ui_yt, namespace='/blind_test_admin_ui_yt')
    player_name_list = game.get_player_name_list_not_played()
    emit_data_to_namespace_blind_test_buz = {'action': "play_blind_test", 'b1': "REPONDRE", 'b2': "", 'b3': "", 'b4': "", 'b5': "", 'player_name_list': player_name_list}
    logger.info("emit to '/blind_test_buz' namespace 'play_blind_test' event with data %s", emit_data_to_namespace_blind_test_buz)
    socketio.emit('play_blind_test', emit_data_to_namespace_blind_test_buz, namespace='/blind_test_buz')
    emit_data_to_namespace_blind_test_ui_yt = {'display': "waiting_players_answer", 'topic': message['topic'], 'player_name_list': player_name_list}
    logger.info("emit to '/blind_test_ui_yt' namespace 'waiting_players_answer' event with data %s", emit_data_to_namespace_blind_test_ui_yt)
    socketio.emit('waiting_players_answer', emit_data_to_namespace_blind_test_ui_yt, namespace='/blind_test_ui_yt')
    emit_play_question_to_namespace_blind_test_ui_yt = {'youtube_id': youtube_answer_id, 'start_time': start_time}
    logger.info("emit to '/blind_test_ui_yt' namespace 'play_question' event with data %s", emit_play_question_to_namespace_blind_test_ui_yt)
    socketio.emit('play_question', emit_play_question_to_namespace_blind_test_ui_yt, namespace='/blind_test_ui_yt')

@socketio.on('good_answer', namespace='/blind_test_admin_ui_yt')
def good_answer(message):
    logger.info("Receive good_answer event from blind_test_admin_ui_yt from player {}".format(message['player_name']))
    game.increase_score(message['player_name'], 10)
    emit_data_to_namespace_blind_test_admin_ui_yt = {'enable_stop_question_button': True}
    # logger.info("Game questions number = %s", len(game.questions))
    if game.is_next_question():
        answer_str = ""
        youtube_answer_id = ""
        game.get_next_question()
        result = game.question
        # logger.debug("New Game question is: %s with type %s", result, type(result))
        for key, value in result.items():
            # logger.debug("key: %s, value: %s", key, value)
            answer_str = f'{answer_str}{key}="{value}" '
        youtube_answer_id = result['id']
        emit_data_to_namespace_blind_test_admin_ui_yt["enable_next_question_button"] = True
        emit_data_to_namespace_blind_test_admin_ui_yt["answer"] = answer_str
        emit_data_to_namespace_blind_test_admin_ui_yt["youtube_answer_id"] = youtube_answer_id
    logger.info("emit to '/blind_test_ui_yt' namespace 'good_answer' event")
    socketio.emit('good_answer', {}, namespace='/blind_test_ui_yt')
    logger.info("emit to '/blind_test_admin_ui_yt' namespace 'stop_blind_test' event with data %s", emit_data_to_namespace_blind_test_admin_ui_yt)
    socketio.emit('stop_blind_test', emit_data_to_namespace_blind_test_admin_ui_yt, namespace='/blind_test_admin_ui_yt')
    new_score = game.get_player_score(message['player_name'])
    logger.info("emit 'update_score_player' event to 'blind_test_admin_ui_yt' namespace with player name {} and score {} points ".format(message['player_name'], new_score))
    socketio.emit('update_score_player',
                  {'player_name': message['player_name'], 'score': new_score},
                  namespace='/blind_test_admin_ui_yt')
    logger.info("emit 'update_score_player' event to 'blind_test_ui_yt' namespace with player name {} and score {} points ".format(message['player_name'], new_score))
    socketio.emit('update_score_player',
                  {'player_name': message['player_name'], 'score': new_score},
                  namespace='/blind_test_ui_yt')
    logger.info("emit 'resume_blind_test' event to 'blind_test_ui_yt'")
    socketio.emit('resume_blind_test', {}, namespace='/blind_test_ui_yt')
    logger.info("emit end_game to blind_test_buz with action 'end_game'")
    socketio.emit('end_game',
                  {'action': "end_game"},
                  namespace='/blind_test_buz')
    game.set_players_round_not_played()
    # logger.info("Game questions number left = %s", len(game.questions))

@socketio.on('wrong_answer', namespace='/blind_test_admin_ui_yt')
def wrong_answer(message):
    message_items = ""
    for key, value in message.items():
        message_items = f"{message_items}, {key} = {value}"
    logger.info("Receive 'wrong_answer' event from '/blind_test_admin_ui_yt' with namespace with message data %s", message_items[1:])
    player_name_list = game.get_player_name_list_not_played()
    logger.info("emit to '/blind_test_ui_yt' namespace 'wrong_answer' event")
    socketio.emit('wrong_answer', {}, namespace='/blind_test_ui_yt')
    emit_data_to_namespace_blind_test_admin_ui_yt = {}
    logger.info("emit to '/blind_test_admin_ui_yt' namespace 'continue_blind_test' event with data %s", emit_data_to_namespace_blind_test_admin_ui_yt)
    socketio.emit('continue_blind_test', emit_data_to_namespace_blind_test_admin_ui_yt, namespace='/blind_test_admin_ui_yt')
    if player_name_list != []:
        emit_data_to_namespace_blind_test_buz = {'action': "play_blind_test", 'b1': "REPONDRE", 'b2': "", 'b3': "", 'b4': "", 'b5': "", 'player_name_list': player_name_list}
        logger.info("emit to '/blind_test_buz' namespace 'play_blind_test' event with data %s", emit_data_to_namespace_blind_test_buz)
        socketio.emit('play_blind_test', emit_data_to_namespace_blind_test_buz, namespace='/blind_test_buz')
    emit_data_to_namespace_blind_test_ui_yt = {'display': "waiting_players_answer", 'player_name_list': player_name_list}
    logger.info("emit to '/blind_test_ui_yt' namespace 'waiting_players_answer' event with data %s", emit_data_to_namespace_blind_test_ui_yt)
    socketio.emit('waiting_players_answer', emit_data_to_namespace_blind_test_ui_yt, namespace='/blind_test_ui_yt')
    logger.info("emit 'resume_blind_test' event to 'blind_test_ui_yt'")
    socketio.emit('resume_blind_test', {}, namespace='/blind_test_ui_yt')

@socketio.on('pause_question', namespace='/blind_test_admin_ui_yt')
def pause_question():
    logger.info("Receive 'pause_question' event from '/blind_test_admin_ui_yt' namespace")
    emit_data_to_namespace_blind_test_ui_yt = {'status': "GAME PAUSED"}
    logger.info("emit to '/blind_test_ui_yt' namespace 'game_status' event with data %s", emit_data_to_namespace_blind_test_ui_yt)
    socketio.emit('game_status', emit_data_to_namespace_blind_test_ui_yt, namespace='/blind_test_ui_yt')
    player_name_list = game.get_player_name_list_not_played()
    logger.info("emit 'pause_blind_test' event to 'blind_test_ui_yt'")
    socketio.emit('pause_blind_test', {}, namespace='/blind_test_ui_yt')
    emit_data_to_namespace_blind_test_buz = {'action': "pause_blind_test", 'b1': "PAUSE", 'b2': "", 'b3': "", 'b4': "", 'b5': "", 'player_name_list': player_name_list}
    logger.info("emit to '/blind_test_buz' namespace 'pause_blind_test' event with data %s", emit_data_to_namespace_blind_test_buz)
    socketio.emit('pause_blind_test', emit_data_to_namespace_blind_test_buz, namespace='/blind_test_buz')

@socketio.on('reprise_question', namespace='/blind_test_admin_ui_yt')
def reprise_question():
    logger.info("Receive 'reprise_question' event from '/blind_test_admin_ui_yt' namespace")
    emit_data_to_namespace_blind_test_ui_yt = {'status': "GAME RESUMED"}
    logger.info("emit to '/blind_test_ui_yt' namespace 'game_status' event with data %s", emit_data_to_namespace_blind_test_ui_yt)
    socketio.emit('game_status', emit_data_to_namespace_blind_test_ui_yt, namespace='/blind_test_ui_yt')
    logger.info("emit 'resume_blind_test' event to 'blind_test_ui_yt'")
    socketio.emit('resume_blind_test', {}, namespace='/blind_test_ui_yt')
    player_name_list = game.get_player_name_list_not_played()
    emit_data_to_namespace_blind_test_buz = {'action': "play_blind_test", 'b1': "REPONDRE", 'b2': "", 'b3': "", 'b4': "", 'b5': "", 'player_name_list': player_name_list}
    logger.info("emit to '/blind_test_buz' namespace 'play_blind_test' event with data %s", emit_data_to_namespace_blind_test_buz)
    socketio.emit('play_blind_test', emit_data_to_namespace_blind_test_buz, namespace='/blind_test_buz')

@socketio.on('next_question', namespace='/blind_test_admin_ui_yt')
def next_question():
    logger.info("Receive next_question event from blind_test_admin_ui_yt")
    emit_data_to_namespace_blind_test_admin_ui_yt = {'enable_stop_question_button': True}
    answer_str = ""
    youtube_answer_id = ""
    result = []
    # logger.info("Game questions number = %s", len(game.questions))
    if game.is_next_question():
        # logger.info("Get Next questions")
        game.set_next_question()
        result = game.question
        emit_data_to_namespace_blind_test_admin_ui_yt["enable_next_question_button"] = True
    else:
        emit_data_to_namespace_blind_test_admin_ui_yt["enable_next_question_button"] = False
        game.question = None
    # logger.debug("result is: %s with type %s", result, type(result))
    if not result:
        stop_question()
        return
    for key, value in result.items():
        # logger.debug("key: %s, value: %s", key, value)
        answer_str = f'{answer_str}{key}="{value}" '
    youtube_answer_id = result['id']
    topic = result.get('topic', "Donnez l'artiste de la chanson")
    start_time = result.get('start_time', "0")
    emit_data_to_namespace_blind_test_admin_ui_yt["answer"] = answer_str
    emit_data_to_namespace_blind_test_admin_ui_yt["youtube_answer_id"] = youtube_answer_id

    logger.info("emit to '/blind_test_admin_ui_yt' namespace 'set_answer' event with data %s", emit_data_to_namespace_blind_test_admin_ui_yt)
    socketio.emit('set_answer', emit_data_to_namespace_blind_test_admin_ui_yt, namespace='/blind_test_admin_ui_yt')
    emit_set_answer_to_namespace_blind_test_ui_yt = {'youtube_answer_id': youtube_answer_id, 'question_type': "youtube_suite"}
    logger.info("emit to '/blind_test_ui_yt' namespace 'set_answer' event with data %s", emit_set_answer_to_namespace_blind_test_ui_yt)
    socketio.emit('set_answer', emit_set_answer_to_namespace_blind_test_ui_yt, namespace='/blind_test_ui_yt')
    game.set_state(GameState.WAITING_PLAYERS)
    game.set_players_round_not_played()
    is_timeout = False
    is_players_report_presence = game.is_players_report_presence
    # logger.debug("is_players_report_presence %s with type %s", is_players_report_presence, type(is_players_report_presence))
    if (not is_players_report_presence):
        is_timeout = True
        for player_name in game.players:
            game.set_ready_for_round(player_name)
    while not is_timeout:
        players = game.players
        waiting_players = ""
        for player_name in players:
            if not game.players[player_name].round_ready:
                waiting_players = "{} {}".format(waiting_players, player_name)
            game.set_not_ready_for_round(player_name)
        socketio.emit('add_players_console',
                      {'name': "GAME", 'time': 0, 'comment': " WAITING FOR PLAYERS{}".format(waiting_players)},
                      namespace='/blind_test_admin_ui_yt')
        emit_data_to_namespace_blind_test_buz = {'action': "player_ready", 'b1': "PRET A JOUER", 'b2': "", 'b3': "", 'b4': "", 'b5': ""}
        logger.info("emit to '/blind_test_buz' namespace 'ready_to_play' event with data %s", emit_data_to_namespace_blind_test_buz)
        socketio.emit('ready_to_play', emit_data_to_namespace_blind_test_buz, namespace='/blind_test_buz')
        emit_data_to_namespace_blind_test_ui_yt = {'display': "is_players_ready"}
        logger.info("emit to '/blind_test_ui_yt' namespace 'is_players_ready' event with data %s", emit_data_to_namespace_blind_test_ui_yt)
        socketio.emit('is_players_ready', emit_data_to_namespace_blind_test_ui_yt, namespace='/blind_test_ui_yt')
        is_timeout = countdown_ready_thread(10)

    game.set_state(GameState.DISPLAY_QUESTION)
    logger.info("All players are ready to play question")
    emit_data_to_namespace_blind_test_admin_ui_yt = {"start_time": start_time}
    logger.info("emit to '/blind_test_admin_ui_yt' namespace 'play_question' event with data %s", emit_data_to_namespace_blind_test_admin_ui_yt)
    socketio.emit('play_question', emit_data_to_namespace_blind_test_admin_ui_yt, namespace='/blind_test_admin_ui_yt')
    emit_play_question_to_namespace_blind_test_ui_yt = {"question_type": "youtube_suite", 'youtube_id': youtube_answer_id, 'start_time': start_time}
    logger.info("emit to '/blind_test_ui_yt' namespace 'play_question' event with data %s", emit_play_question_to_namespace_blind_test_ui_yt)
    socketio.emit('play_question', emit_play_question_to_namespace_blind_test_ui_yt, namespace='/blind_test_ui_yt')
    player_name_list = game.get_player_name_list_not_played()
    emit_data_to_namespace_blind_test_buz = {'action': "play_blind_test", 'b1': "REPONDRE", 'b2': "", 'b3': "", 'b4': "", 'b5': "", 'player_name_list': player_name_list}
    logger.info("emit to '/blind_test_buz' namespace 'play_blind_test' event with data %s", emit_data_to_namespace_blind_test_buz)
    socketio.emit('play_blind_test', emit_data_to_namespace_blind_test_buz, namespace='/blind_test_buz')
    emit_data_to_namespace_blind_test_ui_yt = {'display': "waiting_players_answer", 'topic': topic, 'player_name_list': player_name_list}
    logger.info("emit to '/blind_test_ui_yt' namespace 'waiting_players_answer' event with data %s", emit_data_to_namespace_blind_test_ui_yt)
    socketio.emit('waiting_players_answer', emit_data_to_namespace_blind_test_ui_yt, namespace='/blind_test_ui_yt')

@socketio.on('stop_question', namespace='/blind_test_admin_ui_yt')
def stop_question():
    logger.info("Receive 'stop_question' event from '/blind_test_admin_ui_yt' namespace")
    logger.info("emit 'stop_blind_test' event to 'blind_test_admin_ui_yt'")
    socketio.emit('stop_blind_test',
                  {},
                  namespace='/blind_test_admin_ui_yt')
    game.set_players_round_not_played()
    logger.info("emit end_game event to blind_test_buz with action 'end_game'")
    socketio.emit('end_game',
                  {'action': "end_game"},
                  namespace='/blind_test_buz')
    emit_data_to_namespace_blind_test_ui_yt = {}
    logger.info("emit to '/blind_test_ui_yt' namespace 'end_game' event with data %s", emit_data_to_namespace_blind_test_ui_yt)
    socketio.emit('end_game', emit_data_to_namespace_blind_test_ui_yt, namespace='/blind_test_ui_yt')

@socketio.on('allow_answer', namespace='/blind_test_admin_ui_yt')
def allow_answer():
    logger.info("Receive allow_answer event from blind_test_admin_ui_yt")
    game.set_players_round_not_played()
    player_name_list = game.get_player_name_list_not_played()
    logger.info("emit play_blind_test to blind_test_buz with action 'player_ready' b1=REPONDRE b2=&nbsp; b3=&nbsp; b4=&nbsp; b5=&nbsp; and player name list {}".format(player_name_list))
    socketio.emit('play_blind_test',
                  {'action': "play_blind_test", 'b1': "REPONDRE", 'b2': "", 'b3': "", 'b4': "", 'b5': "", 'player_name_list': player_name_list},
                  namespace='/blind_test_buz')
    emit_data_to_namespace_blind_test_ui_yt = {'display': "waiting_players_answer", 'player_name_list': player_name_list}
    logger.info("emit to '/blind_test_ui_yt' namespace 'waiting_players_answer' event with data %s", emit_data_to_namespace_blind_test_ui_yt)
    socketio.emit('waiting_players_answer', emit_data_to_namespace_blind_test_ui_yt, namespace='/blind_test_ui_yt')

@socketio.on('set_players_ready', namespace='/blind_test_admin_ui_yt')
def set_players_ready():
    logger.info("Receive 'set_players_ready' event from '/blind_test_admin_ui_yt' namespace")
    for player_name in game.players:
        game.set_ready_for_round(player_name)
    player_name_list = game.get_player_name_list_not_played()
    emit_data_to_namespace_blind_test_ui_yt = {'display': "waiting_players_answer", 'player_name_list': player_name_list}
    logger.info("emit to '/blind_test_ui_yt' namespace 'waiting_players_answer' event with data %s", emit_data_to_namespace_blind_test_ui_yt)
    socketio.emit('waiting_players_answer', emit_data_to_namespace_blind_test_ui_yt, namespace='/blind_test_ui_yt')


@socketio.on('add_player', namespace='/blind_test_buz')
def add_player(message):
    message_items = ""
    for key, value in message.items():
        message_items = f"{message_items}, {key} = {value}"
    logger.info("Receive 'add_player' event from '/blind_test_buz' with namespace with message data %s", message_items[1:])
    logger.info("Try to add player '%s' in game", message['name'])
    res = game.add_player(message['name'])
    logger.debug("Result is %s", res)
    if res == "ADDED":
        logger.info("Add player '%s' in game", message['name'])
        emit_data_to_namespace_blind_test_admin_ui_yt = {'player_name': message['name'], 'player_score': 0}
        logger.info("emit to '/blind_test_admin_ui_yt' namespace 'add_player' event with data %s", emit_data_to_namespace_blind_test_admin_ui_yt)
        socketio.emit('add_player', emit_data_to_namespace_blind_test_admin_ui_yt, namespace='/blind_test_admin_ui_yt')
        emit_data_to_namespace_blind_test_ui_yt = {'player_name': message['name'], 'player_score': 0}
        logger.info("emit to '/blind_test_ui_yt' namespace 'add_player' event with data %s", emit_data_to_namespace_blind_test_ui_yt)
        socketio.emit('add_player', emit_data_to_namespace_blind_test_ui_yt, namespace='/blind_test_ui_yt')
    elif res == "ALLREADY_ADD":
        logger.info("NOTHING TO DO")
    else:
        logger.info("Buzzer back to login player")
        socketio.emit(  'end_game',
                        {'action': "end_game"},
                        namespace='/blind_test_buz')



@socketio.on('add_player', namespace='/blind_test_admin_ui_yt')
def add_player(message):
    message_items = ""
    for key, value in message.items():
        message_items = f"{message_items}, {key} = {value}"
    logger.info("Receive 'add_player' event from '/blind_test_admin_ui_yt' with namespace with message data %s", message_items[1:])
    logger.info("Try to add player '%s' in game", message['player_name'])
    res = game.add_player(message['player_name'])
    logger.debug("Result is %s", res)
    if res == "ADDED":
        logger.info("Add player '%s' in game", message['player_name'])
        emit_data_to_namespace_blind_test_admin_ui_yt = {'player_name': message['player_name'], 'player_score': 0}
        logger.info("emit to '/blind_test_admin_ui_yt' namespace 'add_player' event with data %s", emit_data_to_namespace_blind_test_admin_ui_yt)
        socketio.emit('add_player', emit_data_to_namespace_blind_test_admin_ui_yt, namespace='/blind_test_admin_ui_yt')
        emit_data_to_namespace_blind_test_ui_yt = {'player_name': message['player_name'], 'player_score': 0}
        logger.info("emit to '/blind_test_ui_yt' namespace 'add_player' event with data %s", emit_data_to_namespace_blind_test_ui_yt)
        socketio.emit('add_player', emit_data_to_namespace_blind_test_ui_yt, namespace='/blind_test_ui_yt')


def check_str_in_str(str1, str2):
    if str2.lower().find(str1.lower()) != -1:
        return True
    return False

def unicode_to_ascii(str):
    unicode_str = str.replace("\u00e0", "à").replace("\u00e4", "ä").replace("\u00e2", "â").replace("\u00e7", "ç").replace("\u00e8", "è").replace("\u00e9", "é").replace("\u00ea", "ê").replace("\u00eb", "ë").replace("\u00ee", "î").replace("\u00ef", "ï").replace("\u00f4", "ô").replace("\u00f6", "ö").replace("\u00f9", "ù").replace("\u00FB", "û").replace("\u2019", "'")
    return unicode_str

def ascii_to_unicode(str):
    # unicode_str = str.replace("à", "\u00e0").replace("ä", "\u00e4").replace("\u00e2", "â").replace("\u00e7", "ç").replace("\u00e8", "è").replace("\u00e9", "é").replace("\u00ea", "ê").replace("\u00eb", "ë").replace("\u00ee", "î").replace("\u00ef", "ï").replace("\u00f4", "ô").replace("\u00f6", "ö").replace("\u00f9", "ù").replace("\u00FB", "û")
    unicode_str = str.replace("é", "\u00e9")
    return unicode_str

def str_without_sp_chars(str):
    str_without_sp_chars = str.replace("é", "e").replace("à", "a").replace("è", "e").replace("ê", "e").replace("ë", "e").replace("ô", "o").replace("î", "i").replace("ç", "c").replace("ù", "u").replace("û", "u").replace("ö", "o").replace("ä", "a").replace("ï", "i").replace("’", "'")
    return str_without_sp_chars

@socketio.on('search_video', namespace='/blind_test_admin_ui_yt')
def search_video(message):
    message_items = ""
    for key, value in message.items():
        message_items = f"{message_items}, {key} = {value}"
    logger.info("Receive 'search_video' event from '/blind_test_admin_ui_yt' with namespace with message data %s", message_items[1:])
    videos_find_str = ""
    result = {}
    if 'artists' in message:
        artists_to_find = message['artists']
        logger.info("Search youtube video according to '%s' artists", artists_to_find)
        db = TinyDB('database/default.json', indent=4)
        table = db.table('yt')
        song = Query()
        result = table.search(song.artists.matches(".*"+artists_to_find+".*", flags=re.IGNORECASE))
    if 'title' in message:
        title_to_find = message['title']
        logger.info("Search youtube video according to '%s' title", title_to_find)
        db = TinyDB('database/default.json', indent=4)
        table = db.table('yt')
        song = Query()
        result = table.search(song.title.matches(".*"+title_to_find+".*", flags=re.IGNORECASE))
    if 'album' in message:
        album_to_find = message['album']
        logger.info("Search youtube video according to '%s' album", album_to_find)
        db = TinyDB('database/default.json', indent=4)
        table = db.table('yt')
        song = Query()
        result = table.search(song.album.matches(".*"+album_to_find+".*", flags=re.IGNORECASE))
    if 'year' in message:
        year_to_find = message['year']
        logger.info("Search youtube video according to '%s' year", year_to_find)
        db = TinyDB('database/default.json', indent=4)
        table = db.table('yt')
        song = Query()
        result = table.search(song.year.matches(year_to_find+".*", flags=re.IGNORECASE))
    if 'genders' in message:
        genders_to_find = message['genders']
        logger.info("Search youtube video according to '%s' genders", genders_to_find)
        db = TinyDB('database/default.json', indent=4)
        table = db.table('yt')
        song = Query()
        result = table.search(song.genders.matches(".*"+genders_to_find+".*", flags=re.IGNORECASE))
    for item in result:
        logger.info("Result: %s", item)
        for key, value in item.items():
            # logger.debug("key: %s, value: %s", key, value)
            videos_find_str = f'{videos_find_str}{key}="{value}" '
        videos_find_str = f"{videos_find_str}\n"
    emit_data_to_namespace_blind_test_admin_ui_yt = {'videos_find': videos_find_str}
    logger.info("emit to '/blind_test_admin_ui_yt' namespace 'videos_find' event with data %s", emit_data_to_namespace_blind_test_admin_ui_yt)
    socketio.emit('videos_find', emit_data_to_namespace_blind_test_admin_ui_yt, namespace='/blind_test_admin_ui_yt')

@socketio.on('add_video_to_db', namespace='/blind_test_admin_ui_yt')
def add_video_to_db(message):
    message_items = ""
    for key, value in message.items():
        message_items = f"{message_items}, {key} = {value}"
    logger.info("Receive 'add_video_to_db' event from '/blind_test_admin_ui_yt' with namespace with message data %s", message_items[2:])

    message_without_sp_chars = {}
    for key, value in message.items():
        if key not in ['db1', 'db2', 'db3', 'db4', 'db5']:
            message_without_sp_chars[key] = str_without_sp_chars(value)
    # db = TinyDB('db.json', indent=4)
    db = TinyDB('database/default.json', indent=4)
    table = db.table('yt')
    table.insert(message_without_sp_chars)
    for db_name in ['db1', 'db2', 'db3', 'db4', 'db5']:
        if message[db_name]:
            db_file_name = f"database/{message[db_name]}.json"
            db = TinyDB(db_file_name, indent=4)
            table = db.table('yt')
            table.insert(message_without_sp_chars)

    logger.info("emit to '/blind_test_admin_ui_yt' namespace 'video_added' event")
    socketio.emit('video_added', {}, namespace='/blind_test_admin_ui_yt')


@socketio.on('bouton_click_event', namespace='/blind_test_buz')
def bouton_click_event(message):
    game_state = game.state
    message_items = ""
    for key, value in message.items():
        message_items = "{}, {} = {}".format(message_items, key, value)
    logger.info("Receive bouton_click_event from blind_test_buz with {}".format(message_items[1:]))
    if game_state == GameState.WAITING_PLAYERS :
        logger.info("Game state is WAITING_PLAYERS")
        game.set_ready_for_round(message['name'])
        emit_data_to_blind_test_admin_ui_yt = {'player_name': message['name'], 'time': 0, 'comment': "READY TO PLAY"}
        logger.info("emit to '/blind_test_admin_ui_yt' namespace 'set_player_ready' event with data %s", emit_data_to_blind_test_admin_ui_yt)
        socketio.emit('set_player_ready', emit_data_to_blind_test_admin_ui_yt, namespace='/blind_test_admin_ui_yt')
        emit_data_to_blind_test_ui_yt = {'player_name': message['name']}
        logger.info("emit to '/blind_test_ui_yt' namespace 'set_player_ready' event with data %s", emit_data_to_blind_test_ui_yt)
        socketio.emit('set_player_ready', emit_data_to_blind_test_ui_yt, namespace='/blind_test_ui_yt')
    elif game_state == GameState.ASK_QUESTION :
        logger.info("Game state is ASK_QUESTION")
        answer_button = game.answer_button
        emit_data_to_namespace_test = {'name': message['name'], 'time': message['time']}
        logger.info("emit to '/test' namespace 'add_players_console' event with data %s", emit_data_to_namespace_test)
        socketio.emit('add_players_console', emit_data_to_namespace_test, namespace='/test')
        if message['data'] == answer_button:
            game.increase_score(message['name'])
            game.increase_time(message['name'], message['time'])
            game.set_round_played(message['name'])
        else:
            game.increase_timeout(message['name'])
    elif game_state == GameState.DISPLAY_QUESTION:
        logger.info("Game state is DISPLAY_QUESTION")
        if message['status'] == "play_blind_test":
            player_name_list = game.get_player_name_list_not_played()
            emit_data_to_namespace_blind_test_buz = \
                {'action': "pause_blind_test", 'b1': "ATTENDRE REPONSE", 'b2': "", 'b3': "", 'b4': "", 'b5': "", 'player_name_list': player_name_list}
            logger.info("emit to '/blind_test_buz' namespace 'pause_blind_test' event with data %s", emit_data_to_namespace_blind_test_buz)
            socketio.emit('pause_blind_test', emit_data_to_namespace_blind_test_buz, namespace='/blind_test_buz')
            game.set_round_played(message['name'])
            emit_data_to_namespace_blind_test_admin_ui_yt = {'player_name': message['name']}
            logger.info("emit to '/blind_test_admin_ui_yt' namespace 'pause_blind_test' event with data %s", emit_data_to_namespace_blind_test_admin_ui_yt)
            socketio.emit('pause_blind_test', emit_data_to_namespace_blind_test_admin_ui_yt, namespace='/blind_test_admin_ui_yt')
            emit_data_to_blind_test_ui_yt = {'player_name': message['name']}
            logger.info("emit to '/blind_test_ui_yt' namespace 'waiting_player' event with data %s", emit_data_to_blind_test_ui_yt)
            socketio.emit('waiting_player', emit_data_to_blind_test_ui_yt, namespace='/blind_test_ui_yt')
            logger.info("emit to '/blind_test_ui_yt' namespace 'pause_blind_test' event with data %s", emit_data_to_blind_test_ui_yt)
            socketio.emit('pause_blind_test', {}, namespace='/blind_test_ui_yt')
    else:
        logger.info("Unkonwn Game state '{}'".format(game_state))
if __name__ == '__main__':
    hostname = socket.gethostname()
    host_ip = socket.gethostbyname(hostname)
    qr = qrcode.make(f"http://{host_ip}:5000/blind_test_login")
    qr.save("static/qrcode.png")
    logger.info('launch admin interface http://%s:5000/blind_test_admin_ui_yt', hostname)
    logger.info('launch scoreboard http://%s:5000/blind_test_ui_yt', hostname)
    logger.info('launch user login http://%s:5000/blind_test_login', hostname)
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

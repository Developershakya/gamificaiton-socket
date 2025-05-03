from flask import Flask, render_template
from flask_socketio import SocketIO, join_room, emit
from models import db, Player, Question
from questions import QUESTIONS
import random, string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
socketio = SocketIO(app)
db.init_app(app)

rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

with app.app_context():
    db.create_all()
    if Question.query.count() == 0:
        for q in QUESTIONS:
            db.session.add(Question(**q))
        db.session.commit()

def generate_code(length=5):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@socketio.on('generate_code')
def handle_generate_code():
    code = generate_code()
    rooms[code] = {'players': [], 'index': 0, 'scores': {}, 'answers': {}, 'timer_started': False}
    emit('code_generated', code)

@socketio.on('join_room')
def handle_join(data):
    username = data['username']
    room = data['code']

    if room not in rooms:
        emit('room_error', 'Invalid Room Code')
        return

    if len(rooms[room]['players']) >= 2:
        emit('room_error', 'Room Full')
        return

    join_room(room)
    rooms[room]['players'].append(username)
    rooms[room]['scores'][username] = 0
    rooms[room]['answers'][username] = None

    db.session.add(Player(name=username, room=room))
    db.session.commit()

    if len(rooms[room]['players']) == 2:
        send_question(room)
    else:
        emit('waiting', room=room)

def send_question(room):
    room_data = rooms[room]
    questions = Question.query.all()

    if room_data['index'] >= len(questions):
        socketio.emit('quiz_end', room=room)
        return

    q = questions[room_data['index']]
    socketio.emit('new_question', {
        'question': q.question,
        'options': q.options,
        'index': room_data['index'],
        'total': len(questions),
        'players': room_data['players']
    }, room=room)

    room_data['answers'] = {p: None for p in room_data['players']}
    room_data['timer_started'] = True

    socketio.start_background_task(question_timer, room)

def question_timer(room):
    socketio.sleep(10)
    finalize_question(room)

def finalize_question(room):
    room_data = rooms[room]
    question = Question.query.all()[room_data['index']]

    for user in room_data['players']:
        answer = room_data['answers'].get(user)
        if answer == question.answer:
            room_data['scores'][user] += 1
        else:
            room_data['scores'][user] -= 1

        player = Player.query.filter_by(name=user, room=room).first()
        if player:
            player.score = room_data['scores'][user]
    db.session.commit()

    room_data['index'] += 1
    send_question(room)

@socketio.on('answer')
def handle_answer(data):
    username = data['username']
    room = data['room']
    answer = data['answer']
    if room in rooms and username in rooms[room]['answers']:
        rooms[room]['answers'][username] = answer
        if all(rooms[room]['answers'][p] is not None for p in rooms[room]['players']):
            finalize_question(room)




if __name__ == '__main__':
    socketio.run(app, debug=True)


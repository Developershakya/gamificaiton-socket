from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room
import random, string
from database import create_table, create_room, join_room_by_code, get_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

create_table()

questions = [
    {
        "question": "What does LAN stand for?",
        "options": ["Local Around Network", "Listed Area Network", "Line Area Network", "Local Area Network"],
        "answer": "Local Area Network"
    },
    {
        "question": "What does SQL stand for?",
        "options": ["Structured Query Language", "Simple Query List", "Strong Question Logic", "Sequential Query Log"],
        "answer": "Structured Query Language"
    },
    {
        "question": "Which of these is a primary key feature?",
        "options": ["Allows duplicates", "Must be unique", "Can be null", "Can be float"],
        "answer": "Must be unique"
    }
]

scoreboard = {}
current_question_index = {}

@app.route('/')
def index():
    return render_template('index.html')

def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@app.route('/create_room')
def create_room_http():
    code = generate_code()

    # You can replace '127.0.0.1' with actual session or identifier logic if needed
    sid = request.remote_addr  # Using the IP address as the session identifier for simplicity

    # Add this code to your data structures
    create_room(code, sid)           # Your own function to store room
    scoreboard[code] = {sid: 0}
    current_question_index[code] = 0

    return jsonify({'code': code})

@socketio.on('join_code')
def handle_join(data):
    sid = request.sid
    code = data.get('code')
    room = get_room(code)

    if room and not room[2]:  # player2 is None
        join_room_by_code(code, sid)
        join_room(code)
        scoreboard[code][sid] = 0
        emit('joined_successfully', {'code': code, 'player_count': 2}, room=code)

        emit('start_game', {
            'question': questions[0],
            'index': 0,
            'total': len(questions)
        }, room=code)
    else:
        emit('room_full')

@socketio.on('answer')
def handle_answer(data):
    sid = request.sid
    code = data.get('code')
    selected = data.get('selected')
    question_index = current_question_index[code]
    correct = questions[question_index]['answer']

    if selected == correct:
        scoreboard[code][sid] += 1

    if question_index + 1 < len(questions):
        current_question_index[code] += 1
        emit('next_question', {
            'question': questions[question_index + 1],
            'index': question_index + 1,
            'total': len(questions)
        }, room=code)
    else:
        emit('quiz_complete', {'scores': scoreboard[code]}, room=code)

if __name__ == '__main__':
    socketio.run(app, debug=True)

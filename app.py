import sqlite3
import os
from datetime import datetime
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- 強制使用新的資料庫名稱 ---
DB_NAME = "chat_final.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT NOT NULL,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            msg_type TEXT DEFAULT 'text',
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    # 這裡會印出訊息在黑視窗，證明你有跑到新程式
    print(f"DEBUG: {username} 加入了房間 {room}") 
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT username, message, timestamp, msg_type FROM messages WHERE room = ?", (room,))
    history = c.fetchall()
    conn.close()
    emit('load_history', history)

@socketio.on('send_message')
def handle_send_message(data):
    room = data['room']
    username = data['username']
    message = data['message']
    msg_type = data.get('type', 'text')
    timestamp = datetime.now().strftime('%H:%M')

    # 存檔
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO messages (room, username, message, msg_type, timestamp) VALUES (?, ?, ?, ?, ?)",
              (room, username, message, msg_type, timestamp))
    conn.commit()
    conn.close()

    emit('receive_message', {
        'username': username,
        'message': message,
        'timestamp': timestamp,
        'type': msg_type
    }, room=room)

# ... (上面不用動)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))

    print(f"系統啟動！使用 Port: {port}")
    # host='0.0.0.0' 是雲端必備設定
    socketio.run(app, debug=False, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
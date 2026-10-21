import os
import logging
import psycopg
from psycopg.rows import dict_row
from flask import Flask, request, jsonify, Response
from werkzeug.exceptions import HTTPException
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 8192
logging.basicConfig(level=logging.INFO)
requests_total = Counter('notes_http_requests_total', 'Handled API requests', ['method', 'endpoint', 'status'])

def db():
    return psycopg.connect(os.environ['DATABASE_URL'], connect_timeout=5, row_factory=dict_row)

with db() as conn:
    conn.execute('CREATE TABLE IF NOT EXISTS notes (id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY, text varchar(200) NOT NULL)')

@app.after_request
def count_response(response):
    requests_total.labels(request.method, request.endpoint or 'unknown', str(response.status_code)).inc()
    return response

@app.errorhandler(HTTPException)
def bad_http(error):
    return jsonify(error=error.description), error.code

@app.errorhandler(psycopg.Error)
def bad_database(error):
    app.logger.exception('Database request failed')
    return jsonify(error='Database is temporarily unavailable'), 503

def note_text():
    if not request.is_json:
        return None, (jsonify(error='Expected application/json'), 400)
    data = request.get_json()
    if not isinstance(data, dict) or set(data) != {'text'} or not isinstance(data['text'], str):
        return None, (jsonify(error='JSON must contain only the string field text'), 400)
    text = data['text'].strip()
    if not 1 <= len(text) <= 200:
        return None, (jsonify(error='Text length must be from 1 to 200 characters'), 400)
    return text, None

@app.get('/')
@app.get('/health')
def health():
    with db() as conn:
        conn.execute('SELECT 1').fetchone()
    return jsonify(status='ok', student='8vm51-15-mandrikov', app='notes', version=os.getenv('VERSION', 'v1'))

@app.get('/notes')
def list_notes():
    with db() as conn:
        return jsonify(conn.execute('SELECT id,text FROM notes ORDER BY id').fetchall())

@app.post('/notes')
def create_note():
    text, error = note_text()
    if error:
        return error
    with db() as conn:
        note = conn.execute('INSERT INTO notes(text) VALUES (%s) RETURNING id,text', (text,)).fetchone()
    return jsonify(note), 201, {'Location': '/notes/'+str(note['id'])}

@app.get('/notes/<int:note_id>')
def get_note(note_id):
    with db() as conn:
        note = conn.execute('SELECT id,text FROM notes WHERE id=%s', (note_id,)).fetchone()
    return (jsonify(note), 200) if note else (jsonify(error='Note not found'), 404)

@app.put('/notes/<int:note_id>')
def update_note(note_id):
    text, error = note_text()
    if error:
        return error
    with db() as conn:
        note = conn.execute('UPDATE notes SET text=%s WHERE id=%s RETURNING id,text', (text, note_id)).fetchone()
    return (jsonify(note), 200) if note else (jsonify(error='Note not found'), 404)

@app.delete('/notes/<int:note_id>')
def delete_note(note_id):
    with db() as conn:
        note = conn.execute('DELETE FROM notes WHERE id=%s RETURNING id', (note_id,)).fetchone()
    return ('', 204) if note else (jsonify(error='Note not found'), 404)

@app.get('/metrics')
def metrics():
    return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)

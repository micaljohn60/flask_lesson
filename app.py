from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Database connection
def get_db_connection():
    return psycopg2.connect(
        dbname="g12_assignment",
        user="postgres",
        password="admin",
        host="localhost",
        port="5432"
    )

# Initialize the database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            subjects TEXT,
            contact TEXT,
            fees_paid REAL DEFAULT 0.0,
            fees_pending REAL DEFAULT 0.0
        )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignments (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id),
            name TEXT NOT NULL,
            due_date TEXT,
            max_score INTEGER,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id),
            question TEXT,
            time_spent INTEGER,
            correct BOOLEAN
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('students'))
    return redirect(url_for('login'))

@app.route('/students', methods=['GET', 'POST'])
def students():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        name = request.form['name']
        subjects = request.form['subjects']
        contact = request.form['contact']
        fees_paid = float(request.form['fees_paid'])
        fees_pending = float(request.form['fees_pending'])

        cursor.execute('''
            INSERT INTO students (name, subjects, contact, fees_paid, fees_pending)
            VALUES (%s, %s, %s, %s, %s)
        ''', (name, subjects, contact, fees_paid, fees_pending))
        conn.commit()

    cursor.execute('SELECT * FROM students')
    students = cursor.fetchall()
    conn.close()
    return render_template('students.html', students=students)

@app.route('/assignments', methods=['GET', 'POST'])
def assignments():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        due_date = request.form['due_date']
        max_score = int(request.form['max_score'])

        cursor.execute('''
            INSERT INTO assignments (student_id, name, due_date, max_score)
            VALUES (%s, %s, %s, %s)
        ''', (student_id, name, due_date, max_score))
        conn.commit()

    cursor.execute('''
        SELECT assignments.id, students.name AS student_name, assignments.name, 
               assignments.due_date, assignments.max_score, assignments.status
        FROM assignments
        JOIN students ON assignments.student_id = students.id
    ''')
    assignments = cursor.fetchall()
    conn.close()
    return render_template('assignments.html', assignments=assignments)

@app.route('/fees', methods=['GET', 'POST'])
def fees():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        student_id = request.form['student_id']
        payment = float(request.form['payment'])

        cursor.execute('''
            UPDATE students
            SET fees_paid = fees_paid + %s, fees_pending = fees_pending - %s
            WHERE id = %s
        ''', (payment, payment, student_id))
        conn.commit()

    cursor.execute('SELECT * FROM students')
    students = cursor.fetchall()
    conn.close()
    return render_template('fees.html', students=students)

@app.route('/reports', methods=['GET', 'POST'])
def reports():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        student_id = request.form['student_id']
        question = request.form['question']
        time_spent = int(request.form['time_spent'])
        correct = request.form['correct'].lower() == 'true'

        cursor.execute('''
            INSERT INTO reports (student_id, question, time_spent, correct)
            VALUES (%s, %s, %s, %s)
        ''', (student_id, question, time_spent, correct))
        conn.commit()

    cursor.execute('''
        SELECT reports.id, students.name AS student_name, reports.question, 
               reports.time_spent, reports.correct
        FROM reports
        JOIN students ON reports.student_id = students.id
    ''')
    reports = cursor.fetchall()
    conn.close()
    return render_template('reports.html', reports=reports)


# Sign Up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
            conn.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash('Username already exists. Please choose another.', 'danger')
        finally:
            conn.close()

    return render_template('signup.html')

# Sign In
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('students'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)






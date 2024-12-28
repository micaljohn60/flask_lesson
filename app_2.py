from flask import Flask, request, jsonify, session, flash, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key

# Database connection
def get_db_connection():
    conn = sqlite3.connect('school.db')
    conn.row_factory = sqlite3.Row  # To get rows as dictionaries
    return conn

# Initialize the database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subjects TEXT,
            contact TEXT,
            fees_paid REAL DEFAULT 0.0,
            fees_pending REAL DEFAULT 0.0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('students'))
    return redirect(url_for('login'))

# Students List and Create
@app.route('/students', methods=['GET', 'POST'])
def students():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        try:
            name = request.form['name']
            subjects = request.form['subjects']
            contact = request.form['contact']
            fees_paid = float(request.form['fees_paid'])
            fees_pending = float(request.form['fees_pending'])

            cursor.execute('''
                INSERT INTO students (name, subjects, contact, fees_paid, fees_pending)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, subjects, contact, fees_paid, fees_pending))
            conn.commit()
            flash("Student added successfully!", "success")
        except Exception as e:
            conn.rollback()
            flash(f"An error occurred: {e}", "danger")

    cursor.execute('SELECT * FROM students')
    students = cursor.fetchall()
    conn.close()
    return render_template('students.html', students=students)

# Update Student
@app.route('/update_student/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    try:
        data = request.get_json()
        name = data.get('name')
        subjects = data.get('subjects')
        contact = data.get('contact')
        fees_paid = float(data.get('fees_paid', 0))
        fees_pending = float(data.get('fees_pending', 0))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE students
            SET name = COALESCE(?, name),
                subjects = COALESCE(?, subjects),
                contact = COALESCE(?, contact),
                fees_paid = COALESCE(?, fees_paid),
                fees_pending = COALESCE(?, fees_pending)
            WHERE id = ?
        ''', (name, subjects, contact, fees_paid, fees_pending, student_id))

        if cursor.rowcount == 0:
            return jsonify({"error": "Student not found"}), 404

        conn.commit()
        return jsonify({"message": "Student updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

    finally:
        conn.close()

# Delete Student
@app.route('/delete_student/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "Student not found"}), 404

        conn.commit()
        return jsonify({"message": "Student deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

    finally:
        conn.close()

# Sign Up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
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
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
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

# Initialize and run the app
if __name__ == '__main__':
    init_db()
    app.run(debug=True)

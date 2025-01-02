from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2

app = Flask(__name__)

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        dbname="g_12",
        user="postgres",
        password="admin",
        host="localhost",
        port=5432
    )

# Initialize the database and create tables
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
);
    ''')
    
    # Create students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            subjects TEXT,
            contact VARCHAR(15),
            fees_paid NUMERIC DEFAULT 0.0,
            fees_pending NUMERIC DEFAULT 0.0
        )
    ''')
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    ''')
    
    # Create assignments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignments (
            id SERIAL PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            description TEXT
        )
    ''')
    
    # Create grades table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            assignment_id INTEGER NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
            grade NUMERIC CHECK (grade >= 0 AND grade <= 100)
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

# Ensure database is initialized before the app starts

def initialize_database():
    init_db()

# Routes
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', students=students)

@app.route('/assignments', methods=['GET'])
def assignments():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assignments")
    assignments = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('assignments.html', assignments=assignments)

@app.route('/student_details/<int:student_id>', methods=['GET'])
def student_details(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch student's details
    cursor.execute('SELECT * FROM students WHERE id = %s', (student_id,))
    student = cursor.fetchone()

    # Fetch the student's grades and assignments
    cursor.execute('''
        SELECT a.title, g.grade
        FROM grades g
        JOIN assignments a ON g.assignment_id = a.id
        WHERE g.student_id = %s
    ''', (student_id,))
    grades = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('student_details.html', student=student, grades=grades)


@app.route('/grades')
def grades():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT g.id, s.name, a.title, g.grade
        FROM grades g
        JOIN students s ON g.student_id = s.id
        JOIN assignments a ON g.assignment_id = a.id
    ''')
    grades = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('grades.html', grades=grades)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        subjects = request.form['subjects']
        contact = request.form['contact']
        fees_paid = request.form['fees_paid']
        fees_pending = request.form['fees_pending']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO students (name, subjects, contact, fees_paid, fees_pending)
            VALUES (%s, %s, %s, %s, %s)
        ''', (name, subjects, contact, fees_paid, fees_pending))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
    
    return render_template('add_student.html')

@app.route('/add_assignment', methods=['GET', 'POST'])
def add_assignment():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO assignments (title, description)
            VALUES (%s, %s)
        ''', (title, description))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('assignments'))
    
    return render_template('add_assignment.html')

@app.route('/add_grade', methods=['GET', 'POST'])
def add_grade():
    if request.method == 'POST':
        student_id = request.form['student_id']
        assignment_id = request.form['assignment_id']
        grade = request.form['grade']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO grades (student_id, assignment_id, grade)
            VALUES (%s, %s, %s)
        ''', (student_id, assignment_id, grade))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('grades'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.execute("SELECT * FROM assignments")
    assignments = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('add_grade.html', students=students, assignments=assignments)


@app.route('/update_student/<int:student_id>', methods=['GET', 'POST'])
def update_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        subjects = request.form['subjects']
        contact = request.form['contact']
        fees_paid = request.form['fees_paid']
        fees_pending = request.form['fees_pending']

        cursor.execute('''
            UPDATE students
            SET name = COALESCE(%s, name),
                subjects = COALESCE(%s, subjects),
                contact = COALESCE(%s, contact),
                fees_paid = COALESCE(%s, fees_paid),
                fees_pending = COALESCE(%s, fees_pending)
            WHERE id = %s
        ''', (name, subjects, contact, fees_paid, fees_pending, student_id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))

    cursor.execute('SELECT * FROM students WHERE id = %s', (student_id,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('update_student.html', student=student)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user[2], password):  # Check password hash
            flash('Login successful!', 'success')
            return redirect(url_for('index'))  # Redirect to index page
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')  # Hash password

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Username already exists', 'danger')
        else:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            flash('Your account has been created successfully! You can now log in.', 'success')
            return redirect(url_for('login'))

        cursor.close()
        conn.close()

    return render_template('signup.html')


if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)

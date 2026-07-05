from flask import Flask, render_template, request, redirect, session, send_from_directory
from werkzeug.utils import secure_filename
import os
import sqlite3
import random
import string
import json

app = Flask(__name__)
app.secret_key = "uei2026secretkey"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def init_db():
    conn = sqlite3.connect("database/app.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            secret_code TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT NOT NULL,
            teacher_name TEXT NOT NULL,
            join_code TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS class_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            student_email TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
             title TEXT NOT NULL,
             filename TEXT,
             teacher_name TEXT,
             class_id INTEGER
          )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            teacher_name TEXT,
            class_id INTEGER
        )
    """)

    cursor.execute("""
     
    CREATE TABLE IF NOT EXISTS quiz_questions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    quiz_id INTEGER,

    question_type TEXT,

    difficulty TEXT,

    question TEXT,

    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,

    correct_answer TEXT
     )

    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizzes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER,
    title TEXT NOT NULL,
    instructions TEXT,
    duration INTEGER,
    deadline TEXT,
    quiz_type TEXT,
    evaluation_type TEXT,
    marks_per_question INTEGER,
    negative_marks REAL DEFAULT 0,
    shuffle_questions INTEGER DEFAULT 0,
    teacher_name TEXT
     )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_results(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER,
    student_name TEXT,
    score REAL,
    percentage REAL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    time_taken INTEGER
    )
     """)
    


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            posted_by TEXT NOT NULL,
            class_id INTEGER
        )
    """)

    cursor.execute("""
          CREATE TABLE IF NOT EXISTS submissions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER,
    student_name TEXT,
    filename TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
   """)
    
    cursor.execute("""
CREATE TABLE IF NOT EXISTS planner_history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    planner_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    planner_data TEXT
);
""")
    
    cursor.execute("""
CREATE TABLE IF NOT EXISTS admin_announcements(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

    conn.commit()
    conn.close()


def generate_join_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


# ================= HOME =================
@app.route("/")
def home():
    return render_template("home.html")


# ================= AUTH =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        conn = sqlite3.connect("database/app.db")
        user = conn.execute(
            "SELECT * FROM users WHERE email=? AND password=? AND role=?",
            (email, password, role)
        ).fetchone()
        conn.close()

        if user:
            if role == "admin":
                admin_code = request.form.get("admin_code", "")
                if admin_code != user[5]:
                    return "Wrong secret code! <a href='/login'>Try again</a>"

            session["user_id"] = user[0]
            session["name"] = user[1]
            session["email"] = user[2]
            session["role"] = user[4]

            if role == "student":
                return redirect("/student-dashboard")
            elif role == "teacher":
                return redirect("/teacher-dashboard")
            elif role == "admin":
                return redirect("/admin-dashboard")
        else:
            return "Wrong credentials! <a href='/login'>Try again</a>"

    selected_role = request.args.get("role", "student")
    return render_template("login.html", selected_role=selected_role)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        secret_code = request.form.get("admin_code", None)

        conn = sqlite3.connect("database/app.db")
        try:
            conn.execute(
                "INSERT INTO users (name, email, password, role, secret_code) VALUES (?, ?, ?, ?, ?)",
                (name, email, password, role, secret_code)
            )
            conn.commit()
            conn.close()
            return redirect(f"/login?role={role}")
        except:
            conn.close()
            return "Email already exists! <a href='/register'>Go back</a>"

    selected_role = request.args.get("role", "student")
    return render_template("register.html", selected_role=selected_role)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= DASHBOARDS =================
@app.route("/student-dashboard")
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/login")
    conn = sqlite3.connect("database/app.db")
    my_classes = conn.execute("""
        SELECT classes.* FROM classes
        JOIN class_members ON classes.id = class_members.class_id
        WHERE class_members.student_email = ?
    """, (session["email"],)).fetchall()

    admin_announcements = conn.execute("""
SELECT *
FROM admin_announcements
ORDER BY created_at DESC
LIMIT 5
""").fetchall()
    

    conn.close()
    return render_template("student_dashboard.html", 
                           my_classes=my_classes,
                           admin_announcements=admin_announcements
                           )


@app.route("/teacher-dashboard")
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect("/login")
    conn = sqlite3.connect("database/app.db")
    my_classes = conn.execute(
        "SELECT * FROM classes WHERE teacher_name=?", (session["name"],)
    ).fetchall()

    admin_announcements = conn.execute("""
SELECT *
FROM admin_announcements
ORDER BY created_at DESC
LIMIT 5
""").fetchall()
    

    conn.close()
    return render_template("teacher_dashboard.html", 
                           my_classes=my_classes,
                           admin_announcements=admin_announcements)

@app.route("/admin-dashboard")
def admin_dashboard():

    if session.get("role") != "admin":
        return redirect("/login")

    conn = sqlite3.connect("database/app.db")

    total_students = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='student'"
    ).fetchone()[0]

    total_teachers = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='teacher'"
    ).fetchone()[0]

    total_classes = conn.execute(
        "SELECT COUNT(*) FROM classes"
    ).fetchone()[0]

    total_quizzes = conn.execute(
        "SELECT COUNT(*) FROM quizzes"
    ).fetchone()[0]

    total_assignments = conn.execute(
        "SELECT COUNT(*) FROM assignments"
    ).fetchone()[0]

    total_submissions = conn.execute(
        "SELECT COUNT(*) FROM submissions"
    ).fetchone()[0]

    teachers = conn.execute("""
SELECT id, name, email
FROM users
WHERE role='teacher'
""").fetchall()

    students = conn.execute("""
SELECT id, name, email
FROM users
WHERE role='student'
    """).fetchall()

    classes = conn.execute("""
SELECT
    classes.id,
    classes.class_name,
    classes.teacher_name,

    (SELECT COUNT(*)
     FROM class_members
     WHERE class_members.class_id = classes.id) AS students,

    (SELECT COUNT(*)
     FROM resources
     WHERE resources.class_id = classes.id) AS resources,

    (SELECT COUNT(*)
     FROM quizzes
     WHERE quizzes.class_id = classes.id) AS quizzes

FROM classes
ORDER BY classes.class_name
""").fetchall()
    
    announcements = conn.execute("""
SELECT *
FROM admin_announcements
ORDER BY created_at DESC
""").fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_students=total_students,
        total_teachers=total_teachers,
        total_classes=total_classes,
        total_quizzes=total_quizzes,
        total_assignments=total_assignments,
        total_submissions=total_submissions,
        classes=classes,
        announcements=announcements
    )

#=====routes to post announcement=====
@app.route("/post-admin-announcement", methods=["POST"])
def post_admin_announcement():

    if session.get("role") != "admin":
        return redirect("/login")

    message = request.form["message"]

    conn = sqlite3.connect("database/app.db")

    conn.execute("""
    INSERT INTO admin_announcements(message)
    VALUES(?)
    """, (message,))

    conn.commit()
    conn.close()

    return redirect("/admin-dashboard")


# ================= CLASS =================
@app.route("/create-class", methods=["GET", "POST"])
def create_class():
    if session.get("role") != "teacher":
        return redirect("/login")
    if request.method == "POST":
        class_name = request.form["class_name"]
        join_code = generate_join_code()
        conn = sqlite3.connect("database/app.db")
        conn.execute(
            "INSERT INTO classes (class_name, teacher_name, join_code) VALUES (?, ?, ?)",
            (class_name, session["name"], join_code)
        )
        conn.commit()
        conn.close()
        return redirect("/teacher-dashboard")
    return render_template("create_class.html")


@app.route("/join-class", methods=["GET", "POST"])
def join_class():
    if session.get("role") != "student":
        return redirect("/login")
    if request.method == "POST":
        join_code = request.form["join_code"]
        conn = sqlite3.connect("database/app.db")
        class_row = conn.execute("SELECT * FROM classes WHERE join_code=?", (join_code,)).fetchone()
        if class_row:
            conn.execute(
                "INSERT INTO class_members (class_id, student_email) VALUES (?, ?)",
                (class_row[0], session["email"])
            )
            conn.commit()
            conn.close()
            return redirect("/student-dashboard")
        conn.close()
        return "Invalid code! <a href='/join-class'>Try again</a>"
    return render_template("join_class.html")


@app.route("/class/<int:class_id>")
def class_detail(class_id):
    if not session.get("role"):
        return redirect("/login")
    conn = sqlite3.connect("database/app.db")
    class_info = conn.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()
    class_resources = conn.execute("SELECT * FROM resources WHERE class_id=?", (class_id,)).fetchall()
    class_assignments = conn.execute("SELECT * FROM assignments WHERE class_id=?", (class_id,)).fetchall()
    quizzes = conn.execute( "SELECT * FROM quizzes WHERE class_id=?",(class_id,)).fetchall()
    class_announcements = conn.execute("SELECT * FROM announcements WHERE class_id=?", (class_id,)).fetchall()
    submissions = conn.execute("""SELECT *FROM submissions""").fetchall()
    conn.close()
    return render_template("class_detail.html",
                           class_info=class_info,
                           resources=class_resources,
                           assignments=class_assignments,
                           quizzes=quizzes,
                           announcements=class_announcements,
                           submissions=submissions)


# ================= RESOURCES =================
@app.route("/add-resource/<int:class_id>", methods=["POST"])
def add_resource(class_id):
    if session.get("role") != "teacher":
        return redirect("/login")

    title = request.form["title"]

    file = request.files["resource_file"]

    if file.filename == "":
        return "No file selected!"

    filename = secure_filename(file.filename)

    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    conn = sqlite3.connect("database/app.db")
    conn.execute(
        "INSERT INTO resources (title, filename, teacher_name, class_id) VALUES (?, ?, ?, ?)",
        (title, filename, session["name"], class_id)
    )
    conn.commit()
    conn.close()

    return redirect(f"/class/{class_id}")

# ================= ASSIGNMENTS =================
@app.route("/add-assignment/<int:class_id>", methods=["POST"])
def add_assignment(class_id):
    if session.get("role") != "teacher":
        return redirect("/login")
    title = request.form["title"]
    description = request.form["description"]
    conn = sqlite3.connect("database/app.db")
    conn.execute(
        "INSERT INTO assignments (title, description, teacher_name, class_id) VALUES (?, ?, ?, ?)",
        (title, description, session["name"], class_id)
    )
    conn.commit()
    conn.close()
    return redirect(f"/class/{class_id}")


# ================= QUIZ =================
@app.route("/add-question/<int:quiz_id>", methods=["POST"])
def add_question(quiz_id):

    if session.get("role")!="teacher":
        return redirect("/login")

    conn=sqlite3.connect("database/app.db")

    conn.execute("""

    INSERT INTO quiz_questions
    (

    quiz_id,

    question_type,

    difficulty,

    question,

    option_a,

    option_b,

    option_c,

    option_d,

    correct_answer

    )

    VALUES

    (?, ?, ?, ?, ?, ?, ?, ?, ?)

    """,(

    quiz_id,

    request.form["question_type"],

    "Medium",

    request.form["question"],

    request.form["option_a"],

    request.form["option_b"],

    request.form["option_c"],

    request.form["option_d"],

    request.form["correct_answer"]

    ))

    conn.commit()

    conn.close()

    return redirect(f"/quiz/{quiz_id}")



#=========take quiz====================
@app.route("/take-quiz/<int:class_id>", methods=["GET", "POST"])
def take_quiz(class_id):
    if session.get("role") != "student":
        return redirect("/login")
    conn = sqlite3.connect("database/app.db")
    questions = conn.execute("SELECT * FROM quiz_questions WHERE class_id=?", (class_id,)).fetchall()
    conn.close()

    score = None
    if request.method == "POST":
        score = 0
        for q in questions:
            selected = request.form.get(f"q{q[0]}")
            if selected == q[6]:
                score += 1

    return render_template("take_quiz.html", questions=questions, score=score, total=len(questions), class_id=class_id)


# ================= ANNOUNCEMENTS =================
@app.route("/add-announcement/<int:class_id>", methods=["POST"])
def add_announcement(class_id):
    if session.get("role") != "teacher":
        return redirect("/login")
    message = request.form["message"]
    conn = sqlite3.connect("database/app.db")
    conn.execute(
        "INSERT INTO announcements (message, posted_by, class_id) VALUES (?, ?, ?)",
        (message, session["name"], class_id)
    )
    conn.commit()
    conn.close()
    return redirect(f"/class/{class_id}")


# ====================DOWNLOAd ROUTE ==================

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=True
    )

# ============Assignment submission=====================
@app.route("/submit-assignment/<int:assignment_id>", methods=["POST"])
def submit_assignment(assignment_id):

    if session.get("role") != "student":
        return redirect("/login")

    file = request.files["assignment_file"]

    if file.filename == "":
        return redirect(request.referrer)

    filename = secure_filename(file.filename)

    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    conn = sqlite3.connect("database/app.db")

    conn.execute("""
        INSERT INTO submissions
        (assignment_id, student_name, filename)
        VALUES (?, ?, ?)
    """, (
        assignment_id,
        session["name"],
        filename
    ))

    conn.commit()
    conn.close()

    return redirect(request.referrer)


#========study planner===========
from datetime import datetime, timedelta


@app.route("/study-planner", methods=["GET", "POST"])
def study_planner():

    if session.get("role") != "student":
        return redirect("/login")

    if request.method == "POST":

        planner_name = request.form["planner_name"]
        subject_count = int(request.form["subject_count"])

        return render_template(
            "study_details.html",
            planner_name=planner_name,
            subject_count=subject_count
        )

    return render_template("study_planner.html")
@app.route("/generate-plan", methods=["POST"])
def generate_plan():

    if session.get("role") != "student":
        return redirect("/login")
    
    planner_name = request.form["planner_name"]

    count = int(request.form["subject_count"])

    subjects = []

    today = datetime.today().date()

    for i in range(count):

        subject = request.form[f"subject{i}"]
        exam = request.form[f"exam{i}"]

        exam_date = datetime.strptime(exam, "%Y-%m-%d").date()

        subjects.append({
            "name": subject,
            "exam": exam_date
        })

    subjects.sort(key=lambda x: x["exam"])

    plan = []

    current = today

    while subjects:

        subjects.sort(key=lambda x: x["exam"])

        nearest = subjects[0]

        days_left = (nearest["exam"] - current).days

        # Remove expired exams
        if days_left < 0:
            subjects.pop(0)
            continue

        # Exam day
        if days_left == 0:

            plan.append({
                "date": current.strftime("%d %b %Y"),
                "task": f"🎓 {nearest['name']} Exam"
            })

            subjects.pop(0)

            continue

        # One day before exam
        elif days_left == 1:

            plan.append({
                "date": current.strftime("%d %b %Y"),
                "task": f"📝 Mock Test - {nearest['name']}"
            })

        # Two days before exam
        elif days_left == 2:

            plan.append({
                "date": current.strftime("%d %b %Y"),
                "task": f"📖 Final Revision - {nearest['name']}"
            })

        else:

            # Study the subject whose exam is nearest
            plan.append({
                "date": current.strftime("%d %b %Y"),
                "task": f"📚 Study - {nearest['name']}"
            })

        current += timedelta(days=1)

# Save planner history
    conn = sqlite3.connect("database/app.db")
  
    conn.execute("""
              INSERT INTO planner_history
              (student_name, planner_name, planner_data)
              VALUES (?, ?, ?)
             """, (
                     session["name"],
                      planner_name,
                      json.dumps(plan)
            ))

    conn.commit()
    conn.close()

    return render_template(
              "study_plan_result.html",
              plan=plan
        )
    
# ========planner history==============
@app.route("/planner-history")
def planner_history():

    if session.get("role") != "student":
        return redirect("/login")

    conn = sqlite3.connect("database/app.db")

    planners = conn.execute("""
        SELECT id, planner_name, created_at
        FROM planner_history
        WHERE student_name=?
        ORDER BY created_at DESC
    """, (session["name"],)).fetchall()

    conn.close()

    return render_template(
        "planner_history.html",
        planners=planners
    )

#============View planner============
@app.route("/view-planner/<int:planner_id>")
def view_planner(planner_id):

    if session.get("role") != "student":
        return redirect("/login")

    conn = sqlite3.connect("database/app.db")

    planner = conn.execute("""
        SELECT planner_name, planner_data
        FROM planner_history
        WHERE id=?
    """, (planner_id,)).fetchone()

    conn.close()

    if planner is None:
        return "Planner not found"

    planner_name = planner[0]

    plan = json.loads(planner[1])

    return render_template(
        "view_planner.html",
        planner_name=planner_name,
        plan=plan
    )


#=========delete button=================
@app.route("/delete-planner/<int:planner_id>")
def delete_planner(planner_id):

    if session.get("role") != "student":
        return redirect("/login")

    conn = sqlite3.connect("database/app.db")

    conn.execute("""
        DELETE FROM planner_history
        WHERE id=?
        AND student_name=?
    """, (
        planner_id,
        session["name"]
    ))

    conn.commit()
    conn.close()

    return redirect("/planner-history")

#===========quiz version2========================
@app.route("/create-quiz/<int:class_id>", methods=["POST"])
def create_quiz(class_id):

    if session.get("role") != "teacher":
        return redirect("/login")

    shuffle = 1 if request.form.get("shuffle") else 0

    conn = sqlite3.connect("database/app.db")

    conn.execute("""
        INSERT INTO quizzes
        (
        class_id,
        title,
        instructions,
        duration,
        deadline,
        quiz_type,
        evaluation_type,
        marks_per_question,
        shuffle_questions,
        teacher_name
        )

        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        class_id,

        request.form["title"],

        request.form["instructions"],

        request.form["duration"],

        request.form["deadline"],

        request.form["quiz_type"],

        request.form["evaluation"],

        request.form["marks"],

        shuffle,

        session["name"]

    ))

    conn.commit()

    conn.close()

    return redirect(f"/class/{class_id}")

#===========manage quiz===============
@app.route("/quiz/<int:quiz_id>")
def quiz(quiz_id):

    if not session.get("role"):
        return redirect("/login")

    conn = sqlite3.connect("database/app.db")

    quiz = conn.execute(
        "SELECT * FROM quizzes WHERE id=?",
        (quiz_id,)
    ).fetchone()

    questions = conn.execute(
        "SELECT * FROM quiz_questions WHERE quiz_id=?",
        (quiz_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "take_quiz.html",
        quiz=quiz,
        questions=questions
    )


#=========starty quiz==============
from datetime import datetime

@app.route("/start-quiz/<int:quiz_id>", methods=["GET", "POST"])
def start_quiz(quiz_id):

    if session.get("role") != "student":
        return redirect("/login")

    conn = sqlite3.connect("database/app.db")

    # Get quiz details
    quiz = conn.execute(
        "SELECT * FROM quizzes WHERE id=?",
        (quiz_id,)
    ).fetchone()

    if not quiz:
        conn.close()
        return "<h2>Quiz not found.</h2>"

    # Deadline Check
    deadline = datetime.strptime(
        quiz[5],
        "%Y-%m-%dT%H:%M"
    )

    if datetime.now() > deadline:
        conn.close()
        return "<h2>❌ Quiz deadline has passed.</h2>"

    # One Attempt Check
    attempt = conn.execute("""
        SELECT *
        FROM quiz_results
        WHERE quiz_id=?
        AND student_name=?
    """, (
        quiz_id,
        session["name"]
    )).fetchone()

    if attempt:
        conn.close()
        return "<h2>❌ You have already attempted this quiz.</h2>"

    # Get Questions
    questions = conn.execute(
        "SELECT * FROM quiz_questions WHERE quiz_id=?",
        (quiz_id,)
    ).fetchall()

    conn.close()

    # Quiz Submitted
    if request.method == "POST":

        score = 0

        for q in questions:

            answer = request.form.get(f"q{q[0]}")

            if answer:

                # Change q[8] if your correct answer column index is different
                if answer.strip().lower() == str(q[9]).strip().lower():
                    score += int(quiz[8])

        total_marks = len(questions) * int(quiz[8])

        percentage = 0

        if total_marks > 0:
            percentage = round((score / total_marks) * 100, 2)

        conn = sqlite3.connect("database/app.db")

        conn.execute("""
            INSERT INTO quiz_results
            (
                quiz_id,
                student_name,
                score,
                percentage,
                time_taken
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            quiz_id,
            session["name"],
            score,
            percentage,
            0
        ))

        conn.commit()
        conn.close()

        return render_template(
            "quiz_result.html",
            score=score,
            percentage=percentage,
            total=total_marks
        )

    # First Time Opening Quiz
    return render_template(
        "start_quiz.html",
        quiz=quiz,
        questions=questions
    )

#=========delete class route=======
@app.route("/delete-class/<int:class_id>")
def delete_class(class_id):

    if session.get("role") != "admin":
        return redirect("/login")

    conn = sqlite3.connect("database/app.db")

    conn.execute(
        "DELETE FROM classes WHERE id=?",
        (class_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin-dashboard")


# ================= DELETE USER (Admin) =================
@app.route("/delete-user/<int:user_id>")
def delete_user(user_id):
    if session.get("role") != "admin":
        return redirect("/login")
    conn = sqlite3.connect("database/app.db")
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return redirect("/admin-dashboard")


# ================= DELETE QUIZ (Teacher) =================
@app.route("/delete-quiz/<int:quiz_id>")
def delete_quiz(quiz_id):
    if session.get("role") != "teacher":
        return redirect("/login")
    conn = sqlite3.connect("database/app.db")
    # get class_id before deleting so we can redirect back
    quiz = conn.execute(
        "SELECT class_id FROM quizzes WHERE id=?", (quiz_id,)
    ).fetchone()
    conn.execute("DELETE FROM quizzes WHERE id=?", (quiz_id,))
    conn.execute("DELETE FROM quiz_questions WHERE quiz_id=?", (quiz_id,))
    conn.commit()
    conn.close()
    if quiz:
        return redirect(f"/class/{quiz[0]}")
    return redirect("/teacher-dashboard")


# ================= QUIZ RESULTS (Teacher) =================
@app.route("/quiz-results/<int:quiz_id>")
def quiz_results(quiz_id):
    if session.get("role") != "teacher":
        return redirect("/login")
    conn = sqlite3.connect("database/app.db")
    quiz = conn.execute(
        "SELECT * FROM quizzes WHERE id=?", (quiz_id,)
    ).fetchone()
    results = conn.execute(
        "SELECT * FROM quiz_results WHERE quiz_id=? ORDER BY score DESC",
        (quiz_id,)
    ).fetchall()
    conn.close()
    return render_template("quiz_results.html", quiz=quiz, results=results)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

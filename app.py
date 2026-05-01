from flask import Flask, render_template, redirect, request, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db, User, Project, Task, Notification
import re
import os

app = Flask(__name__)

# ================= CONFIG =================
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-secret")
app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY", "jwt-secret")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///db.sqlite3")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
jwt = JWTManager(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


# ================= USER LOADER =================
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ================= DB INIT =================
with app.app_context():
    db.create_all()

    if not User.query.filter_by(email="admin@gmail.com").first():
        admin = User(
            employee_id="EMP001",
            name="Admin",
            email="admin@gmail.com",
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()


# ================= HOME =================
@app.route('/')
def home():
    return redirect('/login')


# ================= SIGNUP =================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':

        password = request.form['password']

        # 🔐 STRONG PASSWORD
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$', password):
            flash("Password must have A-Z, a-z, number & special char (min 8)")
            return redirect('/signup')

        # 🔁 DUPLICATE CHECK
        existing = User.query.filter(
            (User.email == request.form['email']) |
            (User.employee_id == request.form['employee_id'])
        ).first()

        if existing:
            flash("User already exists")
            return redirect('/signup')

        try:
            user = User(
                employee_id=request.form['employee_id'],
                name=request.form['name'],
                email=request.form['email'],
                password=generate_password_hash(password),
                role="member"
            )

            db.session.add(user)
            db.session.commit()

        except:
            db.session.rollback()
            flash("Signup failed")
            return redirect('/signup')

        flash("Signup successful")
        return redirect('/login')

    return render_template('signup.html')


# ================= LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        user = User.query.filter_by(email=request.form['email']).first()

        if not user or not check_password_hash(user.password, request.form['password']):
            flash("Invalid email or password")
            return redirect('/login')

        login_user(user)

        next_page = request.args.get('next')
        return redirect(next_page or ('/admin' if user.role == "admin" else '/dashboard'))

    return render_template('login.html')


# ================= LOGOUT =================
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


# ================= ADMIN =================
@app.route('/admin')
@login_required
def admin():
    if current_user.role != "admin":
        return redirect('/dashboard')

    return render_template(
        'admin_dashboard.html',
        users=User.query.filter_by(role="member").all(),
        projects=Project.query.all(),
        tasks=Task.query.all()
    )


# ================= MEMBER DASHBOARD =================
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != "member":
        return redirect('/admin')

    tasks = Task.query.filter_by(assigned_to=current_user.id).all()

    total = len(tasks)
    completed = len([t for t in tasks if t.status == "Completed"])
    pending = total - completed
    overdue = len([t for t in tasks if t.is_overdue])

    return render_template(
        'member_dashboard.html',
        tasks=tasks,
        total=total,
        completed=completed,
        pending=pending,
        overdue=overdue,
        users=User.query.filter_by(role="member").all(),
        projects=Project.query.all()
    )


# ================= TASKS =================
@app.route('/tasks')
@login_required
def tasks():
    if current_user.role != "member":
        return redirect('/admin')

    return render_template(
        'tasks.html',
        tasks=Task.query.filter_by(assigned_to=current_user.id).all()
    )


# ================= PROJECTS =================
@app.route('/projects')
@login_required
def projects():
    return render_template('projects.html', projects=Project.query.all())


# ================= CREATE PROJECT =================
@app.route('/create_project', methods=['POST'])
@login_required
def create_project():
    if current_user.role != "admin":
        return redirect('/dashboard')

    db.session.add(Project(
        name=request.form['name'],
        status=request.form.get('status', 'Planning'),
        created_by=current_user.id
    ))
    db.session.commit()

    flash("Project created")
    return redirect('/projects')

# ================= CREATE TASK =================
@app.route('/create_task', methods=['POST'])
@login_required
def create_task():
    if current_user.role != "admin":
        return redirect('/dashboard')

    task = Task(
        title=request.form['title'],
        assigned_to=request.form['assigned_to'],
        project_id=request.form['project_id'],
        priority=request.form.get('priority', 'Medium'),
        due_date=datetime.strptime(request.form['due_date'], "%Y-%m-%d") if request.form.get('due_date') else None
    )

    db.session.add(task)
    db.session.commit()

    flash("Task created successfully")
    return redirect('/admin')
#================== UPDATE TASK STATUS =================
@app.route('/update_task/<int:id>')
@login_required
def update_task(id):

    task = Task.query.get_or_404(id)

    # 🔒 security (user only update own task)
    if task.assigned_to != current_user.id:
        return redirect('/dashboard')

    task.status = "Completed"
    db.session.commit()

    flash("Task marked as completed")
    return redirect('/tasks')
# ================= DELETE PROJECT =================
@app.route('/delete_project/<int:id>', methods=['POST'])
@login_required
def delete_project(id):
    if current_user.role != "admin":
        return redirect('/dashboard')

    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()

    flash("Project deleted")
    return redirect('/projects')


# ================= DELETE USER =================
@app.route('/delete_user/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    if current_user.role != "admin":
        return redirect('/dashboard')

    user = User.query.get_or_404(id)

    if user.role == "admin":
        flash("Admin cannot be deleted")
        return redirect('/team')

    db.session.delete(user)
    db.session.commit()

    flash("User deleted")
    return redirect('/team')


# ================= CLEAR TASKS =================
@app.route('/clear_tasks', methods=['POST'])
@login_required
def clear_tasks():
    if current_user.role != "admin":
        return redirect('/dashboard')

    tasks = Task.query.all()
    for t in tasks:
        db.session.delete(t)

    db.session.commit()
    flash("All tasks cleared")
    return redirect('/admin')


# ================= TEAM =================
@app.route('/team')
@login_required
def team():
    if current_user.role != "admin":
        return redirect('/dashboard')

    return render_template('team.html', users=User.query.filter_by(role="member").all())


# ================= SETTINGS =================
@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


# ================= UPDATE PROFILE =================
@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():

    existing = User.query.filter(
        User.email == request.form['email'],
        User.id != current_user.id
    ).first()

    if existing:
        flash("Email already in use")
        return redirect('/settings')

    current_user.name = request.form['name']
    current_user.email = request.form['email']

    db.session.commit()
    flash("Profile updated")
    return redirect('/settings')


# ================= CHANGE PASSWORD =================
@app.route('/change_password', methods=['POST'])
@login_required
def change_password():

    if request.form['new_password'] != request.form['confirm_password']:
        flash("Passwords do not match")
        return redirect('/settings')

    if not check_password_hash(current_user.password, request.form['current_password']):
        flash("Wrong current password")
        return redirect('/settings')

    current_user.password = generate_password_hash(request.form['new_password'])
    db.session.commit()

    flash("Password updated")
    return redirect('/settings')


# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
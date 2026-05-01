from flask import Flask, render_template, redirect, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db, User, Project, Task, Notification

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


# ================= USER LOADER =================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ================= CREATE ADMIN =================
def create_admin():
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

        existing_user = User.query.filter(
            (User.email == request.form['email']) |
            (User.employee_id == request.form['employee_id'])
        ).first()

        if existing_user:
            flash("User already exists")
            return redirect('/signup')

        user = User(
            employee_id=request.form['employee_id'],
            name=request.form['name'],
            email=request.form['email'],
            password=generate_password_hash(request.form['password']),
            role="member"
        )

        db.session.add(user)
        db.session.commit()

        flash("Signup successful")
        return redirect('/login')

    return render_template('signup.html')


# ================= LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        user = User.query.filter_by(email=request.form['email']).first()

        if not user:
            flash("User not found")
            return redirect('/login')

        if not check_password_hash(user.password, request.form['password']):
            flash("Wrong password")
            return redirect('/login')

        login_user(user)

        if user.role == "admin":
            return redirect('/admin')
        else:
            return redirect('/dashboard')

    return render_template('login.html')


# ================= LOGOUT =================
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


# ================= ADMIN DASHBOARD =================
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
    overdue = len([
        t for t in tasks
        if t.due_date and t.due_date < datetime.utcnow() and t.status != "Completed"
    ])

    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()

    # 🔥 IMPORTANT ADD
    users = User.query.filter_by(role="member").all()
    projects = Project.query.all()

    return render_template(
        'member_dashboard.html',
        tasks=tasks,
        total=total,
        completed=completed,
        pending=pending,
        overdue=overdue,
        notifications=notifications,
        users=users,
        projects=projects
    )


# ================= PROJECTS (ADMIN ONLY) =================
@app.route('/projects')
@login_required
def projects():
    if current_user.role != "admin":
        return redirect('/dashboard')

    return render_template('projects.html', projects=Project.query.all())


# ================= TEAM (ADMIN ONLY) =================
@app.route('/team')
@login_required
def team():
    if current_user.role != "admin":
        return redirect('/dashboard')

    return render_template('team.html', users=User.query.all())


# ================= CREATE PROJECT =================
@app.route('/create_project', methods=['POST'])
@login_required
def create_project():
    if current_user.role != "admin":
        return "Unauthorized"

    project = Project(
        name=request.form['name'],
        status=request.form.get('status', 'Planning'),
        created_by=current_user.id
    )

    db.session.add(project)
    db.session.commit()

    return redirect('/admin')


# ================= CREATE TASK =================
@app.route('/create_task', methods=['POST'])
@login_required
def create_task():
    if current_user.role != "admin":
        return "Unauthorized"

    due_date = request.form.get('due_date')
    due_date = datetime.strptime(due_date, "%Y-%m-%d") if due_date else None

    task = Task(
        title=request.form['title'],
        assigned_to=int(request.form['user_id']),
        project_id=int(request.form['project_id']),
        due_date=due_date,
        status="Pending"
    )

    db.session.add(task)

    # 🔔 Notification
    notif = Notification(
        user_id=int(request.form['user_id']),
        message=f"New Task Assigned: {task.title}"
    )
    db.session.add(notif)

    db.session.commit()

    return redirect('/admin')


# ================= UPDATE TASK =================
@app.route('/update_task/<int:id>')
@login_required
def update_task(id):
    task = Task.query.get_or_404(id)

    if task.assigned_to != current_user.id:
        return "Unauthorized"

    task.status = "Completed"
    db.session.commit()

    return redirect('/dashboard')


# ================= MARK NOTIFICATION =================
@app.route('/mark_read/<int:id>')
@login_required
def mark_read(id):
    notif = Notification.query.get_or_404(id)

    if notif.user_id != current_user.id:
        return "Unauthorized"

    notif.is_read = True
    db.session.commit()

    return redirect('/dashboard')


# ================= RUN =================
if __name__ == "__main__":
    with app.app_context():
        create_admin()

    app.run(debug=True)
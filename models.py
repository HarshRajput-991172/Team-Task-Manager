from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# ---------------- USER ----------------
class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(10), default="member", nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    projects = db.relationship(
        'Project',
        backref='creator',
        lazy=True,
        cascade="all, delete-orphan"
    )

    tasks = db.relationship(
        'Task',
        backref='user',
        lazy=True,
        cascade="all, delete-orphan"
    )

    notifications = db.relationship(
        'Notification',
        backref='user',
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.employee_id}>"


# ---------------- PROJECT ----------------
class Project(db.Model):
    __tablename__ = 'project'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default="Planning", nullable=False)

    created_by = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    tasks = db.relationship(
        'Task',
        backref='project',
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Project {self.name}>"


# ---------------- TASK ----------------
class Task(db.Model):
    __tablename__ = 'task'

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)

    status = db.Column(
        db.String(20),
        default="Pending",
        nullable=False
    )

    priority = db.Column(
        db.String(10),
        default="Medium",
        nullable=False
    )

    assigned_to = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey('project.id', ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    due_date = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 🔥 Overdue logic
    @property
    def is_overdue(self):
        return (
            self.due_date is not None and
            self.due_date < datetime.utcnow() and
            self.status != "Completed"
        )

    def __repr__(self):
        return f"<Task {self.title}>"


# ---------------- NOTIFICATION ----------------
class Notification(db.Model):
    __tablename__ = 'notification'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    message = db.Column(db.String(200), nullable=False)

    is_read = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Notification {self.message}>"
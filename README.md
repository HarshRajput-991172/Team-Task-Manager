# 🚀 Task Management System

A role-based task management web application built using Flask.  
It allows admins to manage projects and assign tasks, while members can track and complete their assigned work.

---

## 🔥 Features

### 👨‍💼 Admin
- Create and manage projects
- Assign tasks to team members
- View all tasks and progress

### 👨‍💻 Member
- View assigned tasks
- Mark tasks as completed
- View team members and projects (read-only)

### 🔔 System
- Secure Login & Signup (password hashing)
- Role-Based Access Control (Admin / Member)
- Notifications for assigned tasks
- Task statistics (Completed / Pending / Overdue)
- Responsive UI (Mobile-friendly)

---

## 🛠 Tech Stack

- **Backend:** Python (Flask)
- **Database:** SQLite (SQLAlchemy ORM)
- **Authentication:** Flask-Login
- **Frontend:** HTML, CSS, Bootstrap

---

## 🔑 Default Admin Login

Email: `admin@gmail.com`  
Password: `admin123`

---

## 📂 Project Structure
project/
│── app.py
│── models.py
│── requirements.txt
│── .gitignore
│── templates/
│ ├── base.html
│ ├── login.html
│ ├── signup.html
│ ├── admin_dashboard.html
│ ├── member_dashboard.html

---

## ▶️ Run Locally

```bash
# Clone repo
git clone https://github.com/YOUR_USERNAME/task-manager.git

# Go to folder
cd task-manager

# Install dependencies
pip install -r requirements.txt

# Run app
python app.py

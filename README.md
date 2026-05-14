# College Management System — DBMS Interface

A full-featured desktop application for managing college operations including student registration, faculty management, course enrollment, and academic results — built with a Tkinter GUI and a MySQL relational backend.

## 🎯 Features

- **Role-Based Access**: Separate dashboards for Students, Faculty, and Admin
- **Course Management**: Create, activate/deactivate, and manage seat availability in real time
- **Enrollment System**: Students enroll in courses with automatic seat tracking and QR code generation
- **Results Module**: Faculty assign grades; students view their academic record
- **Student Banning**: Admin/Faculty can restrict student portal access
- **Modern GUI**: Tkinter-based interface with styled cards, rounded buttons, and popup windows
- **Auto ID Generation**: Unique student and faculty IDs generated on registration
- **Database Auto-Init**: Schema and tables created automatically on first launch

## 🛠️ Technology Stack

- **Python 3.8+**
- **Tkinter / ttk** — GUI framework
- **mysql-connector-python** — MySQL database driver
- **Pillow** — Image handling for QR code display
- **qrcode** — QR code generation on enrollment
- **rich** — Styled terminal output (CLI version)
- **ttkthemes** — Extended Tkinter themes

## 📦 Installation

### 1. Prerequisites

Ensure Python 3.8+ and MySQL Server are installed:

```bash
python --version
mysql --version
```

### 2. Configure Database Credentials

Copy the environment template and fill in your MySQL details:

```bash
cp .env.example .env
```

Or edit `config.py` directly for local development:

```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "your_password",
    "database": "collegemanagementsystem",
}
```

> ⚠️ Never commit real credentials. `config.py` edits stay local; `.env` is gitignored.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install mysql-connector-python Pillow qrcode rich ttkthemes
```

### 4. Run the Application

```bash
# GUI version (recommended)
python app.py

# CLI version
python app_cli.py
```

The database and all tables are created automatically on first launch.

## 🖥️ User Interface Overview

### Login Window
- Email and password authentication
- Routes to appropriate dashboard based on role (Student / Faculty / Admin)

### Student Dashboard
Five main actions:
- **📚 View Courses** — Browse all active courses with seat availability
- **➕ Enroll in Course** — Enroll by Course ID and semester; generates a QR code on success
- **➖ Drop Course** — Drop an enrolled course and restore seat count
- **📋 My Enrollments** — View currently enrolled courses with semester info
- **📊 My Results** — View grades assigned by faculty
- **👤 My Profile** — View personal details and registration info

### Faculty Dashboard
Four main actions:
- **➕ Create Course** — Define course ID, name, credits, type, and max seats
- **📂 Manage Courses** — Toggle courses active/inactive; view enrollment counts
- **👥 View Students** — Browse all students; view profiles; ban/unban access
- **📝 Manage Results** — Assign or update grades per student per course

### Admin Access
Admin is a seeded Faculty account (`email: admin`) with full Faculty dashboard privileges.

## 🗄️ Database Schema

The application uses a MySQL database named `collegemanagementsystem` with five tables:

| Table | Primary Key | Description |
|-------|-------------|-------------|
| `Students` | `student_id` (INT) | Student accounts, ban status |
| `Faculty` | `faculty_id` (AUTO_INCREMENT) | Faculty accounts, department |
| `Courses` | `course_id` (VARCHAR) | Course metadata, seat tracking |
| `Enrollments` | `enrollment_id` (AUTO_INCREMENT) | Student-course-semester links |
| `Results` | `result_id` (AUTO_INCREMENT) | Grades per student per course |

### Key Relationships
- `Courses.instructor_id` → `Faculty.faculty_id`
- `Enrollments.student_id` → `Students.student_id`
- `Enrollments.course_id` → `Courses.course_id`
- `Results.student_id` → `Students.student_id`
- `Results.course_id` → `Courses.course_id`

## 🔐 Authentication & Roles

| Role | Login Credentials | Access |
|------|-------------------|--------|
| **Student** | Registered email + password | Student dashboard |
| **Faculty** | Department email + password | Faculty dashboard |
| **Admin** | `admin` / `admin123` (seeded) | Faculty dashboard with full access |

Banned students are blocked from logging in with a clear error message.

## 📋 Enrollment & QR Code

When a student successfully enrolls in a course:
- Seat count in `Courses` is decremented by 1
- A QR code is generated encoding `student_id | course_id | semester`
- QR image saved to `qr_codes/QR_{student_id}_{course_id}.png`
- Confirmation shown in the UI

Dropping a course reverses the seat decrement.

## 🚀 Workflow Example

1. **Launch Application**
   ```bash
   python app.py
   ```

2. **Register as a Student**
   - Click "Register" on the login screen
   - Fill in name, email, password
   - Note your auto-generated Student ID

3. **Login**
   - Enter email and password
   - Routed to Student Dashboard

4. **View and Enroll in a Course**
   - Click "📚 View Courses" to see available courses
   - Click "➕ Enroll in Course", enter Course ID and semester
   - QR code saved automatically on success

5. **View Results**
   - Click "📊 My Results" to see grades posted by faculty

6. **Faculty: Add a Course**
   - Login as Faculty
   - Click "➕ Create Course", fill in course details
   - Course immediately visible to students

7. **Faculty: Post Grades**
   - Click "📝 Manage Results"
   - Select course, select student, enter grade

## 💻 Code Structure

### GUI Application (`app.py`)

```
app.py
├── initialize_database()          — Auto-creates schema and tables
├── get_connection()               — Returns MySQL connection from config
├── StyleConfig (Class)
│   └── configure_styles()        — ttk widget styling
├── UI Utilities
│   ├── create_rounded_button()
│   ├── create_header()
│   └── create_card()
├── Authentication
│   ├── show_login_popup()
│   └── do_login()
├── Registration
│   ├── show_student_registration_popup()
│   ├── show_faculty_registration_popup()
│   ├── do_student_register()
│   └── do_faculty_register()
├── ID Generation
│   ├── generate_student_id()
│   └── generate_faculty_id()
├── Student Dashboard — show_student_dashboard()
│   ├── view_courses()
│   ├── enroll_course()
│   ├── drop_course()
│   ├── my_enrollments()
│   ├── my_results()
│   └── view_profile()
└── Faculty Dashboard — show_faculty_dashboard()
    ├── create_course()
    ├── manage_courses()
    ├── view_students()
    └── manage_results()
```

### CLI Application (`app_cli.py`)

```
app_cli.py
├── get_connection()
├── register_student()
├── view_courses()
├── enroll_course(sid)
├── drop_course(sid)
├── view_my_enrollments(sid)
├── student_dashboard(sid, name)
├── faculty_dashboard()
└── show_login_popup()
```

### Key Design Principles

- **Config Separation** — DB credentials isolated in `config.py`, never hardcoded
- **Auto-Init Schema** — No manual SQL setup needed; `initialize_database()` handles it
- **Role-Based Routing** — Single login entry point branches to correct dashboard
- **Transactional Integrity** — Seat count updates committed atomically with enrollment

## ⚠️ Error Handling

| Error | Handling |
|-------|----------|
| Wrong credentials | Popup with "Invalid email or password" |
| Banned student login | Blocked with ban notification |
| Duplicate enrollment | MySQL `UNIQUE` constraint caught, user notified |
| Course full (0 seats) | Enrollment blocked before INSERT |
| DB connection failure | `messagebox.showerror` with exception detail |
| Missing numeric input | Validation before query execution |

## 🔧 Customization

### Change Default Admin Password
In `initialize_database()`, locate the admin seed INSERT and update:
```python
cur.execute("INSERT INTO Faculty (name, email, password, department) VALUES ('Admin', 'admin', 'your_new_password', 'Administration')")
```

### Adjust Max Enrollment Per Student
In `do_enroll()` inside `enroll_course()`, add a check:
```python
cur.execute("SELECT COUNT(*) FROM Enrollments WHERE student_id=%s", (sid,))
if cur.fetchone()[0] >= 6:  # max 6 courses per student
    messagebox.showwarning(...)
```

### Change QR Code Output Directory
In `enroll_course()`:
```python
os.makedirs("your_custom_folder", exist_ok=True)
qr.save(f"your_custom_folder/QR_{sid}_{cid}.png")
```

## 🐛 Troubleshooting

### Issue: Application won't connect to database
**Solution**: Verify MySQL is running and credentials in `config.py` are correct:
```bash
mysql -u root -p -e "SHOW DATABASES;"
```

### Issue: `mysql.connector` not found
**Solution**:
```bash
pip install mysql-connector-python
```

### Issue: QR code not saving
**Solution**: Ensure `qr_codes/` directory exists or the app has write permission in the working directory.

### Issue: `ttkthemes` import error (CLI)
**Solution**:
```bash
pip install ttkthemes
```

### Issue: Tables not created
**Solution**: Ensure the DB user has `CREATE` privileges. Run `initialize_database()` manually or grant permissions:
```sql
GRANT ALL PRIVILEGES ON collegemanagementsystem.* TO 'root'@'localhost';
```

## 📚 References

- **mysql-connector-python**: https://dev.mysql.com/doc/connector-python/en/
- **Tkinter Documentation**: https://docs.python.org/3/library/tkinter.html
- **qrcode Library**: https://pypi.org/project/qrcode/
- **rich**: https://rich.readthedocs.io/

## 📄 Academic Context

This project was built as a DBMS capstone demonstrating:
- Relational schema design with foreign key constraints
- CRUD operations via Python-MySQL integration
- Role-based access control at the application layer
- Real-world GUI development with Tkinter

## ⚖️ License

This application is provided for academic and educational purposes.

## 🎓 Author Notes

This application was designed for:
- **Academic Demonstrations** — Understanding relational database design
- **DBMS Coursework** — Practical SQL + Python integration
- **Educational Purpose** — Learning GUI-driven database applications
- **Portfolio Projects** — Demonstrating full-stack Python development

The code follows best practices in:
- Database design (normalization, constraints, foreign keys)
- Credential management (config separation, `.gitignore`)
- Software architecture (modular functions, role-based routing)
- Error handling (comprehensive validation and user feedback)

## 🤝 Support

For issues or questions:
1. Check the Troubleshooting section above
2. Verify MySQL is running and credentials are correct
3. Confirm all dependencies are installed via `pip install -r requirements.txt`
4. Review terminal output for specific exception details

---

**Version**: 1.0  
**Last Updated**: 2025  
**Status**: Production Ready

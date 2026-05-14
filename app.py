import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
import datetime
import os
import qrcode
from PIL import Image, ImageTk
from tkinter import font as tkfont
import random
import string

# ========== DATABASE SETUP ==========
from config import DB_CONFIG

def initialize_database():
    try:
        # First connect without specifying database
        _cfg = {k: v for k, v in DB_CONFIG.items() if k != "database"}
        conn = mysql.connector.connect(**_cfg)
        cur = conn.cursor()
        
        # Create database if not exists
        cur.execute("CREATE DATABASE IF NOT EXISTS collegemanagementsystem")
        conn.commit()
        
        # Connect to the database
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Create tables if not exists
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Students (
            student_id INT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            is_banned BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Faculty (
            faculty_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            department VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Courses (
            course_id VARCHAR(20) PRIMARY KEY,
            course_name VARCHAR(100) NOT NULL,
            instructor_id INT NOT NULL,
            credits INT NOT NULL,
            course_type VARCHAR(50) NOT NULL,
            max_seats INT NOT NULL,
            seats_left INT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instructor_id) REFERENCES Faculty(faculty_id)
        )
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Enrollments (
            enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            course_id VARCHAR(20) NOT NULL,
            semester VARCHAR(20) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES Students(student_id),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id),
            UNIQUE(student_id, course_id)
        )
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Results (
            result_id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            course_id VARCHAR(20) NOT NULL,
            grade VARCHAR(2) NOT NULL,
            FOREIGN KEY (student_id) REFERENCES Students(student_id),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id),
            UNIQUE(student_id, course_id)
        )
        """)
        
        # Create admin account if not exists
        cur.execute("SELECT * FROM Faculty WHERE email='admin'")
        if not cur.fetchone():
            cur.execute("INSERT INTO Faculty (name, email, password, department) VALUES ('Admin', 'admin', 'admin123', 'Administration')")
            conn.commit()
        
        conn.close()
        return True
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error initializing database: {err}")
        return False

# ========== GLOBAL STYLING ==========
class StyleConfig:
    PRIMARY = "#4361EE"    # Vibrant blue
    SECONDARY = "#3A0CA3"  # Deep purple
    ACCENT = "#F72585"     # Energetic pink
    LIGHT = "#F8F9FA"      # Soft white
    DARK = "#212529"       # Dark gray
    SUCCESS = "#4CC9F0"    # Bright teal
    WARNING = "#F8961E"    # Warm orange
    DANGER = "#EF233C"     # Alert red
    INFO = "#4895EF"       # Friendly blue
    BACKGROUND = "#E9F5FF" # Light sky blue background
    BANNED = "#6C757D"     # Gray for banned status

    @classmethod
    def configure_styles(cls):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure main styles
        style.configure('TFrame', background=cls.BACKGROUND)
        style.configure('TLabel', background=cls.BACKGROUND, font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=6)
        style.configure('Header.TLabel', font=('Segoe UI', 14, 'bold'), foreground=cls.SECONDARY)
        style.configure('Accent.TButton', background=cls.ACCENT, foreground='white')
        style.configure('Primary.TButton', background=cls.PRIMARY, foreground='white')
        style.configure('Secondary.TButton', background=cls.SECONDARY, foreground='white')
        
        # Treeview styling
        style.configure('Treeview', 
                        background='white',
                        foreground=cls.DARK,
                        rowheight=28,
                        fieldbackground='white',
                        font=('Segoe UI', 9))
        style.map('Treeview', background=[('selected', cls.PRIMARY)])
        style.configure('Treeview.Heading', 
                       background=cls.PRIMARY,
                       foreground='white',
                       padding=5,
                       font=('Segoe UI', 10, 'bold'))
        
        # Entry styling
        style.configure('TEntry', 
                        fieldbackground='white',
                        bordercolor=cls.PRIMARY,
                        lightcolor=cls.PRIMARY,
                        darkcolor=cls.PRIMARY,
                        padding=5)

# ========== GLOBAL ROOT ==========
root = tk.Tk()
root.withdraw()
StyleConfig.configure_styles()

# Initialize database
if not initialize_database():
    messagebox.showerror("Critical Error", "Failed to initialize database. Application will exit.")
    exit()

# ========== DB CONNECTION ==========
def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error connecting to database: {err}")
        return None

# ========== UTILITY FUNCTIONS ==========
def create_rounded_button(parent, text, command, color, width=None):
    btn = tk.Canvas(parent, bg=StyleConfig.BACKGROUND, bd=0, highlightthickness=0, width=width)
    btn.bind("<Button-1>", lambda e: command())
    
    # Draw rounded rectangle
    radius = 15
    btn.create_round_rect(5, 5, (width-5) if width else 95, 35, radius=radius, fill=color, outline=color, width=0, tags="button")
    btn.create_text((width//2) if width else 50, 20, text=text, fill='white', font=('Segoe UI', 10, 'bold'), tags="text")
    
    # Hover effects
    def on_enter(e):
        btn.itemconfig("button", fill=StyleConfig.INFO if color == StyleConfig.PRIMARY else StyleConfig.ACCENT)
    def on_leave(e):
        btn.itemconfig("button", fill=color)
    
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    
    return btn

# Add rounded rectangle method to Canvas class
def _create_round_rect(self, x1, y1, x2, y2, radius=25, **kwargs):
    points = [x1+radius, y1,
              x1+radius, y1,
              x2-radius, y1,
              x2-radius, y1,
              x2, y1,
              x2, y1+radius,
              x2, y1+radius,
              x2, y2-radius,
              x2, y2-radius,
              x2, y2,
              x2-radius, y2,
              x2-radius, y2,
              x1+radius, y2,
              x1+radius, y2,
              x1, y2,
              x1, y2-radius,
              x1, y2-radius,
              x1, y1+radius,
              x1, y1+radius,
              x1, y1]
    return self.create_polygon(points, **kwargs, smooth=True)
tk.Canvas.create_round_rect = _create_round_rect

def create_header(parent, text):
    header_frame = ttk.Frame(parent)
    header_frame.pack(fill='x', pady=(0, 20))
    
    ttk.Label(header_frame, 
              text=text, 
              style='Header.TLabel').pack(side='left')
    
    separator = ttk.Separator(header_frame, orient='horizontal')
    separator.pack(fill='x', expand=True, side='left', padx=10)
    return header_frame

def create_card(parent, title, value, icon, color):
    card = ttk.Frame(parent, style='TFrame', relief='raised', borderwidth=1)
    
    # Icon with colored background
    icon_frame = tk.Canvas(card, width=50, height=50, bg=color, highlightthickness=0)
    icon_frame.create_text(25, 25, text=icon, font=('Segoe UI', 18), fill='white')
    icon_frame.pack(side='left', padx=10, pady=10)
    
    # Text content
    text_frame = ttk.Frame(card)
    text_frame.pack(side='left', fill='y', expand=True)
    ttk.Label(text_frame, text=title, style='TLabel', foreground='gray').pack(anchor='w')
    ttk.Label(text_frame, text=value, font=('Segoe UI', 18, 'bold'), foreground=color).pack(anchor='w')
    
    return card

def show_student_profile(sid, parent_window=None):
    conn = get_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor(dictionary=True)
        
        # Get student basic info
        cur.execute("SELECT * FROM Students WHERE student_id=%s", (sid,))
        student = cur.fetchone()
        
        if not student:
            messagebox.showerror("Error", "Student not found")
            return
            
        # Get enrollments
        cur.execute("""SELECT E.course_id, C.course_name, E.semester, E.timestamp 
                    FROM Enrollments E JOIN Courses C USING(course_id)
                    WHERE E.student_id=%s""", (sid,))
        enrollments = cur.fetchall()
        
        # Get results
        cur.execute("""SELECT R.course_id, C.course_name, R.grade 
                    FROM Results R JOIN Courses C USING(course_id)
                    WHERE R.student_id=%s""", (sid,))
        results = cur.fetchall()
        
        # Create profile window
        profile = tk.Toplevel()
        profile.title(f"Student Profile - {student['name']}")
        profile.geometry("800x600")
        profile.configure(bg=StyleConfig.BACKGROUND)
        
        if parent_window:
            profile.transient(parent_window)
        
        main_frame = ttk.Frame(profile)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header with student info
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 20))
        
        avatar_frame = tk.Canvas(header_frame, width=80, height=80, bg=StyleConfig.PRIMARY, highlightthickness=0)
        avatar_frame.create_text(40, 40, text=student['name'][0].upper(), font=('Segoe UI', 24), fill='white')
        avatar_frame.pack(side='left')
        
        info_frame = ttk.Frame(header_frame)
        info_frame.pack(side='left', padx=15, fill='y')
        
        ttk.Label(info_frame, text=student['name'], font=('Segoe UI', 16, 'bold')).pack(anchor='w')
        ttk.Label(info_frame, text=f"ID: {student['student_id']}").pack(anchor='w')
        ttk.Label(info_frame, text=f"Email: {student['email']}").pack(anchor='w')
        ttk.Label(info_frame, text=f"Status: {'Banned' if student['is_banned'] else 'Active'}", 
                 foreground=StyleConfig.DANGER if student['is_banned'] else StyleConfig.SUCCESS).pack(anchor='w')
        
        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)
        
        # Enrollments tab
        enroll_frame = ttk.Frame(notebook)
        notebook.add(enroll_frame, text="Enrollments")
        
        if enrollments:
            enroll_tree_frame = ttk.Frame(enroll_frame)
            enroll_tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            scrollbar = ttk.Scrollbar(enroll_tree_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            enroll_tree = ttk.Treeview(enroll_tree_frame, 
                                     columns=("CID", "Name", "Semester", "Enrolled On"), 
                                     show="headings", 
                                     yscrollcommand=scrollbar.set)
            scrollbar.config(command=enroll_tree.yview)
            
            enroll_tree.heading("CID", text="Course ID")
            enroll_tree.heading("Name", text="Course Name")
            enroll_tree.heading("Semester", text="Semester")
            enroll_tree.heading("Enrolled On", text="Enrolled On")
            
            enroll_tree.column("CID", width=100)
            enroll_tree.column("Name", width=200)
            enroll_tree.column("Semester", width=100)
            enroll_tree.column("Enrolled On", width=150)
            
            for e in enrollments:
                enroll_tree.insert('', tk.END, values=(e['course_id'], e['course_name'], e['semester'], e['timestamp']))
            enroll_tree.pack(fill='both', expand=True)
        else:
            ttk.Label(enroll_frame, text="No enrollments found").pack(pady=20)
        
        # Results tab
        result_frame = ttk.Frame(notebook)
        notebook.add(result_frame, text="Results")
        
        if results:
            result_tree_frame = ttk.Frame(result_frame)
            result_tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            scrollbar = ttk.Scrollbar(result_tree_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            result_tree = ttk.Treeview(result_tree_frame, 
                                     columns=("CID", "Name", "Grade"), 
                                     show="headings", 
                                     yscrollcommand=scrollbar.set)
            scrollbar.config(command=result_tree.yview)
            
            result_tree.heading("CID", text="Course ID")
            result_tree.heading("Name", text="Course Name")
            result_tree.heading("Grade", text="Grade")
            
            for r in results:
                result_tree.insert('', tk.END, values=(r['course_id'], r['course_name'], r['grade']))
            result_tree.pack(fill='both', expand=True)
        else:
            ttk.Label(result_frame, text="No results found").pack(pady=20)
        
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error fetching student data: {err}")
    finally:
        if conn.is_connected():
            cur.close()
            conn.close()

# ========== LOGIN/REGISTER FUNCTIONS ==========
def do_login(email_entry, pass_entry, popup):
    e = email_entry.get().strip()
    p = pass_entry.get().strip()
    
    if not e or not p:
        messagebox.showwarning("Input Error", "Please enter both email and password")
        return
        
    conn = get_connection()
    if not conn:
        return
        
    try:
        cur = conn.cursor(dictionary=True)
        
        # Check if admin
        if e == "admin" and p == "admin123":
            cur.execute("SELECT * FROM Faculty WHERE email='admin'")
            faculty = cur.fetchone()
            popup.destroy()
            show_faculty_dashboard(faculty['faculty_id'], faculty['name'])
            return
            
        # Check faculty
        cur.execute("SELECT * FROM Faculty WHERE email=%s AND password=%s", (e, p))
        faculty = cur.fetchone()
        if faculty:
            popup.destroy()
            show_faculty_dashboard(faculty['faculty_id'], faculty['name'])
            return
            
        # Check student
        cur.execute("SELECT * FROM Students WHERE email=%s AND password=%s", (e, p))
        student = cur.fetchone()
        
        if student:
            if student['is_banned']:
                messagebox.showerror("Account Banned", "Your account has been banned. Please contact administrator.")
                return
            popup.destroy()
            show_student_dashboard(student['student_id'], student['name'])
        else:
            messagebox.showerror("Invalid Credentials", "Wrong email or password")
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error during login: {err}")
    finally:
        if conn.is_connected():
            cur.close()
            conn.close()

def show_login_popup():
    popup = tk.Toplevel()
    popup.title("Login")
    popup.geometry("500x500")  # Increased height to accommodate register button
    popup.configure(bg=StyleConfig.BACKGROUND)
    popup.protocol("WM_DELETE_WINDOW", root.destroy)

    # Center the window
    popup.update_idletasks()
    width = popup.winfo_width()
    height = popup.winfo_height()
    x = (popup.winfo_screenwidth() // 2) - (width // 2)
    y = (popup.winfo_screenheight() // 2) - (height // 2)
    popup.geometry(f"{width}x{height}+{x}+{y}")

    # Main container
    main_frame = ttk.Frame(popup, style='TFrame')
    main_frame.pack(fill='both', expand=True, padx=40, pady=40)
    
    # Decorative header
    header_frame = tk.Canvas(main_frame, height=100, bg=StyleConfig.PRIMARY, highlightthickness=0)
    header_frame.pack(fill='x', pady=(0, 30))
    header_frame.create_text(250, 50, text="🎓", font=('Segoe UI', 40), fill='white')
    header_frame.create_text(250, 90, text="University Portal", font=('Segoe UI', 14, 'bold'), fill='white')
    
    # Login form
    form_frame = ttk.Frame(main_frame, style='TFrame')
    form_frame.pack(fill='x', pady=10)
    
    ttk.Label(form_frame, text="Email Address:", style='TLabel').pack(anchor='w', pady=(5, 0))
    email_entry = ttk.Entry(form_frame)
    email_entry.pack(fill='x', pady=(0, 15), ipady=5)
    
    ttk.Label(form_frame, text="Password:", style='TLabel').pack(anchor='w', pady=(5, 0))
    pass_entry = ttk.Entry(form_frame, show="•")
    pass_entry.pack(fill='x', pady=(0, 20), ipady=5)
    
    # Login button
    login_btn = create_rounded_button(form_frame, "Login", lambda: do_login(email_entry, pass_entry, popup), StyleConfig.PRIMARY, width=300)
    login_btn.pack(pady=10)
    
    # Registration buttons frame
    reg_frame = ttk.Frame(main_frame)
    reg_frame.pack(fill='x', pady=10)
    
    # Student registration button
    student_reg_btn = create_rounded_button(reg_frame, "Register as Student", 
                                       lambda: [popup.destroy(), show_student_registration_popup()], 
                                       StyleConfig.ACCENT, width=200)
    student_reg_btn.pack(side='left', expand=True, padx=5)
    
    # Faculty registration button
    faculty_reg_btn = create_rounded_button(reg_frame, "Register as Faculty", 
                                       lambda: [popup.destroy(), show_faculty_registration_popup()], 
                                       StyleConfig.SECONDARY, width=200)
    faculty_reg_btn.pack(side='left', expand=True, padx=5)
    
    # Options frame for "Forgot Password" etc.
    options_frame = ttk.Frame(main_frame, style='TFrame')
    options_frame.pack(fill='x', pady=(10, 0))
    
    # Forgot password option (placeholder)
    forgot_btn = ttk.Label(options_frame, text="Forgot password?", style='TLabel', 
                          foreground=StyleConfig.ACCENT, cursor="hand2")
    forgot_btn.pack(side='left')
    forgot_btn.bind("<Button-1>", lambda e: messagebox.showinfo("Forgot Password", "Please contact administrator to reset your password"))

def generate_student_id():
    conn = get_connection()
    if not conn:
        return None
        
    try:
        cur = conn.cursor()
        # Get the highest student ID
        cur.execute("SELECT MAX(student_id) FROM Students")
        max_id = cur.fetchone()[0]
        
        # If no students yet, start from 1924001
        if max_id is None:
            return 1924001
        else:
            return max_id + 1
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error generating student ID: {err}")
        return None
    finally:
        if conn.is_connected():
            cur.close()
            conn.close()

def generate_faculty_id():
    conn = get_connection()
    if not conn:
        return None
        
    try:
        cur = conn.cursor()
        # Get the highest faculty ID
        cur.execute("SELECT MAX(faculty_id) FROM Faculty")
        max_id = cur.fetchone()[0]
        
        # If no faculty yet, start from 1001
        if max_id is None:
            return 1001
        else:
            return max_id + 1
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error generating faculty ID: {err}")
        return None
    finally:
        if conn.is_connected():
            cur.close()
            conn.close()

def do_student_register(entries, reg):
    name = entries[0].get().strip()
    email = entries[1].get().strip()
    pwd = entries[2].get().strip()
    confirm_pwd = entries[3].get().strip()
    
    if not all([name, email, pwd, confirm_pwd]):
        messagebox.showwarning("Input Error", "All fields are required")
        return
        
    if "@" not in email or "." not in email:
        messagebox.showwarning("Input Error", "Please enter a valid email address")
        return
        
    if pwd != confirm_pwd:
        messagebox.showerror("Input Error", "Passwords don't match")
        return
        
    conn = get_connection()
    if not conn:
        return
        
    try:
        cur = conn.cursor()
        # Check if email already exists
        cur.execute("SELECT * FROM Students WHERE email=%s", (email,))
        if cur.fetchone():
            messagebox.showerror("Error", "Email already registered")
            return
        
        # Generate student ID starting from 1924001
        student_id = generate_student_id()
        if not student_id:
            return
            
        cur.execute("INSERT INTO Students(student_id, name, email, password) VALUES (%s,%s,%s,%s)", 
                    (student_id, name, email, pwd))
        conn.commit()
        messagebox.showinfo("Success", f"Registration successful! Your Student ID is {student_id}. Please login.")
        reg.destroy()
        show_login_popup()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error during registration: {err}")
    finally:
        if conn.is_connected():
            cur.close()
            conn.close()

def do_faculty_register(entries, reg):
    name = entries[0].get().strip()
    email = entries[1].get().strip()
    pwd = entries[2].get().strip()
    confirm_pwd = entries[3].get().strip()
    department = entries[4].get().strip()
    
    if not all([name, email, pwd, confirm_pwd, department]):
        messagebox.showwarning("Input Error", "All fields are required")
        return
        
    if "@" not in email or "." not in email:
        messagebox.showwarning("Input Error", "Please enter a valid email address")
        return
        
    if pwd != confirm_pwd:
        messagebox.showerror("Input Error", "Passwords don't match")
        return
        
    conn = get_connection()
    if not conn:
        return
        
    try:
        cur = conn.cursor()
        # Check if email already exists
        cur.execute("SELECT * FROM Faculty WHERE email=%s", (email,))
        if cur.fetchone():
            messagebox.showerror("Error", "Email already registered")
            return
        
        # Generate faculty ID
        faculty_id = generate_faculty_id()
        if not faculty_id:
            return
            
        cur.execute("INSERT INTO Faculty(faculty_id, name, email, password, department) VALUES (%s,%s,%s,%s,%s)", 
                    (faculty_id, name, email, pwd, department))
        conn.commit()
        messagebox.showinfo("Success", f"Registration successful! Your Faculty ID is {faculty_id}. Please login.")
        reg.destroy()
        show_login_popup()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error during registration: {err}")
    finally:
        if conn.is_connected():
            cur.close()
            conn.close()

def show_student_registration_popup():
    reg = tk.Toplevel()
    reg.title("Student Registration")
    reg.geometry("500x550")
    reg.configure(bg=StyleConfig.BACKGROUND)
    reg.protocol("WM_DELETE_WINDOW", lambda: [reg.destroy(), show_login_popup()])

    # Center the window
    reg.update_idletasks()
    width = reg.winfo_width()
    height = reg.winfo_height()
    x = (reg.winfo_screenwidth() // 2) - (width // 2)
    y = (reg.winfo_screenheight() // 2) - (height // 2)
    reg.geometry(f"{width}x{height}+{x}+{y}")

    # Main container
    main_frame = ttk.Frame(reg, style='TFrame')
    main_frame.pack(fill='both', expand=True, padx=40, pady=40)
    
    # Header
    header_frame = tk.Canvas(main_frame, height=80, bg=StyleConfig.ACCENT, highlightthickness=0)
    header_frame.pack(fill='x', pady=(0, 30))
    header_frame.create_text(250, 40, text="👤 Student Registration", font=('Segoe UI', 16, 'bold'), fill='white')
    
    # Registration form
    form_frame = ttk.Frame(main_frame, style='TFrame')
    form_frame.pack(fill='x', pady=10)
    
    fields = [
        ("Full Name", "John Doe"),
        ("Email Address", "example@university.edu"),
        ("Password", ""),
        ("Confirm Password", "")
    ]
    
    entries = []
    for i, (label, placeholder) in enumerate(fields):
        ttk.Label(form_frame, text=label+":", style='TLabel').grid(row=i, column=0, sticky='w', pady=5)
        entry = ttk.Entry(form_frame)
        entry.grid(row=i, column=1, sticky='ew', pady=5, ipady=5)
        entry.insert(0, placeholder)
        entries.append(entry)
    
    # Password fields
    entries[2].config(show="•")
    entries[3].config(show="•")
    
    # Terms checkbox
    terms_var = tk.IntVar()
    terms_check = ttk.Checkbutton(form_frame, text="I agree to terms and conditions", 
                                variable=terms_var, style='TLabel')
    terms_check.grid(row=4, column=0, columnspan=2, pady=10, sticky='w')
    
    # Register button
    register_btn = create_rounded_button(form_frame, "Create Account", 
                                       lambda: do_student_register(entries, reg) if terms_var.get() else 
                                       lambda: messagebox.showwarning("Terms", "Please accept terms and conditions"), 
                                       StyleConfig.SUCCESS, width=300)
    register_btn.grid(row=5, column=0, columnspan=2, pady=20)
    
    # Back to login
    back_frame = ttk.Frame(form_frame, style='TFrame')
    back_frame.grid(row=6, column=0, columnspan=2, sticky='ew')
    
    ttk.Label(back_frame, text="Already have an account?", style='TLabel').pack(side='left')
    login_btn = ttk.Label(back_frame, text="Login here", style='TLabel', 
                         foreground=StyleConfig.ACCENT, cursor="hand2")
    login_btn.pack(side='left', padx=5)
    login_btn.bind("<Button-1>", lambda e: [reg.destroy(), show_login_popup()])

def show_faculty_registration_popup():
    reg = tk.Toplevel()
    reg.title("Faculty Registration")
    reg.geometry("500x600")
    reg.configure(bg=StyleConfig.BACKGROUND)
    reg.protocol("WM_DELETE_WINDOW", lambda: [reg.destroy(), show_login_popup()])

    # Center the window
    reg.update_idletasks()
    width = reg.winfo_width()
    height = reg.winfo_height()
    x = (reg.winfo_screenwidth() // 2) - (width // 2)
    y = (reg.winfo_screenheight() // 2) - (height // 2)
    reg.geometry(f"{width}x{height}+{x}+{y}")

    # Main container
    main_frame = ttk.Frame(reg, style='TFrame')
    main_frame.pack(fill='both', expand=True, padx=40, pady=40)
    
    # Header
    header_frame = tk.Canvas(main_frame, height=80, bg=StyleConfig.SECONDARY, highlightthickness=0)
    header_frame.pack(fill='x', pady=(0, 30))
    header_frame.create_text(250, 40, text="👨‍🏫 Faculty Registration", font=('Segoe UI', 16, 'bold'), fill='white')
    
    # Registration form
    form_frame = ttk.Frame(main_frame, style='TFrame')
    form_frame.pack(fill='x', pady=10)
    
    fields = [
        ("Full Name", "Dr. John Smith"),
        ("Email Address", "faculty@university.edu"),
        ("Password", ""),
        ("Confirm Password", ""),
        ("Department", "Computer Science")
    ]
    
    entries = []
    for i, (label, placeholder) in enumerate(fields):
        ttk.Label(form_frame, text=label+":", style='TLabel').grid(row=i, column=0, sticky='w', pady=5)
        entry = ttk.Entry(form_frame)
        entry.grid(row=i, column=1, sticky='ew', pady=5, ipady=5)
        entry.insert(0, placeholder)
        entries.append(entry)
    
    # Password fields
    entries[2].config(show="•")
    entries[3].config(show="•")
    
    # Terms checkbox
    terms_var = tk.IntVar()
    terms_check = ttk.Checkbutton(form_frame, text="I agree to terms and conditions", 
                                variable=terms_var, style='TLabel')
    terms_check.grid(row=5, column=0, columnspan=2, pady=10, sticky='w')
    
    # Register button
    register_btn = create_rounded_button(form_frame, "Create Account", 
                                       lambda: do_faculty_register(entries, reg) if terms_var.get() else 
                                       lambda: messagebox.showwarning("Terms", "Please accept terms and conditions"), 
                                       StyleConfig.SUCCESS, width=300)
    register_btn.grid(row=6, column=0, columnspan=2, pady=20)
    
    # Back to login
    back_frame = ttk.Frame(form_frame, style='TFrame')
    back_frame.grid(row=7, column=0, columnspan=2, sticky='ew')
    
    ttk.Label(back_frame, text="Already have an account?", style='TLabel').pack(side='left')
    login_btn = ttk.Label(back_frame, text="Login here", style='TLabel', 
                         foreground=StyleConfig.ACCENT, cursor="hand2")
    login_btn.pack(side='left', padx=5)
    login_btn.bind("<Button-1>", lambda e: [reg.destroy(), show_login_popup()])

# ========== STUDENT MODULE ==========
def show_student_dashboard(sid, name):
    dash = tk.Toplevel()
    dash.title(f"{name}'s Dashboard")
    dash.geometry("900x700")
    dash.configure(bg=StyleConfig.BACKGROUND)
    dash.protocol("WM_DELETE_WINDOW", lambda: [dash.destroy(), root.destroy()])

    # First define all the nested functions
    def logout():
        dash.destroy()
        show_login_popup()

    def view_courses():
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT course_id, course_name, seats_left FROM Courses WHERE is_active=TRUE")
            rows = cur.fetchall()
            
            top = tk.Toplevel(dash)
            top.title("Available Courses")
            top.geometry("800x500")
            top.configure(bg=StyleConfig.BACKGROUND)
            
            main_frame = ttk.Frame(top)
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            create_header(main_frame, "Available Courses")
            
            tree_frame = ttk.Frame(main_frame)
            tree_frame.pack(fill='both', expand=True)
            
            scrollbar = ttk.Scrollbar(tree_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            tree = ttk.Treeview(tree_frame, columns=("ID", "Name", "Seats"), show="headings", yscrollcommand=scrollbar.set)
            scrollbar.config(command=tree.yview)
            
            tree.heading("ID", text="Course ID")
            tree.heading("Name", text="Course Name")
            tree.heading("Seats", text="Seats Available")
            
            tree.column("ID", width=100)
            tree.column("Name", width=200)
            tree.column("Seats", width=100)
            
            for row in rows:
                tree.insert('', tk.END, values=(row['course_id'], row['course_name'], row['seats_left']))
            tree.pack(fill='both', expand=True)
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error fetching courses: {err}")
        finally:
            if conn.is_connected():
                cur.close()
                conn.close()

    def enroll_course():
        enroll_win = tk.Toplevel(dash)
        enroll_win.title("Enroll in Course")
        enroll_win.geometry("500x350")
        enroll_win.configure(bg=StyleConfig.BACKGROUND)
        
        main_frame = ttk.Frame(enroll_win)
        main_frame.pack(fill='both', expand=True, padx=30, pady=30)
        
        create_header(main_frame, "Enroll in Course")
        
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill='x', pady=20)
        
        ttk.Label(form_frame, text="Course ID:").grid(row=0, column=0, sticky='w', pady=10)
        cid_entry = ttk.Entry(form_frame)
        cid_entry.grid(row=0, column=1, sticky='ew', pady=10, ipady=5)
        
        ttk.Label(form_frame, text="Semester:").grid(row=1, column=0, sticky='w', pady=10)
        sem_entry = ttk.Entry(form_frame)
        sem_entry.grid(row=1, column=1, sticky='ew', pady=10, ipady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=20)
        
        def do_enroll():
            cid = cid_entry.get().strip()
            sem = sem_entry.get().strip()
            
            if not cid or not sem:
                messagebox.showwarning("Input Error", "Please fill all fields")
                return
                
            conn = get_connection()
            if not conn:
                return
            try:
                cur = conn.cursor(dictionary=True)
                # Check if already enrolled
                cur.execute("SELECT * FROM Enrollments WHERE student_id=%s AND course_id=%s", (sid, cid))
                if cur.fetchone():
                    messagebox.showwarning("Warning", f"You are already enrolled in course {cid}")
                    return
                
                # Check if course exists and has seats
                cur.execute("SELECT seats_left, is_active FROM Courses WHERE course_id=%s", (cid,))
                result = cur.fetchone()
                if not result:
                    messagebox.showerror("Error", "Invalid course ID")
                    return
                
                if not result['is_active']:
                    messagebox.showerror("Error", "This course is not currently active")
                    return
                
                if result['seats_left'] <= 0:
                    messagebox.showerror("Error", "No seats available for this course")
                    return
                
                # Enroll student
                cur.execute("INSERT INTO Enrollments (student_id, course_id, semester) VALUES (%s,%s,%s)",
                            (sid, cid, sem))
                # Update seats
                cur.execute("UPDATE Courses SET seats_left = seats_left - 1 WHERE course_id=%s", (cid,))
                conn.commit()
                
                # Generate QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(f"StudentID:{sid}|CourseID:{cid}|Sem:{sem}")
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                os.makedirs("qr_codes", exist_ok=True)
                img.save(f"qr_codes/QR_{sid}_{cid}.png")
                
                messagebox.showinfo("Success", f"Successfully enrolled in {cid}!\nQR code generated.")
                enroll_win.destroy()
            except mysql.connector.Error as err:
                messagebox.showerror("Database Error", f"Error during enrollment: {err}")
            finally:
                if conn.is_connected():
                    cur.close()
                    conn.close()
        
        create_rounded_button(button_frame, "Enroll Now", do_enroll, StyleConfig.SUCCESS, width=150).pack()

    def drop_course():
        drop_win = tk.Toplevel(dash)
        drop_win.title("Drop Course")
        drop_win.geometry("500x300")
        drop_win.configure(bg=StyleConfig.BACKGROUND)
        
        main_frame = ttk.Frame(drop_win)
        main_frame.pack(fill='both', expand=True, padx=30, pady=30)
        
        create_header(main_frame, "Drop Course")
        
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill='x', pady=20)
        
        ttk.Label(form_frame, text="Course ID:").grid(row=0, column=0, sticky='w', pady=10)
        cid_entry = ttk.Entry(form_frame)
        cid_entry.grid(row=0, column=1, sticky='ew', pady=10, ipady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=20)
        
        def do_drop():
            cid = cid_entry.get().strip()
            if not cid:
                messagebox.showwarning("Input Error", "Please enter a course ID")
                return
                
            conn = get_connection()
            if not conn:
                return
            try:
                cur = conn.cursor()
                # Check if enrolled
                cur.execute("SELECT * FROM Enrollments WHERE student_id=%s AND course_id=%s", (sid, cid))
                if not cur.fetchone():
                    messagebox.showwarning("Warning", f"You are not enrolled in course {cid}")
                    return
                
                # Drop course
                cur.execute("DELETE FROM Enrollments WHERE student_id=%s AND course_id=%s", (sid, cid))
                if cur.rowcount > 0:
                    # Update seats
                    cur.execute("UPDATE Courses SET seats_left = seats_left + 1 WHERE course_id=%s", (cid,))
                    conn.commit()
                    messagebox.showinfo("Success", f"Successfully dropped course {cid}")
                    drop_win.destroy()
                else:
                    messagebox.showerror("Error", "Failed to drop course")
            except mysql.connector.Error as err:
                messagebox.showerror("Database Error", f"Error dropping course: {err}")
            finally:
                if conn.is_connected():
                    cur.close()
                    conn.close()
        
        create_rounded_button(button_frame, "Drop Course", do_drop, StyleConfig.DANGER, width=150).pack()

    def my_enrollments():
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("""SELECT E.course_id, C.course_name, E.semester, E.timestamp 
                        FROM Enrollments E JOIN Courses C USING(course_id)
                        WHERE E.student_id=%s""", (sid,))
            rows = cur.fetchall()
            
            top = tk.Toplevel(dash)
            top.title("My Enrollments")
            top.geometry("800x500")
            top.configure(bg=StyleConfig.BACKGROUND)
            
            main_frame = ttk.Frame(top)
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            create_header(main_frame, "My Enrollments")
            
            tree_frame = ttk.Frame(main_frame)
            tree_frame.pack(fill='both', expand=True)
            
            scrollbar = ttk.Scrollbar(tree_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            tree = ttk.Treeview(tree_frame, 
                              columns=("CID", "Name", "Sem", "Enrolled On"), 
                              show="headings", 
                              yscrollcommand=scrollbar.set)
            scrollbar.config(command=tree.yview)
            
            tree.heading("CID", text="Course ID")
            tree.heading("Name", text="Course Name")
            tree.heading("Sem", text="Semester")
            tree.heading("Enrolled On", text="Enrolled On")
            
            tree.column("CID", width=100)
            tree.column("Name", width=200)
            tree.column("Sem", width=100)
            tree.column("Enrolled On", width=150)
            
            for row in rows:
                tree.insert('', tk.END, values=(row['course_id'], row['course_name'], row['semester'], row['timestamp']))
            tree.pack(fill='both', expand=True)
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error fetching enrollments: {err}")
        finally:
            if conn.is_connected():
                cur.close()
                conn.close()

    def my_results():
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("""SELECT R.course_id, C.course_name, R.grade 
                        FROM Results R JOIN Courses C USING(course_id)
                        WHERE R.student_id=%s""", (sid,))
            rows = cur.fetchall()
            
            top = tk.Toplevel(dash)
            top.title("My Results")
            top.geometry("600x400")
            top.configure(bg=StyleConfig.BACKGROUND)
            
            main_frame = ttk.Frame(top)
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            create_header(main_frame, "My Results")
            
            if rows:
                tree_frame = ttk.Frame(main_frame)
                tree_frame.pack(fill='both', expand=True)
                
                scrollbar = ttk.Scrollbar(tree_frame)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                tree = ttk.Treeview(tree_frame, 
                                  columns=("CID", "Name", "Grade"), 
                                  show="headings", 
                                  yscrollcommand=scrollbar.set)
                scrollbar.config(command=tree.yview)
                
                tree.heading("CID", text="Course ID")
                tree.heading("Name", text="Course Name")
                tree.heading("Grade", text="Grade")
                
                tree.column("CID", width=100)
                tree.column("Name", width=200)
                tree.column("Grade", width=50)
                
                for row in rows:
                    tree.insert('', tk.END, values=(row['course_id'], row['course_name'], row['grade']))
                tree.pack(fill='both', expand=True)
            else:
                ttk.Label(main_frame, text="No results available yet").pack(pady=20)
                
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error fetching results: {err}")
        finally:
            if conn.is_connected():
                cur.close()
                conn.close()

    def view_profile():
        show_student_profile(sid, dash)

    # Now create the dashboard UI
    main_frame = ttk.Frame(dash)
    main_frame.pack(fill='both', expand=True, padx=30, pady=30)

    # Header with welcome message
    welcome_frame = tk.Canvas(main_frame, height=120, bg=StyleConfig.PRIMARY, highlightthickness=0)
    welcome_frame.pack(fill='x', pady=(0, 20))
    
    # Welcome message with student's name
    welcome_frame.create_text(450, 40, text=f"Welcome back, {name}!", font=('Segoe UI', 20, 'bold'), fill='white')
    welcome_frame.create_text(450, 70, text=f"Student ID: {sid}", font=('Segoe UI', 12), fill='white')
    
    # Logout button in header
    logout_btn = tk.Canvas(welcome_frame, width=80, height=30, bg=StyleConfig.DANGER, highlightthickness=0)
    logout_btn.create_text(40, 15, text="Logout", fill='white', font=('Segoe UI', 10, 'bold'))
    logout_btn.bind("<Button-1>", lambda e: logout())
    logout_btn.place(relx=0.95, rely=0.5, anchor='e')
    
    # Quick stats row
    stats_frame = ttk.Frame(main_frame)
    stats_frame.pack(fill='x', pady=(0, 20))
    
    # Get enrollment count
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM Enrollments WHERE student_id=%s", (sid,))
            enroll_count = cur.fetchone()[0]
            
            cur.execute("SELECT AVG(CASE grade WHEN 'A' THEN 4 WHEN 'B' THEN 3 WHEN 'C' THEN 2 WHEN 'D' THEN 1 ELSE 0 END) FROM Results WHERE student_id=%s", (sid,))
            gpa = cur.fetchone()[0] or 0
        except mysql.connector.Error:
            enroll_count = 0
            gpa = 0
        finally:
            if conn.is_connected():
                cur.close()
                conn.close()
    else:
        enroll_count = 0
        gpa = 0
    
    # Create stat cards
    create_card(stats_frame, "Courses Enrolled", enroll_count, "📚", StyleConfig.SUCCESS).pack(side='left', expand=True, fill='x', padx=5)
    create_card(stats_frame, "Current GPA", f"{gpa:.2f}", "🏆", StyleConfig.ACCENT).pack(side='left', expand=True, fill='x', padx=5)
    create_card(stats_frame, "Account Status", "Active", "✅", StyleConfig.INFO).pack(side='left', expand=True, fill='x', padx=5)
    
    # Action buttons
    actions_frame = ttk.Frame(main_frame)
    actions_frame.pack(fill='x', pady=(0, 20))
    
    # Row 1
    row1 = ttk.Frame(actions_frame)
    row1.pack(fill='x', pady=5)
    create_rounded_button(row1, "View Available Courses", view_courses, StyleConfig.PRIMARY, width=200).pack(side='left', padx=5)
    create_rounded_button(row1, "Enroll in Course", enroll_course, StyleConfig.SUCCESS, width=200).pack(side='left', padx=5)
    
    # Row 2
    row2 = ttk.Frame(actions_frame)
    row2.pack(fill='x', pady=5)
    create_rounded_button(row2, "My Enrollments", my_enrollments, StyleConfig.INFO, width=200).pack(side='left', padx=5)
    create_rounded_button(row2, "Drop Course", drop_course, StyleConfig.WARNING, width=200).pack(side='left', padx=5)
    
    # Row 3
    row3 = ttk.Frame(actions_frame)
    row3.pack(fill='x', pady=5)
    create_rounded_button(row3, "My Results", my_results, StyleConfig.SECONDARY, width=200).pack(side='left', padx=5)
    create_rounded_button(row3, "My Profile", view_profile, StyleConfig.ACCENT, width=200).pack(side='left', padx=5)

# ========== FACULTY MODULE ==========
def show_faculty_dashboard(fid, name):
    dash = tk.Toplevel()
    dash.title(f"{name}'s Dashboard")
    dash.geometry("1000x800")
    dash.configure(bg=StyleConfig.BACKGROUND)
    dash.protocol("WM_DELETE_WINDOW", lambda: [dash.destroy(), root.destroy()])

    # Faculty dashboard functions
    def logout():
        dash.destroy()
        show_login_popup()

    def create_course():
        create_win = tk.Toplevel(dash)
        create_win.title("Create New Course")
        create_win.geometry("600x500")
        create_win.configure(bg=StyleConfig.BACKGROUND)
        
        main_frame = ttk.Frame(create_win)
        main_frame.pack(fill='both', expand=True, padx=30, pady=30)
        
        create_header(main_frame, "Create New Course")
        
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill='x', pady=20)
        
        fields = [
            ("Course ID", "CS101"),
            ("Course Name", "Introduction to Programming"),
            ("Credits", "3"),
            ("Course Type", "Core/Elective"),
            ("Max Seats", "30")
        ]
        
        entries = []
        for i, (label, placeholder) in enumerate(fields):
            ttk.Label(form_frame, text=label+":", style='TLabel').grid(row=i, column=0, sticky='w', pady=10)
            entry = ttk.Entry(form_frame)
            entry.grid(row=i, column=1, sticky='ew', pady=10, ipady=5)
            entry.insert(0, placeholder)
            entries.append(entry)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=20)
        
        def do_create():
            cid = entries[0].get().strip()
            name = entries[1].get().strip()
            credits = entries[2].get().strip()
            ctype = entries[3].get().strip()
            max_seats = entries[4].get().strip()
            
            if not all([cid, name, credits, ctype, max_seats]):
                messagebox.showwarning("Input Error", "All fields are required")
                return
                
            try:
                credits = int(credits)
                max_seats = int(max_seats)
            except ValueError:
                messagebox.showerror("Input Error", "Credits and Seats must be numbers")
                return
                
            conn = get_connection()
            if not conn:
                return
                
            try:
                cur = conn.cursor()
                # Check if course exists
                cur.execute("SELECT * FROM Courses WHERE course_id=%s", (cid,))
                if cur.fetchone():
                    messagebox.showerror("Error", "Course ID already exists")
                    return
                
                # Create course
                cur.execute("""
                    INSERT INTO Courses (course_id, course_name, instructor_id, credits, course_type, max_seats, seats_left)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (cid, name, fid, credits, ctype, max_seats, max_seats))
                conn.commit()
                
                messagebox.showinfo("Success", f"Course {cid} created successfully!")
                create_win.destroy()
            except mysql.connector.Error as err:
                messagebox.showerror("Database Error", f"Error creating course: {err}")
            finally:
                if conn.is_connected():
                    cur.close()
                    conn.close()
        
        create_rounded_button(button_frame, "Create Course", do_create, StyleConfig.SUCCESS, width=200).pack()

    def manage_courses():
        conn = get_connection()
        if not conn:
            return
            
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT course_id, course_name, credits, course_type, seats_left, is_active 
                FROM Courses 
                WHERE instructor_id=%s
            """, (fid,))
            courses = cur.fetchall()
            
            top = tk.Toplevel(dash)
            top.title("Manage My Courses")
            top.geometry("900x600")
            top.configure(bg=StyleConfig.BACKGROUND)
            
            main_frame = ttk.Frame(top)
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            create_header(main_frame, "My Courses")
            
            tree_frame = ttk.Frame(main_frame)
            tree_frame.pack(fill='both', expand=True)
            
            scrollbar = ttk.Scrollbar(tree_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            tree = ttk.Treeview(tree_frame, 
                              columns=("CID", "Name", "Credits", "Type", "Seats", "Status"), 
                              show="headings", 
                              yscrollcommand=scrollbar.set)
            scrollbar.config(command=tree.yview)
            
            tree.heading("CID", text="Course ID")
            tree.heading("Name", text="Course Name")
            tree.heading("Credits", text="Credits")
            tree.heading("Type", text="Type")
            tree.heading("Seats", text="Seats Left")
            tree.heading("Status", text="Status")
            
            tree.column("CID", width=100)
            tree.column("Name", width=200)
            tree.column("Credits", width=80)
            tree.column("Type", width=100)
            tree.column("Seats", width=80)
            tree.column("Status", width=100)
            
            for course in courses:
                status = "Active" if course['is_active'] else "Inactive"
                tree.insert('', tk.END, values=(
                    course['course_id'],
                    course['course_name'],
                    course['credits'],
                    course['course_type'],
                    course['seats_left'],
                    status
                ))
            
            tree.pack(fill='both', expand=True)
            
            # Add buttons to toggle course status
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill='x', pady=10)
            
            def toggle_course():
                selected = tree.focus()
                if not selected:
                    messagebox.showwarning("Selection Error", "Please select a course first")
                    return
                    
                item = tree.item(selected)
                cid = item['values'][0]
                current_status = item['values'][5] == "Active"
                
                conn = get_connection()
                if not conn:
                    return
                    
                try:
                    cur = conn.cursor()
                    cur.execute("UPDATE Courses SET is_active=%s WHERE course_id=%s", 
                              (not current_status, cid))
                    conn.commit()
                    
                    # Update treeview
                    tree.item(selected, values=(
                        item['values'][0],
                        item['values'][1],
                        item['values'][2],
                        item['values'][3],
                        item['values'][4],
                        "Inactive" if current_status else "Active"
                    ))
                    
                    messagebox.showinfo("Success", f"Course {cid} status updated")
                except mysql.connector.Error as err:
                    messagebox.showerror("Database Error", f"Error updating course: {err}")
                finally:
                    if conn.is_connected():
                        cur.close()
                        conn.close()
            
            create_rounded_button(btn_frame, "Toggle Status", toggle_course, StyleConfig.INFO, width=150).pack(side='left', padx=5)
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error fetching courses: {err}")
        finally:
            if conn.is_connected():
                cur.close()
                conn.close()

    def view_students():
        conn = get_connection()
        if not conn:
            return
            
        try:
            cur = conn.cursor(dictionary=True)
            # Get all students (both active and banned)
            cur.execute("""
                SELECT s.student_id, s.name, s.email, s.is_banned, COUNT(e.course_id) as courses_enrolled
                FROM Students s
                LEFT JOIN Enrollments e ON s.student_id = e.student_id
                GROUP BY s.student_id
                ORDER BY s.name
            """)
            students = cur.fetchall()
            
            top = tk.Toplevel(dash)
            top.title("Student Management")
            top.geometry("900x600")
            top.configure(bg=StyleConfig.BACKGROUND)
            
            main_frame = ttk.Frame(top)
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            create_header(main_frame, "Student Management")
            
            tree_frame = ttk.Frame(main_frame)
            tree_frame.pack(fill='both', expand=True)
            
            scrollbar = ttk.Scrollbar(tree_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            tree = ttk.Treeview(tree_frame, 
                              columns=("SID", "Name", "Email", "Courses", "Status"), 
                              show="headings", 
                              yscrollcommand=scrollbar.set)
            scrollbar.config(command=tree.yview)
            
            tree.heading("SID", text="Student ID")
            tree.heading("Name", text="Name")
            tree.heading("Email", text="Email")
            tree.heading("Courses", text="Courses Enrolled")
            tree.heading("Status", text="Status")
            
            tree.column("SID", width=100)
            tree.column("Name", width=200)
            tree.column("Email", width=250)
            tree.column("Courses", width=100)
            tree.column("Status", width=100)
            
            for student in students:
                status = "Banned" if student['is_banned'] else "Active"
                tree.insert('', tk.END, values=(
                    student['student_id'],
                    student['name'],
                    student['email'],
                    student['courses_enrolled'],
                    status
                ), tags=("banned" if student['is_banned'] else "active"))
            
            # Configure tag colors
            tree.tag_configure("banned", foreground=StyleConfig.DANGER)
            tree.tag_configure("active", foreground=StyleConfig.SUCCESS)
            
            tree.pack(fill='both', expand=True)
            
            # Add buttons for student management
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill='x', pady=10)
            
            def view_student_profile():
                selected = tree.focus()
                if not selected:
                    messagebox.showwarning("Selection Error", "Please select a student first")
                    return
                    
                item = tree.item(selected)
                sid = item['values'][0]
                show_student_profile(sid, top)
            
            def toggle_ban_status():
                selected = tree.focus()
                if not selected:
                    messagebox.showwarning("Selection Error", "Please select a student first")
                    return
                    
                item = tree.item(selected)
                sid = item['values'][0]
                name = item['values'][1]
                current_status = item['values'][4] == "Banned"
                
                action = "unban" if current_status else "ban"
                if messagebox.askyesno("Confirm Action", f"Are you sure you want to {action} {name}?"):
                    conn = get_connection()
                    if not conn:
                        return
                        
                    try:
                        cur = conn.cursor()
                        cur.execute("UPDATE Students SET is_banned=%s WHERE student_id=%s", 
                                    (not current_status, sid))
                        conn.commit()
                        
                        # Update treeview
                        new_status = "Active" if current_status else "Banned"
                        tree.item(selected, values=(
                            item['values'][0],
                            item['values'][1],
                            item['values'][2],
                            item['values'][3],
                            new_status
                        ), tags=("active" if current_status else "banned"))
                        
                        messagebox.showinfo("Success", f"Student {name} has been {action}ned")
                    except mysql.connector.Error as err:
                        messagebox.showerror("Database Error", f"Error updating student status: {err}")
                    finally:
                        if conn.is_connected():
                            cur.close()
                            conn.close()
            
            create_rounded_button(btn_frame, "View Profile", view_student_profile, StyleConfig.INFO, width=150).pack(side='left', padx=5)
            create_rounded_button(btn_frame, "Ban/Unban", toggle_ban_status, StyleConfig.DANGER, width=150).pack(side='left', padx=5)
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error fetching students: {err}")
        finally:
            if conn.is_connected():
                cur.close()
                conn.close()

    def manage_results():
        conn = get_connection()
        if not conn:
            return
            
        try:
            cur = conn.cursor(dictionary=True)
            # Get courses taught by this faculty
            cur.execute("SELECT course_id, course_name FROM Courses WHERE instructor_id=%s", (fid,))
            courses = cur.fetchall()
            
            if not courses:
                messagebox.showinfo("No Courses", "You are not teaching any courses yet")
                return
                
            top = tk.Toplevel(dash)
            top.title("Manage Results")
            top.geometry("800x600")
            top.configure(bg=StyleConfig.BACKGROUND)
            
            main_frame = ttk.Frame(top)
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            create_header(main_frame, "Manage Results")
            
            # Course selection
            course_frame = ttk.Frame(main_frame)
            course_frame.pack(fill='x', pady=10)
            
            ttk.Label(course_frame, text="Select Course:").pack(side='left')
            course_var = tk.StringVar()
            course_dropdown = ttk.Combobox(course_frame, textvariable=course_var, state='readonly')
            course_dropdown['values'] = [(f"{c['course_id']} - {c['course_name']}") for c in courses]
            course_dropdown.pack(side='left', padx=10)
            course_dropdown.current(0)
            
            # Students in selected course
            students_frame = ttk.Frame(main_frame)
            students_frame.pack(fill='both', expand=True)
            
            scrollbar = ttk.Scrollbar(students_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            students_tree = ttk.Treeview(students_frame, 
                                       columns=("SID", "Name", "Grade"), 
                                       show="headings", 
                                       yscrollcommand=scrollbar.set)
            scrollbar.config(command=students_tree.yview)
            
            students_tree.heading("SID", text="Student ID")
            students_tree.heading("Name", text="Name")
            students_tree.heading("Grade", text="Grade")
            
            students_tree.column("SID", width=100)
            students_tree.column("Name", width=200)
            students_tree.column("Grade", width=50)
            
            students_tree.pack(fill='both', expand=True)
            
            # Grade entry
            grade_frame = ttk.Frame(main_frame)
            grade_frame.pack(fill='x', pady=10)
            
            ttk.Label(grade_frame, text="Grade (A/B/C/D/F):").pack(side='left')
            grade_entry = ttk.Entry(grade_frame, width=5)
            grade_entry.pack(side='left', padx=10)
            
            def load_students():
                selected_course = course_var.get().split(" - ")[0]
                
                conn = get_connection()
                if not conn:
                    return
                    
                try:
                    cur = conn.cursor(dictionary=True)
                    # Get enrolled students
                    cur.execute("""
                        SELECT s.student_id, s.name, r.grade
                        FROM Students s
                        JOIN Enrollments e ON s.student_id = e.student_id
                        LEFT JOIN Results r ON s.student_id = r.student_id AND r.course_id = %s
                        WHERE e.course_id = %s AND s.is_banned = FALSE
                    """, (selected_course, selected_course))
                    
                    # Clear existing entries
                    for row in students_tree.get_children():
                        students_tree.delete(row)
                    
                    # Add new entries
                    for student in cur.fetchall():
                        students_tree.insert('', tk.END, values=(
                            student['student_id'],
                            student['name'],
                            student['grade'] if student['grade'] else ""
                        ))
                    
                except mysql.connector.Error as err:
                    messagebox.showerror("Database Error", f"Error fetching students: {err}")
                finally:
                    if conn.is_connected():
                        cur.close()
                        conn.close()
            
            def update_grade():
                selected = students_tree.focus()
                if not selected:
                    messagebox.showwarning("Selection Error", "Please select a student first")
                    return
                    
                grade = grade_entry.get().strip().upper()
                if grade not in ['A', 'B', 'C', 'D', 'F']:
                    messagebox.showwarning("Input Error", "Grade must be A, B, C, D, or F")
                    return
                    
                selected_course = course_var.get().split(" - ")[0]
                item = students_tree.item(selected)
                sid = item['values'][0]
                
                conn = get_connection()
                if not conn:
                    return
                    
                try:
                    cur = conn.cursor()
                    # Check if result exists
                    cur.execute("SELECT * FROM Results WHERE student_id=%s AND course_id=%s", (sid, selected_course))
                    if cur.fetchone():
                        # Update existing grade
                        cur.execute("""
                            UPDATE Results SET grade=%s 
                            WHERE student_id=%s AND course_id=%s
                        """, (grade, sid, selected_course))
                    else:
                        # Insert new grade
                        cur.execute("""
                            INSERT INTO Results (student_id, course_id, grade)
                            VALUES (%s, %s, %s)
                        """, (sid, selected_course, grade))
                    
                    conn.commit()
                    messagebox.showinfo("Success", "Grade updated successfully")
                    load_students()  # Refresh the list
                except mysql.connector.Error as err:
                    messagebox.showerror("Database Error", f"Error updating grade: {err}")
                finally:
                    if conn.is_connected():
                        cur.close()
                        conn.close()
            
            # Load students for initially selected course
            load_students()
            
            # Bind course selection change
            course_dropdown.bind("<<ComboboxSelected>>", lambda e: load_students())
            
            # Add buttons
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill='x', pady=10)
            
            create_rounded_button(btn_frame, "Update Grade", update_grade, StyleConfig.SUCCESS, width=150).pack()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error fetching courses: {err}")
        finally:
            if conn.is_connected():
                cur.close()
                conn.close()

    # Create faculty dashboard UI
    main_frame = ttk.Frame(dash)
    main_frame.pack(fill='both', expand=True, padx=30, pady=30)

    # Header with welcome message
    welcome_frame = tk.Canvas(main_frame, height=120, bg=StyleConfig.PRIMARY, highlightthickness=0)
    welcome_frame.pack(fill='x', pady=(0, 20))
    
    # Welcome message with faculty's name
    welcome_frame.create_text(500, 40, text=f"Welcome, Professor {name}!", font=('Segoe UI', 20, 'bold'), fill='white')
    welcome_frame.create_text(500, 70, text=f"Faculty ID: {fid}", font=('Segoe UI', 12), fill='white')
    
    # Logout button in header
    logout_btn = tk.Canvas(welcome_frame, width=80, height=30, bg=StyleConfig.DANGER, highlightthickness=0)
    logout_btn.create_text(40, 15, text="Logout", fill='white', font=('Segoe UI', 10, 'bold'))
    logout_btn.bind("<Button-1>", lambda e: logout())
    logout_btn.place(relx=0.95, rely=0.5, anchor='e')
    
    # Quick stats row
    stats_frame = ttk.Frame(main_frame)
    stats_frame.pack(fill='x', pady=(0, 20))
    
    # Get stats
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM Courses WHERE instructor_id=%s", (fid,))
            course_count = cur.fetchone()[0]
            
            cur.execute("""
                SELECT COUNT(DISTINCT e.student_id) 
                FROM Enrollments e
                JOIN Courses c ON e.course_id = c.course_id
                WHERE c.instructor_id=%s
            """, (fid,))
            student_count = cur.fetchone()[0]
            
            cur.execute("SELECT department FROM Faculty WHERE faculty_id=%s", (fid,))
            department = cur.fetchone()[0]
        except mysql.connector.Error:
            course_count = 0
            student_count = 0
            department = "Unknown"
        finally:
            if conn.is_connected():
                cur.close()
                conn.close()
    else:
        course_count = 0
        student_count = 0
        department = "Unknown"
    
    # Create stat cards
    create_card(stats_frame, "Courses Teaching", course_count, "📚", StyleConfig.SUCCESS).pack(side='left', expand=True, fill='x', padx=5)
    create_card(stats_frame, "Students", student_count, "👨‍🎓", StyleConfig.ACCENT).pack(side='left', expand=True, fill='x', padx=5)
    create_card(stats_frame, "Department", department, "🏛️", StyleConfig.INFO).pack(side='left', expand=True, fill='x', padx=5)
    
    # Action buttons
    actions_frame = ttk.Frame(main_frame)
    actions_frame.pack(fill='x', pady=(0, 20))
    
    # Row 1
    row1 = ttk.Frame(actions_frame)
    row1.pack(fill='x', pady=5)
    create_rounded_button(row1, "Create New Course", create_course, StyleConfig.PRIMARY, width=250).pack(side='left', padx=5)
    create_rounded_button(row1, "Manage My Courses", manage_courses, StyleConfig.SUCCESS, width=250).pack(side='left', padx=5)
    
    # Row 2
    row2 = ttk.Frame(actions_frame)
    row2.pack(fill='x', pady=5)
    create_rounded_button(row2, "Student Management", view_students, StyleConfig.INFO, width=250).pack(side='left', padx=5)
    create_rounded_button(row2, "Manage Results", manage_results, StyleConfig.SECONDARY, width=250).pack(side='left', padx=5)

# ========== MAIN EXECUTION ==========
if __name__ == "__main__":
    show_login_popup()
    root.mainloop()

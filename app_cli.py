# college_portal.py

import tkinter as tk
from tkinter import messagebox
from rich.console import Console
from rich.table import Table
import mysql.connector
import datetime
import qrcode
import os

# Hide base tkinter window
root = tk.Tk()
root.withdraw()

console = Console()


# ============================
# MODULE 0: DATABASE CONNECTION
# ============================
from config import DB_CONFIG

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# =================================
# MODULE 1: STUDENT REGISTRATION
# =================================
def register_student():
    conn = get_connection()
    cur = conn.cursor()
    console.print("\n[bold cyan]🔐 Student Registration[/bold cyan]")
    nm = input("Name: ")
    em = input("Email: ")
    pw = input("Password: ")
    try:
        cur.execute(
            "INSERT INTO Students (name, email, password) VALUES (%s, %s, %s)",
            (nm, em, pw)
        )
        conn.commit()
        console.print("[green]✓ Registration successful! You can now log in.[/green]")
    except mysql.connector.IntegrityError as e:
        if "Duplicate entry" in str(e):
            console.print(f"[yellow]⚠ Email exists: {em}. Try login.[/yellow]")
        else:
            console.print(f"[red]❌ Integrity error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
    finally:
        cur.close()
        conn.close()


# =====================================
# MODULE 2: STUDENT FUNCTIONALITY (CLI)
# =====================================
def view_courses():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT course_id, course_name, seats_left FROM Courses")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    tbl = Table(title="Available Courses")
    tbl.add_column("ID"); tbl.add_column("Name"); tbl.add_column("Seats Left")
    for cid, name, seats in rows:
        tbl.add_row(cid, name, str(seats))
    console.print(tbl)

def enroll_course(sid):
    view_courses()
    cid = input("Course ID to enroll: ")
    sem = input("Semester: ")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT seats_left FROM Courses WHERE course_id=%s", (cid,))
    r = cur.fetchone()
    if not r:
        console.print("[red]❌ Invalid Course ID[/red]")
    else:
        seats = r[0]
        if seats <= 0:
            console.print("[yellow]⚠ Course full[/yellow]")
        else:
            cur.execute("INSERT INTO Enrollments (student_id, course_id, semester, timestamp) VALUES (%s,%s,%s,%s)",
                        (sid, cid, sem, datetime.datetime.now()))
            cur.execute("UPDATE Courses SET seats_left = seats_left - 1 WHERE course_id=%s", (cid,))
            conn.commit()
            console.print("[green]✓ Enrolled and QR generated![/green]")
            qr = qrcode.make(f"{sid}|{cid}|{sem}")
            os.makedirs("qr_codes", exist_ok=True)
            qr.save(f"qr_codes/QR_{sid}_{cid}.png")
    cur.close()
    conn.close()

def drop_course(sid):
    view_my_enrollments(sid)
    cid = input("Course ID to drop: ")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Enrollments WHERE student_id=%s AND course_id=%s", (sid, cid))
    cur.execute("UPDATE Courses SET seats_left = seats_left + 1 WHERE course_id=%s", (cid,))
    conn.commit()
    console.print("[green]✓ Dropped course.[/green]")
    cur.close()
    conn.close()

def view_my_enrollments(sid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT E.course_id, C.course_name, E.semester, E.timestamp
        FROM Enrollments E JOIN Courses C USING(course_id)
        WHERE E.student_id=%s
    """, (sid,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    tbl = Table(title="My Enrollments")
    for h in ["Course ID", "Name", "Semester", "Time"]: tbl.add_column(h)
    for r in rows:
        tbl.add_row(*map(str, r))
    console.print(tbl)

def student_dashboard(sid, name):
    console.print(f"\n[bold green]🎓 Welcome, {name}![/bold green]")
    while True:
        console.print("\n[bold]Student Menu[/bold] 1.View Courses 2.Enroll 3.Drop 4.My Enrollments 0.Logout")
        ch = input("Choice: ")
        if ch == "1":
            view_courses()
        elif ch == "2":
            enroll_course(sid)
        elif ch == "3":
            drop_course(sid)
        elif ch == "4":
            view_my_enrollments(sid)
        elif ch == "0":
            console.print("[blue]Logged out.[/blue]")
            root.quit()  # close current popup/event loop
            show_login_popup()  # re-open login
            return  # exit menu loop

        else:
            console.print("[red]Invalid option[/red]")


def faculty_dashboard():
    console.print("\n[bold magenta]👩‍🏫 Faculty Portal[/bold magenta]")
    while True:
        console.print("\n1.Add Course 2.Report 3.Launch Result 4.360 View 0.Logout")
        ch = input("Choice: ")
        if ch == "1": add_course()
        elif ch == "2": report_enrollments()
        elif ch == "3": launch_result()
        elif ch == "4": student_360_view()
        elif ch == "0":
            console.print("[blue]Faculty logged out.[/blue]")
            sys.exit()
        else:
            console.print("[red]Invalid choice[/red]")

# ============================
# MODULE 4: LOGIN POPUP
# ============================
def show_login_popup():
    login_popup = tk.Toplevel()
    login_popup.title("College Login")
    login_popup.geometry("400x300")
    login_popup.configure(bg="#f9f9f9")

    tk.Label(login_popup, text="🎓 Welcome to Portal", font=("Segoe UI", 16, "bold"), bg="#f9f9f9").pack(pady=15)

    frm = tk.Frame(login_popup, bg="#f9f9f9"); frm.pack(pady=10)
    tk.Label(frm, text="Email / Username", bg="#f9f9f9").grid(row=0, column=0, pady=5, sticky="w")
    email_entry = tk.Entry(frm, width=35); email_entry.grid(row=1, column=0, ipady=4)

    tk.Label(frm, text="Password", bg="#f9f9f9").grid(row=2, column=0, pady=10, sticky="w")
    password_entry = tk.Entry(frm, show="*", width=35); password_entry.grid(row=3, column=0, ipady=4)

    def do_login():
        user = email_entry.get(); pw = password_entry.get()
        if user == "admin" and pw == "admin123":
            messagebox.showinfo("Admin", "🎓 Faculty login successful!")
            login_popup.destroy()
            faculty_dashboard()
        elif user and pw:
            try:
                conn = get_connection(); cur = conn.cursor()
                cur.execute("SELECT student_id, name FROM Students WHERE email=%s AND password=%s", (user, pw))
                res = cur.fetchone()
                if res:
                    sid, name = res
                    messagebox.showinfo("Login", f"Welcome {name}!")
                    login_popup.destroy()
                    student_dashboard(sid, name)
                else:
                    messagebox.showerror("Error", "Incorrect student credentials.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Missing", "Enter both email and password")

    def go_register():
        login_popup.destroy()
        register_student_popup()

    tk.Button(login_popup, text="🔐 Login", command=do_login, bg="#4CAF50", fg="white", width=15).pack(pady=10)
    tk.Button(login_popup, text="🆕 Register", command=go_register, bg="#2196F3", fg="white", width=15).pack()

# ============================
# 🚀 ENTRY POINT
# ============================
if __name__ == "__main__":
    show_login_popup()
    tk.mainloop()






import sqlite3
import datetime
import re

def connect_db():
    return sqlite3.connect("leave_mgmt.db")

def create_tables():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS HR (
        hr_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        designation TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS Department (
        dept_id TEXT PRIMARY KEY,
        dept_name TEXT NOT NULL,
        head_emp_code TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS Head (
        emp_code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        designation TEXT NOT NULL,
        post TEXT NOT NULL,
        dept_id TEXT NOT NULL,
        join_date TEXT NOT NULL,
        relieve_date TEXT,
        leave_balance INTEGER NOT NULL,
        live_status TEXT DEFAULT 'live',
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_by_hr TEXT NOT NULL,
        FOREIGN KEY (dept_id) REFERENCES Department(dept_id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS Employee (
        emp_code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        designation TEXT NOT NULL,
        post TEXT NOT NULL,
        dept_id TEXT NOT NULL,
        join_date TEXT NOT NULL,
        relieve_date TEXT,
        leave_balance INTEGER NOT NULL,
        live_status TEXT DEFAULT 'live',
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_by_hr TEXT NOT NULL,
        FOREIGN KEY (dept_id) REFERENCES Department(dept_id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS Leave (
        leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_code TEXT,
        from_date TEXT,
        to_date TEXT,
        days INTEGER,
        reason TEXT,
        leave_type TEXT,
        status TEXT CHECK(status IN ('pending','approved','rejected','cancelled')) DEFAULT 'pending',
        is_lop BOOLEAN,
        is_long_leave BOOLEAN,
        FOREIGN KEY (emp_code) REFERENCES Employee(emp_code)
    )''')

    conn.commit()
    conn.close()

def valid_name(name):
    return bool(re.fullmatch(r"[A-Za-z\s\.\'-]+", name))

def register_hr():
    conn = connect_db()
    cur = conn.cursor()
    
    while True:
        hr_id = input("Enter 6-digit HR ID (must start with 'HR' followed by 4 digits, e.g., HR1234): ")
        if not re.fullmatch(r'^HR\d{4}$', hr_id):
            print("Invalid HR ID format. Must start with 'HR' followed by 4 digits.")
            continue
            
        cur.execute("SELECT 1 FROM Employee WHERE emp_code=? UNION SELECT 1 FROM Head WHERE emp_code=?", (hr_id, hr_id))
        if cur.fetchone():
            print("This ID is already used as an employee code. Please choose a different HR ID.")
            continue
            
        break

    name = input("Enter HR Name: ")
    if not valid_name(name):
        print("Invalid name.")
        return

    designation = input("Enter Designation: ")
    username = input("Create Username: ")
    password = input("Create Password: ")

    try:
        cur.execute("INSERT INTO HR VALUES (?, ?, ?, ?, ?)", (hr_id, name, designation, username, password))
        conn.commit()
        print("HR Registered Successfully.")
    except sqlite3.IntegrityError:
        print("HR ID or Username already exists.")
    conn.close()

def login_hr():
    conn = connect_db()
    cur = conn.cursor()
    username = input("Username: ")
    password = input("Password: ")
    cur.execute("SELECT * FROM HR WHERE username=?", (username,))
    hr = cur.fetchone()
    conn.close()
    if hr and hr[4] == password:
        return hr
    print("Not a Registered HR. Please Register.")
    return None

def create_department():
    conn = connect_db()
    cur = conn.cursor()
    dept_id = input("Enter 4-char Department ID: ")
    if len(dept_id) != 4:
        print("Department ID must be 4 characters.")
        return
    dept_name = input("Department Name: ")
    try:
        cur.execute("INSERT INTO Department VALUES (?, ?, NULL)", (dept_id, dept_name))
        conn.commit()
        print("Department Created.")
    except sqlite3.IntegrityError:
        print("Department ID already exists.")
    conn.close()

def create_employee(hr_name):
    conn = connect_db()
    cur = conn.cursor()

    while True:
        emp_code = input("Enter Unique Employee Code (must be 6 digits): ")
        if not emp_code.isdigit() or len(emp_code) != 6:
            print("Employee Code must be 6 digits.")
            continue
            
        cur.execute("SELECT 1 FROM HR WHERE hr_id=?", (emp_code,))
        if cur.fetchone():
            print("This code is already used as an HR ID. Please choose a different employee code.")
            continue
            
        cur.execute("SELECT 1 FROM Employee WHERE emp_code=? UNION SELECT 1 FROM Head WHERE emp_code=?", (emp_code, emp_code))
        if cur.fetchone():
            print("Employee code already exists.")
            continue
            
        break

    name = input("Enter Employee Name: ")
    if not valid_name(name):
        print("Invalid name.")
        conn.close()
        return

    department = input("Department Name: ")
    dept_id = input("Enter Department ID: ")
    cur.execute("SELECT * FROM Department WHERE dept_id=?", (dept_id,))
    dept = cur.fetchone()
    if not dept:
        print("Department not created. Please create department first.")
        conn.close()
        return

    designation = input("Designation: ")
    post = input("Post: ")
    join_date = input("Join Date (YYYY-MM-DD): ")

    try:
        join_dt = datetime.datetime.strptime(join_date, "%Y-%m-%d").date()
    except ValueError:
        print("Invalid date format.")
        conn.close()
        return

    experience_days = (datetime.date.today() - join_dt).days
    leave_balance = 36 if experience_days >= 365 else 12

    username = emp_code
    password = input("Create Password for Employee: ")
    is_head = input("Is this employee a department head? (yes/no): ").strip().lower() == "yes"

    try:
        if is_head:
            cur.execute("INSERT INTO Head VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, 'live', ?, ?, ?)", 
                        (emp_code, name, department, designation, post, dept_id, join_date, leave_balance,
                         username, password, hr_name))
            cur.execute("UPDATE Department SET head_emp_code=? WHERE dept_id=?", (emp_code, dept_id))
        else:
            cur.execute("INSERT INTO Employee VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, 'live', ?, ?, ?)", 
                        (emp_code, name, department, designation, post, dept_id, join_date, leave_balance,
                         username, password, hr_name))
        conn.commit()
        print("Employee Added.")
    except sqlite3.IntegrityError as e:
        print(f"Error in creating employee: {e}")
    conn.close()

def login_employee():
    conn = connect_db()
    cur = conn.cursor()
    username = input("Username (Emp Code): ")
    password = input("Password: ")
    cur.execute("SELECT * FROM Employee WHERE username=?", (username,))
    emp = cur.fetchone()
    conn.close()
    if emp and emp[11] == password:
        return emp
    print("Login Failed.")
    return None

def login_head():
    conn = connect_db()
    cur = conn.cursor()
    username = input("Head Username (Emp Code): ")
    password = input("Password: ")
    cur.execute("SELECT * FROM Head WHERE username=?", (username,))
    head = cur.fetchone()
    conn.close()
    if head and head[11] == password:
        return head
    print("Login Failed.")
    return None

def apply_leave(emp_code):
    conn = connect_db()
    cur = conn.cursor()
    
    # Get employee details
    cur.execute("SELECT join_date, leave_balance FROM Employee WHERE emp_code=?", (emp_code,))
    emp_data = cur.fetchone()
    if not emp_data:
        print("Employee not found.")
        conn.close()
        return
        
    join_date, balance = emp_data
    join_dt = datetime.datetime.strptime(join_date, "%Y-%m-%d").date()
    experience_days = (datetime.date.today() - join_dt).days
    
    # Input leave details
    from_date = input("From Date (YYYY-MM-DD): ")
    to_date = input("To Date (YYYY-MM-DD): ")
    reason = input("Leave Reason: ")
    leave_type = input("Leave Type (Casual, Sick, Earned, Combo): ").capitalize()
    
    # Validate leave type for employees with <1 year experience
    if experience_days < 365 and leave_type != 'Casual':
        print("Employees with less than one year experience can only take Casual leave.")
        conn.close()
        return
    
    if leave_type not in ['Casual', 'Sick', 'Earned', 'Combo']:
        print("Invalid leave type.")
        conn.close()
        return

    try:
        from_dt = datetime.datetime.strptime(from_date, "%Y-%m-%d").date()
        to_dt = datetime.datetime.strptime(to_date, "%Y-%m-%d").date()
        days = (to_dt - from_dt).days + 1
    except ValueError:
        print("Invalid date format.")
        conn.close()
        return

    is_long = days > 4
    is_lop = False

    # Check leave balance and restrictions
    if experience_days < 365:
        current_month = datetime.date.today().month
        cur.execute("""
            SELECT COALESCE(SUM(days), 0) 
            FROM Leave 
            WHERE emp_code=? 
            AND strftime('%m', from_date)=? 
            AND status='approved'
        """, (emp_code, f"{current_month:02}"))
        approved_days_this_month = cur.fetchone()[0]
        
        if approved_days_this_month + days > 1:  # Only 1 casual leave allowed per month
            extra_days = (approved_days_this_month + days) - 1
            print(f"Warning: Only 1 casual leave allowed per month. {extra_days} days will be marked as LOP.")
            is_lop = True
    elif balance < days:
        is_lop = True

    # Apply the leave
    cur.execute('''INSERT INTO Leave (emp_code, from_date, to_date, days, reason, leave_type, is_lop, is_long_leave)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (emp_code, from_date, to_date, days, reason, leave_type, is_lop, is_long))

    if is_long:
        cur.execute("UPDATE Employee SET live_status='longleave' WHERE emp_code=?", (emp_code,))
    conn.commit()
    conn.close()
    print("Leave Applied.")

def view_leave_status(emp_code):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT leave_id, from_date, to_date, days, reason, leave_type, status, is_lop, is_long_leave 
        FROM Leave 
        WHERE emp_code=?
    """, (emp_code,))
    leaves = cur.fetchall()
    if not leaves:
        print("No leave applications found.")
    else:
        print("\nYour Leave History:")
        print("{:<8} {:<12} {:<12} {:<6} {:<10} {:<8} {:<10} {:<6} {:<10}".format(
            "ID", "From", "To", "Days", "Reason", "Type", "Status", "LOP", "Long Leave"))
        for l in leaves:
            print("{:<8} {:<12} {:<12} {:<6} {:<10} {:<8} {:<10} {:<6} {:<10}".format(
                l[0], l[1], l[2], l[3], l[4][:8]+"..." if len(l[4])>8 else l[4], 
                l[5], l[6], "Yes" if l[7] else "No", "Yes" if l[8] else "No"))
    conn.close()

def cancel_leave(emp_code):
    conn = connect_db()
    cur = conn.cursor()
    
    # Show only pending or approved leaves that can be cancelled
    cur.execute("""
        SELECT leave_id, from_date, to_date, days, reason, leave_type, status 
        FROM Leave 
        WHERE emp_code=? AND status IN ('pending', 'approved')
    """, (emp_code,))
    leaves = cur.fetchall()
    
    if not leaves:
        print("No cancellable leaves found.")
        conn.close()
        return
    
    print("\nCancellable Leaves:")
    print("{:<8} {:<12} {:<12} {:<6} {:<10} {:<8} {:<10}".format(
        "ID", "From", "To", "Days", "Reason", "Type", "Status"))
    for l in leaves:
        print("{:<8} {:<12} {:<12} {:<6} {:<10} {:<8} {:<10}".format(
            l[0], l[1], l[2], l[3], l[4][:8]+"..." if len(l[4])>8 else l[4], 
            l[5], l[6]))
    
    try:
        leave_id = int(input("\nEnter Leave ID to cancel (0 to abort): "))
    except ValueError:
        print("Invalid input. Please enter a number.")
        conn.close()
        return
    
    if leave_id == 0:
        print("Cancellation aborted.")
        conn.close()
        return
    
    # Verify the leave belongs to this employee and is cancellable
    cur.execute("""
        SELECT status, days, is_lop 
        FROM Leave 
        WHERE leave_id=? AND emp_code=? AND status IN ('pending', 'approved')
    """, (leave_id, emp_code))
    leave_info = cur.fetchone()
    
    if not leave_info:
        print("Invalid Leave ID or leave cannot be cancelled.")
        conn.close()
        return
    
    status, days, is_lop = leave_info
    
    confirm = input(f"Are you sure you want to cancel leave ID {leave_id}? (yes/no): ").lower()
    if confirm != 'yes':
        print("Cancellation aborted.")
        conn.close()
        return
    
    try:
        # Update leave status to cancelled
        cur.execute("UPDATE Leave SET status='cancelled' WHERE leave_id=?", (leave_id,))
        
        # If leave was approved and not LOP, restore leave balance
        if status == 'approved' and not is_lop:
            cur.execute("""
                UPDATE Employee 
                SET leave_balance = leave_balance + ? 
                WHERE emp_code=?
            """, (days, emp_code))
        
        # If this was a long leave, update live status
        cur.execute("SELECT is_long_leave FROM Leave WHERE leave_id=?", (leave_id,))
        is_long_leave = cur.fetchone()[0]
        if is_long_leave:
            cur.execute("UPDATE Employee SET live_status='live' WHERE emp_code=?", (emp_code,))
        
        conn.commit()
        print("Leave successfully cancelled.")
    except sqlite3.Error as e:
        print(f"Error cancelling leave: {e}")
        conn.rollback()
    finally:
        conn.close()

def process_head_leaves(head):
    conn = connect_db()
    cur = conn.cursor()
    dept_id = head[5]
    cur.execute('''SELECT L.leave_id, E.emp_code, E.name, L.from_date, L.to_date, L.days, L.reason, L.leave_type
                   FROM Leave L JOIN Employee E ON L.emp_code = E.emp_code
                   WHERE L.status='pending' AND E.dept_id=?''', (dept_id,))
    rows = cur.fetchall()
    if not rows:
        print("No requests currently.")
        conn.close()
        return

    for row in rows:
        leave_id, emp_code, name, from_date, to_date, days, reason, leave_type = row
        print(f"\nLeave ID: {leave_id}, Emp Code: {emp_code}, Name: {name}, From: {from_date}, To: {to_date}, Days: {days}, Type: {leave_type}, Reason: {reason}")
        choice = input("Approve (a) or Reject (r): ").lower()
        if choice == 'a':
            cur.execute("UPDATE Leave SET status='approved' WHERE leave_id=?", (leave_id,))
            cur.execute("UPDATE Employee SET leave_balance = leave_balance - ? WHERE emp_code=? AND leave_balance >= ?", (days, emp_code, days))
        else:
            cur.execute("UPDATE Leave SET status='rejected' WHERE leave_id=?", (leave_id,))
    conn.commit()
    conn.close()

def view_all_leaves_hr():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT L.leave_id, L.emp_code, E.name, E.department, 
               L.from_date, L.to_date, L.days, L.leave_type, L.status,
               L.is_lop, L.is_long_leave,
               CASE WHEN julianday(E.join_date) > julianday('now','-1 year') 
                    THEN 'New' ELSE 'Experienced' END as experience
        FROM Leave L JOIN Employee E ON L.emp_code = E.emp_code
        ORDER BY L.status, L.from_date DESC
    ''')
    leaves = cur.fetchall()
    if not leaves:
        print("No leave records found.")
    else:
        print("\nAll Leave Records:")
        print("{:<8} {:<10} {:<15} {:<15} {:<12} {:<12} {:<6} {:<8} {:<10} {:<6} {:<10} {:<12}".format(
            "ID", "Emp Code", "Name", "Department", "From", "To", "Days", "Type", "Status", "LOP", "Long Leave", "Experience"))
        for l in leaves:
            print("{:<8} {:<10} {:<15} {:<15} {:<12} {:<12} {:<6} {:<8} {:<10} {:<6} {:<10} {:<12}".format(
                l[0], l[1], l[2][:12]+"..." if len(l[2])>12 else l[2], 
                l[3][:12]+"..." if len(l[3])>12 else l[3], l[4], l[5], l[6], 
                l[7], l[8], "Yes" if l[9] else "No", "Yes" if l[10] else "No", l[11]))
    conn.close()

def edit_department():
    conn = connect_db()
    cur = conn.cursor()
    dept_id = input("Enter Department ID to edit: ")
    cur.execute("SELECT * FROM Department WHERE dept_id=?", (dept_id,))
    dept = cur.fetchone()
    if not dept:
        print("Department not found.")
        conn.close()
        return
    print(f"Current Department Name: {dept[1]}")
    new_name = input("Enter new Department Name (leave blank to keep current): ").strip()
    if new_name:
        try:
            cur.execute("UPDATE Department SET dept_name=? WHERE dept_id=?", (new_name, dept_id))
            conn.commit()
            print("Department updated.")
        except sqlite3.IntegrityError:
            print("Error updating department.")
    else:
        print("No changes made.")
    conn.close()

def edit_employee_or_head():
    conn = connect_db()
    cur = conn.cursor()
    emp_code = input("Enter Employee/Head Code to edit: ")
    cur.execute("SELECT * FROM Employee WHERE emp_code=?", (emp_code,))
    emp = cur.fetchone()
    if emp:
        table = "Employee"
    else:
        cur.execute("SELECT * FROM Head WHERE emp_code=?", (emp_code,))
        emp = cur.fetchone()
        if emp:
            table = "Head"
        else:
            print("Employee/Head not found.")
            conn.close()
            return

    print(f"Current Name: {emp[1]}")
    new_name = input("New Name (leave blank to keep current): ").strip()
    if new_name and not valid_name(new_name):
        print("Invalid name.")
        conn.close()
        return

    print(f"Current Department: {emp[2]}")
    new_dept = input("New Department Name (leave blank to keep current): ").strip()

    print(f"Current Designation: {emp[3]}")
    new_desig = input("New Designation (leave blank to keep current): ").strip()

    print(f"Current Post: {emp[4]}")
    new_post = input("New Post (leave blank to keep current): ").strip()

    update_fields = []
    update_values = []

    if new_name:
        update_fields.append("name=?")
        update_values.append(new_name)
    if new_dept:
        update_fields.append("department=?")
        update_values.append(new_dept)
    if new_desig:
        update_fields.append("designation=?")
        update_values.append(new_desig)
    if new_post:
        update_fields.append("post=?")
        update_values.append(new_post)

    if update_fields:
        update_values.append(emp_code)
        sql = f"UPDATE {table} SET {', '.join(update_fields)} WHERE emp_code=?"
        try:
            cur.execute(sql, update_values)
            conn.commit()
            print(f"{table} details updated.")
        except sqlite3.IntegrityError:
            print("Error updating details.")
    else:
        print("No changes made.")
    conn.close()

def delete_record():
    conn = connect_db()
    cur = conn.cursor()
    print("Delete Options:\n1. Department\n2. Employee\n3. Head")
    choice = input("Choose option (1-3): ")
    if choice == '1':
        dept_id = input("Enter Department ID to delete: ")
        cur.execute("SELECT * FROM Department WHERE dept_id=?", (dept_id,))
        if cur.fetchone():
            confirm = input(f"Are you sure to delete Department {dept_id}? (yes/no): ")
            if confirm.lower() == 'yes':
                cur.execute("SELECT * FROM Employee WHERE dept_id=?", (dept_id,))
                emp_exists = cur.fetchone()
                cur.execute("SELECT * FROM Head WHERE dept_id=?", (dept_id,))
                head_exists = cur.fetchone()
                if emp_exists or head_exists:
                    print("Cannot delete department: Employees or Heads assigned to this department.")
                else:
                    cur.execute("DELETE FROM Department WHERE dept_id=?", (dept_id,))
                    conn.commit()
                    print("Department deleted.")
            else:
                print("Delete cancelled.")
        else:
            print("Department not found.")
    elif choice == '2':
        emp_code = input("Enter Employee Code to delete: ")
        cur.execute("SELECT * FROM Employee WHERE emp_code=?", (emp_code,))
        if cur.fetchone():
            confirm = input(f"Are you sure to delete Employee {emp_code}? (yes/no): ")
            if confirm.lower() == 'yes':
                cur.execute("DELETE FROM Employee WHERE emp_code=?", (emp_code,))
                cur.execute("DELETE FROM Leave WHERE emp_code=?", (emp_code,))
                conn.commit()
                print("Employee deleted.")
            else:
                print("Delete cancelled.")
        else:
            print("Employee not found.")
    elif choice == '3':
        emp_code = input("Enter Head Employee Code to delete: ")
        cur.execute("SELECT * FROM Head WHERE emp_code=?", (emp_code,))
        if cur.fetchone():
            confirm = input(f"Are you sure to delete Head {emp_code}? (yes/no): ")
            if confirm.lower() == 'yes':
                cur.execute("UPDATE Department SET head_emp_code=NULL WHERE head_emp_code=?", (emp_code,))
                cur.execute("DELETE FROM Head WHERE emp_code=?", (emp_code,))
                cur.execute("DELETE FROM Leave WHERE emp_code=?", (emp_code,))
                conn.commit()
                print("Head deleted.")
            else:
                print("Delete cancelled.")
        else:
            print("Head not found.")
    else:
        print("Invalid choice.")
    conn.close()

def reset_employee_password(emp_code):
    conn = connect_db()
    cur = conn.cursor()
    
    current_password = input("Enter current password: ")
    cur.execute("SELECT password FROM Employee WHERE emp_code=?", (emp_code,))
    db_password = cur.fetchone()[0]
    
    if current_password != db_password:
        print("Incorrect current password.")
        conn.close()
        return
    
    new_password = input("Enter new password: ")
    confirm_password = input("Confirm new password: ")
    
    if new_password != confirm_password:
        print("Passwords don't match.")
        conn.close()
        return
    
    try:
        cur.execute("UPDATE Employee SET password=? WHERE emp_code=?", (new_password, emp_code))
        conn.commit()
        print("Password updated successfully.")
    except sqlite3.Error as e:
        print("Error updating password:", e)
    finally:
        conn.close()

def reset_head_password(head_code):
    conn = connect_db()
    cur = conn.cursor()
    
    current_password = input("Enter current password: ")
    cur.execute("SELECT password FROM Head WHERE emp_code=?", (head_code,))
    db_password = cur.fetchone()[0]
    
    if current_password != db_password:
        print("Incorrect current password.")
        conn.close()
        return
    
    new_password = input("Enter new password: ")
    confirm_password = input("Confirm new password: ")
    
    if new_password != confirm_password:
        print("Passwords don't match.")
        conn.close()
        return
    
    try:
        cur.execute("UPDATE Head SET password=? WHERE emp_code=?", (new_password, head_code))
        conn.commit()
        print("Password updated successfully.")
    except sqlite3.Error as e:
        print("Error updating password:", e)
    finally:
        conn.close()

def hr_menu(hr):
    while True:
        print(f"\nWelcome HR: {hr[1]}")
        print("1. Create Department")
        print("2. Create Employee")
        print("3. View All Leaves")
        print("4. Edit Department")
        print("5. Edit Employee/Head")
        print("6. Delete Department/Employee/Head")
        print("7. Logout")
        choice = input("Enter choice: ")
        if choice == '1':
            create_department()
        elif choice == '2':
            create_employee(hr[1])
        elif choice == '3':
            view_all_leaves_hr()
        elif choice == '4':
            edit_department()
        elif choice == '5':
            edit_employee_or_head()
        elif choice == '6':
            delete_record()
        elif choice == '7':
            break
        else:
            print("Invalid choice.")

def employee_menu(emp):
    while True:
        print(f"\nWelcome Employee: {emp[1]}")
        print("1. Apply Leave")
        print("2. View Leave Status")
        print("3. Cancel Leave")
        print("4. Reset Password")
        print("5. Logout")
        choice = input("Enter choice: ")
        if choice == '1':
            apply_leave(emp[0])
        elif choice == '2':
            view_leave_status(emp[0])
        elif choice == '3':
            cancel_leave(emp[0])
        elif choice == '4':
            reset_employee_password(emp[0])
        elif choice == '5':
            break
        else:
            print("Invalid choice.")

def head_menu(head):
    while True:
        print(f"\nWelcome Department Head: {head[1]}")
        print("1. Process Leave Requests")
        print("2. Reset Password")
        print("3. Logout")
        choice = input("Enter choice: ")
        if choice == '1':
            process_head_leaves(head)
        elif choice == '2':
            reset_head_password(head[0])
        elif choice == '3':
            break
        else:
            print("Invalid choice.")

def main_menu():
    create_tables()
    while True:
        print("\nMain Menu:")
        print("1. HR Register")
        print("2. HR Login")
        print("3. Employee Login")
        print("4. Head Login")
        print("5. Exit")
        choice = input("Enter choice: ")
        if choice == '1':
            register_hr()
        elif choice == '2':
            hr = login_hr()
            if hr:
                hr_menu(hr)
        elif choice == '3':
            emp = login_employee()
            if emp:
                employee_menu(emp)
        elif choice == '4':
            head = login_head()
            if head:
                head_menu(head)
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main_menu()
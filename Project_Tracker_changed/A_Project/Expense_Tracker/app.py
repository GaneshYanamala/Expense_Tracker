from flask import Flask, request, redirect, url_for, render_template, session,flash
import os
import mysql.connector
from numpy import conj
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer
from  flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature 
from werkzeug.security import generate_password_hash
import csv
from flask import Flask, send_file,make_response
from io import BytesIO, StringIO
from fpdf import FPDF



# from flask import Flask
# from flask_mail import Mail

app = Flask(__name__)

# Configuration for Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@example.com'
app.secret_key = 'your_secret_key'  # Set a secret key for Flask operations
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Set a secure salt value for token generation
app.config['SECURITY_PASSWORD_SALT'] = 'your_security_salt_value'

# Optional: Enable debugging for Flask-Mail
app.config['MAIL_DEBUG'] = True

# Initialize Flask-Mail
mail = Mail(app)

# Routes and other application logic go here


app = Flask(__name__)
app.secret_key = 'your secret key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

ITEMS_PER_PAGE = 2

def create_connection():
    try:
        conn = mysql.connector.connect(
        host='localhost',
        user="root",
        password='Viratkohli@18',
        database='Expense_tracker1'
        )
        return conn
    except mysql.connector.Error as e:
        print("Error connecting to MySQL database:", e)
        return None

@app.route('/')
def index():
    return render_template('Home_page.html')


@app.route('/Register', methods=['GET', 'POST'])
def Register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        print(f"Registering user: {username}, {email}, {password}")  # Debugging line

        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
                account = cursor.fetchone()
                if account:
                    msg = 'Account already exists!'
                elif not username or not password or not email:
                    msg = 'Please fill out the form!'
                else:
                    cursor.execute('INSERT INTO users (username, password, email) VALUES (%s, %s, %s)', (username, password, email))
                    conn.commit()  # Make sure to commit the transaction
                    msg = 'You have successfully registered!'
                    print("User registered successfully")  # Debugging line
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                msg = f'An error occurred: {e}'
            finally:
                cursor.close()
                conn.close()
        else:
            msg = 'Unable to connect to the database.'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('Register.html', msg=msg)

@app.route('/Login', methods=['GET', 'POST'])
def Login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        print(f"Logging in user: {username}")  # Debugging line

        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            try:
                qry = "SELECT * FROM users WHERE username = %s AND password = %s"
                cursor.execute(qry, (username, password))
                account = cursor.fetchone()
                print("IN LOGIN: ", account)  # Debugging line
                if account:
                
                    session['loggedin'] = True
                    session['id'] = account[0]  # Assuming the first column is the ID
                    session['username'] = account[1]  # Assuming the second column is the username
                    msg = 'Logged in successfully!'
                    return redirect(url_for('Dashboard'))
                else:
                    msg = 'Incorrect username/password!'
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                msg = f'An error occurred: {e}'
            finally:
                cursor.close()
                conn.close()
        else:
            msg = 'Unable to connect to the database.'
    return render_template('Login.html', msg=msg)
@app.route("/") 
def Home_page():
    return render_template("Home_page.html")

@app.route('/Logout')
def Logout():
    session.pop('loggedin', None)
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('Home_page'))

@app.route("/Dashboard")
def Dashboard():
    
    conn= create_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch counts for different sections
    cursor.execute('SELECT COUNT(*) AS count FROM users')
    users_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) AS count FROM expenses')
    expenses_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) AS count FROM budjets')
    budjets_count = cursor.fetchone()['count']
    
    # Fetch user stories for pagination
    
    
    return render_template(
        "Dashboard.html",
       
       
        users_count=users_count,
        expenses_count=expenses_count,
        budjets_count=budjets_count
    )


# @app.route('/')
# def dashboard():
#     # Sample data to be passed to the template
#     courses_count = 10
#     faculty_count = 5
#     feedback_count = 20

#     return render_template('dashboard.html', courses_count=courses_count, faculty_count=faculty_count, feedback_count=feedback_count)

# @app.route('/Budjets')
# def Budjets():
#     return "Budjets Page"

# @app.route('/Expenses')
# def Expenses():
#     return "Expenses Page"

# @app.route('/Reports')
# def Reports():
#     return "Reports Page"

@app.route('/Expenses', methods=['GET', 'POST'])
def Expenses():
    msg = ''
    user_id = session.get('user_id')  # Assuming you are storing user_id in session
    
    if request.method == 'POST' and 'amount' in request.form and 'category' in request.form and 'date' in request.form and 'description' in request.form:
        amount = request.form['amount']
        category = request.form['category']
        date = request.form['date']
        description = request.form['description']
        
        print(f"Expenses: {amount}, {category}, {date}, {description}, {user_id}")  # Debugging line

        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO expenses (user_id, amount, category, date, description) VALUES (%s, %s, %s, %s, %s)',
                    (user_id, amount, category, date, description)
                )
                conn.commit()  # Make sure to commit the transaction
                msg = 'Expense added successfully!'
                print("Expense added successfully") 
                return redirect(url_for('view_expenses')) # Debugging line
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                msg = f'An error occurred: {e}'
            finally:
                cursor.close()
                conn.close()
        else:
            msg = 'Unable to connect to the database.'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    
    return render_template('Expenses.html', msg=msg)

@app.route('/edit_expenses/<int:expense_id>', methods=['GET', 'POST'])
def edit_expenses(expense_id):
    id=  session['id']
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
   
    cursor.execute("SELECT * FROM expenses WHERE expense_id=%s AND user_id=%s", (expense_id, id))
    expense = cursor.fetchone()
    
    if request.method == 'POST':
        amount = request.form['amount']
        category = request.form['category']
        date = request.form['date']
        description = request.form['description']
        
        cursor.execute("UPDATE expenses SET amount=%s, category=%s, date=%s, description=%s WHERE expense_id=%s", 
                       (amount, category, date, description, expense_id))
        conn.commit()
        
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('view_expenses'))
    
    cursor.close()
    conn.close()
    return render_template('edit_expenses.html', expense=expense)

@app.route('/view_expenses', methods=['GET'])
def view_expenses():
    if 'loggedin' in session:
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)
        exp = []
        query = "SELECT * FROM expenses WHERE 1=1"
        filters = []

        # Get filter parameters from request
        category = request.args.get('category')

        # Append filters to query
        if category and category != "All":
            query += " AND category = %s"
            filters.append(category)

        try:
            cursor.execute(query, filters)
            exp = cursor.fetchall()
            print('expenses', exp)  # Debugging: Print expenses to console

            # Fetch distinct categories for the filter dropdown
            cursor.execute("SELECT DISTINCT category FROM expenses")
            categories = cursor.fetchall()
            print('categories', categories)  # Debugging: Print categories to console

        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
        finally:
            cursor.close()
            conn.close()  # Close the connection after use
    else:
        exp = []
        categories = []

    return render_template('view_expenses.html', exp=exp, categories=categories, selected_category=category)



@app.route('/filter', methods=['GET', 'POST'])
def filter():
    exp = request.args.get('category')
    return render_template('your_template.html', exp=exp,)


@app.route('/delete_expenses/<int:expense_id>', methods=['POST'])
def delete_expenses(expense_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE expense_id = %s", (expense_id, ))
    conn.commit()
    cursor.close()
    return redirect(url_for('view_expenses'))

@app.route('/delete_budjet/<int:budjet_id>', methods=['POST'])
def delete_budjet(budjet_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM budjets WHERE budjet_id = %s", (budjet_id, ))
    conn.commit()
    cursor.close()
    return redirect(url_for('budgets'))

@app.route('/budgets', methods=['GET', 'POST'])
def budgets():
    user_id = session['id']
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        category = request.form['category']
        limit_ = request.form['limit_']
        
        cursor.execute("INSERT INTO budjets (user_id, category, limit_) VALUES (%s, %s, %s)",
                       (user_id, category, limit_))
        conn.commit()
        flash('Budget set successfully!', 'success')
        return redirect(url_for('budgets'))
    
    cursor.execute("SELECT * FROM budjets WHERE user_id=%s", (user_id,))
    budgets = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('Budgets.html', budgets=budgets)

@app.route('/edit_budget/<int:budjet_id>', methods=['GET', 'POST'])
def edit_budget(budjet_id):
    user_id = session['id']
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM budjets WHERE budjet_id=%s AND user_id=%s", (budjet_id, user_id))
    budget = cursor.fetchone()
    
    if request.method == 'POST':
        category = request.form['category']
        limit_ = request.form['limit_']
        
        cursor.execute("UPDATE budjets SET category=%s, limit_=%s WHERE budjet_id=%s AND user_id=%s",
                       (category, limit_, budjet_id, user_id))
        conn.commit()
        flash('Budget updated successfully!', 'success')
        return redirect(url_for('budgets'))
    
    cursor.close()
    conn.close()
    return render_template('edit_budget.html', budget=budget)

def check_budget_alerts(user_id):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT category, SUM(amount) AS total_spent FROM expenses WHERE user_id=%s GROUP BY category", (user_id,))
    expenses_by_category = cursor.fetchall()
    
    cursor.execute("SELECT category, limit_ FROM budjets WHERE user_id=%s", (user_id,))
    budgets = cursor.fetchall()
    
    alerts = []
    for budget in budgets:
        for expense in expenses_by_category:
            if budget['category'] == expense['category']:
                if expense['total_spent'] >= budget['limit_']:
                    alerts.append(f"You have exceeded your budget limit for {budget['category']}!")
                elif expense['total_spent'] >= 0.9 * budget['limit_']:
                    alerts.append(f"You are close to exceeding your budget limit for {budget['category']}!")
    
    cursor.close()
    conn.close()
    return alerts
@app.route('/dashboard2')

def dashboard():
    user_id = session['id']
    alerts = check_budget_alerts(user_id)
    return render_template('dashboard2.html', alerts=alerts)

mail = Mail(app)

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    mail.send(msg)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            try:
                qry = "SELECT * FROM users WHERE email = %s"
                cursor.execute(qry, (email,))
                account = cursor.fetchone()
                if account:
                    token = generate_confirmation_token(email)
                    reset_url = url_for('reset_password', token=token, _external=True)
                    html = render_template('reset_password_email.html', reset_url=reset_url)
                    send_email(email, 'Password Reset Requested', html)
                    flash('A password reset link has been sent to your email.', 'success')
                else:
                    flash('Email address not found.', 'danger')
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                flash(f'An error occurred: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()
        else:
            flash('Unable to connect to the database.', 'danger')
    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = serializer.loads(token, salt=app.config['SECURITY_PASSWORD_SALT'], max_age=3600)
    except (SignatureExpired, BadSignature):
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('Login'))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
        else:
            conn = create_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    hashed_password = hashed_password(password)  # Use a proper hashing function
                    qry = "UPDATE users SET password = %s WHERE email = %s"
                    cursor.execute(qry, (hashed_password, email))
                    conn.commit()
                    flash('Your password has been updated!', 'success')
                    return redirect(url_for('Login'))
                except mysql.connector.Error as e:
                    print("Error executing SQL query:", e)
                    flash(f'An error occurred: {e}', 'danger')
                finally:
                    cursor.close()
                    conn.close()
            else:
                flash('Unable to connect to the database.', 'danger')
    
    return render_template('reset_password.html', token=token)

def fetch_records():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Expenses")
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    return records

@app.route('/export_csv')
def export_csv():
    conn = create_connection()
    cursor = conn.cursor()
    records = fetch_records()
    
    # Create a string buffer to hold CSV data
    si = StringIO()
    cw = csv.writer(si)
    
    # Write the header
    # cw.writerow([i[0] for i in cursor.description])  # Writing headers
    
    # Write the data
    cw.writerows(records)
    
    # Move to the beginning of the StringIO object
    si.seek(0)
    
    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=records.csv'
    response.headers['Content-type'] = 'text/csv'
    
    return response

@app.route('/export_pdf')
def export_pdf():
    conn = create_connection()
    cursor = conn.cursor()
    records = fetch_records()
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    for row in records:
        row_line = ' | '.join(map(str, row))
        pdf.cell(200, 10, txt=row_line, ln=True, align='C')
    
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    
    pdf_output.seek(0)
    
    response = make_response(pdf_output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=records.pdf'
    response.headers['Content-type'] = 'application/pdf'
    
    return response

@app.route('/download_and_view')
def download_and_view():
    return render_template('download_and_view.html')

@app.route('/view_report')
def view_report():
    embed_url = "https://app.powerbi.com/view?r=YOUR_EMBED_URL"  # Replace with your actual embed URL
    return render_template('power_bi.html', embed_url=embed_url)


if __name__ == '__main__':
    app.run(debug=True)

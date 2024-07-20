from flask import Flask, request, redirect, url_for, render_template, send_from_directory,session
import os
import mysql.connector
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your secret key'
#photo code settings
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
#photo code ends
# Pagination settings
ITEMS_PER_PAGE = 2


try:
    conn = mysql.connector.connect(
    host='localhost',
    user="root",
    password='Viratkohli@18',
    database='Stories'
    )
    cursor = conn.cursor()
 
except mysql.connector.Error as e:
    print("Error connecting to MySQL database:", e)
#decorators define the URL endpoints for the login page.
#Visiting either the root URL (/) or /login will trigger this function
#The methods=['GET', 'POST'] part allows this route to handle both GET and POST requests.
@app.route('/')
@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        try:
            qry = "SELECT * FROM users WHERE username = %s AND password = %s"
            cursor.execute(qry, (username, password))
            account = cursor.fetchone()
            print("IN LOGIN: ",account)
            if account:
                session['loggedin'] = True
                session['userid'] = account[0] # Assuming the first column is the ID
                session['username'] = account[1]  # Assuming the second column is the username
                msg = 'Logged in successfully!'
                # cursor.execute('SELECT * FROM user_stories WHERE user_id = %s', (account[0],))
                # value = cursor.fetchall()
                return redirect(url_for('dashboard'))
                # return render_template('dashboard.html', msg=msg, data=value)
            else:
                msg = 'Incorrect username/password!'
                return render_template('login.html', msg=msg)
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            msg = 'An error occurred. Please try again later.'
            return render_template('login.html', msg=msg)
    return render_template('login.html')
 
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('username', None)
    # flash('You have successfully logged out.', 'success')
    return redirect(url_for('login'))

 
@app.route('/signup', methods =['GET', 'POST'])
def signup():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        try:
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists!'
            elif not username or not password or not email:
                msg = 'Please fill out the form!'
            else:
                cursor.execute('INSERT INTO users (username, password, email) VALUES (%s, %s, %s)', (username, password, email))
                conn.commit()
                msg = 'You have successfully registered!'
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            msg = 'An error occurred. Please try again later.'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('signup.html', msg=msg)

@app.route("/add_story", methods=['GET', 'POST'])
def add_story():
    msg = ''
    # print("logged in mmmm: ",session['loggedin'])
    if 'loggedin' in session:
        if request.method == 'POST' and 'title' in request.form and 'story' in request.form:
            title = request.form['title']
            story = request.form['story']
            user_id = session['userid']
            print("Story title: ",title)
            print("Story: ",story)
            print("user_id: ",user_id)
            #photo upload
            # Retrieve the file from the request
            file = request.files['file']
            print("file photoooo: ",file)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Save the file
                uploads_dir = os.path.join(app.root_path, 'static/uploads')
                # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                os.makedirs(uploads_dir, exist_ok=True)
                photo_path = os.path.join(uploads_dir, filename)
                file.save(photo_path)

            cursor.execute("INSERT INTO user_stories (user_id,title, story,filename) VALUES (%s,%s, %s,%s)", (user_id,title,story,filename))
            conn.commit()
            msg = 'You have successfully updated !'
                # return render_template('dashboard.html', data=value)
                # needs to be changed after testing
            return redirect(url_for('dashboard'))
            
        elif request.method == 'POST':
            msg = 'Please fill out the form !'
            return render_template("add_story.html", msg=msg)
        return render_template("add_story.html")
    return redirect(url_for('login'))
 
    
@app.route("/dashboard")
def dashboard():
    if 'loggedin' in session:
        user_id=session['userid']
        # Get the current page number from the query parameter, default to 1
        page = int(request.args.get('page', 1))
        offset = (page - 1) * ITEMS_PER_PAGE
        # cursor = conn.cursor(dictionary=True)
        # Query to get the total number of items
        cursor.execute('SELECT COUNT(*) AS count FROM user_stories WHERE user_id = %s', (user_id,))
        # total_items = cursor.fetchone()['count']
        total_items = cursor.fetchone()[0]
        total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        print("total pages: ",total_pages)
        # Query to get the items for the current page
        #offset is used to specify from which row we want the data to retrieve
        #Limit is nothing but to restrict the no of rows from the output
        cursor.execute('SELECT * FROM user_stories WHERE user_id = %s LIMIT %s OFFSET %s', (user_id,ITEMS_PER_PAGE, offset))
        # cursor.execute('SELECT * FROM user_stories WHERE user_id = %s', (user_id,))
        value = cursor.fetchall()
        return render_template("dashboard.html",data=value, page=page, total_pages=total_pages)
    return redirect(url_for('login'))

@app.route("/user/user_dashboard")
def user_dashboard():
    # Get the current page number from the query parameter, default to 1
    page = int(request.args.get('page', 1))
    offset = (page - 1) * ITEMS_PER_PAGE
    cursor = conn.cursor(dictionary=True)
    # Query to get the total number of items
    cursor.execute('SELECT COUNT(*) AS count FROM user_stories')
    total_items = cursor.fetchone()['count']
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    print("total pages: ",total_pages)
    # Query to get the items for the current page
    #offset is used to specify from which row we want the data to retrieve
    #Limit is nothing but to restrict the no of rows from the output
    cursor.execute('SELECT * FROM user_stories LIMIT %s OFFSET %s', (ITEMS_PER_PAGE, offset))
    value = cursor.fetchall()
    return render_template("user_dashboard.html",data=value, page=page, total_pages=total_pages)
    
@app.route('/user/user_view_story/<int:story_id>',methods=['POST', 'GET'])
def user_view_story(story_id):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM user_stories WHERE story_id = %s", (story_id,))
        story_data = cursor.fetchone()
    except mysql.connector.Error as e:
        print("Error executing SQL query:", e)
        story_data = None
        
    return render_template('user_view_stories.html', story_data=story_data)
   

@app.route("/update/<story_id>", methods=['POST', 'GET'])
def update(story_id):
    cursor.execute("SELECT * FROM user_stories where story_id = %s", (story_id,))
    value = cursor.fetchone()
    # cursor.close()
    return render_template('edit_story.html', data=value)

@app.route('/edit_story',methods=['POST', 'GET'])
def edit_story():
    if request.method == 'POST':
        story_id=request.form['story_id']
        print("story id in edit: ",story_id)
        title = request.form['title']
        story = request.form['story']
        try:
            update_query = '''UPDATE user_stories SET title = %s, story = %s WHERE story_id = %s'''
            cursor.execute(update_query, (title, story, story_id))
            conn.commit()
            return redirect(url_for('dashboard'))
            
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
    else:
        pass
@app.route('/view_story/<int:story_id>',methods=['POST', 'GET'])
def view_story(story_id):
    if 'loggedin' in session:
        
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM user_stories WHERE story_id = %s", (story_id,))
            story_data = cursor.fetchone()
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            story_data = None
        
        return render_template('view_story.html', story_data=story_data)
    else:
        return redirect(url_for('login'))

@app.route('/edit_account',methods=['POST', 'GET'])
def edit_account():
    print("In edit: ",request.method)
    if request.method == 'POST':
        usr_id=session['userid']
        u_name=request.form['username']
        u_email=request.form['email']
        try:
            update_query = '''UPDATE users SET username = %s, email = %s WHERE user_id = %s'''
            cursor.execute(update_query, (u_name, u_email,usr_id))
            conn.commit()
            return redirect(url_for('dashboard'))
            
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
    else:
        usr_id=session['userid']
        try:
            cursor.execute("SELECT * FROM users where user_id = %s", (usr_id,))
            value = cursor.fetchone()
            return render_template('edit_account.html', data=value)
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)


@app.route('/delete_story/<story_id>', methods=['POST', 'GET'])
def delete_story(story_id):
    try:
        cursor.execute('DELETE FROM user_stories WHERE story_id = %s', (story_id,))
        conn.commit()
        return redirect(url_for('dashboard'))
    except mysql.connector.Error as e:
        print("Error executing SQL query:", e)
@app.route('/search_template',methods=['POST', 'GET'])
def search_template():
    flag='T'
    return render_template('search.html',flag=flag)

@app.route('/search_story',methods=['POST', 'GET'])
def search_story():
    if 'loggedin' in session:
        print("in serach: ",request.method)
        if request.method == 'GET':
            user_id=session['userid']
            s_title=request.args.get('title')
            print("ttttt: ",s_title)
            cursor.execute('SELECT * FROM user_stories WHERE user_id = %s and title like %s' , (user_id,'%'+s_title+'%'))
            # sql_query = "SELECT * FROM story WHERE title LIKE %s"
            # cursor.execute(sql_query, ('%' + search_query + '%',))
            value = cursor.fetchall()
            return render_template("search.html",data=value)
    return redirect(url_for('login'))
if __name__ == '__main__':
    app.run(debug=True)
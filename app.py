from flask import Flask, render_template, redirect, url_for, session, flash, request
from flask_session import Session
from flask_login import login_required, current_user, LoginManager, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {
        'ssl': {'ca': os.path.join(os.path.dirname(__file__), 'cacert.pem')}
    }
}
app.secret_key = 'your-secret-key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    passwordd = db.Column(db.String(100), nullable=False)

    def __init__(self, email, username, passwordd):
        self.email = email
        self.username = username
        self.passwordd = passwordd
        
    def is_active(self):
        return True

    def is_authenticated(self):
        return True
    
    def get_id(self):
        return str(self.id)
login_manager = LoginManager(app)

class Todo(db.Model):
    __tablename__ = 'todolist'

    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    descr = db.Column(db.String(500), nullable=False)
    date_time = db.Column(db.DateTime, default=datetime.utcnow)
    uid = db.Column(db.Integer,nullable=False)
    
    def __init__(self, title, descr, uid):
        self.title = title
        self.descr = descr
        self.uid = uid
    



@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route("/", methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('todo'))
    
    if request.method == 'POST':
        return redirect(url_for('login'))
    
    return render_template('index.html')

@app.route("/home")
def home():
    return render_template('index.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        passwordd = request.form.get("password")
        user = User.query.filter(User.email == email).first()
        if user and user.passwordd == passwordd:
            session['user_id'] = user.id
            session['username'] = user.username
            login_user(user)  # Log in the user
            flash("Congrats!! Logged in!")
            return redirect(url_for('todo'))
        else:
            flash("!!Error Invalid email or password", category='error')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get("email")
        username = request.form.get("username")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        email_exist = User.query.filter(User.email == email).first()
        username_exist = User.query.filter(User.username == username).first()
        if email_exist:
            flash('!!Error Email is already in use!!', category='error')
        elif username_exist:
            flash('!!Error Username is already in use', category='error')
        elif password1 != password2:
            flash('!!Error Passwords do not match', category='error')
        elif len(username) < 2:
            flash('!!Error Username is too short', category='error')
        elif len(password1) < 2:
            flash('!!Error Password is too short', category='error')
        elif len(email) < 4:
            flash('!!Error Invalid email address', category='error')
        else:
            new_user = User(email=email, username=username, passwordd=password1)
            db.session.add(new_user)
            db.session.commit()
            flash('!!Congrats Account Created!')
            return redirect(url_for('home'))

    return render_template('signup.html')


@app.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    session.clear()
    logout_user()  
    return render_template('index.html')


@app.route("/todo", methods=['GET', 'POST'])
@login_required
def todo():
    if request.method == 'POST':
        title = request.form.get('title')
        descr = request.form.get('descr')
        uid = current_user.id 

        new_record = Todo(title=title, descr=descr, uid=uid)
        db.session.add(new_record)
        db.session.commit()

        return redirect(url_for('todo'))
    
    alltodo = Todo.query.filter_by(uid=current_user.id).all()  
    return render_template('todo.html', alltodo=alltodo)


@app.route('/update/<int:sno>', methods=['GET', 'POST'])
def update(sno):
    todo = Todo.query.get(sno)
    
    if todo.uid != current_user.id:
        flash("You are not authorized to update this todo", category='error')
        return redirect(url_for('todo'))
    
    if todo is None:
        flash("Todo not found", category='error')
        return redirect(url_for('todo'))

    if request.method == 'POST':
        title = request.form.get('title')
        descr = request.form.get('descr')

        # Update the fields only if they are provided in the form
        if title:
            todo.title = title
        if descr:
            todo.descr = descr

        db.session.commit()

        flash("Todo updated successfully")
        return redirect(url_for('todo'))

    return render_template('update.html', todo=todo)


@app.route('/delete/<int:sno>')
def delete(sno):
    todo = Todo.query.get(sno)

    if todo is None:
        flash("Todo not found", category='error')
        return redirect(url_for('todo'))

    
    if todo.uid != current_user.id:
        flash("You are not authorized to delete this todo", category='error')
        return redirect(url_for('todo'))

    db.session.delete(todo)
    db.session.commit()

    flash("Todo deleted successfully")
    return redirect(url_for('todo'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

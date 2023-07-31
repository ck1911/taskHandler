from flask import Flask,render_template,request,redirect,flash,jsonify,make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import relationship
from functools import wraps
from flask_login import LoginManager,login_user,login_required,logout_user,current_user
login_manager = LoginManager()


app=Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///todolist.sqlite3"
db=SQLAlchemy(app)
app.app_context().push()

#Model
    
class User(db.Model):
    user_no = db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String,nullable=False)
    created_date=db.Column(db.DateTime,default=datetime.now(),nullable=False)
    email=db.Column(db.String,nullable=False)
    password=db.Column(db.String,nullable=False)
    authenticated=db.Column(db.Boolean,default=True)
    active=db.Column(db.Boolean,default=True)
    anonymous=db.Column(db.Boolean,default=False)
    isAdmin=db.Column(db.Boolean,default=False)
    
    def is_authenticated(self):
        return self.authenticated
    def is_active(self):
        return self.active
    def is_anonymous(self):
        return self.anonymous
    def get_id(self):
        return str(self.user_no)
    
    def is_admin(self):
        return bool(self.isAdmin)
    
    def __repr__(self):
        return 'User Number - {0} || User Name - {1}'.format(self.user_no,self.name)
    
class Task(db.Model):
    task_no = db.Column(db.Integer,primary_key=True)
    task=db.Column(db.String,nullable=False)
    created_date=db.Column(db.DateTime,default=datetime.now(),nullable=False)
    due_date=db.Column(db.DateTime)
    status=db.Column(db.String,default="In-Progress",nullable=False)
    
    new_due_date=db.Column(db.DateTime,nullable=True,default=None)
    extension_status=db.Column(db.String,default=None,nullable=True)
    
    user_id = db.Column(db.Integer,db.ForeignKey('user.user_no'),nullable=False)
    manager_id = db.Column(db.Integer,db.ForeignKey('user.user_no'),nullable=False)
    
    assigned_to=db.relationship("User",foreign_keys="Task.user_id")
    assigned_by=db.relationship("User",foreign_keys="Task.manager_id")
    
    
    
    
    def __repr__(self):
        return 'Task Number - {0} || Task Name - {1}'.format(self.task_no,self.task)
    


    
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == "POST":
        auth = request.form
  
        user = User.query.filter_by(email = auth.get('email')).first()
        if not user:
            # returns 401 if user does not exist
            flash("User dont exist")
            return redirect("/login")        
    
        if check_password_hash(user.password, auth.get('password')):
            
            login_user(user)
            return redirect("/")
        # returns 403 if password is wrong
        flash("Wrong password")
        return redirect("/login")
        
        
        
    return render_template("login.html")

@app.route("/signup",methods=["GET","POST"])
def signup():
    if request.method == "POST":
        # code to validate and add user to database goes here
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password != confirm_password:
            flash('Confirm Password and Password does not match!')
            return redirect("/signup")
            
        

        user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

        if user: # if a user is found, we want to redirect back to signup page so user can try again
            flash('Email address already exists')
            return redirect("/signup")

        # create a new user with the form data. Hash the password so the plaintext version isn't saved.
        new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'),isAdmin=bool(request.form.get("is_admin")))

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")
    return render_template("signup.html")

@app.route("/")
def list_tasks():
    if current_user.is_authenticated:
        if current_user.is_admin(): 
            task=Task.query.filter_by(manager_id=current_user.get_id())
        else:
            task=Task.query.filter_by(user_id=current_user.get_id())
        return render_template("list.html",tsk=task)
    else:
        return redirect("/login")
        

@app.route("/add",methods=["GET","POST"])
@login_required
def create_task():
    if request.method == "POST":
        form=request.form
        date=datetime.fromisoformat(form.get("due_date"))
        user=User.query.get_or_404(int(form.get("user_id")))
        tsk=Task(task=form.get("task_name"),due_date=date,user_id=user.user_no,manager_id=current_user.get_id())
        db.session.add(tsk)
        db.session.commit()
        return redirect("/")
    elif request.method=="GET":
        data=User.query.filter_by(isAdmin=False)
    return render_template("add.html",users=data)

@app.route("/edit/<int:no>",methods=["GET","POST"])
@login_required
def edit_task(no):
    tsk=Task.query.get(no)
    if request.method == "POST":
        form=request.form
        date=datetime.fromisoformat(form.get("due_date"))
        tsk.task=form.get("task_name")
        tsk.due_date=date
        db.session.commit()
        return redirect("/")
    return render_template("edit.html",tsk=tsk)

@app.route("/edit/deadline/<int:no>",methods=["GET","POST"])
@login_required
def update_deadline_task(no):
    tsk=Task.query.get(no)
    if request.method == "POST":
        form=request.form
        new_due_date=datetime.fromisoformat(form.get("due_date"))
        tsk.new_due_date=new_due_date  
        tsk.extension_status="Requested"      
        db.session.commit()
        return redirect("/")
    return render_template("deadlineReq.html",tsk=tsk)

@app.route("/delete/<int:no>")
@login_required
def delete_task(no):
    tsk=Task.query.get(no)
    db.session.delete(tsk)
    db.session.commit()
    return redirect("/")

@app.route("/update/<int:no>/<int:com>")
@login_required
def mark_complete(no,com):
    tsk=Task.query.get(no)
    if(com==1):
        tsk.status="In-Progress"
    else:
        tsk.status="Complete"
    db.session.commit()
    return redirect("/")

@app.route("/show/<int:filter_id>")
@login_required
def show_list(filter_id):
    if current_user.isAdmin:
        if filter_id==1:
            tsk=Task.query.filter_by(status="Complete")
        elif filter_id==2:
            tsk=Task.query.filter_by(status="In-Progress")
        else:
            tsk=Task.query.all()
    else :
        if filter_id==1:
            tsk=Task.query.filter_by(status="Complete",user_id=current_user.get_id())
        elif filter_id==2:
            tsk=Task.query.filter_by(status="In-Progress",user_id=current_user.get_id())
        else:
            tsk=Task.query.filter_by(user_id=current_user.get_id())
    
        
    return render_template("list.html",tsk=tsk)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")





with app.app_context():
        db.create_all()

if __name__ == "__main__":
    # Quick test configuration. Please use proper Flask configuration options
    # in production settings, and use a separate file or environment variables
    # to manage the secret key!
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = 'super secret key'
    

    # session.init_app(app)

    app.debug = True
    login_manager.init_app(app)
    app.run()


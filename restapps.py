import json
from flask import Flask,render_template,request,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
from datetime import datetime

app=Flask(__name__)
api=Api(app)

app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///todolist.sqlite3"
db=SQLAlchemy(app)

# Model
class Task(db.Model):
    task_no = db.Column(db.Integer,primary_key=True)
    task=db.Column(db.String,nullable=False)
    created_date=db.Column(db.DateTime,default=datetime.now(),nullable=False)
    due_date=db.Column(db.DateTime)
    status=db.Column(db.String,default="In-Progress",nullable=False)
    
    def __repr__(self):
        return 'Task Number - {0} || Task Name - {1}'.format(self.task_no,self.task)
    
    def to_dict(self):
        return {"TaskNO":self.task_no, "Task":self.task,"Created_Date":str(self.created_date),"Due_Date":str(self.due_date)}
    
class GetTasks(Resource):
    def get(self):
        tasks=Task.query.all()
        tasks=[tsk.to_dict() for tsk in tasks]
        return {"Tasks":tasks}
    
class PostTask(Resource):
    def post(self):
        if request.is_json:
            date=datetime.fromisoformat(request.json["due_date"])
            tsk=Task(task=request.json["task"],due_date=date)
            db.session.add(tsk)
            db.session.commit()
            tsk=tsk.to_dict() 
            return tsk
        return "Error"
    

    
class EditTask(Resource):
    def get(self,no):
            tsk=Task.query.get(no)
            tsk=tsk.to_dict() 
            return tsk
    def put(self,no):
        if request.is_json:
            tsk=Task.query.get(no)
            if tsk:
                date=datetime.fromisoformat(request.json["due_date"])
                tsk.task=request.json["task"]
                tsk.due_date=date
                db.session.commit()
                return tsk.to_dict()
    def delete(self,no):
        tsk=Task.query.get(no)
        if tsk:
            db.session.delete(tsk)
            db.session.commit()
            return "Success"
        
    

    
api.add_resource(GetTasks,"/")
api.add_resource(PostTask,"/add")
api.add_resource(EditTask,"/<int:no>")
app.run(debug=True)
    
    
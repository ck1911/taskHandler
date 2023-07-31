from flask import Flask,request,make_response
import jwt

app=Flask(__name__)

def token_required(func):
    def decorated(*args,**kwargs):
        token=request.args.get("token")
    
        if token:
            try:
                data=jwt.decode(token,"secret",algorithms=["HS256"])
                return func(*args,**kwargs)
            except:
                return {"Error":"Invalid Token"}
        else:
            return {"Error":"Token Does not exist"}
    return decorated

@app.route("/")
def unprotected():
    return {"success":"No token needed"}


@app.route("/p")
@token_required
def protected():
    return {"success":"U Can access this page"}


@app.route("/login")
def login():
    auth=request.authorization
    if auth and auth.password=="password":
        token=jwt.encode({"user":auth.username,"exp": 1371720939},"secret",algorithm="HS256")
        return {"success":"login success","username":auth.username,"token":token}
    else:
        return make_response("invalid",401,{"WWW-Authenticate":"Basic realm=Login Required"})

app.run()
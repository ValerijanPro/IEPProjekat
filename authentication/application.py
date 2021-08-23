from flask import Flask,request,Response,jsonify,make_response;
from configuration import Configuration;
from models import database, User,UserRole,Role;
from email.utils import parseaddr;
from flask_jwt_extended import JWTManager, create_access_token,jwt_required, create_refresh_token,get_jwt,get_jwt_identity;
from sqlalchemy import and_;


application= Flask(__name__);
application.config.from_object(Configuration);

#helper functions
def numberOfMissingFields(email,password,forename,surname,jmbg):
    count=0;
    if(email):
        count = count + 1;
    if (password):
        count = count + 1;
    if (forename):
        count = count + 1;
    if (surname):
        count = count + 1;
    if (jmbg):
        count = count + 1;
    return count;

def checkEmptyFields(emailEmpty,passwordEmpty,forenameEmpty,surnameEmpty,jmbgEmpty, count):
    message="";
    if (emailEmpty or passwordEmpty or forenameEmpty or surnameEmpty or jmbgEmpty):
        message = "Field ";

    if (emailEmpty):
        message += "email";
        count = count - 1;
        if (count > 0):
            message += ", "
    if (passwordEmpty):
        message += "password";
        count = count - 1;
        if (count > 0):
            message += ", "
    if (forenameEmpty):
        message += "forename";
        count = count - 1;
        if (count > 0):
            message += ", "
    if (surnameEmpty):
        message += "surname";
        count = count - 1;
        if (count > 0):
            message += ", "
    if (jmbgEmpty):
        message += "jmbg";
    if (message != ""):
        message += " is missing."
    return message;

def checkJMBG(jmbg):
    OK=True;
    dan=int(jmbg[0])*10+int(jmbg[1]);
    mesec=int(jmbg[2])*10+int(jmbg[3]);
    # godina = int(jmbg[4]) * 100 + int(jmbg[5])*10+int(jmbg[6]);
    region=int(jmbg[7])*10+int(jmbg[8]);
    # broj=int(jmbg[9]) * 100 + int(jmbg[10])*10+int(jmbg[11]);
    kontrolna=int(jmbg[12]);

    m= 11 - ((     7 * ( int(jmbg[0]) + int(jmbg[6]) ) + 6*( int(jmbg[1]) + int(jmbg[7]) ) +
                     5 * ( int(jmbg[2]) + int(jmbg[8])  ) + 4*( int(jmbg[3]) + int(jmbg[9]) )+
                     3 * ( int(jmbg[4]) + int(jmbg[10]) ) + 2*( int(jmbg[5]) + int(jmbg[11]) )
                )) % 11 ;

    if(m>9):
        m=0;
    "1212567891234"
    if(dan>31 or mesec>12 or region<70 or (m!=kontrolna) ):
        OK=False;
    return OK;

def checkPassword(password):
    val = True;

    if len(password) < 8:
        val = False
    if not any(char.isdigit() for char in password):
        val = False
    if not any(char.isupper() for char in password):
        val = False
    if not any(char.islower() for char in password):
        val = False

    return val;

@application.route( "/register" , methods = [ "POST" ] )
def register():
    jmbg=request.json.get("jmbg","");
    email=request.json.get("email","");
    password = request.json.get("password", "");
    forename=request.json.get("forename","");
    surname=request.json.get("surname","");

    emailEmpty=len(email)==0;
    passwordEmpty = len(password) == 0;
    forenameEmpty = len(forename) == 0;
    surnameEmpty=len(surname)==0;
    jmbgEmpty=len(jmbg)==0;

    count=numberOfMissingFields(emailEmpty,passwordEmpty,forenameEmpty,surnameEmpty,jmbgEmpty);
    message=checkEmptyFields(emailEmpty,passwordEmpty,forenameEmpty,surnameEmpty,jmbgEmpty, count);

    #provera praznih polja
    if(message!=""):
        response = make_response(jsonify({"message": message}),400);
        response.headers["Content-Type"] = "application/json"
        return response

    #provera jmbg
    okJMBG=checkJMBG(jmbg);
    if(not okJMBG):
        response = make_response(jsonify({"message": "Invalid jmbg."}), 400);
        response.headers["Content-Type"] = "application/json"
        return response

    #provera email
    result=parseaddr(email);
    if(len(result[1])==0):
        response = make_response(jsonify({"message": "Invalid email."}), 400 );
        response.headers["Content-Type"] = "application/json"
        return response

    #provera password
    okPassword=checkPassword(password);
    if (not okPassword):
        response = make_response(jsonify({"message": "Invalid password."}), 400);
        response.headers["Content-Type"] = "application/json"
        return response

    #provera vec postoji korisnik
    user = User.query.filter(User.email == email ).first();
    if(user):
        response = make_response(jsonify({"message": "Email already exists."}), 400);
        response.headers["Content-Type"] = "application/json"
        return response

    user = User(email=email, password=password, forename=forename, surname=surname, JMBG=jmbg);
    database.session.add(user);
    database.session.commit();

    userRole=UserRole(userId=user.id, roleId=2);
    database.session.add(userRole);
    database.session.commit();

    return Response(status=200);

jwt=JWTManager(application);

@application.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "");
    password = request.json.get("password", "");

    emailEmpty = len(email) == 0;
    passwordEmpty = len(password) == 0;
    #provera praznih polja
    if (emailEmpty or passwordEmpty ):
        count=0;
        if(emailEmpty):
            count=count+1;
        if(passwordEmpty):
            count=count+1;
        message = "Field ";
        if (emailEmpty):
            message += "email";
            count = count - 1;
            if (count > 0):
                message += ", "
        if (passwordEmpty):
            message += "password";
        message += " is missing."
        response = make_response(jsonify({"message": message}), 400);
        response.headers["Content-Type"] = "application/json"
        return response

    # provera email
    result = parseaddr(email);
    if (len(result[1]) == 0):
        response = make_response(jsonify({"message": "Invalid email."}), 400);
        response.headers["Content-Type"] = "application/json"
        return response;


    user=User.query.filter(
        and_(
            User.email==email, User.password==password
        )
    ).first();
    #provera ne postoji korisnik
    if(not user):
        response = make_response(jsonify({"message": "Invalid credentials."}), 400);
        response.headers["Content-Type"] = "application/json"
        return response

    additionalClamis={
        "jmbg":user.JMBG,
        "forename":user.forename,
        "surname":user.surname,
        "roles": [str(role) for role in user.roles]
    }

    accessToken=create_access_token(identity=user.email, additional_claims=additionalClamis );
    refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClamis );


    response = make_response(jsonify(accessToken=accessToken, refreshToken=refreshToken), 200);
    response.headers["Content-Type"] = "application/json"
    return response

# @application.route("/check",methods=["POST"])
# @jwt_required ( )
# def check ( ):
#     return "Token is valid";

@application.route("/refresh",methods=["POST"])
@jwt_required ( refresh=True )
def refresh ( ):
    identity=get_jwt_identity();
    refreshClaims=get_jwt();

    additionalClaims={
        "jmbg":refreshClaims["jmbg"],
        "forename":refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles":refreshClaims["roles"]

    }
    accessToken=create_access_token(identity=identity, additional_claims=additionalClaims);

    response = make_response(jsonify(accessToken=accessToken), 200);
    response.headers["Content-Type"] = "application/json"
    return response;

@application.route("/",methods=["GET"])
def index():
    return "Hello world123";

@application.route("/delete",methods=["POST"])
@jwt_required (  )
def delete():

    email = request.json.get("email", "");

    emailEmpty = len(email) == 0;

    #provera prazan email
    if(emailEmpty):
        message = "Field email is missing.";
        response = make_response(jsonify({"message": message}), 400);
        response.headers["Content-Type"] = "application/json"
        return response

    # provera email
    result = parseaddr(email);
    if (len(result[1]) == 0):
        response = make_response(jsonify({"message": "Invalid email."}), 400);
        response.headers["Content-Type"] = "application/json"
        return response;

    identity = get_jwt_identity();
    refreshClaims = get_jwt();

    additionalClaims = {
        "jmbg": refreshClaims["jmbg"],
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles": refreshClaims["roles"]

    }

    user = User.query.filter(User.email == email).first();
    #provera ne postoji korisnik
    if(not user):
        response = make_response(jsonify({"message": "Unknown user."}), 400);
        response.headers["Content-Type"] = "application/json"
        return response;

    User.query.filter(User.email == email).delete();

    database.session.commit();

    return Response(status=200);

if(__name__=="__main__"):
    database.init_app(application);
    application.run(debug=True, host="0.0.0.0", port=5002);

from flask import Flask, request, make_response, jsonify, Response;
from configuration import Configuration;
from flask_jwt_extended import JWTManager, create_access_token,jwt_required, create_refresh_token,get_jwt,get_jwt_identity;

from models import database,Participant, ParticipantType, Election, ElectionType, Vote;
from redis import Redis;
from adminDecorator import roleCheck;
from flask_jwt_extended import JWTManager;

application= Flask(__name__);
application.config.from_object(Configuration)
jwt=JWTManager(application);

@application.route("/createParticipant", methods=["POST"] )

@roleCheck(role="admin")
def createParticipant():

    name = request.json.get("name", "");
    individual = request.json.get("individual", "");

    nameEmpty = len(name) == 0;
    individualEmpty=(not isinstance(individual, bool));

    # provera praznih polja
    if (nameEmpty or individualEmpty):
        count = 0;
        if (nameEmpty):
            count = count + 1;
        if (individualEmpty):
            count = count + 1;
        message = "Field ";
        if (nameEmpty):
            message += "name";
            count = count - 1;
            if (count > 0):
                message += ", "
        if (individualEmpty):
            message += "individual";
        message += " is missing."
        response = make_response(jsonify({"message": message}), 400);
        return response

    identity = get_jwt_identity();
    refreshClaims = get_jwt();

    additionalClaims = {
        "jmbg": refreshClaims["jmbg"],
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles": refreshClaims["roles"]
    }
    type=ParticipantType.POJEDINAC;
    if(not individual) :
        type=ParticipantType.PARTIJA;

    new = Participant(name=name,type=type);
    database.session.add(new);
    database.session.commit();

    return make_response(jsonify({"id": new.id}), 200);

@application.route("/getParticipants", methods=["GET"] )

@roleCheck(role="admin")
def getParticipants():

    identity = get_jwt_identity();
    refreshClaims = get_jwt();

    additionalClaims = {
        "jmbg": refreshClaims["jmbg"],
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles": refreshClaims["roles"]
    }

    participants= Participant.query.all ( );

    formattedList=[];
    for p in participants:
        individual=p.type==ParticipantType.POJEDINAC;
        formattedList.append(
            {
               "id" : p.id,
                "name" : p.name,
                "individual" :individual

            }
        )
    return make_response(jsonify({"participants": formattedList}),200);

@application.route("/createElection", methods=["POST"] )

@roleCheck(role="admin")
def createElection():

    identity = get_jwt_identity();
    refreshClaims = get_jwt();

    additionalClaims = {
        "jmbg": refreshClaims["jmbg"],
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles": refreshClaims["roles"]
    }

    participants= Participant.query.all ( );

    formattedList=[];
    for p in participants:
        individual=p.type==ParticipantType.POJEDINAC;
        formattedList.append(
            {
               "id" : p.id,
                "name" : p.name,
                "individual" :individual

            }
        )
    return make_response(jsonify({"participants": formattedList}),200);


if(__name__=="__main__"):
    database.init_app(application);
    application.run(debug=True);

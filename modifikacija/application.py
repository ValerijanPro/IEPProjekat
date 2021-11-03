from datetime import datetime,timedelta

from flask import Flask, request, make_response, jsonify, Response;
from werkzeug.exceptions import BadRequestKeyError

from configuration import Configuration;
from flask_jwt_extended import JWTManager, create_access_token,jwt_required, create_refresh_token,get_jwt,get_jwt_identity;
from sqlalchemy import and_,or_;
from models import database,Participant, ParticipantType, Election, ElectionType, Vote, ElectionParticipant;
from redis import Redis;
#from adminDecorator import roleCheck;
from flask_jwt_extended import JWTManager;
from decimal import *;
import io;
import csv;
from flask_jwt_extended import verify_jwt_in_request, get_jwt;
from functools import wraps;


from dateutil import parser


application= Flask(__name__);
application.config.from_object(Configuration)
jwt=JWTManager(application);


#helper functions


def roleCheck(role):
    def innerRole(function):
        @wraps(function)
        def decorator(*arguments, **keywordArguments):
            verify_jwt_in_request();
            claims=get_jwt();

            if(("roles" in claims) and (role in claims["roles"])):
                return function(*arguments,**keywordArguments);
            else:
                return make_response(jsonify({"msg": "Missing Authorization Header"}), 401);
        return decorator;
    return innerRole;

def checkAlreadyExistingElections(start, end):
    if(start>=end):
        return True;

    elections=Election.query.all();
    for e in elections:
        if( (e.beginning >= start and e.beginning<=end) and e.end>=end ):
            return True;
        if (e.beginning >= start  and e.end <= end):
            return True;
        if ((e.end >= start and end >= e.end) and e.beginning<=start):
            return True;
        if (e.beginning <= start and end<=e.end):
            return True;

    return False;

#individual F-parlamentarni,  T-predsednicki
def checkBadElectionType(participants, individual):

    for p in participants:
        participant=Participant.query.filter(Participant.id==p).first();
        if(not participant):

            return True;
        if(participant.type==ParticipantType.POJEDINAC and (not individual)):

            return True;
        if (participant.type == ParticipantType.PARTIJA and ( individual)):

            return True;
    return False;

def getCurrentElection():
    sada=datetime.now()+timedelta(hours=2);
    return Election.query.filter(

        and_(
            Election.beginning <= sada ,
            Election.end >= sada

        )


    ).first();

def calculateResultPresidential(p, election,invalidVotes):
    #ukupanBrojGlasova na ovim izborima
    ukupno=len(Vote.query.filter(Vote.idElection==election.id).all());
    mojBrojGlasova=len(Vote.query.filter(
        and_(Vote.idElection==election.id,
             Vote.idParticipant==p.id,
             Vote.valid==True)
    ).all());
    getcontext().prec=2;
    if(ukupno==0):
        return 0;
    return round(float((mojBrojGlasova*1.0)/(ukupno)),2);


@application.route("/getS/<idElection>/<name>", methods=["GET"] )
def r(idElection,name):


    # participants= Participant.query.all ( );
    #
    # formattedList=[];
    # for p in participants:
    #     individual=p.type==ParticipantType.POJEDINAC;
    #     formattedList.append(
    #         {
    #            "id" : p.id,
    #             "name" : p.name,
    #             "individual" :individual
    #
    #         }
    #     )
    search = "%{}%".format(name)
    return str(
        ElectionParticipant.query.join(Participant).filter(
            and_( ElectionParticipant.idElection==idElection,
                  Participant.name.like(
                    search
                  )
                  )
        ).with_entities(ElectionParticipant.idElection, ElectionParticipant.RB).all()
    );

    return "asd";
    #return make_response(jsonify({"participants": formattedList}),200);



if(__name__=="__main__"):
    database.init_app(application);
    application.run(debug=True, host="0.0.0.0", port=5004);

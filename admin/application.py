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

@application.route("/createParticipant", methods=["POST"] )
@roleCheck(role="admin")
def createParticipant():
    try:
        name = request.json.get("name", "");
        individual = request.json.get("individual", "");
    except Exception as error:
        return make_response(jsonify({"asd":"asd"}),400);

    nameEmpty = len(name) == 0;
    individualEmpty=(not isinstance(individual, bool));

    # provera praznih polja
    if (nameEmpty or individualEmpty):
        if(nameEmpty):
            message="Field name is missing.";
        elif(individualEmpty):
            message="Field individual is missing."
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

    participant=Participant.query.filter(
        Participant.name==name
    ).first();
    if(participant):
        message="Vec postoji";
        response = make_response(jsonify({"message": message}), 400);
        return response

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
    try:

        startString = request.json.get("start", "");
        endString = request.json.get("end", "");
        individual = request.json.get("individual", "");
        participants = request.json.get("participants", "a");
    except Exception as error:
        return make_response(jsonify({"asd":"asd"}),400);

    startEmpty=len(startString)==0;
    endEmpty = len(endString) == 0;
    badIndividual = (not isinstance(individual, bool));
    participantsEmpty = (participants=="a");

    #provera fale polja
    if (startEmpty or endEmpty or badIndividual or participantsEmpty):
        message="";
        if(startEmpty):
            message="Field start is missing.";
        elif(endEmpty):
            message = "Field end is missing.";
        elif(badIndividual):
            message = "Field individual is missing.";
        elif(participantsEmpty):
            message = "Field participants is missing.";
        response = make_response(jsonify({"message": message}), 400);
        response.headers["Content-Type"] = "application/json"
        return response

    try:
        start = parser.parse(startString)
        #start=datetime.strptime(startString, "%Y-%m-%dT%H:%M:%S");
    except Exception as error:
        response = make_response(jsonify({"message": "Invalid date and time."}), 400);
        response.headers["Content-Type"] = "application/json"
        return response

    try:
        end = parser.parse(endString)
        #end = datetime.strptime(endString, "%Y-%m-%dT%H:%M:%S");
    except Exception as error:
        response = make_response(jsonify({"message": "Invalid date and time."}), 400);
        response.headers["Content-Type"] = "application/json"
        return response

    #vrem zona
    # start=start+timedelta(hours=2);
    # end = end + timedelta(hours=2);

    #provera format

    badStart = (not isinstance(start, datetime));
    badEnd = (not isinstance(end, datetime));
    alreadyExistingElections=checkAlreadyExistingElections(start,end);

    if(badStart or badEnd or (not(start<end)) or alreadyExistingElections):
        response = make_response(jsonify({"message": "Invalid date and time."}), 400);
        response.headers["Content-Type"] = "application/json"
        return response



    # provera participanti

    badElectionType=checkBadElectionType(participants, individual)
    participantsNotEnough=(len(participants) < 2 and participants!="a");

    if(participantsNotEnough or badElectionType):
        response = make_response(jsonify({"message": "Invalid participants."}), 400);
        response.headers["Content-Type"] = "application/json"
        return response

    tip=ElectionType.PREDSEDNICKI;
    if(not individual):
        tip=ElectionType.PARLAMENTARNI;

    new=Election(beginning=start, end=end, type=tip);
    database.session.add(new);
    database.session.commit();
    pollNumbers=[];
    broj=1;
    for p in participants:
        novi=ElectionParticipant(idElection=new.id, idParticipant=p,RB=broj);
        database.session.add(novi);
        database.session.commit();
        pollNumbers.append(broj);
        broj=broj+1;


    return make_response(jsonify({"pollNumbers": pollNumbers}), 200);


@application.route("/getElections", methods=["GET"] )
@roleCheck(role="admin")
def getElections():

    identity = get_jwt_identity();
    refreshClaims = get_jwt();

    additionalClaims = {
        "jmbg": refreshClaims["jmbg"],
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles": refreshClaims["roles"]
    }

    elections= Election.query.all ( );

    formattedList=[];
    for e in elections:

        participants = [];
        vezna = ElectionParticipant.query.filter(ElectionParticipant.idElection == e.id).all();
        for v in vezna:
            part = Participant.query.filter(Participant.id == v.idParticipant).first();
            participants.append({
                "id": part.id,
                "name": part.name
            });

        individual=e.type==ElectionType.PREDSEDNICKI;

        formattedList.append(
            {
               "id" : e.id,
                "start":e.beginning.isoformat(),
                "end": e.end.isoformat(),
                "individual" :individual,
                "participants": participants
            }
        )




    return make_response(jsonify({"elections": formattedList}),200);

@application.route("/start", methods=["GET"] )
def start():
    sve=ElectionParticipant.query.filter().delete();
    sve = Vote.query.filter().delete();
    sve = Election.query.filter().delete();
    sve = Participant.query.filter().delete();
    # for s in sve:
    #     s.delete();
    # database.session.commit();
    #
    # sve = Vote.query.all();
    # for s in sve:
    #     s.delete();
    # database.session.commit();
    #
    # sve = Election.query.all();
    # for s in sve:
    #     s.delete();
    # database.session.commit();
    #
    # sve = Participant.query.all();
    # for s in sve:
    #     s.delete();
    database.session.commit();

@application.route("/getResults", methods=["GET"] )
@roleCheck(role="admin")
def getResults():

    try:
        electionId=request.args["id"];
    except Exception:
        response = make_response(jsonify({"message": "Field id is missing."}), 400);
        response.headers["Content-Type"] = "application/json"
        return response

    identity = get_jwt_identity();
    refreshClaims = get_jwt();

    additionalClaims = {
        "jmbg": refreshClaims["jmbg"],
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles": refreshClaims["roles"]
    }
    #TODO:
    #provera nije uneto polje ID uopste

    #provera ne postoji izbor sa datim id
    election= Election.query.filter ( Election.id==electionId).first();
    if(not election):
        response = make_response(jsonify({"message": "Election does not exist."}), 400);
        response.headers["Content-Type"] = "application/json"
        return response

    #provera nisu zavrseni admin
    if( getCurrentElection()):
        response = make_response(jsonify({"message": "Election is ongoing."}), 400);
        response.headers["Content-Type"] = "application/json"
        return response;

    #dohvatimo sve participante na ovim izborima
    participants=[];
    invalidVotes=[];
    vezna = ElectionParticipant.query.filter(ElectionParticipant.idElection == election.id).all();
    if (election.type == ElectionType.PREDSEDNICKI):
        for v in vezna:
            p=Participant.query.filter(Participant.id==v.idParticipant).first();
            #izracunamo rezultat za svakog
            result=calculateResultPresidential(p,election,invalidVotes);
            participants.append({
                "pollNumber": v.RB,
                "name": p.name,
                "result": float(result)
            })

            # nevalidni
            lista = Vote.query.filter(
                and_(Vote.idElection == election.id,
                     Vote.idParticipant == p.id,
                     Vote.valid == False)
            ).all();
            for l in lista:
                invalidVotes.append({
                    "electionOfficialJmbg": l.jmbg,
                    "ballotGuid": l.guid,
                    "pollNumber": l.RB,
                    "reason": l.reason

                });

    else:
        #parlamentarni
        recnikRezultataGlasova={}; #par  idUcesnik:brojGlasova
        recnikBrojaMandata={};
        for v in vezna:
            p = Participant.query.filter(Participant.id == v.idParticipant).first();
            #validni glasovi
            mojBrojGlasova = len(Vote.query.filter(
                and_(Vote.idElection == election.id,
                     Vote.idParticipant == p.id,
                     Vote.valid==True)
            ).all());
            #nevalidni
            lista=Vote.query.filter(
                and_(Vote.idElection == election.id,
                     Vote.idParticipant == p.id,
                     Vote.valid == False)
            ).all();
            for l in lista:
                invalidVotes.append({
                    "electionOfficialJmbg":l.jmbg,
                    "ballotGuid": l.guid,
                    "pollNumber": l.RB,
                    "reason":l.reason

                });
            recnikRezultataGlasova[p.id] = mojBrojGlasova;

            recnikBrojaMandata[p.id] = 0;

        # nemaGlasova=True;
        # for key in recnikRezultataGlasova:
        #     if(recnikRezultataGlasova[key]!=0):
        #         nemaGlasova=False;
        #         break;
        # if(nemaGlasova):
        #     return make_response(jsonify({"participants": participants, "invalidVotes": invalidVotes}), 200);

        maxMandata=250;
        ukupnoGlasova=0;
        for key in recnikRezultataGlasova:
            ukupnoGlasova+=recnikRezultataGlasova[key];

        cenzus=0.05*ukupnoGlasova; # 5%
        trenutnoMandata=0;

        #izbacimo one ispod cenzusa
        recnikBrojMandataIspodCenzusa={};
        for key in recnikRezultataGlasova:
            if(float(recnikRezultataGlasova[key])<cenzus):
                recnikBrojaMandata.pop(key);
                recnikBrojMandataIspodCenzusa[key]=0;

        for key in recnikBrojMandataIspodCenzusa:
            recnikRezultataGlasova.pop(key);

        #pravljenje rezultata
        while(trenutnoMandata<maxMandata):
                pobednik=0;
                first=None;
                for kljuc in recnikRezultataGlasova: #dohv samo prvi kljuc
                    first=kljuc;
                    break;
                pobednik=first;
                maxKolicnik=float(recnikRezultataGlasova[first]/(recnikBrojaMandata[first]+1))
                for kljuc in recnikRezultataGlasova:
                    if(kljuc==first):
                        continue;
                    kolicnik=float(recnikRezultataGlasova[kljuc]/(recnikBrojaMandata[kljuc]+1));
                    if(kolicnik > maxKolicnik):
                        pobednik=kljuc;
                        maxKolicnik=kolicnik;
                    # elif(kolicnik == maxKolicnik):
                    #     if(recnikRezultataGlasova[kljuc]>recnikRezultataGlasova[pobednik]):
                    #         pobednik=kljuc;
                if(recnikRezultataGlasova[pobednik]!=0):
                    recnikBrojaMandata[pobednik]=recnikBrojaMandata[pobednik]+1;
                trenutnoMandata=trenutnoMandata+1;

        #ispod cenzusa stranke
        for kljuc in recnikBrojMandataIspodCenzusa:
            p = Participant.query.filter(Participant.id == kljuc).first();
            v = ElectionParticipant.query.filter(
                and_(ElectionParticipant.idElection == electionId,
                     ElectionParticipant.idParticipant == p.id)
            ).first();
            participants.append({
                "pollNumber": v.RB,
                "name": p.name,
                "result": 0
            })
        #iznad cenzusa stranke
        for kljuc in recnikBrojaMandata:
            p=Participant.query.filter(Participant.id == kljuc).first();
            v=ElectionParticipant.query.filter(
                and_(ElectionParticipant.idElection == electionId,
                     ElectionParticipant.idParticipant==p.id)
            ).first();
            participants.append({
                "pollNumber": v.RB,
                "name": p.name,
                "result": int(recnikBrojaMandata[kljuc])
            })
    return make_response(jsonify({"participants": participants, "invalidVotes":invalidVotes}),200);

#
# @application.route("/vote", methods=["POST"] )
# @roleCheck(role="zvanicnik")
# def vote():
#
#     identity = get_jwt_identity();
#     refreshClaims = get_jwt();
#
#     additionalClaims = {
#         "jmbg": refreshClaims["jmbg"],
#         "forename": refreshClaims["forename"],
#         "surname": refreshClaims["surname"],
#         "roles": refreshClaims["roles"]
#     }
#     try:
#
#         content = request.files["file"].stream.read().decode("utf-8");
#
#         if(not content):
#             response = make_response(jsonify({"message": "Field file missing."}), 400);
#             response.headers["Content-Type"] = "application/json"
#             return response
#     except BadRequestKeyError:
#         response = make_response(jsonify({"message": "Field file missing."}), 400);
#         response.headers["Content-Type"] = "application/json"
#         return response
#
#
#     stream = io.StringIO(content);
#     reader = csv.reader(stream);
#
#     jmbg=refreshClaims["jmbg"];
#
#     forRedis = [];
#     votes = [];
#     lineNumber=0;
#     for row in reader:
#         idVote=int(row[0]);
#         redniBroj=int(row[1]);
#         #provera fale polja
#         if((not idVote) or (not redniBroj) ):
#             response = make_response(jsonify({"message": "Incorrect number of values on line "+str(lineNumber)+"."}), 400);
#             response.headers["Content-Type"] = "application/json"
#             return response
#         #provera OK redni broj
#         if (redniBroj<=0):
#             response = make_response(jsonify({"message": "Incorrect poll number on line " + str(lineNumber) + "."}),
#                                      400);
#             response.headers["Content-Type"] = "application/json"
#             return response
#         # idCurrentElection=getCurrentElection().id;
#         #
#         # vezna=ElectionParticipant.query.filter(
#         #     and_(
#         #         ElectionParticipant.idElection == idCurrentElection,
#         #         ElectionParticipant.RB==redniBroj
#         #     )).first();
#         # #provera nema po datom rednom broju
#         # if(not vezna):
#         #     response = make_response(jsonify({"message": "Incorrect number of values on line " + str(lineNumber) + "."}),
#         #                              400);
#         #     response.headers["Content-Type"] = "application/json"
#         #     return response
#         # idParticipant=vezna.idParticipant;
#         # vote=Vote(id=idVote,jmbg=jmbg,idElection=idCurrentElection,idParticipant=idParticipant, valid=True,reason="asd");
#
#         forRedis.append(
#             {
#             "jmbg":jmbg,
#             "idVote":idVote,
#
#             "rb":redniBroj
#             }
#         );
#         lineNumber=lineNumber+1;
#
#     with Redis(Configuration.REDIS_HOST) as red:
#        for a in forRedis:
#         red.lpush(Configuration.REDIS_VOTES_LIST, str(a));
#
#     #database.session.add_all(votes);
#     #database.session.commit();
#     return Response(200);




#helper ruta za tes tiranje
@application.route("/asd", methods=["GET"] )
@roleCheck(role="admin")
def asd():
    #return Response(datetime.now().isoformat(),200)
    trenutna=getCurrentElection();
    if(trenutna!=None):
        return make_response(jsonify(
            {"datetime.now() = ":str(datetime.now()),
             "datetime.now() + timedelta(hours=2) = ":str(datetime.now()+timedelta(hours=2)),
             "ongoing election id=":trenutna.id
             }
        ));
    else:
        return Response(status=200);
    #return make_response(jsonify({"current": trenutna.id}),200);

@application.route("/a", methods=["GET"] )
@roleCheck(role="admin")
def a():
    #return Response(datetime.now().isoformat(),200)
    glas=Vote(guid=1,jmbg="2701999710196",idElection=1,idParticipant=1,valid=True);
    database.session.add(glas);
    database.session.commit();
    votes=Vote.query.filter().all();
    return make_response(jsonify({"votes":votes},200));

if(__name__=="__main__"):
    database.init_app(application);
    application.run(debug=True, host="0.0.0.0", port=5001);

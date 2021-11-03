import json
import os
import time
from datetime import datetime,timedelta
from sqlalchemy import text
import sqlalchemy
from flask import Flask, request, make_response, jsonify, Response;
from werkzeug.exceptions import BadRequestKeyError

from configuration import Configuration;
from flask_jwt_extended import JWTManager, create_access_token,jwt_required, create_refresh_token,get_jwt,get_jwt_identity;
from sqlalchemy import and_,or_;
from models import database,Participant, ParticipantType, Election, ElectionType, Vote, ElectionParticipant;
from redis import Redis;

from flask_jwt_extended import JWTManager;
from decimal import *;
import io;
import csv;


#helper functions
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
    return float((mojBrojGlasova*1.0)/(ukupno));



if(__name__=="__main__"):

    gotovo=False;
    #zona=int(os.environ["mytimezone"])*3600;
    konekcija=None;
    while(not gotovo):
        try:
            engine=sqlalchemy.create_engine(Configuration.SQLALCHEMY_DATABASE_URI);
            konekcija=engine.connect();
            gotovo=True;
        except Exception:
            time.sleep(29);
        gotovo=True;
        konekcija.close();
    with Redis(Configuration.REDIS_HOST) as red:
        while(True):
            #print("paprika");
            vote=red.rpop(Configuration.REDIS_VOTES_LIST);
            if(not vote):
                continue;
            novi=vote.decode("utf-8").replace("'",'"');
            j=json.loads(novi);
            vote=j;

            konekcija=engine.connect();
            #provera postoje tekuci admin
            trenutni=konekcija.execute(text("select * from elections where end>=:p and beginning<=:p").bindparams(p= str(datetime.now()+timedelta(hours=2)))).fetchall();
            if(len(trenutni)==0):
                continue; #odbacimo glas
            idTrenutniIzbori=trenutni[0][0];
            idVote=vote["idVote"];
            idParticipant=None;
            rb=vote["rb"];
            jmbg=vote["jmbg"];
            reason="OK";
            valid=True;
            #print("idVote = "+str(idVote)+", rb = "+vote["rb"]);
            #provera postoje glasovi sa istim idVote
            glasovi = konekcija.execute(text("select * from votes where guid=:p").bindparams(
                p=idVote)).fetchall();
            if(len(glasovi)!=0):
                #vec postoji glas sa ovim id
                idParticipant=glasovi[0].idParticipant;
                # temp=konekcija.execute(text("select * from votes")).fetchall();
                # idVote=temp[-1].id+1;
                reason="Duplicate ballot."
                valid=False;
            else:
                vezna=konekcija.execute(text("select * from electionparticipants where idElection=:a and RB=:b").bindparams(a=idTrenutniIzbori,b=rb)).fetchall();
                if(len(vezna)==0):
                    #TODO:
                    #Za koga glasam, ako RB nije OK?
                    prviParticipant = konekcija.execute(text("select min(id) from participants")).first();
                    idParticipant=int(prviParticipant[0]);
                    reason="Invalid poll number.";
                    valid=False;
                else:
                    idParticipant=vezna[0].idParticipant;
            asd = text(
                "insert into votes(guid, idParticipant , valid , idElection , jmbg, reason, RB) value( :idVote,:idParticipant  ,:valid ,:idElection  , :jmbg, :reason, :RB )").bindparams(
                idVote=idVote, idParticipant=idParticipant, valid=valid,idElection=idTrenutniIzbori,jmbg=jmbg, reason=reason, RB=rb
                )
            konekcija.execute(asd)
            konekcija.close()

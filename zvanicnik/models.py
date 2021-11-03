from flask_sqlalchemy import SQLAlchemy;
database = SQLAlchemy ( );
import enum;

class ElectionParticipant ( database.Model ):
    __tablename__ = "electionparticipants";
    id = database.Column ( database.Integer, primary_key = True );
    idElection = database.Column ( database.Integer, database.ForeignKey ( "elections.id" ), nullable = False );
    idParticipant = database.Column(database.Integer, database.ForeignKey("participants.id"), nullable = False);
    RB=database.Column ( database.Integer,nullable = False );

class Vote ( database.Model ):
    __tablename__ = "votes";
    id = database.Column ( database.Integer, primary_key = True );
    guid = database.Column(database.String(256), nullable=False);
    jmbg = database.Column ( database.String(13),  nullable = False );
    idElection = database.Column ( database.Integer, database.ForeignKey ( "elections.id" ), nullable = False );
    idParticipant = database.Column(database.Integer, database.ForeignKey("participants.id"), nullable = False);
    valid=database.Column ( database.Boolean,  nullable = False );
    reason=database.Column ( database.String(256) );
    RB = database.Column(database.Integer, nullable=False);
    election = database.relationship("Election", back_populates="votes");
    participant = database.relationship("Participant", back_populates="votes");
    def __repr__ ( self ):
        return "({}, {}, {}, {}, {}, {}, {}, {})".format ( self.id, self.guid, self.jmbg, self.idElection, self.idParticipant, self.valid, self.election, self.participant );

class ElectionType(enum.Enum):
     PARLAMENTARNI = 0
     PREDSEDNICKI = 1

class ParticipantType(enum.Enum):
     PARTIJA = 0
     POJEDINAC = 1


class Election ( database.Model ):
     __tablename__ = "elections";

     id = database.Column ( database.Integer, primary_key = True );

     beginning = database.Column(database.DateTime, nullable=False);
     end = database.Column(database.DateTime, nullable=False);
     type = database.Column(database.Enum(ElectionType), nullable=False);
     participants = database.relationship("Participant", secondary=ElectionParticipant.__table__, back_populates="elections");

     votes = database.relationship ( "Vote", back_populates = "election" );


     def __repr__ ( self ):
         return "({}, {}, {}, {}, {})".format ( self.id, self.beginning, self.end, self.type, self.votes );


class Participant ( database.Model ):
    __tablename__ = "participants";
    id = database.Column ( database.Integer, primary_key = True );
    name = database.Column ( database.String ( 256 ), nullable = False );
    type = database.Column(database.Enum(ParticipantType), nullable=False);

    votes = database.relationship("Vote", back_populates="participant");
    elections = database.relationship("Election", secondary=ElectionParticipant.__table__,
                                         back_populates="participants");

    def __repr__ ( self ):
        return "({}, {}, {}, {})".format ( self.id, self.name, self.type, self.votes);



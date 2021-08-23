from flask_sqlalchemy import SQLAlchemy;
database = SQLAlchemy ( );
import enum;

class Vote ( database.Model ):
    __tablename__ = "votes";
    id = database.Column ( database.Integer, primary_key = True );
    jmbg = database.Column ( database.Integer,  nullable = False );
    idElection = database.Column ( database.Integer, database.ForeignKey ( "elections.id" ), nullable = False );
    idParticipant = database.Column(database.Integer, database.ForeignKey("participants.id"), nullable = False);
    valid=database.Column ( database.Boolean,  nullable = False );

    election = database.relationship("Election", back_populates="votes");
    participant = database.relationship("Participant", back_populates="votes");
    def __repr__ ( self ):
        return "({}, {}, {}, {}, {}, {}, {})".format ( self.id, self.jmbg, self.idElection, self.idParticipant, self.valid, self.election, self.participant );

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

     votes = database.relationship ( "Vote", back_populates = "election" );


     def __repr__ ( self ):
         return "({}, {}, {}, {}, {})".format ( self.id, self.beginning, self.end, self.type, self.votes );


class Participant ( database.Model ):
    __tablename__ = "participants";
    id = database.Column ( database.Integer, primary_key = True );
    name = database.Column ( database.String ( 256 ), nullable = False );
    type = database.Column(database.Enum(ParticipantType), nullable=False);

    votes = database.relationship("Vote", back_populates="participant");

    def __repr__ ( self ):
        return "({}, {}, {}, {})".format ( self.id, self.name, self.type, self.votes);



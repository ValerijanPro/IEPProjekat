from flask import Flask;
from configuration import Configuration;
from flask_migrate import Migrate,init,migrate,upgrade;
from models import database,Election,ElectionType,ElectionParticipant,ParticipantType,Participant,Vote;
from sqlalchemy_utils import database_exists, create_database;

application=Flask(__name__);
application.config.from_object(Configuration);

migrateObject=Migrate(application, database);

done=False;

while(not done):
    try:
        if (not database_exists(application.config["SQLALCHEMY_DATABASE_URI"])):
            create_database(application.config["SQLALCHEMY_DATABASE_URI"]);
        database.init_app(application);

        with application.app_context() as context:
            init();
            migrate(message="Production migration");
            upgrade();

            done=True;
    except Exception as error:
        print(error);



    # election1=Election(beginning="2018-01-01T15:00:00",end="2021-08-25T17:50:00", type=ElectionType.PARLAMENTARNI);
    # election2 = Election(beginning="2019-01-01T15:00:00", end="2019-01-02T15:00:00", type=ElectionType.PREDSEDNICKI);
    #
    # database.session.add(election1);
    # database.session.add(election2);
    # database.session.commit();
    #
    # sns=Participant(name="SNS",type=ParticipantType.PARTIJA);
    # dss = Participant(name="DSS", type=ParticipantType.PARTIJA);
    # ldp = Participant(name="LDP", type=ParticipantType.PARTIJA);
    # sps=Participant(name="SPS",type=ParticipantType.PARTIJA);
    #
    # vucic = Participant(name="vucic", type=ParticipantType.POJEDINAC);
    # dacic = Participant(name="dacic", type=ParticipantType.POJEDINAC);
    #
    # database.session.add(sns);
    # database.session.add(dss);
    # database.session.add(ldp);
    # database.session.add(sps);
    # database.session.add(vucic);
    # database.session.add(dacic);
    # database.session.commit();
    #
    # a1 = ElectionParticipant(idElection=1, idParticipant=1, RB=1);
    # a2 = ElectionParticipant(idElection=1, idParticipant=2, RB=2);
    # a3 = ElectionParticipant(idElection=1, idParticipant=3, RB=3);
    # a4 = ElectionParticipant(idElection=1, idParticipant=4, RB=4);
    #
    # b1 = ElectionParticipant(idElection=2, idParticipant=5, RB=1);
    # b2 = ElectionParticipant(idElection=2, idParticipant=6, RB=2);
    #
    # database.session.add(a1);
    # database.session.add(a2);
    # database.session.add(a3);
    # database.session.add(a4);
    # database.session.add(b1);
    # database.session.add(b2);
    # database.session.commit();






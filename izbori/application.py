

from flask import Flask;
from configuration import Configuration;
from flask import Flask,request,Response,jsonify,make_response;
from models import database, Participant, ParticipantType;
# from user.threads import threadsBlueprint;
# from user.comments import commentsBlueprint;
# from user.tags import tagsBlueprint;

application= Flask(__name__);
application.config.from_object(Configuration)

# @application.route("/threads",methods=["GET"])
# def threads():
#     return str(Thread.query.all());

# application.register_blueprint(threadsBlueprint,url_prefix="/threads");
# application.register_blueprint(tagsBlueprint,url_prefix="/tags");
# application.register_blueprint(commentsBlueprint,url_prefix="/comments");


@application.route( "/" , methods = [ "GET" ] )
def register():

    Ucesnik=Participant.query.filter(Participant.id == 1 ).first();



    response = make_response(jsonify(message=Ucesnik.type==ParticipantType.POJEDINAC), 200);
    response.headers["Content-Type"] = "application/json"
    return response


if(__name__=="__main__"):
    database.init_app(application);
    application.run(debug=True);

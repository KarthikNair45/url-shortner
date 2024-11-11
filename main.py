import random
from datetime import datetime, timedelta

from flask import Flask,Response,redirect
from flask_marshmallow import Marshmallow

from schemas import UrlSchema
from models import Url
from database import db

import logging

from shorten_url import shorten_url

app=Flask(__name__)
ma = Marshmallow(app)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.info("\t*APP STARTED*")
urlSchema=UrlSchema()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route("/health")
def health():
    return Response("Perfect Health",status=201)

@app.route("/url/<string:url>",methods=["POST"])
def push_url(url):
    '''To create a new shortened url'''
    try:
        shorter=shorten_url(random.randrange(0,len(url)))
        data={'url':url,'shortened_url':shorter}
        user=Url(**data)
        db.session.add(user)
        db.session.commit()
        return(shorter)
    except Exception as e:
        print(e)

@app.route("/url/<string:short_url>",methods=["GET"])
def return_url(short_url):
    '''To get the full url'''
    logger.info("Running Redirect")
    try:
        url = db.session.execute(db.select(Url).filter_by(shortened_url=short_url)).scalar_one()
        formatted_url=urlSchema.dumps(url)
        print(formatted_url)
        date = url.created.replace(tzinfo=None)
        datediff = datetime.now() - date
        logger.info(f"Difference in Time is {datediff}")
        if datediff<timedelta(minutes=1):
            return redirect(f"/{url.url}")
        else:
            delete_url(url.shortened_url)
            return 'Expired Create a short url again'
    except Exception as e:
        print(e)
        return 'No Url found'

@app.route("/url/<string:full_url>",methods=["PUT"])
def update_url(full_url):
    '''To update an already existing url.'''
    try:
        received_url=db.session.execute(db.select(Url).filter_by(url=full_url)).scalar_one()
        shorter=shorten_url(random.randrange(0,len(full_url)))
        received_url.shortened_url=shorter
        db.session.commit()
        return urlSchema.dumps(received_url)
    except Exception as e:
        print(e)

@app.route("/url/<string:url>",methods=["DELETE"])
def delete_url(url):
    '''To delete an url from the db'''
    try:
        deleted_url=db.session.execute(db.select(Url).filter_by(shortened_url=url)).scalar_one()
        db.session.delete(deleted_url)
        db.session.commit()
        return urlSchema.dumps(deleted_url)
    except Exception as e:
        print(e)

@app.route("/<string:redirected>")
def redirect_url(redirected):
    '''Redirected Route'''
    return f"Redirected to {redirected}"

if __name__=="__main__":
    app.run(host="0.0.0.0",debug=True)
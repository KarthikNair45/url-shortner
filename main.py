import random
from datetime import datetime, timedelta

from flask import Flask,Response,redirect
from flask_marshmallow import Marshmallow

from schemas import UrlSchema
from models import Url
from database import db
from sqlalchemy.exc import IntegrityError

import json
import logging
import os
from shorten_url import shorten_url
import redis

app=Flask(__name__)
ma = Marshmallow(app)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.info("\t*APP STARTED*")
redis_client = redis.Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
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
    logging.debug("Attempting to shorten URL")
    shorter=shorten_url(random.randrange(3,len(url)))
    logging.debug("URL shortened Sucessfully")
    data={'url':url,'shortened_url':shorter}
    user=Url(**data)
    redis_client.setex(shorter, 360, json.dumps(data))
    try:
        db.session.add(user)
        db.session.commit()
        return(shorter)
    except IntegrityError as e:
        logger.error("Integrity Error the URL already exists in the DB")
        return "The url already exists."
    except Exception as e:
        print(e)
        return "Error while pushing data to Database"
@app.route("/url/<string:short_url>",methods=["GET"])
def return_url(short_url):
    '''To get the full url'''
    logger.info("Running Redirect")
    try:
        url=redis_client.get(name=short_url)#to convert bytes to str
        #if redis returns None then fetch from database and update redis otherwise use data inside redis memory
        print(url)
        if url==None:
            url = db.session.execute(db.select(Url).filter_by(shortened_url=short_url)).scalar_one()
            formatted_url=urlSchema.dumps(url)
            logger.info(f'{formatted_url}')
            date = url.created.replace(tzinfo=None)#remove timezone info
            datediff = datetime.now() - date
            logger.info(f"Difference in Time is {datediff}")
            if datediff<timedelta(hours=1):
                data={'url':url.url,'shortened_url':url.shortened_url}
                logger.debug("Caching url for 6 minutes")
                redis_client.setex(url.shortened_url, 360, json.dumps(data))
                logger.info("Redirecting to New URL")
                return redirect(f"/{url.url}")
            else:
                delete_url(url.shortened_url)
                return 'Expired Create a short url again'
        else:
            expanded_url=json.loads(url.decode("utf-8"))
            logger.debug('Using cached data')
            logger.info('Redirecting to New URL')
            return redirect(f"/{expanded_url['url']}")
    except Exception as e:
        print(e)
        return 'No Url found'

@app.route("/url/<string:full_url>",methods=["PUT"])
def update_url(full_url):
    '''To update an already existing url.'''
    try:
        received_url=db.session.execute(db.select(Url).filter_by(url=full_url)).scalar_one()
        print(urlSchema.dumps(received_url))
        redis_key=received_url.shortened_url
        cache_data=redis_client.get(name=redis_key)
        shortened_url=shorten_url(random.randrange(0,len(full_url)))
        data={'url':full_url,'shortened_url':shortened_url}
        if cache_data==None:
            redis_client.setex(name=shortened_url,time=360,value=json.dumps(data))
        else:
            print(received_url.shortened_url)
            redis_client.delete(received_url.shortened_url)
            redis_client.setex(name=shortened_url,time=360,value=json.dumps(data))
        received_url.shortened_url=shortened_url
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
        redis_client.delete(url)
        db.session.commit()
        return urlSchema.dumps(deleted_url)
    except Exception as e:
        logger.error("Short url doesn't exist in the database")
        return "Short url doesn't exist in the database"

@app.route("/<string:redirected>")
def redirect_url(redirected):
    '''Redirected Route'''
    return f"Redirected to {redirected}"

if __name__=="__main__":
    app.run(host="0.0.0.0",debug=True)
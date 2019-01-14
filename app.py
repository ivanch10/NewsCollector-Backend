"""Imports library for Flask."""
from flask import Flask, jsonify, redirect, url_for, request
from flask_cors import CORS

"""Imports library for MongoDB."""
from flask_pymongo import PyMongo
from utils.json import JSONEncoder
import json

"""Imports from constants."""
from constants.db import MONGO_DBNAME, MONGO_URI
import pdb

"""Setup the app."""
app = Flask(__name__)
CORS(app)


"""Mongo DB configuration."""
app.config['MONGO_DBNAME'] = MONGO_DBNAME
app.config['MONGO_URI'] = MONGO_URI
mongo = PyMongo(app)

"""Defines the root server for the back end server."""
@app.route('/')
def root():
    message = "Root for the data server."
    return jsonify(message)

"""Route for updating user setting stored in mongoDB"""
@app.route('/setting')
def store_setting_route():
    user_id      = int(request.args.get('user_id')) ## user_id = 1
    time         = int(request.args.get('time'))
    abc          = int(request.args.get('abc'))
    fox          = int(request.args.get('fox'))
    npr          = int(request.args.get('npr'))
    news_per_page= int(request.args.get('news_per_page'))
    technology   = int(request.args.get('technology'))
    business     = int(request.args.get('business'))
    politics     = int(request.args.get('politics'))
    entertainment= int(request.args.get('entertainment'))
    
    user_setting_table = mongo.db.user_setting
    user_setting_table.replace_one({"user_id"      : user_id},
                                   {"user_id"      : user_id,
                                    "time"         : time,
                                    "abc"          : abc,
                                    "fox"          : fox,
                                    "npr"          : npr,
                                    "technology"   : technology,
                                    "business"     : business,
                                    "politics"     : politics,
                                    "entertainment": entertainment,
                                    "news_per_page": news_per_page
                                   })
    return get_all_news()

"""read user setting from database"""
def read_setting_route(user_id):
    user_setting_table = mongo.db.user_setting
    user_setting = user_setting_table.find_one({'user_id':user_id})
    return user_setting

"""Get news by source and tag from database"""
def get_news(source, tag, skip, no_per_page):
    return list(mongo.db[source].find({'tag': tag}).sort('date', -1)
                                      .skip(skip).limit(no_per_page))

"""Calculate the number news per source and per tag with weighting, and then get news"""
def get_news_by_topic(topic_dict):

    """Get user id and page no."""
    user_id = get_user_id()
    page_no = get_page_no()

    user_setting = read_setting_route(user_id)
    news_source = ["time", "fox", "abc", "npr"]

    """calculate the weight for each news source"""
    news_source_weight = []
    total_ratio = 0
    for source in news_source:
        var = user_setting[source]
        news_source_weight.append(var)
        total_ratio += var
        
    news_per_page = user_setting["news_per_page"]

    """calculate number of news for each source"""
    news_per_source = []
    for weight in news_source_weight:
        news_per_source.append(news_per_page*weight//total_ratio)
    
    """calculate number and ratio for each topic"""
    topic_ratio  = []
    topic_total = 0
    for topic in topic_dict:
        var = user_setting[(topic)]
        topic_ratio.append(var)
        topic_total += var

    """Calculate the number of news per source and per tag with weighting, and get news"""
    news = []    
    for source_i in range(0,len(news_source)):
        
        topic_per_page = []
        skip_no = []

        """calculate for pagination"""
        for i in range(0,len(topic_dict)):
            var = news_per_source[source_i]* topic_ratio[i]//topic_total
            topic_per_page.append(var)
            skip_no.append( (page_no - 1)* var )
               
        for i in range(0,len(topic_dict)):
            if topic_per_page[i] != 0:
                news += get_news(news_source[source_i], topic_dict[i], skip_no[i], topic_per_page[i])

    news = sorted(news, key=lambda news: news["date"], reverse = True)
                                    
    news =  JSONEncoder().encode(news)
    return jsonify(json.loads(news))

"""Get all news"""
@app.route('/all')
def get_all_news():
    topic_dict = ["politics", "technology", "business", "entertainment"]
    return get_news_by_topic(topic_dict)

"""Searching news by topics"""
@app.route('/tag/<string:tag>')
def get_news_by_tag(tag):
    topic_dict = [tag]
    return get_news_by_topic(topic_dict)

"""Get user id from html request"""
def get_user_id():
    user_id = request.args.get('user_id')
    if not user_id:
        return 999 ## default value: 999, default general User
    else:
        return int(user_id)   

"""Get page no from html request"""
def get_page_no():
    page_no = request.args.get('page')
    if not page_no:
        return 1
    else:
        return int(page_no)    

"""Searching news by keywords"""
@app.route('/search/<string:keyword>')
def search_news_by_keyword(keyword):

    """Get user id and page no."""
    user_id = get_user_id()
    page_no = get_page_no()
    
    user_setting = read_setting_route(user_id)
    
    news_per_page = user_setting["news_per_page"]
    news_source = ["time", "fox", "abc", "npr"]

    """pagination"""
    no_of_source = len(news_source)
    news_per_source_per_page = news_per_page//no_of_source   
    skip_no = (page_no - 1)* news_per_source_per_page

    """Generate all querys for all words in keywords"""
    query_list = []
    for key in keyword.split(' '):
        for search_in in ['summary', 'title']:
            query_list.append( {search_in: {'$regex':key, "$options": "i"}} )
    query = { "$or": query_list}


    """Get news with querys"""
    news = []
    for source in news_source:
        news += list(mongo.db[source].find(query).sort('date', -1)
                          .skip(skip_no).limit(news_per_source_per_page) )

    news = sorted(news, key=lambda news: news["date"], reverse = True)
    
    return jsonify(json.loads(JSONEncoder().encode( news )))

if __name__ == "__main__":
    app.run(debug=True)

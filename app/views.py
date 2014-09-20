from app import app
from flask import render_template, request, flash, redirect, url_for
import pymysql as mdb
import foodgroups
import jinja2
import pdb
import app.helpers.maps as maps

# db = mdb.connect(user="username",host="localhost",passwd="secretsecret",db="world_innodb",
#     charset='utf8')

@app.route('/')
@app.route('/index')
def splash():
    return render_template('splash.html')
        
	
@app.route('/blog')
def blog():
    return render_template('chord.html')

@app.route("/test")
def test_chord():
    return render_template('test.html')
	
@app.route("/foodgroups",methods=['GET'])
def food_groups_page():

    user_location = request.args.get("origin")
    if len(user_location) == 0:
        return render_template('splash.html')
        
    lat,lon,full_add,data = maps.geocode(user_location)
    sortkey = int(request.args.get("keychain"))
    clusters,restdata, cluster_info = foodgroups.foodGroups(lat,lon,key = sortkey)
    restaurants = []
    for ix,a in restdata.iterrows():
        thisdat = a
        restaurants.append(dict(lat=thisdat['latitude']
                ,long=thisdat['longitude']
                ,clusterid=thisdat['ranking']
                ))      
    
    return render_template('results3.html',results=restaurants,c_info = cluster_info, user_lat = lat, user_long = lon, faddress = full_add, ncluster = clusters['n_clusters'])

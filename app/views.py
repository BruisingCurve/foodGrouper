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
    return render_template('blogsplash.html')
    
@app.route('/chinese')
def chinese():
    return render_template('chord.html')

@app.route("/about")
def about_page():
    return render_template('FoodGrouprSlides/index.html')

@app.route("/contact")
def connect_page():
    return render_template('contact.html')

@app.route("/foodgroups",methods=['GET'])
def food_groups_page():
    try:
        user_location = request.args.get("origin")
        if len(user_location) == 0:
            return render_template('oops.html')
            
        lat,lon,full_add,data = maps.geocode(user_location)
        sortkey = int(request.args.get("keychain"))
        clusters,restdata, cluster_info = foodgroups.foodGroups(lat,lon,key = sortkey,cache=True)
        restaurants = []
        for ix,a in restdata.iterrows():
            thisdat = a
            restaurants.append(dict(lat=thisdat['latitude']
                    ,long=thisdat['longitude']
                    ,clusterid=thisdat['ranking']
                    ,url=thisdat['url']
                    ,name=thisdat['name']
                    ,pic=thisdat['photo']
                    ))      
        return render_template('results3.html',results=restaurants,c_info = cluster_info, user_lat = lat, user_long = lon, faddress = full_add, ncluster = clusters['n_clusters'])

    except:
        # Well something went wrong in here
        return render_template('oops.html')
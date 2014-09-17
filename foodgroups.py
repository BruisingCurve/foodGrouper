#!/usr/bin/env python
"""
WhereToLunch.py
author p.phelps
DBScan clustering of restaurants
"""

import json
import numpy as np
import scipy as sp
import pandas as pd
import matplotlib.pyplot as plt
import jsonOpen, figSetup
from collections import defaultdict, Counter
from sklearn.cluster import DBSCAN
from sklearn import metrics
from sklearn.preprocessing import StandardScaler
import rauth
import urllib2
import configparser
import foursquare
import pdb, time
import app.helpers.maps as maps

class struct():
    pass
    
def distance_on_unit_sphere(lat1, long1, lat2, long2):

    # Convert latitude and longitude to 
    # spherical coordinates in radians.
    degrees_to_radians = np.pi/180.0
        
    # phi = 90 - latitude
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians
        
    # theta = longitude
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians
    
        
    # Compute spherical distance from spherical coordinates.
        
    # For two locations in spherical coordinates 
    # (1, theta, phi) and (1, theta, phi)
    # cosine( arc length ) = 
    #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length
    
    cos_var = (np.sin(phi1)*np.sin(np.array([a for a in phi2]))*np.cos(theta1 - np.array([a for a in theta2])) + 
           np.cos(phi1)*np.cos(np.array([a for a in phi2])))
    arc = np.arccos( cos_var )

    # Remember to multiply arc by the radius of the earth 
    # in your favorite set of units to get length.
    return arc
    
def compute_miles(lat1,long1,lat2,long2):
    '''Compute the distance (in miles) between two latitude/longitude coordinates'''
    R_earth = 3963.1676 #miles
    return R_earth * distance_on_unit_sphere(lat1, long1, lat2, long2)

def lists_overlap(a, b):
    for i in a:
        if i in b:
            return True
        return False

def clusterThose(G,eps=0.1,min_samples=4):
    ''' Scale the data and cluster'''
    scaler = StandardScaler(copy=True)
    X_centered = scaler.fit(G).transform(G)
    db = DBSCAN(eps, min_samples).fit( X_centered )
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    X = scaler.inverse_transform(X_centered)
    return X, n_clusters_, labels, core_samples_mask
    
def get_search_parameters(lat,long,offset=0):
    #See the Yelp API for more details
#     params = {}
#     params["category_filter"] = "restaurants"
#     params["ll"] = "{},{}".format(str(lat),str(long))
#     #params["radius_filter"] = "16092"
#     params["sort"] = "1"
#     params["limit"] = "20"
#     params["offset"] = "%i"%offset
    
    params = {}
    params['ll'] = "{},{}".format(str(lat),str(long))
    params['limit'] = "50"
    params['section'] = "food"
    params['venuePhotos'] = "1"
    params['sortByDistance'] = "1"
    params['opneNow'] = "1"
    params["offset"] = "%i"%offset
    
    return params
  
def cleanData(data):
    ''' 
    Clean YELP result dictionaries into handy dataframes
    Want business location (lat, long), business name, 
    '''
    businesslist = data['businesses']
    df = pd.DataFrame(columns = ('name','full_address','rating',
            'review_count','distance','categories','snippet','latitude','longitude','latlongfound'))
    failures = []
    for i in range(len(businesslist)):
    
        try:
            full_address = ''
            for a in businesslist[i]['location']['display_address']:
                full_address = full_address +' %s'%a
        except:
            continue    
        
#         full_address = businesslist[i]['location']['display_address'][0] + ' '+businesslist[i]['location']['display_address'][1]
         
        try:
            loc = businesslist[i]['location']['coordinate']
            lat = loc['latitude']
            long = loc['longitude']
            latlongfound = 1
        except:
            # Probably doesn't have a coordinate
            failures.append(full_address)
            latlongfound = 0
            lat = 0.0
            long = 0.0
             
        categories = ''
        try:
            for a in businesslist[i]['categories']:
                categories+= a[1]+',' #lowercase
        except:
            pass
        
        try:
            df.loc[len(df)+1] = [businesslist[i]['name']
                    , full_address
                    , businesslist[i]['rating']
                    , businesslist[i]['review_count']
                    , businesslist[i]['distance']
                    , categories
                    , businesslist[i]['snippet_text']
                    , lat
                    , long
                    , latlongfound
                    ]
        except:
            pass
            
    try:
        url = 'http://www.datasciencetoolkit.org/street2coordinates'
        # Convert failures to json and read from web API (datasciencetoolkit.org)
        req = urllib2.Request(url,json.dumps(failures))
        response = urllib2.urlopen(req)
        healing = json.loads(response.read())
    except:
        healing = {}
        for a in failures:
            try:
                lat,lon,full_add,data = maps.geocode(a)
                healing[a] = {}
                healing[a]['latitude'] = lat
                healing[a]['longitude'] = lon
            except:
                break

    for a in healing.keys():
        try:
            df.loc[df[df['full_address']==a].index,'latitude'] = healing[a]['latitude']
            df.loc[df[df['full_address']==a].index,'longitude'] = healing[a]['longitude']
            df.loc[df[df['full_address']==a].index,'latlongfound'] = 1
        except:
            pass
    
    return df[df['latlongfound']==1]
  
def cleanData4Square(data):
    ''' 
    Clean 4Square result dictionaries into handy dataframes
    Want business location (lat, long), business name, 
    '''
    
    businesslist = data['groups'][0]['items'];
    
    df = pd.DataFrame(columns = ('name','full_address','street','rating',
            'review_count','distance','categories','price','latitude','longitude','latlongfound',
            'photo','hasphoto','IsOpenNow'))
    failures = []
    for i in range(len(businesslist)):
    
        try:
            full_address = ''
            full_address = full_address + businesslist[i]['venue']['location']['address']+', '
            full_address = full_address + businesslist[i]['venue']['location']['formattedAddress'][1]
        except:
            continue
            
        try:
            lat = businesslist[i]['venue']['location']['lat']
            long = businesslist[i]['venue']['location']['lng']
            latlongfound = 1
        except:
            # Probably doesn't have a coordinate
            failures.append(full_address)
            latlongfound = 0
            lat = 0.0
            long = 0.0
             
        categories = ''
        try:
            for a in businesslist[i]['venue']['categories']: categories+= a['shortName']+','
        except:
            pass 
               
        photourl = ''
        try:
            prefix = businesslist[i]['venue']['specials']['items'][0]['photo']['prefix']
            suffix = businesslist[i]['venue']['specials']['items'][0]['photo']['suffix']
            photourl = prefix + '100X100' + suffix
            hasphoto = 2
        except:
            try:
                prefix = businesslist[i]['venue']['featuredPhotos']['items'][0]['prefix']
                suffix = businesslist[i]['venue']['featuredPhotos']['items'][0]['suffix']
                photourl = prefix + '100X100' + suffix
                hasphoto = 1
            except:
                hasphoto = 0
                pass
                
        
        try:
            df.loc[len(df)+1] = [businesslist[i]['venue']['name']
                    , full_address
                    , businesslist[i]['venue']['location']['address']
                    , businesslist[i]['venue']['rating']
                    , businesslist[i]['venue']['ratingSignals']
                    , businesslist[i]['venue']['location']['distance']
                    , categories
                    , businesslist[i]['venue']['price']['tier']
                    , lat
                    , long
                    , latlongfound
                    , photourl
                    , hasphoto
                    , businesslist[i]['venue']['hours']['isOpen']
                    ]
        except:
            pass
    
    
    try:
        url = 'http://www.datasciencetoolkit.org/street2coordinates'
        # Convert failures to json and read from web API (datasciencetoolkit.org)
        req = urllib2.Request(url,json.dumps(failures))
        response = urllib2.urlopen(req)
        healing = json.loads(response.read())
    except:
        healing = {}
        for a in failures:
            try:
                lat,lon,full_add,data = maps.geocode(a)
                healing[a] = {}
                healing[a]['latitude'] = lat
                healing[a]['longitude'] = lon
            except:
                break

    for a in healing.keys():
        try:
            df.loc[df[df['full_address']==a].index,'latitude'] = healing[a]['latitude']
            df.loc[df[df['full_address']==a].index,'longitude'] = healing[a]['longitude']
            df.loc[df[df['full_address']==a].index,'latlongfound'] = 1
        except:
            pass
    
    return df[df['latlongfound']==1]
  
def get_results(params):
 
    #Obtain these from Yelp's manage access page
    configini = configparser.ConfigParser()
    configini.read('app/secrets/config.ini')
    
#     session = rauth.OAuth1Session(
#         consumer_key = configini['YELP']['consumer_key']
#         ,consumer_secret = configini['YELP']['consumer_secret']
#         ,access_token = configini['YELP']['token']
#         ,access_token_secret = configini['YELP']['token_secret'])
#     request = session.get("http://api.yelp.com/v2/search",params=params) 

    client = foursquare.Foursquare(
        client_id=configini['4SQUARE']['client_id']
        , client_secret=configini['4SQUARE']['client_secret'])
    
    t = time.time()
    request = client.venues.explore(params)
    print 'fetching %f s'%(time.time() - t)
    #Transforms the JSON API response into a Pandas dataframe
    t = time.time()
    #data = cleanData(request.json())
    data = cleanData4Square(request)
        
    print 'cleaning %f s'%(time.time()-t)
#     session.close()
   
    return data
    
def fetchData(lat,long,cache=False,offset=0):


    params = get_search_parameters(lat,long,offset=offset)
    data = get_results(params)
    return data
    
def priceString(thisprice):
    if thisprice == 1:
        return "<$10",""
    elif thisprice == 2:
        return "$10","$20"
    elif thisprice == 3:
        return "$20","$30"
    elif thisprice == 4:
        return "$40+", ""
    else:
        return "",""
        
def clusterDescriptor(cluster_categories):


    our_descriptors = list(cluster_categories)
    for i in range(len(our_descriptors)):
        our_descriptors[i] = our_descriptors[i][:-1]
    counts = Counter()
    for description in our_descriptors:
        counts.update(word.strip('.,?!"\'').lower() for word in description.split(','))
    # Take the highlights
    highlights = counts.most_common(3)
    
    
    # Human parsing
    if len(cluster_categories) < 4:
        des_str = "There's a few restaurants here: "
        for a in set(our_descriptors):
            des_str += a.lower()+', '
        des_str = des_str[:-2]
        return des_str
    
    if highlights[0][1]/float(len(cluster_categories)) <= 0.5:
        des_str = "Try here for "
        for a in highlights:
            des_str += a[0]+ ", "
        des_str = des_str[:-2]
        
        if len(cluster_categories) > len(highlights):
            des_str += " and more."
        else:
            des_str += "."
        return des_str
        
    else:
        des_str = "A %s nighborhood"%(highlights[0][0])
        if len(highlights) > 1:
            if highlights[1][1] >= 0.33:
                des_str += ' with some %s'%highlights[1][0]
            else:
                des_str += " with a dash of %s."%highlights[1][0]
            
        return des_str
        
def optimizeClusters(cluster_info,key=0):
    '''
    Optimize which three clusters to give the user
    optional parameter key controls which optimization to use
    key = 1 (distance, current default)
    key = 2 (price)
    key = 3 (rating)
    key = 0 (most popular)
    '''
          
    # 3 most popular
    if key == 0:
        pop = []
        for i in range(len(cluster_info)):
            pop.append(cluster_info[i]['reviews'])
        sorted_clusters = [i[0] for i in sorted(zip(cluster_info,pop),key= lambda l: l[1],reverse=True)] 
                 
    # 3 closest
    if key == 1:
        dist_from_user = []
        for i in range(len(cluster_info)):
            dist_from_user.append(cluster_info[i]['avg_dist'])
        sorted_clusters = [i[0] for i in sorted(zip(cluster_info,dist_from_user),key= lambda l: l[1])]  
        
    # 3 best rated
    if key == 3:
        rat = []
        for i in range(len(cluster_info)):
            rat.append(cluster_info[i]['avgrating'])
        sorted_clusters = [i[0] for i in sorted(zip(cluster_info,rat),key= lambda l: l[1],reverse=True)]

    return sorted_clusters
    
def foodGroups(lat,long,key=0):
    
    center = struct()
    center.lat = lat
    center.long = long
    
    t = time.time()
    data = fetchData(center.lat,center.long,cache=False)

    print 'Full Retrieve %f s'%(time.time()-t)
    data['dist_to_user'] = data['distance'] * 0.000621371 #meters to miles

    n_clusters_ = -1
    eps = 0.1
    min_samples = 3
    
    t = time.time()
    
    # Only use open places [may do better with all places to build clusters?]
    #data = data[data.IsOpenNow == True]

    for thiseps in np.arange(0.05,0.5,0.1):
        this_X,this_n_clusters_,this_labels,this_core_samples_mask = clusterThose(data[['latitude','longitude']],eps=thiseps,min_samples=min_samples)
        if this_n_clusters_ > n_clusters_:
            # Try to optimize around finding clusters
            eps = thiseps
            X = this_X
            n_clusters_ = this_n_clusters_
            labels = this_labels
            core_samples_mask = this_core_samples_mask
            
    print 'clustering %f s'%(time.time()-t)
    

    # Let's compute cluster informatics
    cluster_info = []
    for jj in range(n_clusters_):
        thiscluster = data[labels==jj]
        cluster = {}
        cluster["label"] = jj
        cluster["avgrating"] = np.mean(thiscluster.rating)
        cluster["stdrating"] = np.std(thiscluster.rating)
        cluster["avgprice"] = np.mean(thiscluster.price)
        cluster["stdprice"] = np.std(thiscluster.price)
        cluster["maxprice"] = np.max(thiscluster.price)
        cluster["minprice"] = np.min(thiscluster.price)
        cluster["reviews"] = sum(thiscluster.review_count)
        
        if len(data[labels==-1])>3:
            cluster["popularity"] = np.mean(thiscluster.review_count)/float(np.mean(data[labels==-1].review_count))
        else:
            cluster["popularity"] = np.mean(thiscluster.review_count)
        
        if np.max(thiscluster.price) == np.min(thiscluster.price):
            minprice_string,maxprice_string = priceString(cluster["maxprice"])
            if len(maxprice_string) == 0:
                cluster["price_string"] = minprice_string
            else:
                cluster["price_string"] = minprice_string + " to " + maxprice_string
        else:
            minprice_string,throwaway = priceString(cluster["minprice"])
            throwaway,maxprice_string = priceString(cluster["maxprice"])
            cluster["price_string"] = minprice_string + " to " + maxprice_string
        cluster["rest_num"] = len(thiscluster)
        cluster["categories"] = set(thiscluster["categories"])
#         cluster["hull"] = sp.spatial.ConvexHull(X[labels==jj])
        cluster["Description"] = clusterDescriptor(thiscluster["categories"])
        cluster["center"] = [np.mean(thiscluster['latitude']),np.mean(thiscluster['longitude'])]
        
        # Find the point nearest the center
        temp_cluster = thiscluster[['latitude','longitude','street']]
        temp_cluster['dist_to_mean'] = abs(thiscluster['latitude']-cluster["center"][0]) + abs(thiscluster['longitude']-cluster['center'][1])
        cluster["name"] = temp_cluster.sort(columns='dist_to_mean')[:1]["street"].iloc[0]
        cluster["avg_dist"] = np.mean(thiscluster['dist_to_user'])
        cluster["open_ratio"] =  sum(thiscluster.IsOpenNow)/float(len(thiscluster))
        cluster_info.append(cluster)

    cluster_info = optimizeClusters(cluster_info,key=key)
    
    # Order the data
    data['labels'] = labels
    newdata = pd.DataFrame(columns=data.columns)
    ranking = 0
    for a in cluster_info:
        ranking += 1
        thiscluster = data[data['labels']==a['label']]
        thiscluster['ranking'] = ranking
        newdata = pd.concat([newdata,thiscluster],axis=0)
        
    clusters = {}
    clusters['eps'] = eps
    clusters['X'] = X
    clusters['n_clusters'] = n_clusters_
    clusters['labels'] = labels
    clusters['core_samples_mask'] = core_samples_mask

    return clusters, newdata, cluster_info

def main():

    center = struct()
    center.lat = 37.786382
    center.long = -122.432883
    clusters,data,cluster_info = foodGroups(center.lat, center.long )
    X=clusters['X']
    n_clusters_ = clusters['n_clusters']
    labels = clusters['labels']
    core_samples_mask = clusters['core_samples_mask']

    fig,ax = figSetup.figSetup()
    # Black removed and is used for noise instead.
    unique_labels = set(labels)
    colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))
    for k, col in zip(unique_labels, colors):
        if k == -1:
            # Black used for noise.
            col = 'k'

        class_member_mask = (labels == k)
        xy = X[class_member_mask & core_samples_mask]
        plt.plot(xy[:, 1], xy[:, 0], 'o', markerfacecolor=col,
                 markeredgecolor='k', markersize=14)
        
        xy = X[class_member_mask & ~core_samples_mask]
        plt.plot(xy[:, 1], xy[:, 0], 'o', markerfacecolor=col,
                 markeredgecolor='k', markersize=6)
                 
        plt.plot(center.long,center.lat,'*g',markersize=8)
    
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    plt.show()

if __name__ == '__main__':
	main()
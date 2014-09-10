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
from collections import defaultdict
from sklearn.cluster import DBSCAN
from sklearn import metrics
from sklearn.preprocessing import StandardScaler
import rauth
import urllib2
import configparser
import pdb
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
    params = {}
#     params["term"] = "restaurant"
    params["category_filter"] = "restaurants"
    params["ll"] = "{},{}".format(str(lat),str(long))
    #params["radius_filter"] = "16092"
    params["sort"] = "1"
    params["limit"] = "20"
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
    
        full_address = ''
        for a in businesslist[i]['location']['display_address']:
            full_address = full_address +' %s'%a
            
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
            pdb.set_trace()
            print 'failwhale'
            pass
        
        
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
    
    healing = {}
    for a in failures:
        lat,lon,full_add,data = maps.geocode(a)
        healing[a] = {}
        healing[a]['latitude'] = lat
        healing[a]['longitude'] = lon

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
    
    session = rauth.OAuth1Session(
        consumer_key = configini['YELP']['consumer_key']
        ,consumer_secret = configini['YELP']['consumer_secret']
        ,access_token = configini['YELP']['token']
        ,access_token_secret = configini['YELP']['token_secret'])
     
    request = session.get("http://api.yelp.com/v2/search",params=params)
   
    #Transforms the JSON API response into a Pandas dataframe
    data = cleanData(request.json())
    session.close()
   
    return data
    
def fetchData(lat,long,cache=False,offset=0):

    if cache:
        data = jsonOpen.jsonOpen('yelp_pheonix_business.json')
        return

    params = get_search_parameters(lat,long,offset=offset)
    data = get_results(params)
    return data

def foodGroups(lat,long):
    
    center = struct()
    center.lat = lat
    center.long = long
    cutoff = 0.5
    
    for i in range(2):
        if i == 0:
            data = fetchData(center.lat,center.long,cache=False)
        else:
            data = data.append(fetchData(center.lat,center.long,cache=False,offset=20*i),ignore_index=True)
    
    data['dist_to_user'] = data['distance'] * 0.000621371 #meters to miles
#     results = data[data['dist_to_user']<=cutoff]
    results = data
    
#     while len(results)<20:
#         cutoff = cutoff * 3
#         results = data[data['dist_to_user']<=cutoff]
#         if cutoff > 7:
#             break
    
    n_clusters_ = 0
    eps = .2
    min_samples = 4
    
    while n_clusters_ < 5:
        X, n_clusters_,labels,core_samples_mask = clusterThose(results[['latitude','longitude']],eps=eps,min_samples=min_samples)
        min_samples = min_samples - 1
        eps += 0.1
        if min_samples == 2:
            break
    
#     print('Estimated number of clusters: %d' % n_clusters_)
#     print("Homogeneity: %0.3f" % metrics.homogeneity_score(labels_true, labels))
#     print("Completeness: %0.3f" % metrics.completeness_score(labels_true, labels))
#     print("V-measure: %0.3f" % metrics.v_measure_score(labels_true, labels))
#     print("Adjusted Rand Index: %0.3f"
#         % metrics.adjusted_rand_score(labels_true, labels))
#     print("Adjusted Mutual Information: %0.3f"
#         % metrics.adjusted_mutual_info_score(labels_true, labels))
#     print("Silhouette Coefficient: %0.3f"
#         % metrics.silhouette_score(X, labels))

    clusters = {}
    clusters['X'] = X
    clusters['n_clusters'] = n_clusters_
    clusters['labels'] = labels
    clusters['core_samples_mask'] = core_samples_mask

    return clusters

def main():

    center = struct()
    center.lat = 37.786382
    center.long = -122.432883
    clusters = foodGroups(center.lat, center.long )
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
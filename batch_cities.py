#!/usr/bin/env python
"""
batch_cities.py
author p.phelps
Run clustering over batched cities (from MySQL and add returned n_clusters to the database)
"""

import pymysql as mdb
import pandas as pd
import pandas.io.sql as psql
import foodgroups
import pdb
import time
from threading import Thread
from random import randint

def noInterrupt(con,cur,insert,df,cluster_results):
    try:
        
        cur.execute(insert)
        con.commit()
        our_id_q = 'SELECT MAX(request_id) FROM foodgrouper.requests;'
        cur.execute(our_id_q)
        our_id = cur.fetchone()
        cluster_results['request_id'] = our_id[0]
        df['request_id'] = our_id[0]
        df.to_sql(name='Results',con=con,flavor='mysql',if_exists='append',index=True)
        
        # Saved the restaurants now save their cluster information
        our_r_id_q = 'Select result_id FROM foodgrouper.Results order by result_id DESC LIMIT %i;'%(len(df))
        cur.execute(our_r_id_q)
        our_r_id = cur.fetchall()
        useful_rid = []
        for a in our_r_id:
            useful_rid.append(a[0])
        cluster_results['result_id'] = useful_rid[::-1]
               
        cluster_results.to_sql(name='ClusterResults',con=con,flavor='mysql',if_exists='append',index=True)
        
    finally:
        pass
        
def main():

    db = mdb.connect(user="root",host="localhost",passwd="konnichiwa1",db="foodgrouper")
    query = 'Select * from foodgrouper.CityPopulation;'
    df = psql.frame_query(query, db)
    cur = db.cursor()
    
    for i in range(103,len(df[['latitude','longitude']])):
        latlong = df[['latitude','longitude']][i-1:i]
        clusters,data = foodgroups.foodGroups(latlong['latitude'][i-1],latlong['longitude'][i-1])
        
        cluster_results = pd.DataFrame()
        cluster_results['labels'] = clusters['labels']
        cluster_results['core_samples_mask'] = clusters['core_samples_mask']
        cluster_results['eps'] = clusters['eps']
        
        insert_request = "INSERT INTO foodgrouper.requests(latitude,longitude,City,State) VALUES (%f, %f, '%s', '%s');"%(latlong['latitude'][i-1]
                ,latlong['longitude'][i-1],df['City'][i-1:i][i-1],df['State'][i-1:i][i-1])
                
        print "Writing city %i: %s, %s data to DB."%(i,df['City'][i-1:i][i-1],df['State'][i-1:i][i-1])
        
        a = Thread(target=noInterrupt, args=(db,cur,insert_request,data,cluster_results))
        a.start()
        a.join()
        time.sleep(randint(1,3))

    cur.close()
    con.close()
if __name__ == '__main__':
	main()
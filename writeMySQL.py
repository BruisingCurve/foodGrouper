 
#!/usr/bin/env python
"""
writeMySQL.py
author p.phelps
MySQL foodgrouper caching
"""

import pymysql as mdb
import configparser
from threading import Thread
import pandas as pd
import unicodedata

def cleanData(df):
    '''
    Clean up possible unicode characters in the data
    '''
    if isinstance(df.full_address,unicode):
        df.full_address = [unicodedata.normalize('NFKD',thisword).encode('ascii','ignore') for thisword in df.full_address]
    if isinstance(df.name,unicode):
        df.name = [unicodedata.normalize('NFKD',thisword).encode('ascii','ignore') for thisword in df.name]
    if isinstance(df.categories,unicode):
        df.categories = [unicodedata.normalize('NFKD',thisword).encode('ascii','ignore') for thisword in df.categories]
    if isinstance(df.categories,unicode):
        df.street = [unicodedata.normalize('NFKD',thisword).encode('ascii','ignore') for thisword in df.street]
    return df

def noInterrupt(con,cur,insert,df,c_info,cluster_results):
    try:
        cur.execute(insert)
        con.commit()
        our_id_q = 'SELECT MAX(request_id) FROM foodgrouper.requests;'
        cur.execute(our_id_q)
        our_id = cur.fetchone()
        cluster_results['request_id'] = our_id[0]
        df['request_id'] = our_id[0]
        
        df = cleanData(df)
        df.to_sql(name='Results',con=con,flavor='mysql',if_exists='append',index=True)


        # Saved the restaurants now save their cluster information
        our_r_id_q = 'Select result_id FROM foodgrouper.Results order by result_id DESC LIMIT %i;'%(len(df))
        cur.execute(our_r_id_q)
        our_r_id = cur.fetchall()
        useful_rid = []
        for a in our_r_id:
            useful_rid.append(a[0])
         
        cluster_results['result_id'] = useful_rid[::-1]
        cluster_results['request_id'] = our_id[0]
        
        
#         temp_info = c_info[['label','avg_dist','avgprice','avgrating','request_id','maxprice','minprice','rest_num',
#             'stdprice','stdrating','var_score','rest_frac']]
        for a in c_info:
            a['request_id'] = our_id[0]
            cinfo_insert = "Insert into foodgrouper.ClusterInfo(label,avg_dist,avgprice,avgrating,request_id,maxprice,minprice,rest_num,stdprice,stdrating,var_score,rest_frac,n_review,review_frac) values (%i,%f,%f,%f,%i,%i,%i,%i,%f,%f,%f,%f,%i,%f);"%(
                        a['label'],
                        a['avg_dist'],
                        a['avgprice'],
                        a['avgrating'],
                        a['request_id'],
                        a['maxprice'],
                        a['minprice'],
                        a['rest_num'],
                        a['stdprice'],
                        a['stdrating'],
                        a['var_score'],
                        a['rest_frac'],
                        a['reviews'],
                        a['review_frac']
                        )
            cur.execute(cinfo_insert)
            con.commit()
        cluster_results.to_sql(name='ClusterResults',con=con,flavor='mysql',if_exists='append',index=True)
  
    finally:
        pass

def writeMySQL(lat,lng,clusters,data,c_info):

    configini = configparser.ConfigParser()
    configini.read('app/secrets/config.ini')

    db = mdb.connect(user=configini['MYSQL']['user'],host="localhost",passwd=configini['MYSQL']['word'],db=configini['MYSQL']['db'])
    cur = db.cursor()

    # Convert cluster results to pd.DataFrame
    cluster_results = pd.DataFrame()
    cluster_results['labels'] = clusters['labels']
    cluster_results['core_samples_mask'] = clusters['core_samples_mask']
    cluster_results['eps'] = clusters['eps']
    cluster_results=cluster_results[cluster_results.labels!= -1]

    insert_request = "INSERT INTO foodgrouper.requests(latitude,longitude) VALUES (%f, %f);"%(lat, lng)
    
    a = Thread(target=noInterrupt, args=(db,cur,insert_request,data,c_info,cluster_results))
    a.start()
    a.join()

    cur.close()
    db.close()

    return



""" This is the master script that does these steps:
    -- fetch a batch of alerts from kafka
    -- run the watchlist code and insert the hits
    -- run the active user queries and produce kafka
    -- build a CSV file of three tables with the batch: 
        objects, sherlock_classifications, watchlist_hits, area_hits
    -- scp those files to lasair-db
    -- ssh to ingest those files to master database
"""
import os,sys
sys.path.append('../../common')
import time, tempfile
from socket import gethostname
from datetime import datetime
import settings
from src.manage_status import manage_status
from src import slack_webhook, date_nid, db_connect
import run_active_queries
from check_alerts_watchlists import get_watchlist_hits, insert_watchlist_hits
from check_alerts_areas import get_area_hits, insert_area_hits
from counts import since_midnight, grafana_today

def main(nprocesses=1, topic='ztf_sherlock'):
    print('------------------')
    ##### clear out the local database
    os.system('date')
    print('clear local caches')
    sys.stdout.flush()
    cmd = 'python3 refresh.py'
    if os.system(cmd) != 0:
        rtxt = "ERROR in filter/filter.py: refresh.py failed"
        print(rtxt)
        slack_webhook.send(settings.SLACK_URL, rtxt)
        sys.stdout.flush()
        sys.exit(-1)
    
    ##### fetch a batch of annotated alerts
    print('INGEST start %s' % datetime.utcnow().strftime("%H:%M:%S"))
    print("Topic is %s" % topic)
    t = time.time()
    
    cmd =  'python3 consume_alerts.py '
    cmd += '--maxalert %d ' % settings.KAFKA_MAXALERTS
    cmd += '--nprocess %d ' % nprocesses
    cmd += '--group %s '    % settings.KAFKA_GROUPID
    cmd += '--host %s '     % settings.KAFKA_SERVER
    cmd += '--topic ' + topic
    
    print(cmd)
    # rc is the return code from ingestion, number of alerts received
    rc = os.system(cmd)
    if rc < 0:
        rtxt = "ERROR in filter/filter: consume_alerts failed"
        slack_webhook.send(settings.SLACK_URL, rtxt)
        print(rtxt)
        sys.stdout.flush()
        sys.exit(-1)
    
    print('INGEST duration %.1f seconds' % (time.time() - t))
    
    try:
        msl_local = db_connect.local()
    except:
        print('ERROR in filter/filter: cannot connect to local database')
        sys.stdout.flush()
        sys.exit(-1)
    
    ##### run the watchlists
    print('WATCHLIST start %s' % datetime.utcnow().strftime("%H:%M:%S"))
    sys.stdout.flush()
    t = time.time()
    try:
        hits = get_watchlist_hits(msl_local, settings.WATCHLIST_MOCS, settings.WATCHLIST_CHUNK)
    except Exception as e:
        rtxt = "ERROR in filter/get_watchlist_hits"
        rtxt += str(e)
        slack_webhook.send(settings.SLACK_URL, rtxt)
        print(rtxt)
        sys.stdout.flush()
        sys.exit(-1)
    
    print('got %d watchlist hits' % len(hits))
    sys.stdout.flush()
    
    if len(hits) > 0:
        try:
            insert_watchlist_hits(msl_local, hits)
        except Exception as e:
            rtxt = "ERROR in filter/insert_watchlist_hits"
            rtxt += str(e)
            slack_webhook.send(settings.SLACK_URL, rtxt)
            print(rtxt)
            sys.stdout.flush()
            sys.exit(-1)
    
    print('WATCHLIST %.1f seconds' % (time.time() - t))
    sys.stdout.flush()
    
    ##### run the areas
    print('AREA start %s' % datetime.utcnow().strftime("%H:%M:%S"))
    sys.stdout.flush()
    t = time.time()
    try:
        hits = get_area_hits(msl_local, settings.AREA_MOCS)
    except Exception as e:
        rtxt = "ERROR in filter/get_area_hits"
        rtxt += str(e)
        slack_webhook.send(settings.SLACK_URL, rtxt)
        print(rtxt)
        sys.stdout.flush()
        sys.exit(-1)
    
    print('got %d area hits' % len(hits))
    sys.stdout.flush()
    if len(hits) > 0:
        try:
            insert_area_hits(msl_local, hits)
        except Exception as e:
            rtxt = "ERROR in filter/insert_area_hits"
            rtxt += str(e)
            slack_webhook.send(settings.SLACK_URL, rtxt)
            print(rtxt)
            sys.stdout.flush()
            sys.exit(-1)
    print('AREA %.1f seconds' % (time.time() - t))
    sys.stdout.flush()
    
    ##### run the user queries
    print('QUERIES start %s' % datetime.utcnow().strftime("%H:%M:%S"))
    sys.stdout.flush()
    t = time.time()
    try:
        query_list = run_active_queries.fetch_queries()
    except Exception as e:
        rtxt = "ERROR in filter/run_active_queries.fetch_queries"
        rtxt += str(e)
        slack_webhook.send(settings.SLACK_URL, rtxt)
        print(rtxt)
        sys.stdout.flush()
        sys.exit(-1)
    
    try:
        run_active_queries.run_queries(query_list)
    except Exception as e:
        rtxt = "ERROR in filter/run_active_queries.run_queries"
        rtxt += str(e)
        slack_webhook.send(settings.SLACK_URL, rtxt)
        print(rtxt)
        sys.stdout.flush()
        sys.exit(-1)
    print('QUERIES %.1f seconds' % (time.time() - t))
    sys.stdout.flush()
    
    ##### run the annotation queries
    print('ANNOTATION QUERIES start %s' % datetime.utcnow().strftime("%H:%M:%S"))
    sys.stdout.flush()
    t = time.time()
    try:
        run_active_queries.run_annotation_queries(query_list)
    except Exception as e:
        rtxt = "WARNING in filter/run_active_queries.run_annotation_queries"
        rtxt += str(e)
        print(rtxt)
        sys.stdout.flush()
    print('ANNOTATION QUERIES %.1f seconds' % (time.time() - t))
    
    ##### build CSV file with local database
    t = time.time()
    print('SEND to ARCHIVE')
    sys.stdout.flush()
    cmd = 'sudo rm /data/mysql/*.txt'
    os.system(cmd)
    
    cmd = 'mysql --user=ztf --database=ztf --password=%s < output_csv.sql' % settings.LOCAL_DB_PASS
    if os.system(cmd) != 0:
        rtxt = 'ERROR in filter/filter: cannot build CSV from local database'
        slack_webhook.send(settings.SLACK_URL, rtxt)
        print(rtxt)
        sys.stdout.flush()
        sys.exit(-1)
    
    tablelist = ['objects', 'sherlock_classifications', 'watchlist_hits', 'area_hits']
    
    ##### send CSV file to central database
    t = time.time()

    for table in tablelist:
        sql  = "LOAD DATA LOCAL INFILE '/data/mysql/%s.txt' " % table
        sql += "REPLACE INTO TABLE %s FIELDS TERMINATED BY ',' " % table
        sql += "ENCLOSED BY '\"' LINES TERMINATED BY '\n'"

        tmpfilename = tempfile.NamedTemporaryFile().name + '.sql'
        f = open(tmpfilename, 'w')
        f.write(sql)
        f.close()

        cmd =  "mysql --user=%s --database=ztf --password=%s --port=%s --host=%s < %s" 
        cmd = cmd % (settings.DB_USER_READWRITE, settings.DB_PASS_READWRITE, settings.DB_PORT, settings.DB_HOST, tmpfilename)
        if os.system(cmd) != 0:
            rtxt = 'ERROR in filter/filter: cannot push local to master database'
            slack_webhook.send(settings.SLACK_URL, rtxt)
            print(rtxt)
            sys.stdout.flush()
            sys.exit(-1)
        print(table, 'ingested to master')

    print('Transfer to master %.1f seconds' % (time.time() - t))
    sys.stdout.flush()
    
    ms = manage_status(settings.SYSTEM_STATUS)
    nid = date_nid.nid_now()
    d = since_midnight()
    ms.set({
        'today_ztf':grafana_today(), 
        'today_database':d['count'], 
        'min_delay':d['delay'], 
        'total_count': d['total_count'],
        'nid': nid}, 
        nid)
    print('Exit status', rc)
    sys.stdout.flush()
    if rc > 0: sys.exit(1)
    else:      sys.exit(0)

if __name__ == '__main__':
    # number of processes, input topic
    if len(sys.argv) > 2:
        rc = main(int(sys.argv[1]), sys.argv[2])
    elif len(sys.argv) > 1:
        rc = main(int(sys.argv[1]), 'ztf_sherlock')
    else:
        rc = main(2, 'ztf_sherlock')
    sys.exit(rc)

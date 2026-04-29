import os
import json
import time
from datetime import datetime, timezone
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pymongo import MongoClient
import redis
from bson import ObjectId
from processor import process

# Worker uses BRPOPLPUSH to move messages to a processing list, removing after success.
# Failed messages are moved to a DLQ after max retries.

MONGO = os.environ.get('MONGO_URI','mongodb://mongo:27017/tasks')
REDIS = os.environ.get('REDIS_URL','redis://redis:6379')
QUEUE = os.environ.get('REDIS_QUEUE','tasks:queue')
PROCESSING = QUEUE + ':processing'
DLQ = QUEUE + ':dlq'
MAX_RETRIES = int(os.environ.get('MAX_RETRIES','5'))

rc = redis.Redis.from_url(REDIS, decode_responses=True)
mc = MongoClient(MONGO)
db = mc.get_database()
tasks = db.tasks



def handle_payload(raw):
    try:
        payload = json.loads(raw)
        taskId = payload.get('taskId')
        if not taskId:
            rc.lpush(DLQ, raw)
            return
        objid = ObjectId(taskId)
        t = tasks.find_one({'_id': objid})
        if not t:
            # nothing to do, remove from processing
            try:
                rc.lrem(PROCESSING, 1, raw)
            except Exception:
                pass
            return
        # mark processing in DB with timestamp
        processing_ts = payload.get('processing_ts')
        try:
            if processing_ts:
                proc_dt = datetime.fromisoformat(processing_ts)
            else:
                proc_dt = datetime.now(timezone.utc)
        except Exception:
            proc_dt = datetime.now(timezone.utc)
        tasks.update_one({'_id': objid}, {'$set': {'status':'running', 'processingAt': proc_dt}})
        try:
            res = process(t.get('operation'), t.get('inputText',''))
            tasks.update_one({'_id': objid}, {'$set': {'result': res, 'status':'success'}, '$push': {'logs': 'processed'}})
            # remove from processing list
            rc.lrem(PROCESSING, 1, raw)
        except Exception as e:
            # increment retries and decide DLQ
            r = tasks.find_one_and_update({'_id': objid}, {'$inc': {'retries': 1}, '$push': {'logs': str(e)}}, return_document=False)
            retries = (r.get('retries',0) if r else 0) + 1
            if retries >= MAX_RETRIES:
                tasks.update_one({'_id': objid}, {'$set': {'status':'failed'}})
                rc.lpush(DLQ, raw)
                rc.lrem(PROCESSING, 1, raw)
            else:
                # leave in processing to be picked up by requeue job or move back
                rc.lrem(PROCESSING, 1, raw)
                rc.lpush(QUEUE, raw)
    except Exception:
        # malformed payload -> push to DLQ
        try:
            rc.lpush(DLQ, raw)
        except Exception:
            pass

def main():
    while True:
        try:
            # block until item available, atomically move to processing list
            raw = rc.brpoplpush(QUEUE, PROCESSING, timeout=5)
            if not raw:
                time.sleep(0.2)
                continue
            # attach processing timestamp to the item in PROCESSING list
            try:
                payload = json.loads(raw)
            except Exception:
                payload = {'raw': raw}
            payload['processing_ts'] = datetime.now(timezone.utc).isoformat()
            new_raw = json.dumps(payload)
            # replace the entry in processing list: remove old and push updated
            try:
                rc.lrem(PROCESSING, 1, raw)
                rc.lpush(PROCESSING, new_raw)
            except Exception:
                # if replace fails, continue with original raw
                new_raw = raw
            handle_payload(new_raw)
        except redis.exceptions.RedisError:
            time.sleep(1)
        except Exception:
            time.sleep(0.5)

if __name__=='__main__':
    # start health server
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != '/healthz':
                self.send_response(404)
                self.end_headers()
                return
            ok = False
            try:
                if rc.ping() and mc.admin.command('ping'):
                    ok = True
            except Exception:
                ok = False
            if ok:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK')
            else:
                self.send_response(500)
                self.end_headers()

    def run_health():
        server = HTTPServer(('0.0.0.0', 8080), HealthHandler)
        server.serve_forever()

    t = threading.Thread(target=run_health, daemon=True)
    t.start()
    main()

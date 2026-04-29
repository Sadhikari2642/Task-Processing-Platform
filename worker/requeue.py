import os
import json
import time
from datetime import datetime, timezone
import redis
from pymongo import MongoClient

REDIS = os.environ.get('REDIS_URL','redis://redis:6379')
QUEUE = os.environ.get('REDIS_QUEUE','tasks:queue')
PROCESSING = QUEUE + ':processing'
DLQ = QUEUE + ':dlq'
STALE_SECONDS = int(os.environ.get('REQUEUE_STALE_SECONDS','300'))
MONGO = os.environ.get('MONGO_URI','mongodb://mongo:27017/tasks')

rc = redis.Redis.from_url(REDIS, decode_responses=True)
mc = MongoClient(MONGO)
db = mc.get_database()
tasks = db.tasks

def iso_to_ts(s):
    try:
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()
    except Exception:
        return 0

def main():
    now = time.time()
    items = rc.lrange(PROCESSING, 0, -1)
    for raw in items:
        try:
            payload = json.loads(raw)
            # prioritize processing_ts (set when claimed), fallback to creation ts
            ts = payload.get('processing_ts') or payload.get('ts')
            pts = iso_to_ts(ts)
            if now - pts > STALE_SECONDS:
                # move back to queue for retry and update DB status
                try:
                    rc.lrem(PROCESSING, 1, raw)
                except Exception:
                    pass
                rc.lpush(QUEUE, raw)
                # update DB
                taskId = payload.get('taskId')
                if taskId:
                    try:
                        from bson import ObjectId
                        objid = ObjectId(taskId)
                        tasks.update_one({'_id': objid}, {'$set': {'status': 'pending'}, '$push': {'logs': 'requeued: visibility timeout'}})
                    except Exception:
                        pass
        except Exception:
            # malformed -> move to DLQ
            try:
                rc.lrem(PROCESSING, 1, raw)
                rc.lpush(DLQ, raw)
            except Exception:
                pass

if __name__=='__main__':
    main()

import json
import threading
import time
from queue import Queue


class RealtimeHub:
    def __init__(self):
        self._subscribers = set()
        self._lock = threading.Lock()

    def subscribe(self):
        subscriber = Queue(maxsize=100)
        with self._lock:
            self._subscribers.add(subscriber)
        return subscriber

    def unsubscribe(self, subscriber):
        with self._lock:
            self._subscribers.discard(subscriber)

    def publish(self, event_type, resource, method):
        message = json.dumps(
            {
                "type": event_type,
                "resource": resource,
                "method": method,
                "timestamp": int(time.time()),
            },
            ensure_ascii=False,
        )
        with self._lock:
            subscribers = tuple(self._subscribers)
        for subscriber in subscribers:
            try:
                subscriber.put_nowait(message)
            except Exception:
                self.unsubscribe(subscriber)


realtime = RealtimeHub()

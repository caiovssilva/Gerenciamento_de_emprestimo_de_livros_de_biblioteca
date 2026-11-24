import json

from sync_hub import RealtimeHub


def test_realtime_hub_delivers_data_change_to_subscribers():
    hub = RealtimeHub()
    subscriber = hub.subscribe()

    hub.publish("data_changed", "loans", "POST")

    payload = json.loads(subscriber.get(timeout=1))
    assert payload["type"] == "data_changed"
    assert payload["resource"] == "loans"
    assert payload["method"] == "POST"


def test_realtime_hub_removes_subscriber():
    hub = RealtimeHub()
    subscriber = hub.subscribe()

    hub.unsubscribe(subscriber)

    assert subscriber not in hub._subscribers

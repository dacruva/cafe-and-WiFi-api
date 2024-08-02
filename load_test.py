"""

This Molotov script has:

- a global setup fixture that sets a global headers dict
- an init worker fixture that sets the session headers
- 3 scenario
- 2 tear downs fixtures

how to run
molotov load_test.py -p 10 -w 200 -d 10

"""
import json
import time
from molotov import (
    get_context,
    global_setup,
    global_teardown,
    scenario,
    setup,
    teardown,
)
import molotov

_API = "http://localhost:5000/random"
_HEADERS = {}
_T = {}


def _now():
    return time.time() * 1000


@molotov.events()
async def record_time(event, **info):
    req = info.get("request")
    if event == "sending_request":
        _T[req] = _now()
    elif event == "response_received":
        _T[req] = _now() - _T[req]



# notice that the global setup, global teardown and teardown
# are not a coroutine.
@global_setup()
def init_test(args):
    _HEADERS["SomeHeader"] = "1"


# @global_teardown()
# def end_test():
#     print("This is the end")


@setup()
async def init_worker(worker_num, args):
    headers = {"AnotherHeader": "1"}
    headers.update(_HEADERS)
    return {"headers": headers}


@teardown()
def end_worker(worker_num):
    print("This is the end for %d" % worker_num)


@molotov.global_teardown()
def display_average():
    average = sum(_T.values()) / len(_T)
    print("\nAverage response time %dms" % average)


# @scenario(weight=40)
async def scenario_one(session):
    async with session.get(_API) as resp:
        if get_context(session).statsd:
            get_context(session).statsd.incr("BLEH")
        res = await resp.json()
        assert res["result"] == "OK"
        assert resp.status == 200
    display_average()



@scenario(weight=30)
async def scenario_two(session):
    async with session.get(_API) as resp:
        assert resp.status == 200
    display_average()



# @scenario(weight=30)
async def scenario_three(session):
    cafe_data = json.dumps({"OK": 1})
    async with session.post(_API, data=cafe_data) as resp:
        assert resp.status == 200
    display_average()

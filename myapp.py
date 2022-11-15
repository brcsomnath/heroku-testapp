from pymongo import MongoClient

from flask import Flask, jsonify, request
import requests
import json
import time
import datetime

from bson import json_util

app = Flask(__name__)


client = MongoClient(
    # "mongodb+srv://brcsomnath:somnath@cluster0.yotvcvg.mongodb.net/test"
    "mongodb+srv://somnath_db:hf931nG5qL2zTWXL@cluster0.jt4v9ik.mongodb.net/?retryWrites=true&w=majority"
)
db = client["somnath_db"]

token = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyMzhRUEYiLCJzdWIiOiJCNEYzNVEiLCJpc3MiOiJGaXRiaXQiLCJ0eXAiOiJhY2Nlc3NfdG9rZW4iLCJzY29wZXMiOiJyc29jIHJzZXQgcm94eSBycHJvIHJudXQgcnNsZSByYWN0IHJyZXMgcmxvYyByd2VpIHJociBydGVtIiwiZXhwIjoxNjkyMzIyMTc4LCJpYXQiOjE2NjA3ODYxNzh9.t4-tjP-pBKe-wdbYLTL9t-h7wAOWsAlu-cGurSkfJiU"
header = {"Accept": "application/json", "Authorization": "Bearer {}".format(token)}


def parse_json(data):
    return json.loads(json_util.dumps(data))


def get_offset(time):
    tm_hr, tm_min, tm_sec = time.split(":")
    tm_hr = int(tm_hr)
    tm_min = int(tm_min)
    tm_sec = int(tm_sec)
    now = datetime.datetime.now()
    print(f"now: {now}")
    print(f"time: {time}")

    curr_hr = now.hour
    curr_min = now.minute
    curr_sec = now.second
    curr_time = (curr_hr) * 60 * 60 + curr_min * 60 + curr_sec
    if curr_time < 300 * 60:
        curr_time += 19 * 60 * 60
    else:
        curr_time -= 5 * 60 * 60

    tm_time = (tm_hr) * 60 * 60 + tm_min * 60 + tm_sec
    # assert curr_time >= tm_time
    offset = curr_time - tm_time
    return offset


def get_today():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d")


@app.route("/myjoke", methods=["GET"])
def mymethod():
    joke = "Why did everyone cross the road? Ha! ha, ha!"
    ret = {"category": "very funny", "value": joke}
    return jsonify(ret)


@app.route("/heartrate/last", methods=["GET"])
def get_heartrate():
    today = "today"
    url = (
        "https://api.fitbit.com/1/user/-/activities/heart/date/"
        + today
        + "/1d/1min.json"
    )
    resp = requests.get(url, headers=header).json()

    data = resp["activities-heart-intraday"]["dataset"][::-1]
    for i in range(len(data)):
        time = data[i]["time"]
        val = data[i]["value"]
        if val > 0:
            offset = get_offset(time)
            ret = {"heart-rate": val, "time offset": offset}
            return jsonify(ret)

    return "No heart rate found for today"


@app.route("/steps/last", methods=["GET"])
def get_steps():
    today = "today"
    acturl = (
        f"https://api.fitbit.com/1/user/-/activities/steps/date/{today}/1d/1min.json"
    )
    steps_resp = requests.get(acturl, headers=header).json()

    step_count = 0
    time = None
    for v in steps_resp["activities-steps-intraday"]["dataset"]:
        step_count += v["value"]
        if time is None and v["value"] > 0:
            time = v["time"]

    acturl = (
        f"https://api.fitbit.com/1/user/-/activities/distance/date/{today}/1d/1min.json"
    )
    dist_resp = requests.get(acturl, headers=header).json()
    distance = 0
    for v in dist_resp["activities-distance-intraday"]["dataset"]:
        distance += v["value"]

    offset = get_offset(time)

    return jsonify(
        {
            "step-count": step_count,
            "distance": round(distance, 2),
            "time offset": offset,
        }
    )


@app.route("/sleep/<jtype>", methods=["GET"])
def get_sleep(jtype):
    # 2022-08-24
    acturl = f"https://api.fitbit.com/1.2/user/-/sleep/date/{jtype}.json"
    resp = requests.get(acturl, headers=header).json()
    return jsonify(resp["summary"]["stages"])


@app.route("/activity/<jtype>", methods=["GET"])
def get_activity(jtype):
    # 2022-08-24
    acturl = f"https://api.fitbit.com/1/user/-/activities/date/{jtype}.json"
    resp = requests.get(acturl, headers=header).json()
    summary = resp["summary"]
    ret = {
        "very-active": summary["veryActiveMinutes"],
        "lightly-active": summary["lightlyActiveMinutes"],
        "sedentary": summary["sedentaryMinutes"],
    }
    return jsonify(ret)


@app.route("/sensors/env", methods=["GET"])
def get_environment():
    row = db.env.find().sort("_id", -1).limit(1)
    resp = parse_json(row)[0]

    data = {}
    data["temp"] = float(resp["temp"])
    data["humidity"] = float(resp["humidity"])
    data["timestamp"] = float(resp["timestamp"])
    return jsonify(data)


@app.route("/sensors/pose", methods=["GET"])
def get_pose():
    row = db.pose.find().sort("_id", -1).limit(1)
    resp = parse_json(row)[0]

    data = {}
    data["presence"] = resp["presence"]
    data["pose"] = resp["pose"]
    data["timestamp"] = float(resp["timestamp"])
    return jsonify(data)


@app.route("/post/env", methods=["POST"])
def post_env():
    content = request.get_json(force=True)
    content["timestamp"] = time.time()
    db.env.insert_one(content)
    return "Success"


@app.route("/post/pose", methods=["POST"])
def post_pose():
    content = request.get_json(force=True)
    content["timestamp"] = time.time()
    db.pose.insert_one(content)
    return "Success"


if __name__ == "__main__":
    app.run(debug=True)

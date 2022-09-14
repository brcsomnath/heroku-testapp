from flask import Flask, jsonify
import requests
import json
import datetime

app = Flask(__name__)


token = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyMzhRUEYiLCJzdWIiOiJCNEYzNVEiLCJpc3MiOiJGaXRiaXQiLCJ0eXAiOiJhY2Nlc3NfdG9rZW4iLCJzY29wZXMiOiJyc29jIHJzZXQgcm94eSBycHJvIHJudXQgcnNsZSByYWN0IHJyZXMgcmxvYyByd2VpIHJociBydGVtIiwiZXhwIjoxNjkyMzIyMTc4LCJpYXQiOjE2NjA3ODYxNzh9.t4-tjP-pBKe-wdbYLTL9t-h7wAOWsAlu-cGurSkfJiU"
header = {"Accept": "application/json", "Authorization": "Bearer {}".format(token)}


def get_offset(date_time_str):
    last_time = datetime.datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
    offset = datetime.datetime.now() - last_time
    return offset.seconds


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
    today = get_today()
    url = (
        "https://api.fitbit.com/1/user/-/activities/heart/date/"
        + today
        + "/1d/1min.json"
    )
    resp = requests.get(url, headers=header).json()
    if len(resp["activities-heart-intraday"]["dataset"]) == 0:
        print("Pick another date")
        return
    heartrate = resp["activities-heart-intraday"]["dataset"][-1]["value"]
    time = resp["activities-heart-intraday"]["dataset"][-1]["time"]

    date_time_str = f"{today} {time}"
    offset = get_offset(date_time_str)
    ret = {"heart-rate": heartrate, "time offset": f"{offset/60-240} sec"}
    return jsonify(ret)


@app.route("/steps/last", methods=["GET"])
def get_steps():
    today = get_today()
    acturl = f"https://api.fitbit.com/1/user/-/activities/steps/date/{today}/1d.json"
    resp = requests.get(acturl, headers=header).json()

    steps = resp["activities-steps-intraday"]["dataset"][-1]["value"]
    time = resp["activities-steps-intraday"]["dataset"][-1]["time"]
    print(resp)

    date_time_str = f"{today} {time}"
    offset = get_offset(date_time_str)
    ret = {"step-count": steps, "time offset": f"{offset/60-240} min"}
    return jsonify(ret)


@app.route("/sleep/<jtype>", methods=["GET"])
def get_sleep(jtype):
    acturl = f"https://api.fitbit.com/1.2/user/-/sleep/date/{jtype}.json"
    resp = requests.get(acturl, headers=header).json()
    return jsonify(resp["summary"]["stages"])


@app.route("/activity/<jtype>", methods=["GET"])
def get_activity(jtype):
    acturl = f"https://api.fitbit.com/1/user/-/activities/date/{jtype}.json"
    resp = requests.get(acturl, headers=header).json()
    summary = resp["summary"]
    ret = {
        "very-active": summary["veryActiveMinutes"],
        "lightly-active": summary["lightlyActiveMinutes"],
        "sedantary": summary["sedentaryMinutes"],
    }
    return jsonify(ret)


@app.route("/sensor/env", methods=["GET"])
def get_environment():
    first = "2022-06-14"
    last = "2022-09-13"
    acturl = f"https://api.fitbit.com/1/user/-/temp/core/date/{first}/{last}.json"
    resp = requests.get(acturl, headers=header).json()
    print(resp)
    return resp


if __name__ == "__main__":
    app.run(debug=True)

from fastapi import fastapi, Request, HTTPException,requests
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
import motor.motor_asyncio
from datetime import datetime,timedelta
import pydantic
import uvicorn
import json
import os
import re



app = fastapi()
client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGO_DB_CONNECTION'))
database = client.state


pydantic.json.ENCODERS_BY_TYPE[ObjectId] = str

origins = ["https://simple-smart-hub-client.netlify.app/"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/state",status_code=200)
async def sendState(request:Request):

    state = await request.json()
    state["datetime"] = (datetime.now + timedelta(hours=-5)).strftime('%Y-%m-%dT%H:%M:%S')
    new_state = await database["states"].find_one(state)
    updated_state = await database["states"].find_one({"_id": new_state.inserted_id})

    return updated_state

@app.put("/api/settings",status_code=200)
async def acquireSettings(request: Request):
    
    setting = await request.json()
    element = await database["settings"].find().to_list(1)
    if setting["user_light"] == "sunset":
        timenow = sunset()
    else: 
        timenow = setting["user_light"]
    temporary_settings = {}
    temporary_settings["user_light"] = ((datetime.now() + timedelta(hours=-5)).date()).strftime('%Y-%m-%dT')+ timenow
    temporary_settings["light_time_off"] = (datetime.strptime(temporary_settings["user_light"],'%Y-%m-%dT%H:%M:%S')) + parse_time(setting["light_duration"]).strftime('%Y-%m-%dT%H:%M:%S')
    temporary_settings["user_temp"] = setting["user_temp"]

    if len(element) == 0: 
        new_setting = await database["seetings"].insert_one(temporary_settings)
        final_setting = await database["settings"].find_one({"_id": new_setting.inserted_id})
        return final_setting
    else:
        id = element[0]["_id"]
        updated_setting = await database["settings"].update_one({"_id": id}, {"$set": temporary_settings})
        final_setting = await database["setting"].find_one({"_id" : id})
        if updated_setting.modified_count >= 1: 
            return final_setting
    raise HTTPException(status_code=400, detail = "ERROR")

@app.get("/api/state")
async def getState():
    current_state = await database["states"].sort("datetime", -1).to_list(1)
    current_setting = await database["settings"].find_one().to_list(1)
    occupancy = current_state[0]["occupance"]

    currentTime = datetime.strptime(datetime.strftime(datetime.now + timedelta(hours=-5), '%Y-%m-%dT%H:%M:%S'), '%Y-%m-%dT%H:%M:%S') 
    user_set_time = datetime.strptime(current_setting[0]["user_light"], '%Y-%m-%dT%H:%M:%S')
    light_time_up = datetime.strptime(current_setting[0][["light_time_off"]], '%Y-%m-%dT%H:%M:%S')

    fanState = ((float(current_state[0]["Temperature"]))>float(current_settingp[0]["Temperature"])) and occupancy
    lightState = (currentTime > user_set_time) and (currentTime < light_time_up) and (occupancy)

    Dictionary = {"fan":fanState , "light":lightState}
    return Dictionary

@app.get("/api/graph",status_code = 200)
async def plot(request: Request, size: int):
    stateData = await database["states"].find().sort("datetime",-1).to_list()
    stateData.reverse()
    return stateData

def sunset():
    response = requests.get('https://api.sunrise-sunset.org/json?lat=18.1096&lng=-77.2975&date=today')
    jsonForm = response.json()
    sunset_time = jsonForm["results"]["sunset"]
    sunset_time = datetime.strptime(sunset_time, "%H:%M:%S", + timedelta(hours=-5))
    sunset_time = datetime.strftime(sunset_time, "%H:%M:%S")
    return sunset_time

regex = re.compile(r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')

def parse_time(time_str):
    parts = regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)


import urllib
import requests
from quart import request
from websocket import create_connection
import json
from twilio.twiml.voice_response import VoiceResponse
from websocket._abnf import ABNF
from manage import app

global Glob
Glob = {}

try:
    Glob['ws'] = Glob['ws']
except:
    Glob['ws'] = ""

INSTRUCTION = ", Please answer and press any sign."


async def voice_survey():
    response = VoiceResponse()
    await welcome_user(response.say)
    await redirect_to_first_question(response)
    return str(response)


async def welcome_user(send_function):
    call_id = request.args['CallSid']
    connection_to_communicate = Glob["ws_" + call_id]
    connection_to_communicate.send("hello")
    reply = connection_to_communicate.recv()
    j = json.loads(reply)
    if j['ask_flag'] == False:
        welcome_text = j['text']
    else:
        welcome_text = j['text']
    send_function(welcome_text + INSTRUCTION, voice='alice', language='en-AU')


async def redirect_to_first_question(response):
    response.record(action="/answer_backend", method='GET', trim="do-not-trim")
    return response


@app.route("/answer_backend", methods=["POST", "GET"])
async def answer_backend():
    response = VoiceResponse()
    call_id = request.args["CallSid"]
    try:
        connection_to_communicate = Glob["ws_" + call_id]
    except:
        print("error")
    RecordingUrl = request.args["RecordingUrl"]
    parsed_RecordingUrl = urllib.parse.unquote(RecordingUrl)
    recording = requests.get(parsed_RecordingUrl)
    print("sending response from %s" % parsed_RecordingUrl)
    connection_to_communicate.send(recording.content, opcode=ABNF.OPCODE_BINARY)
    reply = connection_to_communicate.recv()
    j = json.loads(reply)
    if j['ask_flag'] == False:
        if j['ask_flag'] == False and j['exit_flag'] == False:
            second_response = await get_second_response_from_stephnie(connection_to_communicate)
            text = j['text'] + second_response
        else:
            text = j['text']
            response.say(text, voice='alice', language='en-AU')
            response.hangup()
            connection_to_communicate.close()
            return str(response)
    else:
        text = j['text']
    print(text)
    response.say(text + INSTRUCTION, voice='alice', language='en-AU')
    response.record(action="/answer_backend", method='GET', trim="do-not-trim")
    return str(response)


async def get_second_response_from_stephnie(connection_to_communicate):
    reply = connection_to_communicate.recv()
    j = json.loads(reply)
    return j['text']


@app.route("/status_change", methods=["POST", "GET"])
async def status_chagne():
    call_id = request.args["CallSid"]
    call_status = request.args["CallStatus"]
    if call_status == "completed":
        connection_to_communicate = Glob["ws_" + call_id]
        connection_to_communicate.close()
        print("call is completed")
    return "call is completed"


@app.route("/voice")
async def say_hi():
    print("creating connection")
    call_id = request.args['CallSid']
    websocket = create_connection("ws://WEBSOCKET:8000")
    Glob['ws_' + call_id] = websocket
    response = await voice_survey()
    return response

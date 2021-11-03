# -*- coding: utf-8 -*-
# Copyright 2018 IBM Corp. All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the “License”)
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Ross Burns: Added functionality for a login, a logout, and the ability
#   to have multiple user sessions.
#

import json
import os
from dotenv import load_dotenv
from flask import Flask, Response
from flask import jsonify, session
from flask import request, redirect, render_template, url_for
from flask_socketio import SocketIO
from flask_cors import CORS
from ibm_watson import AssistantV2
from ibm_watson import SpeechToTextV1
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core import get_authenticator_from_environment
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from functools import wraps

import assistant_setup

app = Flask(__name__)
app.secret_key = 'b0286e60-aeef-45ba-9858-e83f2fe62ed6'
socketio = SocketIO(app)
port = os.environ.get("PORT") or os.environ.get("VCAP_APP_PORT") or 443
CORS(app)

SessionDictionary = {}

class WatsonAssistantSession(object):
    m_session = None
    m_assistant = None
    m_assistantId = None

#    def __init__(self):

    #end_def __init__

    def createSession(self, assistantId, authToken):
        print("Entering WatsonAssistantSession::createSession()")
        errorStr = ''
        if((assistantId is not None and assistantId != '') and (authToken is not None and authToken != '')):
            try:
                authenticator = IAMAuthenticator(authToken)
                self.m_assistantId = assistantId
                self.m_assistant = AssistantV2(version="2019-11-06", authenticator=authenticator)
            except:
                errorStr = "Exception thrown while trying to authenticate session."
                return errorStr
            if(self.m_assistant is None):
                errorStr = "Assistant is not defined - Probable Authentication Failure."
                return errorStr            
            try:
                self.m_session = self.m_assistant.create_session(self.m_assistantId).get_result()
            except:
                self.m_session = None
                errorStr = "Exception thrown while trying to create session to assistant. Please try again."
                return errorStr
            if self.m_session is None:
                errorStr = "Session object is not defined!"
                return errorStr
        else:
            errorStr = "Assistant Id and/or API AuthToken is null. Cannot attempt session creation."
            return errorStr
        self.m_assistantId = assistantId
        return errorStr
    #end_def createSession

    def destroySession(self):
        print("Entering WatsonAssistantSession::destroySession()")
        errorStr = ''

        if(self.m_session is not None and self.m_session["session_id"] != ''):
            try:
                self.m_assistant.delete_session(self.m_assistantId, self.m_session["session_id"])
                #status_code = response.get_status_code()
                #print("Logout response code: %d." % status_code)
            except:
                errorStr = "Exception thrown while logging out."
            self.m_session = None
        return errorStr
    #end_def destroySession

    def getSessionId(self):
        if(self.m_session is not None):
            return self.m_session["session_id"]
        else:
            return ''
    #end_def getSessionId

    def sessionValid(self):
        if(self.m_session is not None and self.m_session["session_id"] != ''):
            return True
        else:
            return False

    def getAssistantId(self):
        if(self.m_assistantId is not None):
            return self.m_assistantId
        else:
            return ''
    #end_def getAssistantId

    def getAssistant(self):
        return self.m_assistant
    #end_def getAssistant
#end_class WatsonAssistantSession

#Decorator login_required
def login_required(function_to_wrap):
    @wraps(function_to_wrap)
    def wrap(*args, **kwargs):
        global SessionDictionary
        sessionKey = None
        watsonAsstSession = None

        if 'assistantInstance' in session:
            sessionKey = session.get('assistantInstance', None)
            if(sessionKey is not None):
                print("Assistant session id:" + sessionKey)
                watsonAsstSession = SessionDictionary.get(sessionKey)
                if(watsonAsstSession is not None and watsonAsstSession.sessionValid() == True):
                    return function_to_wrap(*args, **kwargs)
                else:
                    print("Watson session not valid.")
                    return redirect(url_for('login'))
        else:
            print("Web server does not contain the session identifier for this session.")
            return redirect(url_for('login'))
    return wrap

# Redirect http to https on CloudFoundry
@app.before_request
def before_request():
    fwd = request.headers.get('x-forwarded-proto')

    # Not on Cloud Foundry
    if fwd is None:
        return None
    # On Cloud Foundry and is https
    elif fwd == "https":
        return None
    # On Cloud Foundry and is http, then redirect
    elif fwd == "http":
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    print("logout() route selected.")
    global SessionDictionary
    sessionKey = None
    watsonAsstSession = None

    if 'assistantInstance' in session:
        sessionKey = session.pop('assistantInstance', None)
        if(sessionKey is not None):
            print("Assistant session id:" + sessionKey)
            try:
                watsonAsstSession = SessionDictionary.pop(sessionKey)
            except:
                print("Session not in session dictionary: " + sessionKey)

            if(watsonAsstSession is not None and watsonAsstSession.sessionValid() == True):
                errorStr = watsonAsstSession.destroySession()
                if(errorStr != ''):
                    print("Logout error: " + errorStr)
#end logout()

@app.route('/', methods=['POST', 'GET'])
def root():
    print("login() route selected.")    
    return redirect(url_for('login'))
#end root()

@app.route('/login', methods=['POST', 'GET'])
def login():
    print("login() route selected.")
    error = ''
    global SessionDictionary
    assistantId = None
    authToken = None
    sessionKey = None
    watsonAsstSession = None

    logout()

    if request.method == 'POST':
        assistantId = request.form['assistantid']
        authToken = request.form['apiauthtoken']
        if(assistantId == '' or authToken == ''):
            error = 'Invalid Credentials. Please try again.'
            return render_template('login.html', error=error)
        else:
            watsonAsstSession = WatsonAssistantSession()
            error = watsonAsstSession.createSession(assistantId, authToken)
            if(error != ''):
                return render_template('login.html', error=error)
            else:
                sessionKey = watsonAsstSession.getSessionId()
                SessionDictionary[sessionKey] = watsonAsstSession
                session['assistantInstance'] = sessionKey
                print("New session instance: "+sessionKey)
                return redirect(url_for('home'))
    return render_template('login.html', error=error)
#end login()

@app.route('/home')
@login_required
def home():
    print("home() route selected.")    
    return app.send_static_file('index.html')
#end home()

@app.route('/api/conversation', methods=['POST', 'GET'])
@login_required
def getConvResponse():
    print("conversation() route selected.")
    global SessionDictionary
    sessionKey = None
    watsonAsstSession = None

    convText = request.form.get('convText')
    sessionKey = session.get('assistantInstance', None)
    watsonAsstSession = SessionDictionary.get(sessionKey)

    response = watsonAsstSession.getAssistant().message(watsonAsstSession.getAssistantId(),
                                watsonAsstSession.getSessionId(),
                                input={'text': convText}
                                )
    response = response.get_result()
    reponseText = response["output"]["generic"][0]["text"]
    responseDetails = {'responseText': reponseText }
    return jsonify(results=responseDetails)
#end getConvResponse()

@app.route('/api/text-to-speech', methods=['POST'])
@login_required
def getSpeechFromText():
    print("text-to-speech() route selected.")

    inputText = request.form.get('text')
    ttsService = TextToSpeechV1()
    def generate():
        if inputText:
            audioOut = ttsService.synthesize(
                inputText,
                accept='audio/wav',
                voice='en-US_AllisonVoice').get_result()

            data = audioOut.content
        else:
            print("Empty response")
            data = "I have no response to that."

        yield data

    return Response(response=generate(), mimetype="audio/x-wav")
#end getSpeechFromText()

@app.route('/api/speech-to-text', methods=['POST'])
@login_required
def getTextFromSpeech():
    print("speech-to-text() route selected.")    
    
    sttService = SpeechToTextV1()
    response = sttService.recognize(
            audio=request.get_data(cache=False),
            content_type='audio/wav',
            timestamps=True,
            word_confidence=True,
            smart_formatting=True).get_result()

    # Ask user to repeat if STT can't transcribe the speech
    if len(response['results']) < 1:
        return Response(mimetype='plain/text',
                        response="Sorry, didn't get that. please try again!")

    text_output = response['results'][0]['alternatives'][0]['transcript']
    text_output = text_output.strip()
    return Response(response=text_output, mimetype='plain/text')
#end getTextFromSpeech()

if __name__ == "__main__":
    load_dotenv(verbose=True)
    app.run(host='0.0.0.0', port=int(port), ssl_context='adhoc')
#end main()

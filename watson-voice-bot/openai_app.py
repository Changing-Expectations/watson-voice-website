# -*- coding: utf-8 -*-
# ******************** Open AI Assistant **********************
# *************************************************************
# Provides functions to use OpenAI Assistant, TTS, and STT APIs
# to provide a web-based voice-interactive frontend to OpenAI
# Chatbots / Assistants, provided the Assistant Id and the API
# key.
#
# Author: Ross Burns
#
# v1.0: Initial release

import json
import os
import tempfile
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, session, request, redirect, render_template, url_for
from flask_socketio import SocketIO
from flask_cors import CORS
from openai import OpenAI
from functools import wraps

app = Flask(__name__)
app.secret_key = 'b0286e60-aeef-45ba-9858-e83f2fe62ed6'
socketio = SocketIO(app)
port = os.environ.get("PORT") or os.environ.get("VCAP_APP_PORT") or 5000
CORS(app)

SessionDictionary = {}
voice = "alloy"

class OpenAIAssistantSession(object):
    m_client = None
    m_session = None
    m_session_id = None
    m_assistant = None
    m_assistant_id = None
    m_initial_login = True

#    def __init__(self):

    #end_def __init__

    def create_session(self, assistant_id, auth_token):
        print("Entering OpenAIAssistantSession::create_session()")

        openai_api_key = auth_token 
        error_str = ''
        if((assistant_id is not None and assistant_id != '') and (auth_token is not None and auth_token != '')):
            try:
                self.m_assistant_id = assistant_id
                self.m_client = OpenAI(api_key = openai_api_key)
                self.m_assistant = self.m_client.beta.assistants.retrieve(assistant_id = self.m_assistant_id)
                if(self.m_assistant is not None):
                    self.m_session = self.m_client.beta.threads.create()
                    if(self.m_session is None):
                        error_str = "Error while trying to create session (thread) with assistant."
                        return error_str
                    self.m_session_id = self.m_session.id
            except:
                error_str = "Exception thrown while trying to authenticate session."
                return error_str
            if(self.m_assistant is None):
                error_str = "Assistant is not defined - Probable Authentication Failure."
                return error_str
        else:
            error_str = "Assistant Id and/or API AuthToken is null. Cannot attempt session creation."
            return error_str
        return error_str

    def get_client_handle(self):
        return self.m_client

    def destroy_session(self):
        """
        Deletes the current session with the assistant.

        Returns:
            str: An error message if an exception occurs during the deletion process, otherwise an empty string.
        """
        error_str = ""
        try:
            if self.m_session and self.m_assistant_id and self.m_assistant and self.m_session_id:
                self.m_client.beta.threads.delete(self.m_session_id)
                self.m_session = None
                self.m_session_id = None
            else:
                error_str = "Incomplete information for deleting session."
        except Exception as e:
            error_str = "Exception thrown while deleting session: {}".format(str(e))
        return error_str
        #end_def destroy_session


    def get_session_id(self):
        """
        Returns the session ID of the current assistant session.

        Returns:
            str: The session ID, or an empty string if the session is not defined.
        """
        print("get_session_id()")
        if self.m_session is None:
            return ""
        if self.m_session_id is None:
            return ""
        return self.m_session_id
    #end_def get_session_id

    def is_session_valid(self):
        """Returns True if the current session is valid, otherwise False."""
        return self.m_session is not None


    def get_assistant_id(self):
        """
        Returns the ID of the assistant.

        Returns:
            str: The assistant ID, or an empty string if it is not defined.
        """
        return self.m_assistant_id if self.m_assistant_id else ''
    #end_def get_assistant_id


    def get_assistant(self):
        """
        Returns the OpenAI assistant object.

        Returns:
            OpenAI.Assistant: The OpenAI assistant object.
        """
        return self.m_assistant
    #end_def get_assistant
#end_class OpenAIAssistantSession


#Decorator login_required
def login_required(function_to_wrap):
    @wraps(function_to_wrap)
    def wrap(*args, **kwargs):
        session_key = session.get('assistantInstance')
        if session_key is not None:
            assistant_session = SessionDictionary.get(session_key)
            if assistant_session and assistant_session.is_session_valid():
                return function_to_wrap(*args, **kwargs)
            else:
                return redirect(url_for('login'))
        else:
            return redirect(url_for('login'))
    return wrap

# Redirect http to https on CloudFoundry
@app.before_request
def redirect_http_to_https():
    forwarded_proto = request.headers.get('X-Forwarded-Proto')

    if forwarded_proto == 'http':
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)
#end redirect_http_to_https()

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    print("logout() route selected.")

    assistant_session = None
    session_key = session.pop('assistantInstance', None)

    if session_key is not None:
        try:
            assistant_session = SessionDictionary.pop(session_key)
        except:
            pass

        if assistant_session is not None and assistant_session.is_session_valid():
            error_str = assistant_session.destroy_session()
            if error_str:
                print("Logout error:", error_str)

    return redirect(url_for('login'))
#end logout()

@app.route('/', methods=['POST', 'GET'])
def root():
    print("root() route selected.")

    """Redirects all requests to the login page."""
    return redirect(url_for('login'))
#end root()

@app.route('/login', methods=['POST', 'GET'])
def login():
    print("login() route selected.")

    error_message = ''
    global SessionDictionary
    global voice
    assistant_id = None
    auth_token = None
    session_key = None
    global openai_assistant_session
    openai_assistant_session = None

    logout()

    if request.method == 'POST':
        assistant_id = request.form['assistantid']
        auth_token = request.form['apiauthtoken']
        voice = request.form['voice']
        if assistant_id == '' or auth_token == '':
            error_message = 'Invalid Credentials. Please try again.'
            return render_template('login.html', error=error_message)
        elif(voice == ''):
            error = 'Invalid voice selection. Please try again.'
            return render_template('login.html', error=error_message)
        else:
            openai_assistant_session = OpenAIAssistantSession()
            error_message = openai_assistant_session.create_session(assistant_id, auth_token)
            if error_message:
                return render_template('login.html', error=error_message)
            else:
                session_key = openai_assistant_session.get_session_id()
                SessionDictionary[session_key] = openai_assistant_session
                session['assistantInstance'] = session_key
                return redirect(url_for('home'))
    return render_template('login.html', error=error_message)
#end login()

@app.route('/home')
@login_required
def home():
    print("home() route selected.")    

    return app.send_static_file('index.html')
#end home()

@app.route('/api/conversation', methods=['POST', 'GET'])
@login_required
def get_conversation_response():
    print("conversation() route selected.")

    session_key = session.get('assistant_instance')
    session_object = SessionDictionary.get(session_key)

    if(openai_assistant_session.m_initial_login == True):
        conversation_text = "Hello"
        openai_assistant_session.m_initial_login = False
    else:
        conversation_text = request.form.get('convText')

    thread_message = openai_assistant_session.get_client_handle().beta.threads.messages.create(
        thread_id=openai_assistant_session.get_session_id(),
        role="user",
        content=conversation_text,
    )
    run = openai_assistant_session.get_client_handle().beta.threads.runs.create(
        thread_id = openai_assistant_session.get_session_id(),
        assistant_id = openai_assistant_session.get_assistant_id(),
    )

    while run.status != "completed":
        run = openai_assistant_session.get_client_handle().beta.threads.runs.retrieve(
            thread_id=openai_assistant_session.get_session_id(),
            run_id=run.id
        )

    messages = openai_assistant_session.get_client_handle().beta.threads.messages.list(
        thread_id = openai_assistant_session.get_session_id()
    )
    response_text = messages.data[0].content[0].text.value
    response_details = {'responseText': response_text}
    return jsonify(results=response_details)
#end getConvResponse()

@app.route('/api/text-to-speech', methods=['POST'])
@login_required
def getSpeechFromText():
    print("text-to-speech() route selected.")    

    global voice
    text_input = request.form.get('text')

    def generate_response():
        if text_input:
            audioOut =  openai_assistant_session.get_client_handle().audio.speech.create(
                model="tts-1",
                voice=voice,
                response_format='wav',
                input=text_input)

            data = audioOut.content

            yield data

    return Response(response=generate_response(), mimetype="audio/x-wav")
#end getSpeechFromText()

@app.route('/api/speech-to-text', methods=['POST'])
@login_required
def getTextFromSpeech():
    print("speech-to-text() route selected.")    

    temp_file, filename = tempfile.mkstemp(suffix=".wav")

    with open(filename, "wb") as f:
        f.write(request.get_data(cache=False))
        f.close()

    with open(filename, "rb") as f:
        transcript = openai_assistant_session.get_client_handle().audio.transcriptions.create(
            file=f,
            model="whisper-1",
            response_format="text",
            language="en")
        f.close()

    os.unlink(filename)

    return Response(response=transcript, mimetype="plain/text")
#end getTextFromSpeech()

if __name__ == "__main__":
    load_dotenv()
    app.run(host='0.0.0.0', port=int(port), debug=True, ssl_context='adhoc')
#end main()

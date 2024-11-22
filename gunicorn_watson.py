# Gunicorn configuration file
# https://docs.gunicorn.org/en/stable/configure.html#configuration-file
# https://docs.gunicorn.org/en/stable/settings.htmla

workers = 1
threads = 5
backlog = 2048
certfile = '/etc/swdcs/ssl/swdcs.crt'
keyfile = '/etc/swdcs/ssl/swdcs.key'
bind = "0.0.0.0:443"
pidfile = '/home/swdcs/pidfile'
errorlog = '/home/swdcs/errorlog'
daemon = False
debug = False
loglevel = 'info'
accesslog = '/home/swdcs/accesslog'
timeout = 120

raw_env= [
"SPEECH_TO_TEXT_AUTH_TYPEi=iam",
"SPEECH_TO_TEXT_APIKEY=jlO-aBgLQdwDq-q80IcKXfp0fXClxkFw90tFw2WbA7pY",
"SPEECH_TO_TEXT_URL=https://api.us-south.speech-to-text.watson.cloud.ibm.com",
"TEXT_TO_SPEECH_AUTH_TYPE=iam",
"TEXT_TO_SPEECH_APIKEY=JHZmIUxYIW2CN3KShqYrTSNREY9YeFsYk39OWrccZvvz",
"TEXT_TO_SPEECH_URL=https://api.us-south.text-to-speech.watson.cloud.ibm.com",
"ASSISTANT_AUTH_TYPE=iam",
"ASSISTANT_URL=https://api.us-south.assistant.watson.cloud.ibm.com",
"ASSISTANT_SOUTH_URL=https://api.us-south.assistant.watson.cloud.ibm.com",
"ASSISTANT_EAST_URL=https://api.us-east.assistant.watson.cloud.ibm.com",
"ASSISTANT_GB_URL=https://api.eu-gb.assistant.watson.cloud.ibm.com",
"ASSISTANT_DE_URL=https://api.eu-de.assistant.watson.cloud.ibm.com",
"ASSISTANT_TOK_URL=https://api.jp-tok.assistant.watson.cloud.ibm.com",
"ASSISTANT_BRA_URL=https://api.br-sao.assistant.watson.cloud.ibm.com",
"ASSISTANT_CAD_URL=https://api.ca-tor.assistant.watson.cloud.ibm.com",
"ASSISTANT_SYD_URL=https://api.au-syd.assistant.watson.cloud.ibm.com"
]

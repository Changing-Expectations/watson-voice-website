# watson-voice-website
Website for watson chatbot interaction via voice

SETUP >>>>>

<<< Create account for webservice >>>
create "swdcs" account (use "adduser" command)
(As root) add swdcs to sudo group: "usermod -aG sudo swdcs"

<<< Bring down website source code >>>
<<< future git clone command here to pull down website source >>>
(make sure user / group for all files is swdcs (use chgrp -R and chusr -R in home dir if needed))

<<< Start building infrastructure >>>
sudo apt update
sudo apt install nodejs  (to get npm)
sudo apt install python3 (if not already installed)
sudo apt install python3-pip
sudo pip3 install -r ./dependencies.txt
cd "watson-voice-bot" and then "npm install"

<<< Need to build UWSGI web server with SSL support for HTTPs >>>
sudo apt install libssl-dev
pip install uwsgi -I --no-cache-dir    (note: -I may not be needed if uwsgi was never installed before)


(sudo or root user) Move/copy "watson.service" file to "/etc/systemd/system"  (Might need to adjust user/grp on file)
(may need to do a "systemctl daemon-reload" command to pull in file above)
sudo systemctl start watson.service      (starts webservice)
sudo systemctl enable watson.service     (start on reboot)

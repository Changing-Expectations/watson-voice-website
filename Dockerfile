# This Dockerfile is to build the runtime for the SWDCS website that runs a speech interface to watson via the browser
# Pull the minimal Ubuntu image
FROM ubuntu:noble

# For git download of code, copy over private key, and set permissions
RUN mkdir /root/.ssh/
ADD id_rsa /root/.ssh/id_rsa
RUN chown -R root:root /root/.ssh
RUN chmod 600 /root/.ssh/id_rsa

# Create known_hosts
RUN touch /root/.ssh/known_hosts

# Remove host checking
RUN echo "Host bitbucket.org\n\tStrictHostKeyChecking no\n" >> /root/.ssh/config

RUN apt-get -y update
RUN apt-get -y install vim && apt-get -y install git && apt-get -y install npm && apt-get -y install python3 && apt-get -y install python3-pip && apt-get -y install python3-dev && apt-get -y install build-essential && apt-get -y install libssl-dev && apt-get -y install libffi-dev && apt-get -y install python3-setuptools && apt-get -y install sudo && apt-get -y install supervisor && apt-get -y install libcap2-bin

# Supervisord will be used to run services in the container
COPY supervisor.conf /etc/supervisor.conf

# Install SWDCS cert for SSL
RUN mkdir -p /etc/swdcs/ssl
COPY swdcs.crt /etc/swdcs/ssl/
COPY swdcs.key /etc/swdcs/ssl/

# Add swdcs user
RUN useradd -ms /bin/bash swdcs  && echo 'swdcs:swdcs' | chpasswd

# Clone the conf files into the docker container
USER swdcs
RUN git clone https://github.com/Changing-Expectations/watson-voice-website.git /home/swdcs/website

# OpenAI site: Overwrite Watson with OpenAI files
#COPY  /home/swdcs/website/watson-voice-website/openai_app.py /home/swdcs/website/watson-voice-website/app.py
#COPY  /home/swdcs/website/watson-voice-website/templates/login_openai.html /home/swdcs/website/watson-voice-website/templates/login.html
#COPY  /home/swdcs/website/watson-voice-website/static/logout_openai.html /home/swdcs/website/watson-voice-website/static/logout.html

# Copy the gunicorn env vars
COPY gunicorn_watson.py /home/swdcs/website/watson-voice-bot

# The website's main directory
WORKDIR /home/swdcs/website

# Install the website python dependencies (do as root since launching gunicorn as root)
USER root
COPY dependencies.txt .
RUN pip3 install gunicorn --break-system-packages
RUN pip3 install -r ./dependencies.txt --break-system-packages

# The website's runtime privs are dropped to swdcs account level
USER swdcs
WORKDIR /home/swdcs/website/watson-voice-bot
RUN npm install

# Make the log directory
RUN mkdir -p /home/swdcs/website/log

USER root
# Remove private repo key
RUN rm /root/.ssh/id_rsa

# Expose the port for access
EXPOSE 443/tcp
#EXPOSE 8080/tcp

# Provide priveledge to port
RUN setcap 'CAP_NET_BIND_SERVICE=+eip' /usr/bin/python3.12

CMD ["/usr/bin/supervisord","-n","-c","/etc/supervisor.conf"]


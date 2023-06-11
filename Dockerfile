# This Dockerfile is to build the runtime for the SWDCS website that runs a speech interface to watson via the browser
# Pull the minimal Ubuntu image
FROM ubuntu:latest

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
RUN apt-get -y install vim && apt-get -y install git && apt-get -y install npm && apt-get -y install python3 && apt-get -y install python3-pip && apt-get -y install python3-dev && apt-get -y install build-essential && apt-get -y install libssl-dev && apt-get -y install libffi-dev && apt-get -y install python3-setuptools && apt-get -y install sudo && apt-get -y install gunicorn && apt-get -y install nginx -y && apt-get -y install supervisor

# Supervisord will be used to run services in the container
COPY supervisor.conf /etc/supervisor.conf

# Install SWDCS cert for SSL
RUN mkdir -p /etc/swdcs/ssl
COPY swdcs.crt /etc/swdcs/ssl/
COPY swdcs.key /etc/swdcs/ssl/

# For later python package installs
RUN pip3 install wheel

# Add swdcs user
RUN useradd -ms /bin/bash swdcs  && echo 'swdcs:swdcs' | chpasswd

# Clone the conf files into the docker container
USER swdcs
RUN git clone https://github.com/Changing-Expectations/watson-voice-website.git /home/swdcs/website

# Copy the GUnicorn env vars
COPY gunicorn_watson.py /home/swdcs/website/watson-voice-bot

# The website's main directory
WORKDIR /home/swdcs/website

# Install the website python dependencies (do as root since launching gunicorn as root)
USER root
RUN pip3 install -r ./dependencies.txt

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
RUN setcap 'CAP_NET_BIND_SERVICE=+eip' /usr/bin/python3.10

CMD ["/usr/bin/supervisord","-n","-c","/etc/supervisor.conf"]

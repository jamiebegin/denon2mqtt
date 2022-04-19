#!/bin/env python3
import logging
import sys
import os
import time
import socket
from threading import Thread
from queue import Queue
import paho.mqtt.client as mqtt

log = logging.getLogger('denon2mqtt')

class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, level):
       self.logger = logger
       self.level = level
       self.linebuf = ''

    def write(self, buf):
       for line in buf.rstrip().splitlines():
          self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass

class AVRSend(Thread):
    def __init__(self, sock, q_to_receiver):
        Thread.__init__(self)
        self.sock = sock
        self.q_to_receiver = q_to_receiver

    def run(self):
        while 1:
            time.sleep(0.1)
            if not self.q_to_receiver.empty():
                msg = self.q_to_receiver.get()
                log.info("  To receiver <-- {}".format(msg))
                self.sock.send(msg.encode())

class AVRSocket(Thread):
    def __init__(self, receiver_host, q_to_receiver, q_from_receiver):
        Thread.__init__(self)
        self.receiver_host = receiver_host
        self.q_to_receiver = q_to_receiver
        self.q_from_receiver = q_from_receiver

    def listen(self):
        msg = ''
        while 1:
            time.sleep(0.1)
            while (data := self.sock.recv(1)) != b'\r':
                msg += data.decode('ascii')
            else:
                log.info("From receiver --> {}".format(msg))
                self.q_from_receiver.put(msg)
                msg = ''

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log.info("Connecting to receiver at '{}'...".format(self.receiver_host))
        self.sock.connect((self.receiver_host, 23))
        log.info("Connected.")
        self.sender = AVRSend(self.sock, self.q_to_receiver)
        self.sender.daemon = True
        self.sender.name = "TXThread"
        self.sender.start()        
        self.listen()

class DenonReceiver(object):
    def __init__(self, receiver_host, broker_host, broker_port, mqtt_topic):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.mqtt_topic = mqtt_topic
        self.q_to_receiver = Queue()
        self.q_from_receiver = Queue()

        self.avr = AVRSocket(receiver_host, self.q_to_receiver, 
            self.q_from_receiver)
        self.avr.daemon = True
        self.avr.name = "RXThread"

    def listen(self):
        def on_connect(client, userdata, flags, rc):
            log.info("Connected to MQTT broker.")
            client.subscribe("{}/#".format(self.mqtt_topic))

        def on_message(client, userdata, message):
            cmd = message.payload.decode("ascii")
            log.debug("message received {}".format(cmd))
            log.debug("message topic {}".format(message.topic))
            log.debug("message qos {}".format(message.qos))
            log.debug("message retain flag {}".format(message.retain))

            if message.topic.startswith("{}/command".format(self.mqtt_topic)):
                self.q_to_receiver.put(cmd)

        self.avr.start()
        self.client = mqtt.Client(clean_session=True)
        self.client.on_connect = on_connect
        self.client.on_message = on_message
        self.client.connect(self.broker_host, port=self.broker_port, keepalive=60)
        self.client.loop_start()

        while 1:
            time.sleep(0.1)
            if not self.q_from_receiver.empty():
                msg = self.q_from_receiver.get()
                payload = msg
                self.client.publish("{}/status".format(self.mqtt_topic), 
                    payload=payload, qos=0, retain=False)

if __name__ == "__main__":
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - (%(threadName)s) %(message)s')

    ch = logging.StreamHandler()
    log_level = logging.INFO
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    sys.stderr = StreamToLogger(log,logging.ERROR)

    RECEIVER_HOST = os.environ.get('RECEIVER_HOST')
    if not RECEIVER_HOST:
        log.critical("RECEIVER_HOST env variable not set. Exiting.")
        sys.exit(1)

    BROKER_HOST = os.environ.get('BROKER_HOST')
    if not BROKER_HOST:
        log.critical("BROKER_HOST env variable not set. Exiting.")
        sys.exit(1)

    BROKER_PORT = os.environ.get('BROKER_PORT')
    if not BROKER_PORT: BROKER_PORT = 1883
    BROKER_PORT = int(BROKER_PORT)

    MQTT_TOPIC = os.environ.get('MQTT_TOPIC')
    if not MQTT_TOPIC: MQTT_TOPIC = "denon"
    log.info("Starting with config:")
    log.info("RECEIVER_HOST={}".format(RECEIVER_HOST))
    log.info("BROKER_HOST={}".format(BROKER_HOST))
    log.info("BROKER_PORT={}".format(BROKER_PORT))
    log.info("MQTT_TOPIC={}".format(MQTT_TOPIC))

    d = DenonReceiver(RECEIVER_HOST, BROKER_HOST, BROKER_PORT, MQTT_TOPIC)
    d.listen()

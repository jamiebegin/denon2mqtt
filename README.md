# denon2mqtt
MQTT bridge for Denon AVR receivers.

Publish commands to `denon/command` and subscribe to `denon/status`. Transparently bridges I/O between a MQTT broker and the AVR's telnet interface.

Dead simple and ultra-lightweight method to intergrate a Denon AVR receiver into a home automation system. Should work with any Denon AVR receiver since it doesn't try to encaspulate the low-level protocol and make it user-friendly. It's intended to be used as a "set it and forget it" Docker container that just passes bytes to a MQTT subscriber where the real work happens. I wrote it because neither of the AVR nodes available in NodeRed to worked correctly with my Denon AVR-S760H and I wanted something more flexible than the Home Assistant intergration.

[Denon AVR control protocol reference](http://assets.eu.denon.com/DocumentMaster/DE/AVR1713_AVR1613_PROTOCOL_V8.6.0.pdf) (PDF)

Build: `sudo docker build -t denon2mqtt .`

`docker-compose.yaml`:
```
version: '3.4'
services:
  test:
    image: denon2mqtt
    container_name: denon2mqtt
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-file: "10"
        max-size: "2m"
    environment:
      - TZ="America/Detroit"
      - RECEIVER_HOST=192.168.1.100
      - BROKER_HOST=192.168.1.2
      - BROKER_PORT=1883
      - MQTT_TOPIC=denon
    volumes:
      - /etc/localtime:/etc/localtime:ro
```

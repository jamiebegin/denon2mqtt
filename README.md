# denon2mqtt
MQTT bridge for Denon AVR receivers.

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

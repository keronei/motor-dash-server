import os
import asyncio
import RPi.GPIO as GPIO
import socketio
import pynmea2
from aiohttp import web
import time
import string
import serial
import logging

ALLOWED_ORIGINS = ["http://localhost:8090"]
PULSE_PIN = 17
pulse_count = 0
rounded=0
start_time = time.time()

def pulse_callback(channel):
    global pulse_count
    pulse_count += 1

GPIO.setmode(GPIO.BCM)
GPIO.setup(PULSE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
sio = socketio.AsyncServer(cors_allowed_origins=ALLOWED_ORIGINS)

GPIO.add_event_detect(PULSE_PIN, GPIO.RISING, callback=pulse_callback)

app = web.Application()
sio.attach(app)

parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
angular_path = os.path.join(parent_dir, 'd3-car-dashboard/dist/d3-car-dashboard/browser')
app.router.add_static('/', path=angular_path, name='static')

# Configure logging to write to a file
logging.basicConfig(
    filename='/home/project/server_script_errors.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'  # Customize log format
)


async def handle_root(request):
    return web.FileResponse(os.path.join(angular_path, 'index.html'))

@sio.event
async def connect(sid, environ):
    origin=environ.get('HTTP_ORIGIN', '')
    if origin not in ALLOWED_ORIGINS:
        print(f'Connection from {origin} imetupwa')
        await sio.disconnect(sid)

    else:
        print(f'Allowing connection from {origin}')

@sio.event
async def disconnect(sid):
    logging.debug(f"Disconnected from {sid} at speed {rounded}km/h")
    print('Disconnected', sid)

@sio.on('message')
async def send_gpio_data(message, sid):
    print('Going to send data')
    global start_time
    global pulse_count
    global rounded

    try:
        port="/dev/ttyS0"
        ser=serial.Serial(port=port, baudrate=9600, timeout=0.5)

        while True:
            incomingData=ser.readline()

            if incomingData[0:6].decode('utf-8') == "$GPRMC":
                newdata=pynmea2.parse(incomingData.decode('utf-8'))
                knots=newdata.spd_over_grnd
                kmh=knots * 1.852
                rounded=round(kmh)
            else:
                print(f"Other: {incomingData[0:6]}")

            elapsed_time = time.time() - start_time

            if elapsed_time >= 0.20:
                rpm = pulse_count * 60
                start_time = time.time()
                pulse_count = 0

            data = {'speed': rounded, 'rpm': rpm}
            
            await sio.emit(event='ecuData', data=data)
            print(f"Data sent: {data}, sleeping...")
            
            await asyncio.sleep(0.1)
    except Exception as error:
        print(f'Error in sending data: {error}')
        logging.error(f"Error in sending data: {error}")
        rounded=-5

    finally:
        GPIO.cleanup()
        print("Done, should clean up")

if __name__ == '__main__':
    web.run_app(app=app,host='0.0.0.0', port=8090)

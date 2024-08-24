import asyncio
import RPi.GPIO as GPIO
import socketio
from aiohttp import web
import time

ALLOWED_ORIGINS = ["http://localhost:45100"]
PULSE_PIN = 17
pulse_count = 0
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
    print('Disconnected', sid)

@sio.on('message')
async def send_gpio_data(message, sid):
    print('Going to send data')
    global start_time
    global pulse_count
    try:
        while True:
            elapsed_time = time.time() - start_time

            if elapsed_time >= 1.0:
                rpm = pulse_count * 60
                print(f"RPM: {rpm}")
                start_time = time.time()
                pulse_count = 0

            data = {'speed': 100, 'rpm': rpm}
            
            await sio.emit(event='ecuData', data=data)
            print("Data sent, sleeping...")
            
            await asyncio.sleep(0.1)
    except Exception as error:
        print(f'Error in sending data: {error}')

    finally:
        GPIO.cleanup()

if __name__ == '__main__':
    web.run_app(app=app,host='0.0.0.0', port=8090)

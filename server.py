import os
import asyncio
import socketio
import json
from aiohttp import web
import serial
import logging

ALLOWED_ORIGINS = ["http://localhost:8090"]

sio = socketio.AsyncServer(cors_allowed_origins=ALLOWED_ORIGINS)

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
    logging.debug(f"Disconnected from {sid} at output {data}")
    print('Disconnected', sid)

@sio.on('message')
async def send_gpio_data(message, sid):
    print('Going to send data')
    global start_time
    global pulse_count
    global data

    data = {'speed':0}

    try:
        port="/dev/ttyUSB0"
        ser=serial.Serial(port=port, baudrate=9600, timeout=0.5)

        while True:
            incomingData=ser.readline()
            try:
                in_data = incomingData.decode('utf-8').strip()
                if 'speed' in in_data:
                    data = json.loads(in_data)
            except Exception as ep:
                print(f"Decode error: {ep}")
                logging.error(f"Decode error: {ep}")
            
            await sio.emit(event='ecuData', data=data)
            print(f"Data sent: {data}, sleeping...")
            ser.reset_input_buffer()
            
            await asyncio.sleep(0.1)
    except Exception as error:
        print(f'Error in sending data: {error}')
        logging.error(f"Error in sending data: {error}")

    finally:
        print("Done, should clean up")

if __name__ == '__main__':
    web.run_app(app=app,host='0.0.0.0', port=8090)

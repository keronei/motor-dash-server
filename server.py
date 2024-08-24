import asyncio
import json
import socketio
from aiohttp import web

ALLOWED_ORIGINS = ["http://localhost:45100"]

sio = socketio.AsyncServer(cors_allowed_origins=ALLOWED_ORIGINS)
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
    try:
        while True:
            data = {'speed': 100, 'rpm': 1700}
            await sio.emit(event='ecuData', data=data)
            print("Data sent, sleeping...")
            
            await asyncio.sleep(1)
    except Exception as error:
        print(f'Error in sending data: {error}')

if __name__ == '__main__':
    web.run_app(app=app,host='0.0.0.0', port=8090)

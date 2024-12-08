from aiohttp import web
import socketio
import json

sio = socketio.AsyncServer(cors_allowed_origins='*')
app = web.Application()
sio.attach(app)
rooms = {}

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def join(sid, data):
    print(f"Client {sid} joining room {data['room']}")
    room = data['room']
    try:
        if room not in rooms:
            rooms[room] = set()
        if len(rooms[room]) >= 2:
            await sio.emit('room_full', {'room': room}, to=sid)
            return
        await sio.enter_room(sid, room)  
        rooms[room].add(sid)
        await sio.emit('ready', {'room': room, 'clients': len(rooms[room])}, room=room)
    except Exception as e:
        print(f"Error in join handler: {e}")
        await sio.emit('error', {'message': str(e)}, to=sid)

@sio.event
async def offer(sid, data):
    print(f"Offer:{sid} {rooms[data['room']]}")
    await sio.emit('offer', data, room=data['room'], skip_sid=sid)

@sio.event
async def answer(sid, data):
    print(f"Answer")
    await sio.emit('answer', data, room=data['room'], skip_sid=sid)

@sio.event
async def ice_candidate(sid, data):
    print(f"ICE candidate")
    await sio.emit('ice_candidate', data, room=data['room'], skip_sid=sid)

@sio.event
async def message(sid, data):
    print(f"Message")
    await sio.emit('message', data, room=data['room'], skip_sid=sid)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    rooms_to_check = list(rooms.keys())
    for room in rooms_to_check:
        if sid in rooms[room]:
            rooms[room].remove(sid)
            if len(rooms[room]) == 0:
                del rooms[room]
            else:
                await sio.emit('peer_disconnected', to=room)
            break  

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)


# Websocket server example that synchronizes state acress clients

import asyncio
import json
import logging
import websockets
import sys
from hashlib import sha512
from pprint import pprint

if len(sys.argv) < 2:
	print("server.py <port>")
	sys.exit(0)

logging.basicConfig()

state = {'value': 0}

users = set()

def state_event():
	return json.dumps({'type': 'state', **state})


def users_event():
	return json.dumps({'type': 'users', 'count': len(users)})


async def notify_state():
	# Do not accept an empty list
	if users:
		message = state_event()
		await asyncio.wait([user.send(message) for user in users])


async def notify_users():
	# Do not accept an empty list
	if users:
		message = users_event()
		await asyncio.wait([user.send(message) for user in users])


async def register(websocket):
	# print("#################################################")
	print(sha512(str(websocket.__dict__).encode('utf-8')).hexdigest(), "\n")
	pprint(str(websocket.__dict__).encode('utf-8'))
	users.add(websocket)
	await notify_users()


async def unregister(websocket):
	users.remove(websocket)
	await notify_users()


async def counter(websocket, path):
	# register(websocket) sends user_event() to websocket
	print('Listening')
	await register(websocket)
	try:
		print('Got Connection')
		await websocket.send(state_event())
		print("Got Event")
		async for message in websocket:
			data =  json.loads(message)
			if data['action'] == 'minus':
				state['value'] -= 1
				await notify_state()
			elif data['action'] == 'plus':
				state['value'] += 1
				await notify_state()
			else:
				logging.error(f"Unsupported event: {data}")
	finally:
		print("Unregistering")
		await unregister(websocket)
		print("Unregistered")



if __name__ == '__main__':
	asyncio.get_event_loop().run_until_complete(websockets.serve(counter, '0.0.0.0', sys.argv[1]))
	asyncio.get_event_loop().run_forever()

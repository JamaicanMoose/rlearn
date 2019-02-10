import asyncio
import websockets
import base64 as b64
import dill
from keras.models import Sequential
import numpy as np
import rlearn.serialization as rls
import hashlib


class Session:
    def __init__(self, serverUrl):
        self.server = 'ws://' + serverUrl
        self.session = None

    # @classmethod
    # async def connect(cls, serverUrl):
    #     s = cls(serverUrl)
    #     s.session = await websockets.connect(s.server)
    #     return s

    def addData(self, x, y, name):
        async def f():
            await self.send_data(x, y, name)
        asyncio.get_event_loop().run_until_complete(f())

    async def train(self):
        session = await websockets.connect(self.server)


    async def ping(self):
        print('hi')
        session = await websockets.connect(self.server)
        await session.send(dill.dumps({'type': 'ping'}))
        echo = await session.recv()
        print(echo)
        await session.close()

    async def ping_context(self):
        async with websockets.connect(self.server) as session:
            await session.send(dill.dumps({'type': 'ping'}))
            echo = await session.recv()
            print(echo)

    async def list_data(self):
        session = await websockets.connect(self.server)
        await session.send(dill.dumps({'type': 'listdata'}))
        dlist = await session.recv()
        print(dill.loads(dlist))
        await session.close()

    async def send_job(self, type, model, data, **kwargs):
        session = await websockets.connect(self.server)
        await session.send(dill.dumps({
            'type': 'job',
            'jobinfo': {

            }
        }))


    async def send_data(self, x, y, name):
        session = await websockets.connect(self.server)
        dstr = dill.dumps({'x': rls.serialize(x), 'y': rls.serialize(y)})
        await session.send(dill.dumps({
            'type': 'data',
            'data': {
                'name': name,
                'hash': hashlib.md5(dstr).hexdigest(),
                'datastr': dstr
            }
        }))
        resp = await session.recv()
        print(dill.loads(resp))
        await session.close()


async def start():
    s = Session('localhost:8765')
    await s.send_data([1, 2, 3], [4, 5, 6], 'test')
    await s.send_data([2, 2, 2], [3, 4, 5], 'test2')
    await s.list_data()
    print('done')

#asyncio.get_event_loop().run_until_complete(start())

s = Session('localhost:8765')
s.addData(np.array([1, 2, 3]), np.array([4, 5, 6]), 'test')
s.addData(np.array([2, 2, 2]), np.array([3, 4, 5]), 'test2')

async def f2():
    await s.list_data()

asyncio.get_event_loop().run_until_complete(f2())


__all__ = ['Server', 'Plugin', 'build_header']
__version__ = '2.0.0'
__author__ = 'mingfengpigeon <mingfengpigeon@gmail.com>'

import asyncio
import copy
import json
import uuid

import websockets


class Server:
    def __init__(self, server: str = '0.0.0.0', port: int = 8000, debug_mode: bool = False) -> None:
        self._server = server
        self._port = port
        self._debug_mode = debug_mode
        self._plugins = []
        self._sent_commands = {}
        self._subscribed_events = {}

    def handler(self) -> list:
        return copy.deepcopy(self._plugins)

    def add_plugin(self, plugin) -> None:
        self._plugins.append(plugin)

    def remove_plugin(self, plugin) -> None:
        self._plugins.remove(plugin)

    def run_forever(self) -> None:
        asyncio.run(self._run_forever())

    async def _run_forever(self) -> None:
        async with websockets.serve(self._on_connect, self._server, self._port):
            await asyncio.Future()

    async def _on_connect(self, websocket, path) -> None:
        plugins = []
        for plugin in self._plugins:
            plugins.append(plugin(websocket, path, self._sent_commands, self._subscribed_events, self._debug_mode))
        for plugin in plugins:
            asyncio.create_task(plugin.on_connect())
        while True:
            try:
                response = await websocket.recv()
            except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosedError):
                tasks = []
                for plugin in plugins:
                    tasks.append(plugin.on_disconnect())
                for task in tasks:
                    await task
                break
            else:
                response = json.loads(response)
                message_purpose = response['header']['messagePurpose']
                if message_purpose == 'commandResponse':
                    request_id = response['header']['requestId']
                    if request_id in self._sent_commands:
                        asyncio.create_task(self._sent_commands[request_id](response))
                        del self._sent_commands[request_id]
                else:
                    event_name = response['header']['eventName']
                    asyncio.create_task(self._subscribed_events[event_name](response))


class Plugin:
    def __init__(self, websocket, path, sent_commands: dict, subscribed_events: dict, debug_mode: bool = False) -> None:
        self._websocket = websocket
        self._path = path
        self._sent_commands = sent_commands
        self._subscribed_events = subscribed_events
        self._debug_mode = debug_mode

    async def on_connect(self) -> None:
        pass

    async def on_disconnect(self) -> None:
        pass

    async def on_receive(self, response) -> None:
        pass

    async def send(self, request: str) -> None:
        await self._websocket.send(request)

    async def send_command(self, command: str, callback=None) -> None:
        request = {
            'body': {'commandLine': command},
            'header': build_header('commandRequest')
        }
        if callback:
            self._sent_commands[request['header']['requestId']] = callback
        await self.send(json.dumps(request))

    async def subscribe(self, event_name: str, callback) -> None:
        request = {
            'body': {'eventName': event_name},
            'header': build_header('subscribe')
        }
        self._subscribed_events[event_name] = callback
        await self.send(json.dumps(request))

    async def unsubscribe(self, event_name: str) -> None:
        request = {
            'body': {'eventName': event_name},
            'header': build_header('unsubscribe')
        }
        del self._subscribed_events[event_name]
        await self.send(json.dumps(request))


def build_header(message_purpose: str, request_id: str | None = None):
    if not request_id:
        request_id = str(uuid.uuid4())
    return {
        'requestId': request_id,
        'messagePurpose': message_purpose,
        'version': '1',
        'messageType': 'commandRequest',
    }

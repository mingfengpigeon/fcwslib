__all__ = ['Server', 'Plugin', 'build_header']
__version__ = '2.1.0'
__author__ = 'mingfengpigeon <mingfengpigeon@gmail.com>'

import asyncio
import copy
import json
import uuid

import websockets


class Server:
    sent_commands: dict = {}
    subscribed_events: dict = {}
    _plugins: list = []
    _connections: list = []

    def __init__(self, server: str = '0.0.0.0', port: int = 8000, debug_mode: bool = False) -> None:
        self._server: str = server
        self._port: int = port
        self._debug_mode: bool = debug_mode

    def handler(self) -> list:
        return copy.deepcopy(self._plugins)

    def add_plugin(self, plugin) -> None:
        if self._plugins:
            for connection in self._connections:
                plugin_: Plugin = plugin()
                asyncio.create_task(plugin_.on_connect())
                connection.append(plugin_)
        self._plugins.append(plugin)

    def remove_plugin(self, plugin) -> None:
        if self._connections:
            for connection in self._connections:
                for plugin_ in connection.plugins:
                    if isinstance(plugin_, plugin):
                        plugin_.remove(plugin_)
                    break
        self._plugins.remove(plugin)

    async def run_forever(self) -> None:
        async with websockets.serve(self._on_connect, self._server, self._port):
            await asyncio.Future()

    async def _on_connect(self, websocket, path) -> None:
        plugins: list = []
        self._connections.append({
            "websocket": websocket,
            "path": path,
            "plugins": plugins,
        })
        for plugin in self._plugins:
            plugins.append(plugin(websocket, path, self, self._debug_mode))
        for plugin in plugins:
            asyncio.create_task(plugin.on_connect())
        while True:
            try:
                response: dict = json.loads(await websocket.recv())
            except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosedError):
                tasks = []
                for plugin in plugins:
                    tasks.append(plugin.on_disconnect())
                for task in tasks:
                    await task
                break
            else:
                message_purpose: str = response['header']['messagePurpose']
                if message_purpose == 'commandResponse':
                    request_id: str = response['header']['requestId']
                    if request_id in self.sent_commands:
                        asyncio.create_task(self.sent_commands[request_id](response))
                        del self.sent_commands[request_id]
                else:
                    event_name: str = response['header']['eventName']
                    asyncio.create_task(self.subscribed_events[event_name](response))

    async def disconnect(self, websocket) -> None:
        websocket.disconnect()
        for number in range(len(self._connections) - 1):
            connection: dict = self._connections[number]
            if connection['websocket'] == websocket:
                del self._connections[number]


class Plugin:
    def __init__(self, websocket, path, server: Server, debug_mode: bool = False) -> None:
        self._websocket = websocket
        self._path = path
        self._server = server
        self._debug_mode: bool = debug_mode

    async def on_connect(self) -> None:
        pass

    async def on_disconnect(self) -> None:
        pass

    async def on_receive(self, response) -> None:
        pass

    async def send_command(self, command: str, callback=None) -> None:
        request: dict = {
            'body': {'commandLine': command},
            'header': build_header('commandRequest')
        }
        if callback:
            self._server.sent_commands[request['header']['requestId']] = callback
        keywords: dict = {}
        if self._debug_mode:
            keywords['indent'] = 4
        await self._websocket.send(json.dumps(request, **keywords))

    async def subscribe(self, event_name: str, callback) -> None:
        request: dict | str = {
            'body': {'eventName': event_name},
            'header': build_header('subscribe')
        }
        self._server.subscribed_events[event_name] = callback
        keywords: dict = {}
        if self._debug_mode:
            keywords['indent'] = 4
        await self._websocket.send(json.dumps(request, **keywords))

    async def unsubscribe(self, event_name: str) -> None:
        request: dict = {
            'body': {'eventName': event_name},
            'header': build_header('unsubscribe')
        }
        del self._server.subscribed_events[event_name]
        keywords: dict = {}
        if self._debug_mode:
            keywords['indent'] = 4
        await self._websocket.send(json.dumps(request, keywords))

    async def disconnect(self) -> None:
        await self._server.disconnect(self._websocket)


def build_header(message_purpose: str, request_id: str | None = None):
    if not request_id:
        request_id: str = str(uuid.uuid4())
    return {
        'requestId': request_id,
        'messagePurpose': message_purpose,
        'version': '1',
        'messageType': 'commandRequest',
    }

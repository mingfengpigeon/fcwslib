__all__ = []
__version__ = '2.1.0'
__author__ = 'mingfengpigeon <mingfengpigeon@gmail.com>'

import asyncio

import fcwslib


class Plugin(fcwslib.Plugin):
    async def on_connect(self) -> None:
        print('Connected')
        await self.send_command('list', callback=self.list)
        await self.subscribe('PlayerMessage', callback=self.player_message)

    async def on_disconnect(self) -> None:
        print('Disconnected')

    async def on_receive(self, response) -> None:
        print('Receive other response {}'.format(response))

    async def list(self, response) -> None:
        print('Receive command response {}'.format(response))

    async def player_message(self, response) -> None:
        print('Receive event response {}'.format(response))


async def main() -> None:
    server = fcwslib.Server(debug_mode=True)
    server.add_plugin(Plugin)
    task = asyncio.create_task(server.run_forever())
    await task


if __name__ == '__main__':
    asyncio.run(main())

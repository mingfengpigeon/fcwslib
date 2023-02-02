__all__ = []
__version__ = '1.0.0'
__author__ = 'mingfengpigeon <mingfengpigeon@gmail.com>'

import fcwslib


class Handler(fcwslib.Handler):
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


def main() -> None:
    server = fcwslib.Server()
    server.set_handler(Handler)
    server.run_forever()


if __name__ == '__main__':
    main()

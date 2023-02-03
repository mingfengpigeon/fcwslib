# Introduction

A library that makes development of Python Minecraft Bedrock Edition websocket applications easier.

# Install

```bash
pip install fcwslib
```

# Demo

```python
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


def main() -> None:
    server = fcwslib.Server()
    server.add_plugin(Plugin)
    server.run_forever()


if __name__ == '__main__':
    main()

```
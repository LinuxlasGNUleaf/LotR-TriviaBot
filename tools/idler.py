import asyncio
import signal


def handle_sigterm():
    asyncio.get_event_loop().stop()


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.add_signal_handler(signal.SIGTERM, handle_sigterm)
    loop.run_forever()

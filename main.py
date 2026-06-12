import os
import asyncio
from aiohttp import web

from bot.main import main as bot_main


async def health(request):
    return web.Response(text="OK")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print("PORT =", os.environ.get("PORT"))
    print(f"Listening on 0.0.0.0:{port}")

    while True:
        await asyncio.sleep(3600)


async def run():
    web_task = asyncio.create_task(start_web_server())
    bot_task = asyncio.create_task(bot_main())

    await asyncio.gather(web_task, bot_task)


if __name__ == "__main__":
    asyncio.run(run())
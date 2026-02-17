import ulogging
from beepbeep import BeepBeep
import asyncio
logger = ulogging.get_logger("main")

async def main():
    beepbeep = BeepBeep()
    await beepbeep.initialize()

asyncio.run(main())
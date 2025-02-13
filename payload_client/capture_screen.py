import asyncio
import io
from typing import IO

import pyautogui
import pyscreeze


import mss
import mss.tools

async def upload(queue: asyncio.Queue, uploader):
    while True:
        img = await queue.get()  # ✅ Await the queue
        if img is None:
            break
        #uploader.send_screenshot(mss.tools.to_png(img.rgb, img.size))
        uploader.send_screenshot(img)

async def grab(queue: asyncio.Queue):
    while True:
        im1 = pyautogui.screenshot()
        byte_streams = io.BytesIO(b"")
        im1.save(byte_streams, "png")
        await queue.put(byte_streams)
        await asyncio.sleep(1)


    """rect = {"top": 0, "left": 0, "width": 600, "height": 800}
    with mss.mss() as sct:
        for _ in range(10):  # Capture 10 frames
            screenshot = sct.grab(rect)
            await queue.put(screenshot)  # ✅ Async queue.put()
            await asyncio.sleep(1)  # ✅ Async sleep

    await queue.put(None)  # ✅ Send stop signal"""

async def screen_capture_async(uploader):
    queue = asyncio.Queue()  # ✅ Use asyncio.Queue()

    # Run grabber and uploader concurrently
    await asyncio.gather(
        grab(queue),
        upload(queue, uploader)
    )

# Example usage:


def screen_capture(uploader):
    print("HI")
    loop = asyncio.new_event_loop()  # ✅ Create a new event loop
    asyncio.set_event_loop(loop)
    loop.run_until_complete(screen_capture_async(uploader))  # ✅ Run the async function
    loop.close()  # ✅ Clean up the loop

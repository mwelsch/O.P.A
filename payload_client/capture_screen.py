import asyncio
import io
import threading
import pyautogui

class ScreenCapture:
    def __init__(self, uploader):
        self.uploader = uploader
        self._timeout = 1.0  # Default to 1 FPS
        self._timeout_lock = threading.Lock()
        self._running_event = threading.Event()
        self._loop = None
        self._grab_task = None
        self._upload_task = None
        self._queue = None
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()

    def _run_event_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._queue = asyncio.Queue()
        self._loop.run_forever()

    def start_screen_capture(self):
        if self._running_event.is_set():
            return
        self._running_event.set()
        self._grab_task = asyncio.run_coroutine_threadsafe(self._grab(), self._loop)
        self._upload_task = asyncio.run_coroutine_threadsafe(self._upload(), self._loop)

    async def _grab(self):
        while self._running_event.is_set():
            im = pyautogui.screenshot()
            byte_stream = io.BytesIO()
            im.save(byte_stream, format="png")
            await self._queue.put(byte_stream)
            with self._timeout_lock:
                timeout = self._timeout
            await asyncio.sleep(timeout)

    async def _upload(self):
        while True:
            img = await self._queue.get()
            if img is None:
                break
            self.uploader.send_screenshot(img.getvalue())

    def stop_screen_capture(self):
        if not self._running_event.is_set():
            return
        self._running_event.clear()
        # Signal upload to stop by sending None
        asyncio.run_coroutine_threadsafe(self._queue.put(None), self._loop).result()
        # Wait for tasks to complete
        self._grab_task.result()
        self._upload_task.result()

    def set_frames_per_second(self, fps):
        if fps <= 0:
            raise ValueError("FPS must be greater than 0")
        with self._timeout_lock:
            self._timeout = 1.0 / fps
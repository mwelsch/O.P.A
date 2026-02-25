import base64
import io
from PIL import Image
import mss

def capture_screenshot():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=70)
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{img_base64}"

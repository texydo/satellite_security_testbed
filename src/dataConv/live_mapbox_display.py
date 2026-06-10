import pygame
import time
import threading
import requests
from PIL import Image
from io import BytesIO
from queue import Queue

# Mapbox Access Token
mapbox_access_token = 'put your Mapbox access token here'

# Global variables
image_queue = Queue()
_coord_queue = None
_display_thread = None
_fetch_thread = None
_running = False

def get_mapbox_image(lat, lon, zoom=15, width=1280, height=1280):
    url = f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/{lon},{lat},{zoom}/{width}x{height}?access_token={mapbox_access_token}"
    response = requests.get(url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    return None

def crop_to_1920x1080(image):
    aspect_ratio = 1920 / 1080
    img_width, img_height = image.size
    new_width = img_height * aspect_ratio
    if new_width > img_width:
        new_width = img_width
        new_height = img_width / aspect_ratio
    else:
        new_height = img_height
    left = (img_width - new_width) / 2
    top = (img_height - new_height) / 2
    right = (img_width + new_width) / 2
    bottom = (img_height + new_height) / 2
    return image.crop((left, top, right, bottom))

def _fetch_images():
    global _running
    try:
        while _running:
            if not _coord_queue.empty():
                lat, lon = _coord_queue.get()
                try:
                    img = get_mapbox_image(lat, lon)
                    if img:
                        img = crop_to_1920x1080(img).resize((1920, 1080), Image.LANCZOS)
                        img = img.convert("RGB")  # Ensure compatibility
                        surface = pygame.image.fromstring(img.tobytes(), img.size, img.mode)
                        image_queue.put(surface)
                except Exception as e:
                    print(f"[ERROR] Failed to fetch image: {e}")
            time.sleep(1)
    except Exception as fatal:
        print(f"[FATAL ERROR] in fetch thread: {fatal}")

def _display_images():
    global _running
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Satellite Live View")
    clock = pygame.time.Clock()

    try:
        while _running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    stop_display()

            if not image_queue.empty():
                screen.blit(image_queue.get(), (0, 0))
                pygame.display.flip()

            clock.tick(1)  # 1 FPS

    except Exception as e:
        print(f"[DISPLAY ERROR] {e}")

    finally:
        pygame.quit()
        print("[INFO] Pygame closed cleanly.")

def start_display(coord_queue):
    global _coord_queue, _running, _display_thread, _fetch_thread
    _coord_queue = coord_queue
    _running = True
    _fetch_thread = threading.Thread(target=_fetch_images, daemon=True)
    _display_thread = threading.Thread(target=_display_images, daemon=True)
    _fetch_thread.start()
    _display_thread.start()

def stop_display():
    global _running
    _running = False

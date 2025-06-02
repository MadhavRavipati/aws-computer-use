# ABOUTME: VNC client implementation using python-vncdotool
# ABOUTME: Provides actual VNC connection and control functionality

import asyncio
import base64
import io
import logging
from typing import Optional, Tuple
from PIL import Image
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)

class VNCClient:
    """VNC client wrapper for actual VNC connections"""
    
    def __init__(self, host: str = 'localhost', port: int = 5900, password: str = ''):
        self.host = host
        self.port = port
        self.password = password
        self.vnc_api = None
        
    async def connect(self):
        """Connect to VNC server using vncdotool"""
        try:
            # Import vncdotool (install with: pip install vncdotool)
            import vncdotool.api
            
            # Connect to VNC server
            connection_string = f"{self.host}::{self.port}"
            if self.password:
                self.vnc_api = vncdotool.api.connect(connection_string, password=self.password)
            else:
                self.vnc_api = vncdotool.api.connect(connection_string)
                
            logger.info(f"Connected to VNC server at {self.host}:{self.port}")
            return True
            
        except ImportError:
            logger.error("vncdotool not installed. Install with: pip install vncdotool")
            # Fallback to RFB protocol implementation
            return await self._connect_rfb()
        except Exception as e:
            logger.error(f"Failed to connect to VNC: {e}")
            return False
    
    async def _connect_rfb(self):
        """Fallback RFB protocol implementation"""
        try:
            reader, writer = await asyncio.open_connection(self.host, self.port)
            
            # Read RFB protocol version
            version = await reader.read(12)
            logger.info(f"VNC Protocol: {version.decode().strip()}")
            
            # Send client protocol version
            writer.write(b"RFB 003.008\n")
            await writer.drain()
            
            # Simple connection established
            self.reader = reader
            self.writer = writer
            return True
            
        except Exception as e:
            logger.error(f"RFB connection failed: {e}")
            return False
    
    async def screenshot(self) -> Optional[str]:
        """Capture screenshot from VNC"""
        if self.vnc_api:
            try:
                # Capture screenshot using vncdotool
                self.vnc_api.refreshScreen()
                
                # Get the PIL Image from vncdotool
                img = self.vnc_api.screen
                
                # Convert to base64
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                
                return base64.b64encode(buffer.getvalue()).decode()
                
            except Exception as e:
                logger.error(f"Screenshot capture failed: {e}")
                return None
        else:
            # Fallback screenshot method
            return await self._screenshot_fallback()
    
    async def _screenshot_fallback(self):
        """Fallback screenshot using x11vnc utilities"""
        try:
            # Use vncsnapshot command if available
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                cmd = [
                    'vncsnapshot',
                    '-passwd', self.password if self.password else '',
                    f'{self.host}:{self.port - 5900}',
                    tmp.name
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    with open(tmp.name, 'rb') as f:
                        img_data = f.read()
                    os.unlink(tmp.name)
                    return base64.b64encode(img_data).decode()
                else:
                    logger.error(f"vncsnapshot failed: {result.stderr}")
                    return None
                    
        except FileNotFoundError:
            logger.error("vncsnapshot not found. Install with: apt-get install vncsnapshot")
            return None
        except Exception as e:
            logger.error(f"Fallback screenshot failed: {e}")
            return None
    
    async def click(self, x: int, y: int, button: int = 1):
        """Send mouse click to VNC"""
        if self.vnc_api:
            try:
                # Move to position and click
                self.vnc_api.mouseMove(x, y)
                self.vnc_api.mousePress(button)
                await asyncio.sleep(0.1)
                self.vnc_api.mouseRelease(button)
                return True
            except Exception as e:
                logger.error(f"Click failed: {e}")
                return False
        else:
            # Send raw RFB pointer event
            return await self._send_pointer_event(x, y, button)
    
    async def _send_pointer_event(self, x: int, y: int, button_mask: int):
        """Send raw RFB pointer event"""
        if hasattr(self, 'writer'):
            try:
                # RFB PointerEvent message
                # Message type (5), button mask (1 byte), x (2 bytes), y (2 bytes)
                import struct
                msg = struct.pack('!BBHH', 5, button_mask, x, y)
                self.writer.write(msg)
                await self.writer.drain()
                return True
            except Exception as e:
                logger.error(f"Pointer event failed: {e}")
                return False
        return False
    
    async def type_text(self, text: str):
        """Type text via VNC"""
        if self.vnc_api:
            try:
                self.vnc_api.type(text)
                return True
            except Exception as e:
                logger.error(f"Type text failed: {e}")
                return False
        else:
            # Send individual key events
            for char in text:
                await self._send_key_event(ord(char), True)
                await self._send_key_event(ord(char), False)
                await asyncio.sleep(0.05)
            return True
    
    async def _send_key_event(self, key: int, down: bool):
        """Send raw RFB key event"""
        if hasattr(self, 'writer'):
            try:
                # RFB KeyEvent message
                # Message type (4), down flag (1 byte), padding (2 bytes), key (4 bytes)
                import struct
                msg = struct.pack('!BBHHI', 4, 1 if down else 0, 0, key)
                self.writer.write(msg)
                await self.writer.drain()
                return True
            except Exception as e:
                logger.error(f"Key event failed: {e}")
                return False
        return False
    
    async def key_press(self, key: str):
        """Send special key press"""
        if self.vnc_api:
            try:
                self.vnc_api.keyPress(key)
                return True
            except Exception as e:
                logger.error(f"Key press failed: {e}")
                return False
        else:
            # Map common keys to keysyms
            key_map = {
                'enter': 0xff0d,
                'tab': 0xff09,
                'escape': 0xff1b,
                'backspace': 0xff08,
                'delete': 0xffff,
                'up': 0xff52,
                'down': 0xff54,
                'left': 0xff51,
                'right': 0xff53,
            }
            
            if key.lower() in key_map:
                keysym = key_map[key.lower()]
                await self._send_key_event(keysym, True)
                await self._send_key_event(keysym, False)
                return True
            return False
    
    async def disconnect(self):
        """Disconnect from VNC"""
        if self.vnc_api:
            try:
                # vncdotool doesn't have explicit disconnect
                self.vnc_api = None
            except:
                pass
        
        if hasattr(self, 'writer'):
            self.writer.close()
            await self.writer.wait_closed()
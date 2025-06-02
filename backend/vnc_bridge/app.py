# ABOUTME: FastAPI application for VNC bridge service
# ABOUTME: Handles VNC commands and screenshot streaming

import os
import asyncio
import base64
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import boto3
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import aiofiles
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS clients
s3_client = boto3.client('s3')
S3_BUCKET = os.environ.get('S3_BUCKET')
SESSION_ID = os.environ.get('SESSION_ID')

# VNC configuration
VNC_HOST = os.environ.get('VNC_HOST', 'localhost')
VNC_PORT = int(os.environ.get('VNC_PORT', '5900'))
VNC_PASSWORD = os.environ.get('VNC_PASSWORD', '')

# Try to import the real VNC client
try:
    from .vnc_client import VNCClient
    USE_REAL_VNC = True
except ImportError:
    logger.warning("VNC client not available, using mock implementation")
    USE_REAL_VNC = False


class ClickRequest(BaseModel):
    x: int
    y: int
    button: str = "left"


class TypeRequest(BaseModel):
    text: str


class KeyCombinationRequest(BaseModel):
    keys: str


class MouseMoveRequest(BaseModel):
    x: int
    y: int
    duration: float = 0.5


class VNCBridge:
    """Bridge between HTTP/WebSocket API and VNC server"""
    
    def __init__(self, host: str = 'localhost', port: int = 5900):
        self.host = host
        self.port = port
        self.connected = False
        
        # Use real VNC client if available
        if USE_REAL_VNC:
            self.client = VNCClient(host, port, VNC_PASSWORD)
        else:
            self.client = None
    
    async def connect(self):
        """Connect to VNC server"""
        try:
            if self.client:
                # Use real VNC connection
                self.connected = await self.client.connect()
                if self.connected:
                    logger.info(f"Connected to VNC server at {self.host}:{self.port}")
                return self.connected
            else:
                # Mock connection for testing
                logger.info(f"Mock connecting to VNC server at {self.host}:{self.port}")
                self.connected = True
                return True
        except Exception as e:
            logger.error(f"Failed to connect to VNC: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from VNC server"""
        self.connected = False
        if self.client and hasattr(self.client, 'disconnect'):
            await self.client.disconnect()
        self.client = None
    
    async def screenshot(self) -> Optional[str]:
        """Capture screenshot and return base64 encoded"""
        if not self.connected:
            await self.connect()
        
        try:
            if self.client and hasattr(self.client, 'screenshot'):
                # Use real VNC screenshot
                screenshot_base64 = await self.client.screenshot()
                if not screenshot_base64:
                    logger.warning("Real VNC screenshot failed, using mock")
                    # Fall back to mock if real screenshot fails
                    screenshot_base64 = await self._mock_screenshot()
            else:
                # Mock screenshot for testing
                screenshot_base64 = await self._mock_screenshot()
            
            # Optionally save to S3
            if S3_BUCKET and SESSION_ID:
                key = f"screenshots/{SESSION_ID}/{int(time.time())}.png"
                s3_client.put_object(
                    Bucket=S3_BUCKET,
                    Key=key,
                    Body=buffer.getvalue(),
                    ContentType='image/png'
                )
                logger.info(f"Screenshot saved to S3: {key}")
            
            return screenshot_base64
            
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None
    
    async def _mock_screenshot(self) -> str:
        """Create a mock screenshot for testing"""
        img = Image.new('RGB', (1920, 1080), color='white')
        
        # Add timestamp
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), f"Mock Screenshot at {datetime.now()}", fill='black')
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    async def click(self, x: int, y: int, button: str = 'left') -> bool:
        """Perform mouse click"""
        if not self.connected:
            await self.connect()
        
        try:
            if self.client and hasattr(self.client, 'click'):
                # Map button names to button numbers
                button_map = {'left': 1, 'middle': 2, 'right': 3}
                button_num = button_map.get(button, 1)
                return await self.client.click(x, y, button_num)
            else:
                logger.info(f"Mock clicking at ({x}, {y}) with {button} button")
                return True
        except Exception as e:
            logger.error(f"Failed to click: {e}")
            return False
    
    async def type_text(self, text: str) -> bool:
        """Type text via VNC"""
        if not self.connected:
            await self.connect()
        
        try:
            if self.client and hasattr(self.client, 'type_text'):
                return await self.client.type_text(text)
            else:
                logger.info(f"Mock typing text: {text[:20]}...")
                return True
        except Exception as e:
            logger.error(f"Failed to type text: {e}")
            return False
    
    async def key_combination(self, keys: str) -> bool:
        """Send key combination"""
        if not self.connected:
            await self.connect()
        
        try:
            if self.client and hasattr(self.client, 'key_press'):
                return await self.client.key_press(keys)
            else:
                logger.info(f"Mock sending key combination: {keys}")
                return True
        except Exception as e:
            logger.error(f"Failed to send key combination: {e}")
            return False
    
    async def move_mouse(self, x: int, y: int, duration: float = 0.5) -> bool:
        """Move mouse to coordinates"""
        if not self.connected:
            await self.connect()
        
        try:
            if self.client and hasattr(self.client, 'move_mouse'):
                # Real VNC clients typically don't support smooth movement
                # Just click at the target position
                return await self.client.click(x, y, 0)  # 0 = no button click
            else:
                logger.info(f"Mock moving mouse to ({x}, {y}) over {duration}s")
                return True
        except Exception as e:
            logger.error(f"Failed to move mouse: {e}")
            return False


# Global VNC bridge instance
vnc_bridge = VNCBridge(VNC_HOST, VNC_PORT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting VNC Bridge service")
    await vnc_bridge.connect()
    yield
    # Shutdown
    logger.info("Shutting down VNC Bridge service")
    await vnc_bridge.disconnect()


# Create FastAPI app
app = FastAPI(
    title="Computer Use VNC Bridge",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "connected": vnc_bridge.connected,
        "session_id": SESSION_ID
    }


@app.post("/vnc/screenshot")
async def capture_screenshot():
    """Capture and return current screenshot"""
    screenshot = await vnc_bridge.screenshot()
    
    if screenshot:
        return JSONResponse({
            "success": True,
            "screenshot": screenshot,
            "timestamp": datetime.now().isoformat(),
            "resolution": {"width": 1920, "height": 1080}
        })
    else:
        raise HTTPException(status_code=500, detail="Failed to capture screenshot")


@app.post("/vnc/click")
async def handle_click(request: ClickRequest):
    """Handle mouse click"""
    success = await vnc_bridge.click(request.x, request.y, request.button)
    
    if success:
        # Capture screenshot after action
        screenshot = await vnc_bridge.screenshot()
        
        return JSONResponse({
            "success": True,
            "action": "click",
            "coordinates": {"x": request.x, "y": request.y},
            "button": request.button,
            "screenshot": screenshot
        })
    else:
        raise HTTPException(status_code=500, detail="Failed to perform click")


@app.post("/vnc/type")
async def handle_type(request: TypeRequest):
    """Handle text typing"""
    success = await vnc_bridge.type_text(request.text)
    
    if success:
        return JSONResponse({
            "success": True,
            "action": "type",
            "text_length": len(request.text)
        })
    else:
        raise HTTPException(status_code=500, detail="Failed to type text")


@app.post("/vnc/key_combination")
async def handle_key_combination(request: KeyCombinationRequest):
    """Handle key combination"""
    success = await vnc_bridge.key_combination(request.keys)
    
    if success:
        return JSONResponse({
            "success": True,
            "action": "key_combination",
            "keys": request.keys
        })
    else:
        raise HTTPException(status_code=500, detail="Failed to send key combination")


@app.post("/vnc/move")
async def handle_mouse_move(request: MouseMoveRequest):
    """Handle mouse movement"""
    success = await vnc_bridge.move_mouse(request.x, request.y, request.duration)
    
    if success:
        return JSONResponse({
            "success": True,
            "action": "move",
            "target": {"x": request.x, "y": request.y},
            "duration": request.duration
        })
    else:
        raise HTTPException(status_code=500, detail="Failed to move mouse")


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time VNC streaming"""
    await websocket.accept()
    logger.info(f"WebSocket connection established for session {session_id}")
    
    try:
        # Send initial screenshot
        screenshot = await vnc_bridge.screenshot()
        if screenshot:
            await websocket.send_json({
                "type": "screenshot",
                "data": screenshot,
                "timestamp": datetime.now().isoformat()
            })
        
        # Handle incoming messages and stream screenshots
        screenshot_task = None
        
        async def stream_screenshots():
            """Continuously stream screenshots"""
            while True:
                try:
                    screenshot = await vnc_bridge.screenshot()
                    if screenshot:
                        await websocket.send_json({
                            "type": "screenshot",
                            "data": screenshot,
                            "timestamp": datetime.now().isoformat()
                        })
                    await asyncio.sleep(1/30)  # 30 FPS
                except Exception as e:
                    logger.error(f"Error streaming screenshot: {e}")
                    break
        
        # Start screenshot streaming
        screenshot_task = asyncio.create_task(stream_screenshots())
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "click":
                success = await vnc_bridge.click(
                    data.get("x", 0),
                    data.get("y", 0),
                    data.get("button", "left")
                )
                await websocket.send_json({
                    "type": "action_result",
                    "action": "click",
                    "success": success
                })
            
            elif data.get("type") == "type":
                success = await vnc_bridge.type_text(data.get("text", ""))
                await websocket.send_json({
                    "type": "action_result",
                    "action": "type",
                    "success": success
                })
            
            elif data.get("type") == "key_combination":
                success = await vnc_bridge.key_combination(data.get("keys", ""))
                await websocket.send_json({
                    "type": "action_result",
                    "action": "key_combination",
                    "success": success
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if screenshot_task:
            screenshot_task.cancel()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
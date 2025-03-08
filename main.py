from fastapi import FastAPI, File, UploadFile, Form, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import asyncio
import json
import os
import time
import shutil
import uuid
from typing import List, Dict, Set, Optional
from datetime import datetime
import logging

# Import S3 utilities
import s3_utils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Synchronized Video Streaming")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Templates (now in browser directory)
templates = Jinja2Templates(directory="browser")

# In-memory video storage
videos = []
current_index = 0
connected_clients: Set[asyncio.Queue] = set()

# Video file extensions to recognize
VIDEO_EXTENSIONS = (".mp4", ".webm", ".ogg", ".mov", ".avi", ".mkv")

# Initialize with videos from static, uploads, and S3
def init_videos():
    global videos
    videos = []  # Clear existing videos
    
    # Scan static directory for videos
    logger.info("Scanning static directory for videos...")
    if os.path.exists("static"):
        for filename in os.listdir("static"):
            if filename.lower().endswith(VIDEO_EXTENSIONS):
                videos.append({
                    "url": f"/static/{filename}",
                    "duration": 10,  # Default duration for static videos
                    "likes": 0
                })
                logger.info(f"Added static video: {filename}")
    
    # Scan uploads directory for videos
    logger.info("Scanning uploads directory for videos...")
    if os.path.exists("uploads"):
        for filename in os.listdir("uploads"):
            if filename.lower().endswith(VIDEO_EXTENSIONS):
                videos.append({
                    "url": f"/uploads/{filename}",
                    "duration": 30,  # Default duration for uploaded videos
                    "likes": 0
                })
                logger.info(f"Added uploaded video: {filename}")
    
    # Get videos from S3
    logger.info("Fetching videos from S3...")
    try:
        s3_videos = s3_utils.list_videos_from_s3()
        for video in s3_videos:
            videos.append({
                "url": video["url"],
                "duration": 30,  # Default duration for S3 videos
                "likes": 0
            })
            logger.info(f"Added S3 video: {video['key']}")
    except Exception as e:
        logger.error(f"Error fetching S3 videos: {e}")
    
    # If no videos found, add placeholder message
    if not videos:
        logger.warning("No videos found in static, uploads, or S3!")
        
    logger.info(f"Initialized with {len(videos)} videos")
    
    # Log all videos for debugging
    for i, video in enumerate(videos):
        logger.info(f"Video {i+1}: {video['url']}")

# Main page
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Ambient TV version
@app.get("/ambient", response_class=HTMLResponse)
async def get_ambient(request: Request):
    return templates.TemplateResponse("ambient.html", {"request": request})

# Upload page
@app.get("/upload", response_class=HTMLResponse)
async def get_upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

# SSE endpoint for video updates
@app.get("/video-updates")
async def video_updates(request: Request):
    async def event_generator():
        # Create a queue for this client
        queue = asyncio.Queue()
        connected_clients.add(queue)
        logger.info(f"Client connected. Total clients: {len(connected_clients)}")
        
        try:
            # Send current video immediately upon connection
            if videos:
                current_video = videos[current_index]
                await queue.put(json.dumps({
                    "video_url": current_video["url"],
                    "start_time": int(time.time()),
                    "duration": current_video["duration"],
                    "likes": current_video["likes"],
                    "index": current_index,
                    "total": len(videos)
                }))
            
            # Keep connection open and wait for updates
            while True:
                if await request.is_disconnected():
                    break
                
                # Wait for the next update
                data = await queue.get()
                yield f"data: {data}\n\n"
                
        except asyncio.CancelledError:
            logger.info("Connection closed by client")
        finally:
            connected_clients.remove(queue)
            logger.info(f"Client disconnected. Remaining clients: {len(connected_clients)}")
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Background task to iterate through videos
async def video_iterator():
    global current_index
    
    while True:
        if not videos:
            await asyncio.sleep(1)
            continue
            
        current_video = videos[current_index]
        duration = current_video["duration"]
        
        # Broadcast current video to all clients
        message = json.dumps({
            "video_url": current_video["url"],
            "start_time": int(time.time()),
            "duration": duration,
            "likes": current_video["likes"],
            "index": current_index,
            "total": len(videos)
        })
        
        for client_queue in connected_clients:
            await client_queue.put(message)
        
        logger.info(f"Broadcasting video {current_index+1}/{len(videos)}: {current_video['url']}")
        
        # Wait for the duration of the video
        await asyncio.sleep(duration)
        
        # Move to next video
        current_index = (current_index + 1) % len(videos)

# Upload endpoint for S3
@app.post("/uploads")
async def upload_video_to_s3(
    video: UploadFile = File(...),
    duration: int = Form(30)
):
    # Validate file type
    if not s3_utils.is_valid_video_file(video.filename):
        raise HTTPException(status_code=400, detail="Invalid file type. Only video files are allowed.")
    
    # Generate a unique filename to avoid collisions
    original_filename = video.filename
    filename_parts = os.path.splitext(original_filename)
    unique_filename = f"{filename_parts[0]}_{uuid.uuid4().hex[:8]}{filename_parts[1]}"
    
    # Upload to S3
    try:
        success, result = s3_utils.upload_file_to_s3(
            video.file, 
            unique_filename, 
            video.content_type or "video/mp4"
        )
        
        if success:
            # Add to video list
            videos.append({
                "url": result,  # result contains the URL
                "duration": duration,
                "likes": 0
            })
            
            logger.info(f"Video uploaded to S3: {unique_filename}")
            return {"success": True, "message": "Video uploaded successfully", "url": result}
        else:
            # If S3 upload failed but we have credentials, try local upload as fallback
            if not all([s3_utils.AWS_ACCESS_KEY_ID, s3_utils.AWS_SECRET_ACCESS_KEY, s3_utils.S3_BUCKET_NAME]):
                logger.warning("S3 credentials not configured, falling back to local upload")
                return await upload_video_local(video, duration)
            else:
                # S3 error with credentials configured
                logger.error(f"S3 upload failed: {result}")
                raise HTTPException(status_code=500, detail=f"S3 upload failed: {result}")
    
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        # Try local upload as fallback
        return await upload_video_local(video, duration)

# Fallback local upload
async def upload_video_local(video: UploadFile, duration: int):
    """Fallback to local upload if S3 fails or is not configured."""
    try:
        # Ensure uploads directory exists
        os.makedirs("uploads", exist_ok=True)
        
        # Save the uploaded file locally
        file_path = os.path.join("uploads", video.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
        
        # Add to video list
        videos.append({
            "url": f"/uploads/{video.filename}",
            "duration": duration,
            "likes": 0
        })
        
        logger.info(f"Video uploaded locally: {video.filename}")
        return {"success": True, "message": "Video uploaded locally", "url": f"/uploads/{video.filename}"}
    
    except Exception as e:
        logger.error(f"Local upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Like endpoint
@app.post("/like/{index}")
async def like_video(index: int):
    if 0 <= index < len(videos):
        videos[index]["likes"] += 1
        likes = videos[index]["likes"]
        logger.info(f"Video {index+1} liked. Total likes: {likes}")
        return {"success": True, "likes": likes}
    return {"success": False, "message": "Invalid video index"}

# Get list of all videos
@app.get("/videos")
async def get_videos():
    return {"videos": videos, "current_index": current_index}

# Startup event
@app.on_event("startup")
async def startup_event():
    init_videos()
    asyncio.create_task(video_iterator())

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
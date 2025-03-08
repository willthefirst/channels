# Synchronized Video Streaming Platform

A simple platform where all clients watch the same video at the same time, controlled by a server-side iterator.

## Features

- Synchronized video playback across all connected clients
- Server-controlled video timing and switching
- Like/dislike functionality
- Video upload capability (local or S3)
- Real-time progress tracking
- Ambient viewing mode

## Technical Implementation

- **Backend**: FastAPI with Server-Sent Events (SSE)
- **Frontend**: Plain HTML/CSS/JavaScript with standard video element
- **Synchronization**: Server-side iterator that broadcasts current video to all clients
- **Storage**: Local file system or Amazon S3

## Setup

1. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Configure S3 (optional):

   - Copy `.env.example` to `.env`
   - Fill in your AWS credentials and S3 bucket information

   ```
   AWS_ACCESS_KEY_ID=your_access_key_id
   AWS_SECRET_ACCESS_KEY=your_secret_access_key
   AWS_REGION=us-east-1
   S3_BUCKET_NAME=your-video-bucket-name
   ```

3. Run the application:

   ```
   python main.py
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:8000         # Standard interface
   http://localhost:8000/ambient # Minimal ambient interface
   http://localhost:8000/upload  # Upload page
   ```

## How It Works

1. The server maintains a list of videos from local storage and/or S3
2. Videos play sequentially, with the server controlling timing
3. All clients stay synchronized through SSE updates
4. Users can upload videos through the upload page
5. Two viewing modes: standard (with likes) and ambient (minimal)

## Directory Structure

- `main.py`: FastAPI application with SSE implementation
- `s3_utils.py`: Utility functions for S3 operations
- `browser/index.html`: Standard frontend with video player and controls
- `browser/ambient.html`: Minimal ambient viewing interface
- `browser/upload.html`: Video upload interface
- `static/`: Directory for static files (sample videos)
- `uploads/`: Directory for user-uploaded videos (local fallback)

## API Endpoints

- `GET /`: Main page with video player
- `GET /ambient`: Minimal ambient viewing interface
- `GET /upload`: Video upload interface
- `GET /video-updates`: SSE endpoint for video updates
- `POST /uploads`: Upload endpoint for videos (S3 or local)
- `POST /like/{index}`: Like a video
- `GET /videos`: Get list of all videos

## S3 Integration

The platform can store and serve videos from Amazon S3:

1. **Configuration**: Set AWS credentials in the `.env` file
2. **Upload**: Videos are uploaded to S3 with public-read ACL
3. **Fallback**: If S3 upload fails or credentials are missing, falls back to local storage
4. **Synchronization**: Videos from S3 are included in the rotation alongside local videos

## Ambient Mode

For a distraction-free viewing experience:

- No like buttons or other controls
- Minimal interface with just the video
- Temporary title display that fades out
- Fullscreen by default

## Sample Videos

The application comes with sample videos in the `static` directory. If no videos are available, users can upload their own.

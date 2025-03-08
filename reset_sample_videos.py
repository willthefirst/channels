"""
Generate sample videos for testing the synchronized video streaming platform.
This script creates simple MP4 files with colored backgrounds and text.
"""

import os
import subprocess
import sys
import time
import logging
import platform
from datetime import datetime

# Function to clear terminal screen
def clear_screen():
    """Clear the terminal screen based on the operating system."""
    if platform.system() == "Windows":
        os.system('cls')
    else:  # For Linux and macOS
        os.system('clear')

# Custom handler that clears screen before first log message
class ClearScreenHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.first_emit = True
    
    def emit(self, record):
        if self.first_emit:
            clear_screen()
            self.first_emit = False
        
        # Format the message
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%H:%M:%S')
        message = formatter.format(record)
        print(message)

# Configure logging with only our custom handler
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Remove any existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
# Add our custom handler
logger.addHandler(ClearScreenHandler())

def check_ffmpeg():
    """Check if ffmpeg is installed."""
    logger.info("Checking if ffmpeg is installed...")
    try:
        result = subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        version = result.stdout.decode('utf-8').split('\n')[0]
        logger.info(f"Found ffmpeg: {version}")
        return True
    except FileNotFoundError:
        logger.error("ffmpeg not found in PATH")
        return False

def generate_video(output_path, duration, color, text, index, total):
    """Generate a simple video with ffmpeg."""
    start_time = time.time()
    
    logger.info(f"[{index}/{total}] Starting generation of {output_path}")
    logger.info(f"  - Duration: {duration}s, Color: {color}, Text: '{text}'")
    
    # Check if file already exists
    if os.path.exists(output_path):
        logger.info(f"  - File already exists, will be overwritten")
    
    command = [
        'ffmpeg', '-y',
        '-f', 'lavfi', 
        '-i', f'color=c={color}:s=640x360:d={duration}',
        '-vf', f"drawtext=text='{text}':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        output_path
    ]
    
    # Show the command being executed
    logger.debug(f"  - Executing: {' '.join(command)}")
    
    # Run the command and capture output
    process = subprocess.Popen(
        command, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    # Print progress dots
    sys.stdout.write(f"  - Processing: ")
    sys.stdout.flush()
    
    while process.poll() is None:
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(0.5)
    
    sys.stdout.write("\n")
    
    # Get the result
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        elapsed_time = time.time() - start_time
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # Size in MB
        
        logger.info(f"  - ✅ Generated successfully in {elapsed_time:.2f}s")
        logger.info(f"  - File size: {file_size:.2f} MB")
        logger.info(f"  - Saved to: {os.path.abspath(output_path)}")
    else:
        logger.error(f"  - ❌ Failed to generate video")
        logger.error(f"  - Error: {stderr}")
    
    return process.returncode == 0

def main():
    """Main function to generate sample videos."""
    logger.info("=" * 60)
    logger.info("Starting sample video generation")
    logger.info("=" * 60)
    
    # Check ffmpeg
    if not check_ffmpeg():
        logger.error("Error: ffmpeg is not installed. Please install ffmpeg to generate sample videos.")
        logger.info("On macOS: brew install ffmpeg")
        logger.info("On Ubuntu/Debian: sudo apt-get install ffmpeg")
        logger.info("On Windows: Download from https://ffmpeg.org/download.html")
        sys.exit(1)
    
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        logger.info("Creating 'static' directory")
        os.makedirs('static', exist_ok=True)
    else:
        logger.info("'static' directory already exists")
    
    # Generate sample videos
    videos = [
        ('static/default1.mp4', 10, 'blue', 'Sample Video 1'),
        ('static/default2.mp4', 10, 'red', 'Sample Video 2'),
        ('static/default3.mp4', 10, 'green', 'Sample Video 3'),
    ]
    
    logger.info(f"Will generate {len(videos)} sample videos")
    
    start_time = time.time()
    success_count = 0
    
    for i, (output_path, duration, color, text) in enumerate(videos, 1):
        if generate_video(output_path, duration, color, text, i, len(videos)):
            success_count += 1
    
    total_time = time.time() - start_time
    
    logger.info("=" * 60)
    logger.info(f"Generation complete: {success_count}/{len(videos)} videos created successfully")
    logger.info(f"Total time: {total_time:.2f} seconds")
    logger.info("=" * 60)
    
    if success_count == len(videos):
        logger.info("All sample videos generated successfully!")
        logger.info("You can now run the main application with: python main.py")
    else:
        logger.warning(f"Some videos failed to generate ({len(videos) - success_count} failures)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1) 
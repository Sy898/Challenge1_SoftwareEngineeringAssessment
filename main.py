from fastapi import FastAPI, UploadFile, File, HTTPException, Path
from fastapi.responses import FileResponse
from pathlib import Path as SysPath
from PIL import Image, ExifTags
import os
from datetime import datetime
from transformers import BlipProcessor, BlipForConditionalGeneration
import time
import uuid
from fastapi import BackgroundTasks

app = FastAPI()

images_dir = "images/"

images_db = {}

processing_times = []  # store processing durations
success_count = 0
failure_count = 0

# Create image folder if it does not exist
SysPath(images_dir).mkdir(parents=True, exist_ok=True)

# Dictionary to track status
image_status = {}

SUPPORTED_TYPES = {"image/jpeg", "image/png"}
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# Load pre-trained model
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")
@app.post("/api/images")
async def create_upload_image(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    global success_count, failure_count

    # Check if the filename already exists
    if file.filename in image_status:
        raise HTTPException(status_code=400, detail="File with this filename already uploaded")

    # 1. Check MIME type
    if file.content_type not in SUPPORTED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPG and PNG files are supported")

    # 2. Check extension
    ext = file.filename.lower().rsplit(".", 1)[-1]  # get extension
    if f".{ext}" not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file extension. Use JPG or PNG")

    # Save the uploaded file immediately
    contents = await file.read()
    file_path = f"{images_dir}{file.filename}"
    with open(file_path, "wb") as f:
        f.write(contents)

    # Generate a unique image_id and mark status
    image_id = str(uuid.uuid4())
    image_status[file.filename] = "processing"
    images_db[image_id] = {
        "filename": file.filename,
        "status": "processing"
    }

    # Schedule background processing
    background_tasks.add_task(process_image_in_background, file.filename, file_path, image_id)

    # Process should be non-blocking and return a unique id to the user immediately (see Automated Processing for Images) (Bonus)
    # Return immediately with image_id
    return {"filename": file.filename, "id": image_id, "status": "processing"}

def process_image_in_background(filename, file_path, image_id):
    global success_count, failure_count

    start_time = time.time() # record current time

    try:
        #open image with PIL
        img = Image.open(file_path) #to prevent file modification for file format to work
        img2 = img.convert('RGB')

        #generate thumbnails
        thumb1_dir = f"{images_dir}thumb1_{filename}"
        thumb2_dir = f"{images_dir}thumb2_{filename}"

        #create first thumbnail (200x200)
        thumb1 = img.copy()
        thumb1.thumbnail((200, 200))
        thumb1.save(thumb1_dir)

        #create second thumbnail (50x50)
        thumb2 = img.copy()
        thumb2.thumbnail((50, 50))
        thumb2.save(thumb2_dir)

        # Generate caption using BLIP model from huggingface.co
        inputs = processor(images=img2, return_tensors="pt")
        out = model.generate(**inputs)
        caption = processor.decode(out[0], skip_special_tokens=True)

        # EXIF data (Bonus)
        exif_data = {}
        if hasattr(img, "_getexif") and img._getexif() is not None:
            for tag, value in img._getexif().items():
                key = ExifTags.TAGS.get(tag, tag)

                # Convert non-serializable types (like IFDRational) into strings
                try:
                    if isinstance(value, (bytes, bytearray)):
                        value = value.decode(errors="ignore")  # decode bytes
                    else:
                        value = str(value)  # fallback to string
                except Exception:
                    value = str(value)

                exif_data[key] = value

        # After processing EXIF, check if exists
        if exif_data:
            exif_output = exif_data
        else:
            exif_output = "No EXIF data found"

        metadata = {
            "dimensions": img.size,
            "format": img.format,
            "size": f"{os.path.getsize(file_path)} bytes",
            "date time of the file": f"{datetime.now()}",
        }

        # Update image_db
        images_db[image_id].update({
            "caption": caption,
            "thumbnail_size_200x200": thumb1_dir,
            "thumbnail_size_50x50": thumb2_dir,
            "metadata": metadata,
            "exif": exif_output,
            "status": "processed"
        })

        image_status[filename] = "processed"
        success_count += 1
        processing_times.append(time.time() - start_time)

        with open("output.txt", "a") as f: #store processed results in output.txt
            f.write(
                f"filename: {filename}\n"
                f"image id: {image_id}\n"
                f"captions: {caption}\n"
                f"thumbnail_size_200x200: {str(thumb1_dir)}\n"
                f"thumbnail_size_50x50: {str(thumb2_dir)}\n"
                f"metadata: {metadata}\n"
                f"exif: {exif_output}\n"
                f"status: processed\n"
            )

    except Exception as e:
        failure_count += 1
        image_status[filename] = "failed"
        images_db[image_id].update({
            "status": "failed",
            "error": str(e)
        })

@app.get("/api/images")
def list_images():
    images = os.listdir(images_dir)
    results = []

    for img in images:
        status = image_status.get(img, "processed")  # default to processed
        results.append({
            "filename": img,
            "status": status
        })

    return results

@app.get("/api/images/{image_id}")
def get_image_details(image_id: str):
    if image_id not in images_db:
        raise HTTPException(status_code=404, detail="Image ID not found")

    return images_db[image_id]  # returns exactly the same structure as POST

# Return small or medium thumbnail
@app.get("/api/images/{image_id}/thumbnails/{size}")
def get_thumbnail(image_id: str, size: str = Path(..., pattern="small|medium")):
    if image_id not in images_db:
        raise HTTPException(status_code=404, detail="Image ID not found")

    image_info = images_db[image_id]

    if size == "small":
        thumb_path = image_info["thumbnail_size_50x50"]
    else:  # medium
        thumb_path = image_info["thumbnail_size_200x200"]

    if not os.path.exists(thumb_path):
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    return FileResponse(thumb_path)

# Return processing statistics
@app.get("/api/stats")
def get_stats():
    avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
    total = success_count + failure_count
    success_rate = (success_count / total * 100) if total else 0
    failure_rate = (failure_count / total * 100) if total else 0

    return {
        "total_processed": total,
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate_percent": success_rate,
        "failure_rate_percent": failure_rate,
        "average_processing_time_sec": avg_time
    }

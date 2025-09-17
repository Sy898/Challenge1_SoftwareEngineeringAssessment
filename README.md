# **Project Overview:**

---
## Challenge 1: Software Engineering Assessment

### Challenge Overview

Create an image processing pipeline API that automatically processes images, generates thumbnails, extracts
metadata, and provides analysis through API endpoints.

## **Notes:**

---
Changed Phone Model and Software to censor information

Duplicate file names and unsupported file types does not count towards failure as they are rejected before processing.


# **Installation Steps:**

---
pip install fastapi

pip install uvicorn

pip install python-multipart

pip install pillow

pip install transformers torch torchvision

## **API Documentation:**

---
URL: http://127.0.0.1:8000/docs

### 1. Upload Image

Endpoint: `POST /api/images`

Uploads an image to the server. The API will:

    Save the image.
    
    Generate thumbnails (200x200 and 50x50).
    
    Create a caption using a pre-trained BLIP model.
    
    Extract metadata and EXIF data (if none → "No EXIF data found").
    
    Assign a UUID to the image.
    
    Store all metadata, caption, thumbnails, and status ("processed") in output.txt.

The process is non-blocking: the API immediately returns a unique image ID (the assigned UUID) to the user.

If processing fails, the API sets in `images_db`:

    {
      "status": "failed",
      "error": "<error message>"
    }

In normal case, after processing, everything goes into output.txt with "processed".

Request:

`Content-Type: multipart/form-data`

Body Parameter:

file (required): The image file to upload (.jpg, .jpeg, or .png).

Response:

200 OK(Successful):

    Example:
    {
      "filename": "20240225_142303.jpg",
      "id": "a6c838d4-58cf-4e19-ad63-54597bf90108",
      "status": "processing"
    }

output.txt for existing exif data:

    filename: 20240225_142303.jpg
    image id: a6c838d4-58cf-4e19-ad63-54597bf90108
    captions: there is a motorcycle that is parked in a garage
    thumbnail_size_200x200: images/thumb1_20240225_142303.jpg
    thumbnail_size_50x50: images/thumb2_20240225_142303.jpg
    metadata: {'dimensions': (4000, 3000), 'format': 'JPEG', 'size': '3592114 bytes', 'date time of the file': '2025-09-16 20:25:33.681641'}
    exif: {'ImageWidth': '4000', 'ImageLength': '3000', 'ResolutionUnit': '2', 'ExifOffset': '226', 'Make': 'samsung', 'Model': 'SM-A000A', 'Software': 'A000000000000', 'Orientation': '6', 'DateTime': '2024:02:25 14:23:03', 'YCbCrPositioning': '1', 'XResolution': '72.0', 'YResolution': '72.0', 'ExifVersion': '0220', 'ShutterSpeedValue': '0.030303030303030304', 'ApertureValue': '2.52', 'DateTimeOriginal': '2024:02:25 14:23:03', 'DateTimeDigitized': '2024:02:25 14:23:03', 'ExposureBiasValue': '0.0', 'MaxApertureValue': '2.52', 'MeteringMode': '2', 'ColorSpace': '1', 'Flash': '0', 'FocalLength': '9.0', 'ExifImageWidth': '4000', 'ExifImageHeight': '3000', 'DigitalZoomRatio': '3.0', 'FocalLengthIn35mmFilm': '72', 'SceneCaptureType': '0', 'OffsetTime': '+08:00', 'OffsetTimeOriginal': '+08:00', 'SubsecTime': '681', 'SubsecTimeOriginal': '681', 'SubsecTimeDigitized': '681', 'ExposureTime': '0.030303030303030304', 'FNumber': '2.4', 'ImageUniqueID': 'M10XLNF00MM', 'ExposureProgram': '2', 'ISOSpeedRatings': '1000', 'ExposureMode': '0', 'WhiteBalance': '0'}
    status: processed

output.txt for no exif data:

    filename: funny cat.jpeg
    image id: 33cb2dea-7c4f-4803-b0be-606504172c8b
    captions: there is a cat that is holding a sandwich in its paws
    thumbnail_size_200x200: images/thumb1_funny cat.jpeg
    thumbnail_size_50x50: images/thumb2_funny cat.jpeg
    metadata: {'dimensions': (1242, 1556), 'format': 'JPEG', 'size': '169008 bytes', 'date time of the file': '2025-09-16 20:26:39.500014'}
    exif: No EXIF data found
    status: processed

400 Bad Request – invalid file type, extension, or filename already exists

    Example 1:
    Failed Result(Duplicate file name)
    {
      "detail": "File with this filename already uploaded"
    }
    
    Example 2:
    Failed Result(Unsupported file type)
    {
      "detail": "Only JPG and PNG files are supported"
    }

Other than invalid file type, file extension, duplicated filenames, the `POST /api/images` endpoint always returns 200 OK with `{filename, id, status: "processing"}`.

If processing later fails in the background, the image record will be updated with:

    {
      "status": "failed",
      "error": "<error message>"
    }

Users can check failures by calling `GET /api/images` or `GET /api/images/{image_id}`.

Duplicate filenames → 400 Bad Request

Unsupported file type → 400 Bad Request

Note: The API does not return 500 Internal Server Error for processing failures. Instead, failures are logged in the database with "status": "failed".

### 2. List All Images

Endpoint: `GET /api/images`
Description: Lists all images currently stored, including thumbnails, along with their processing status.

Response:

    [
      {
        "filename": "20240225_142303.jpg",
        "status": "processed"
      },
      {
        "filename": "20240225_161225.jpg",
        "status": "processed"
      },
      {
        "filename": "thumb1_20240225_142303.jpg",
        "status": "processed"
      },
      {
        "filename": "thumb1_20240225_161225.jpg",
        "status": "processed"
      },
      {
        "filename": "thumb2_20240225_142303.jpg",
        "status": "processed"
      },
      {
        "filename": "thumb2_20240225_161225.jpg",
        "status": "processed"
      }
    ]

### 3. Get Image Details

Endpoint: `GET /api/images/{image_id}`
Description: Get details of a specific image by its unique ID.

Path Parameters:

`image_id` (string, required) – UUID of the image

Responses:

200 OK – Returns the same structure as the `POST /api/images` response

#### Successful:

**Input:**

    image_id: a6c838d4-58cf-4e19-ad63-54597bf90108

**Output:**

    {
      "filename": "20240225_142303.jpg",
      "status": "processed",
      "caption": "there is a motorcycle that is parked in a garage",
      "thumbnail_size_200x200": "images/thumb1_20240225_142303.jpg",
      "thumbnail_size_50x50": "images/thumb2_20240225_142303.jpg",
      "metadata": {
        "dimensions": [
          4000,
          3000
        ],
        "format": "JPEG",
        "size": "3592114 bytes",
        "date time of the file": "2025-09-16 20:25:33.681641"
      },
      "exif": {
        "ImageWidth": "4000",
        "ImageLength": "3000",
        "ResolutionUnit": "2",
        "ExifOffset": "226",
        "Make": "samsung",
        "Model": "SM-A000A",
        "Software": "A000000000000",
        "Orientation": "6",
        "DateTime": "2024:02:25 14:23:03",
        "YCbCrPositioning": "1",
        "XResolution": "72.0",
        "YResolution": "72.0",
        "ExifVersion": "0220",
        "ShutterSpeedValue": "0.030303030303030304",
        "ApertureValue": "2.52",
        "DateTimeOriginal": "2024:02:25 14:23:03",
        "DateTimeDigitized": "2024:02:25 14:23:03",
        "ExposureBiasValue": "0.0",
        "MaxApertureValue": "2.52",
        "MeteringMode": "2",
        "ColorSpace": "1",
        "Flash": "0",
        "FocalLength": "9.0",
        "ExifImageWidth": "4000",
        "ExifImageHeight": "3000",
        "DigitalZoomRatio": "3.0",
        "FocalLengthIn35mmFilm": "72",
        "SceneCaptureType": "0",
        "OffsetTime": "+08:00",
        "OffsetTimeOriginal": "+08:00",
        "SubsecTime": "681",
        "SubsecTimeOriginal": "681",
        "SubsecTimeDigitized": "681",
        "ExposureTime": "0.030303030303030304",
        "FNumber": "2.4",
        "ImageUniqueID": "M10XLNF00MM",
        "ExposureProgram": "2",
        "ISOSpeedRatings": "1000",
        "ExposureMode": "0",
        "WhiteBalance": "0"
      }
    }

#### When EXIF data not present:

**Input:** 

    image_id: 33cb2dea-7c4f-4803-b0be-606504172c8b

**Output:**

    {
      "filename": "funny cat.jpeg",
      "status": "processed",
      "caption": "there is a cat that is holding a sandwich in its paws",
      "thumbnail_size_200x200": "images/thumb1_funny cat.jpeg",
      "thumbnail_size_50x50": "images/thumb2_funny cat.jpeg",
      "metadata": {
        "dimensions": [
          1242,
          1556
        ],
        "format": "JPEG",
        "size": "169008 bytes",
        "date time of the file": "2025-09-16 20:26:39.500014"
      },
      "exif": "No EXIF data found"
    }

404 Not Found – Image ID does not exist

#### Unsuccessful:

**Input:**

    image_id: aaa

**Output:**

    {
      "detail": "Image ID not found"
    }

### 4. Get Thumbnail

Endpoint: `GET /api/images/{image_id}/thumbnails/{size}`
Description: Retrieve a small (50x50) or medium (200x200) thumbnail for the specified image.

Path Parameters:

`image_id` (string, required) – UUID of the image

`size` (string, required) – small or medium

Responses:

200 OK – Returns the thumbnail image as a file

**Input:**

    image_id:a6c838d4-58cf-4e19-ad63-54597bf90108
    size:medium

**Output:**

[medium thumbnail size image shown here]

404 Not Found – Image ID or thumbnail not found

#### Unsuccessful 1(image_id not found):

**Input:**

    image_id: aaa
    size: medium

**Output:**

    {
      "detail": "Image ID not found"
    }

#### Unsuccessful 2(size not found):

**Input:**

    image_id: a6c838d4-58cf-4e19-ad63-54597bf90108
    size: extra large

**Output:**

    Error message popup:

    Please correct the following validation errors and try again.
        For 'size': Value must follow pattern small|medium.

### 5. Get Processing Statistics

Endpoint: `GET /api/stats`

Description: Returns statistics about image processing including total processed images, success/failure count, success/failure rate, and average processing time.

Response:

    {
      "total_processed": 2,
      "success_count": 2,
      "failure_count": 0,
      "success_rate_percent": 100,
      "failure_rate_percent": 0,
      "average_processing_time_sec": 1.9362304210662842
    }

## **Example Usage (i.e. how to run the code)**

---
Clone repository from GitHub. Pull the latest code.

Install based on installation steps shown above.

How to run the code:

On Terminal, Start the server:
    
    uvicorn main:app --reload
    
Open API Docs(FastAPI)
    
    Go to http://127.0.0.1:8000/docs on browser

Firstly, upload an image(`POST /api/images`):

    Example:
    
    {
      "filename": "20240225_142303.jpg",
      "id": "a6c838d4-58cf-4e19-ad63-54597bf90108",
      "status": "processing"
    }

output.txt for existing exif data:

    filename: 20240225_142303.jpg
    image id: a6c838d4-58cf-4e19-ad63-54597bf90108
    captions: there is a motorcycle that is parked in a garage
    thumbnail_size_200x200: images/thumb1_20240225_142303.jpg
    thumbnail_size_50x50: images/thumb2_20240225_142303.jpg
    metadata: {'dimensions': (4000, 3000), 'format': 'JPEG', 'size': '3592114 bytes', 'date time of the file': '2025-09-16 20:25:33.681641'}
    exif: {'ImageWidth': '4000', 'ImageLength': '3000', 'ResolutionUnit': '2', 'ExifOffset': '226', 'Make': 'samsung', 'Model': 'SM-A000A', 'Software': 'A000000000000', 'Orientation': '6', 'DateTime': '2024:02:25 14:23:03', 'YCbCrPositioning': '1', 'XResolution': '72.0', 'YResolution': '72.0', 'ExifVersion': '0220', 'ShutterSpeedValue': '0.030303030303030304', 'ApertureValue': '2.52', 'DateTimeOriginal': '2024:02:25 14:23:03', 'DateTimeDigitized': '2024:02:25 14:23:03', 'ExposureBiasValue': '0.0', 'MaxApertureValue': '2.52', 'MeteringMode': '2', 'ColorSpace': '1', 'Flash': '0', 'FocalLength': '9.0', 'ExifImageWidth': '4000', 'ExifImageHeight': '3000', 'DigitalZoomRatio': '3.0', 'FocalLengthIn35mmFilm': '72', 'SceneCaptureType': '0', 'OffsetTime': '+08:00', 'OffsetTimeOriginal': '+08:00', 'SubsecTime': '681', 'SubsecTimeOriginal': '681', 'SubsecTimeDigitized': '681', 'ExposureTime': '0.030303030303030304', 'FNumber': '2.4', 'ImageUniqueID': 'M10XLNF00MM', 'ExposureProgram': '2', 'ISOSpeedRatings': '1000', 'ExposureMode': '0', 'WhiteBalance': '0'}
    status: processed

List all uploaded images(`GET /api/images`):

    Example

    [
      {
        "filename": "20240225_142303.jpg",
        "status": "processed"
      },
      {
        "filename": "20240225_161225.jpg",
        "status": "processed"
      },
      {
        "filename": "funny cat.jpeg",
        "status": "processed"
      },
      {
        "filename": "thumb1_20240225_142303.jpg",
        "status": "processed"
      },
      {
        "filename": "thumb1_20240225_161225.jpg",
        "status": "processed"
      },
      {
        "filename": "thumb1_funny cat.jpeg",
        "status": "processed"
      },
      {
        "filename": "thumb2_20240225_142303.jpg",
        "status": "processed"
      },
      {
        "filename": "thumb2_20240225_161225.jpg",
        "status": "processed"
      },
      {
        "filename": "thumb2_funny cat.jpeg",
        "status": "processed"
      }
    ]

Get image details(`GET /api/images/{image_id}`):

Enter the image id for example: a6c838d4-58cf-4e19-ad63-54597bf90108

    {
      "filename": "20240225_142303.jpg",
      "status": "processed",
      "caption": "there is a motorcycle that is parked in a garage",
      "thumbnail_size_200x200": "images/thumb1_20240225_142303.jpg",
      "thumbnail_size_50x50": "images/thumb2_20240225_142303.jpg",
      "metadata": {
        "dimensions": [
          4000,
          3000
        ],
        "format": "JPEG",
        "size": "3592114 bytes",
        "date time of the file": "2025-09-16 20:25:33.681641"
      },
      "exif": {
        "ImageWidth": "4000",
        "ImageLength": "3000",
        "ResolutionUnit": "2",
        "ExifOffset": "226",
        "Make": "samsung",
        "Model": "SM-A000A",
        "Software": "A000000000000",
        "Orientation": "6",
        "DateTime": "2024:02:25 14:23:03",
        "YCbCrPositioning": "1",
        "XResolution": "72.0",
        "YResolution": "72.0",
        "ExifVersion": "0220",
        "ShutterSpeedValue": "0.030303030303030304",
        "ApertureValue": "2.52",
        "DateTimeOriginal": "2024:02:25 14:23:03",
        "DateTimeDigitized": "2024:02:25 14:23:03",
        "ExposureBiasValue": "0.0",
        "MaxApertureValue": "2.52",
        "MeteringMode": "2",
        "ColorSpace": "1",
        "Flash": "0",
        "FocalLength": "9.0",
        "ExifImageWidth": "4000",
        "ExifImageHeight": "3000",
        "DigitalZoomRatio": "3.0",
        "FocalLengthIn35mmFilm": "72",
        "SceneCaptureType": "0",
        "OffsetTime": "+08:00",
        "OffsetTimeOriginal": "+08:00",
        "SubsecTime": "681",
        "SubsecTimeOriginal": "681",
        "SubsecTimeDigitized": "681",
        "ExposureTime": "0.030303030303030304",
        "FNumber": "2.4",
        "ImageUniqueID": "M10XLNF00MM",
        "ExposureProgram": "2",
        "ISOSpeedRatings": "1000",
        "ExposureMode": "0",
        "WhiteBalance": "0"
      }
    }

Get thumbnail(`GET/api/images/{image_id}/thumbnails/{size}`):

Enter image id for example: 96eeca95-66da-4516-806d-572f06055559

Enter size for example: medium

Response:

    [medium-sized thumbnail image displayed here]

Get stats (`GET /api/stats`):

Example:

    {
      "total_processed": 2,
      "success_count": 2,
      "failure_count": 0,
      "success_rate_percent": 100,
      "failure_rate_percent": 0,
      "average_processing_time_sec": 1.9362304210662842
    }

## **Processing pipeline explanation**

---
On Terminal:

    uvicorn main:app --reload

    Go to http://127.0.0.1:8000/docs

When a user uploads an image through `POST /api/images`, the system starts a non-blocking processing pipeline:

### 1. Upload & Check

The user uploads an image via `/api/images`.

The server checks:

If the filename is already uploaded -> rejects duplicate filenames.

If the file type is JPG, JPEG or PNG -> rejects others.

If the file extension is .jpg, .jpeg or .png -> rejects others.

### 2. Save Image

The uploaded image is saved in the images/ folder. If images/ folder does not exist, create folder.

If folder missing -> created at app start

Its status is marked as "processing".

### 3. Process Image

Open & Convert: Open the image with Pillow and have 2 versions. img opened as original, img2 converts img to RGB. This prevents the files from opening twice.

Thumbnails: Create two thumbnails:

    Medium: 200x200
    
    Small: 50x50

Caption: Use the BLIP model to generate a description of the image.

EXIF Data: Extract metadata using original image that was not converted to RGB (camera info, GPS, etc.), if available.

Metadata: Collect basic info: dimensions, format, file size, upload time.

### 4. Store & Return

The process is non-blocking: the API immediately returns a unique image ID (the assigned UUID) to the user.

Store all info in `images_db`.

Update status to "processed".

Log results in output.txt.

The API immediately returns only `{filename, image_id, status="processing"}`.

Full details (caption, metadata, EXIF, thumbnails) can be retrieved via `GET /api/images/{image_id}` after processing completes.

### 5. Error Handling

The `POST /api/images` always returns 200 with "status": "processing".

If the background processing fails, status becomes "failed" in `images_db` and `image_status`.

500 Internal Server Error – No longer returned for processing failures.

Instead, the image status will be "failed" in the background.

Users can see failed processing when they call `GET /api/images` or `GET /api/images/{image_id}`.

### 6. Other Endpoints

`/api/images`: List all uploaded images with status.

`/api/images/{image_id}`: Get full details for a specific image.

`/api/images/{image_id}/thumbnails/{size}`: Return small or medium thumbnail for a specific image.

`/api/stats`: Show processing statistics (success/failure count, average processing time).

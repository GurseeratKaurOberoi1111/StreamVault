# StreamVault

A complete educational streaming platform with separate frontend source, Python backend, local SQLite storage and an AWS CloudFormation deployment. No CloudFront. No npm installation required.

## Run locally

Install Python 3.12 or newer from https://www.python.org/downloads/.

Windows: extract the ZIP, then double click `START_WINDOWS.bat`.

Mac or Linux: open a terminal in this folder and run:

```bash
python3 backend/local_server.py
```

Open http://localhost:8000. Create your own account. There are no preset credentials.

A 24 second synthetic playback test is included as `media/sintel.mp4`. Click **Watch Sintel** to test the player after signing in. The clip is visibly labelled as a test; it is not the actual Sintel film. The other five films require your own legally obtained media files.

## What works

* Responsive film catalogue with six entries and original SVG landscape artwork
* Search by title, description or genre; genre filters
* Registration, sign in, sign out and expiring sessions
* A personal watchlist stored separately for each account
* Continue watching; playback position saved every 10 seconds, on pause and when closing
* Native browser video controls, seeking and fullscreen
* Private S3 video delivery through expiring signed URLs on AWS
* Local video seeking through HTTP byte range responses

## Deploy on AWS

Follow `docs/AWS_DEPLOYMENT.md`. The ready to upload file is **template.yaml** in the project root.

Architecture: browser → API Gateway HTTP API → Python Lambda → DynamoDB. Lambda serves the frontend and APIs from one origin. Video bytes go directly from private S3 to the browser using a signed URL. Local development uses the same handler with a SQLite adapter.

The AWS resources are not created until you deploy the template in your own account.

## Project files

| Path | Purpose |
| --- | --- |
| frontend/index.html | Page structure and dialogs |
| frontend/styles.css | Responsive visual design |
| frontend/app.js | Catalogue, account, list and player interactions |
| frontend/assets/ | Original SVG film illustrations |
| backend/app.py | Shared API handler, sessions, validation and storage adapters |
| backend/catalog.json | Film metadata |
| backend/local_server.py | Local HTTP server and video seeking |
| infrastructure/base.yaml | Editable CloudFormation infrastructure |
| template.yaml | Generated complete deployment template |
| media/sintel.mp4 | Clearly labelled synthetic playback test |
| scripts/build.py | Embeds frontend and backend into template.yaml |
| scripts/upload_demo.py | Optional demo upload using AWS CLI |
| tests/test_app.py | Backend regression tests |
| docs/ | Deployment, API reference, validation and media notes |

## Edit and rebuild

Edit the source files, then run:

```bash
python scripts/build.py
python -m unittest discover -s tests -v
```

Use `python3` instead of `python` if needed. Rebuild before uploading or updating `template.yaml`. The build uses only Python's standard library. The generated template contains its own application source so the Console deployment does not need a separate Lambda ZIP, build service or public website bucket.

For local development and tests no third party packages are needed. The AWS Lambda version uses the Boto3 SDK supplied by the Python runtime. A production release should pin and package its SDK dependencies rather than relying on runtime updates.

## Limits

This is a small course demonstration, not a commercial streaming service. There is no billing, subscription model, admin uploader, DRM, transcoding, adaptive bitrate or email verification. Authentication has API request throttling but no dedicated per account abuse protection. Signed video URLs act as temporary bearer links and can be shared until expiry. Reload a film to get a fresh URL after one hour. Full source is included; no real film files are bundled.

AWS usage can incur storage, API, database, compute and data transfer charges. Use a budget alert and delete the stack after the demonstration. See deployment instructions for cleanup. The local server is for development on your own computer.

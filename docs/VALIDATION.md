# Validation record

Verified on 24 October 2026 using Python 3.12 and Node.js 24.

* All 27 backend regression tests passed, including explicit UTF-8 loading under a simulated Windows default encoding.
* HTTP integration checks passed against the actual local HTTP server: frontend assets, registration, sign in, account cookie, first watchlist save, first progress save, persistent state read, playable URL, prefix and suffix byte ranges, sign out and rejection of anonymous media requests.
* JavaScript syntax checked with node --check frontend/app.js.
* Generated CloudFormation YAML parsed successfully. Embedded Lambda Python source compiled and served its embedded HTML, CSS, JavaScript and SVG without relying on source files being present in the Lambda package.
* Generated template is below the 51200 byte direct request limit. scripts/build.py enforces this limit.
* Included video inspected with ffprobe: H.264 video, AAC audio, 640 by 360, 24 seconds.

The template has not been deployed to a live AWS account in this run. AWS IAM permissions, resource creation and playback from S3 still need verification after deployment. A browser visual and interaction pass could not be completed because the remote browser could not reach the local development server. Responsive styles and frontend actions are implemented but should be checked in your browser using the demonstration steps in AWS_DEPLOYMENT.md.

No AWS credentials, real user database, session cookies or generated test accounts are included in the ZIP.

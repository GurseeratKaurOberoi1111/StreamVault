# API reference

All requests use the same origin as the website. POST bodies must be JSON objects with Content-Type application/json. Cross origin mutations are rejected. Session cookies are HttpOnly and SameSite=Lax; AWS additionally uses Secure. There is no frontend secret or AWS access key.

| Method | Path | Authentication | Input or result |
| --- | --- | --- | --- |
| GET | /api/health | Public | Service and adapter name |
| GET | /api/catalog | Public | titles array |
| GET | /api/me | Optional | user string or null |
| POST | /api/register | Public | username, password; creates account |
| POST | /api/login | Public | username, password; creates session cookie |
| POST | /api/logout | Optional | Empty object; revokes current session |
| GET | /api/library | Required | library and progress objects keyed by title ID |
| POST | /api/library | Required | id, saved boolean |
| POST | /api/progress | Required | id, seconds number from 0 through 100000 |
| GET | /api/play/{id} | Required | url, expiresIn; returns 404 for unavailable media |

Usernames contain 3 to 32 ASCII letters, numbers or underscores and are normalized to lowercase. Passwords have 8 to 128 characters. Stored password digests use PBKDF2 HMAC SHA256 with random 16 byte salt and 600000 iterations. Session tokens are random 32 byte values; only their SHA256 digests are stored. Sessions expire after seven days and logout deletes the current session. Session expiry is enforced during every authenticated request even before asynchronous DynamoDB TTL deletion occurs.

DynamoDB has a string partition key named pk. User items use user#username; session items use session#digest; saved state uses state#username#title#saved; progress uses state#username#title#progress. A fixed six title catalogue allows direct GetItem calls without table scans. Each state entry is independently written so the first save works and unrelated title updates do not overwrite one another.

The local server has an authenticated /media/{id}.mp4 endpoint with HTTP byte ranges. AWS instead signs private S3 objects for one hour; video bytes do not pass through Lambda or API Gateway.

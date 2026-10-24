# Deploy StreamVault on AWS

## 1. Create the stack

1. Extract the project ZIP first. Do not upload the ZIP to CloudFormation.
2. Sign in to AWS Console. Select **Asia Pacific (Mumbai), ap-south-1** if this is your chosen project region.
3. Open **CloudFormation → Stacks → Create stack → With new resources (standard)**.
4. Choose **Upload a template file**, select the root `template.yaml`, and continue.
5. Use a stack name such as `streamvault-demo`. No parameters or API keys are needed.
6. Continue through the options. Acknowledge creation of IAM resources and submit.
7. Wait for the whole stack to reach **CREATE_COMPLETE**. If it fails, inspect the earliest failed resource in **Events**.
8. Open **Outputs**. Record **WebsiteURL**, **MediaBucketName**, **TableName** and **FunctionName**.
9. Open WebsiteURL in your browser. The home page should show six films. Create an account and sign in.

CloudFront is not used. API Gateway provides the HTTPS website entry point and forwards both page and API requests to Lambda.

## 2. Enable the included playback test

1. Open **S3** and select the bucket matching **MediaBucketName**.
2. Create a folder named `videos`.
3. Open that folder, choose **Upload**, and select the included `media/sintel.mp4` file.
4. Complete the upload. Its exact object key must be `videos/sintel.mp4`.
5. Leave public access blocked. Do not add a public bucket policy.
6. Return to StreamVault, sign in and click **Watch Sintel**. The synthetic test clip should play.

Optional CLI alternative, after installing and configuring AWS CLI:

```bash
python scripts/upload_demo.py YOUR_MEDIA_BUCKET_NAME
```

## 3. Add actual films

Use MP4 files that you are authorized to host. Recommended encoding is H.264 video with AAC audio, with MP4 metadata at the beginning of the file for prompt playback. The included synthetic clip can be replaced with actual licensed Sintel media. Check the film licence and attribution requirements before distribution.

| Catalogue entry | Exact S3 key | Local file path |
| --- | --- | --- |
| Big Buck Bunny | videos/bigbuckbunny.mp4 | media/bigbuckbunny.mp4 |
| Sintel | videos/sintel.mp4 | media/sintel.mp4 |
| Tears of Steel | videos/tearsofsteel.mp4 | media/tearsofsteel.mp4 |
| Elephants Dream | videos/elephantsdream.mp4 | media/elephantsdream.mp4 |
| Cosmos Laundromat | videos/cosmoslaundromat.mp4 | media/cosmoslaundromat.mp4 |
| Spring | videos/spring.mp4 | media/spring.mp4 |

The illustrations are original abstract artwork made for this project, not official posters. The film names and descriptions are catalogue examples, not a claim that actual film media is included.

## 4. Demonstrate the project

1. Show the website home page, search and genre filter.
2. Register an account and add Sintel to My List.
3. Open My List, reload and show that it persists.
4. Play the synthetic clip for about 10 seconds, then close it.
5. Open Continue Watching and resume the clip.
6. Sign out and sign back in to show persistence.
7. In DynamoDB, open the table from Outputs and explore items: user, hashed session and per film state. Never expose password hashes or session records in public screenshots.
8. Show the private `videos/sintel.mp4` S3 object and the Lambda/API Gateway resources.

## 5. Update after source changes

Run `python scripts/build.py`. In CloudFormation select the existing stack, choose **Update stack**, replace the template with the rebuilt `template.yaml`, review the change set and submit. Wait for **UPDATE_COMPLETE**. Existing accounts and lists persist when the table is not replaced. Local SQLite accounts and video files do not automatically migrate to AWS.

## Troubleshooting

* Website loads but video is unavailable: verify the exact bucket and object key, then reopen the film.
* Player opens but cannot decode media: use H.264/AAC MP4. A `.mp4` extension alone does not guarantee browser support.
* Playback stops after leaving a tab open for a long time: close and reopen the film to renew the signed URL.
* Cookies fail: use the exact HTTPS WebsiteURL from Outputs. Do not open index.html directly from disk.
* Server error: check the Lambda CloudWatch logs for FunctionName. The client intentionally does not expose internal details.
* Stack rollback: review CloudFormation Events for permission, quota or organization policy errors. API Gateway does not bypass account or organization restrictions on other AWS services.
* A throttling response: wait and retry; this demo limits API traffic to 10 requests per second with a burst of 20, subject to API Gateway's best effort throttling.

## Costs and cleanup

Set an AWS Budget alert before leaving this deployed. This project makes no free usage guarantee.

To remove it, empty the media bucket first, then delete the CloudFormation stack. Verify DELETE_COMPLETE. CloudWatch log groups created by Lambda may remain; remove the project's log group separately if you no longer need it. Download any state or media you want to retain before deleting resources.

## AWS references

* HTTP API Lambda integration and cookies: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html
* Inline Lambda function source: https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-properties-lambda-function-code.html
* DynamoDB session cleanup with TTL: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html
* CloudFormation template limits: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-limits.html
* Runtime SDK packaging: https://docs.aws.amazon.com/lambda/latest/dg/python-package.html

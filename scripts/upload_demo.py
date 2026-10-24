import argparse
import subprocess
from pathlib import Path
parser=argparse.ArgumentParser(description='Upload the synthetic playback test to the private media bucket using your configured AWS CLI.')
parser.add_argument('bucket',help='MediaBucketName from CloudFormation Outputs')
args=parser.parse_args()
file=Path(__file__).resolve().parents[1]/'media/sintel.mp4'
if not args.bucket or '/' in args.bucket or args.bucket.startswith('-'):
    parser.error('Supply just the S3 bucket name')
subprocess.run(['aws','s3','cp',str(file),'s3://'+args.bucket+'/videos/sintel.mp4','--content-type','video/mp4'],check=True)

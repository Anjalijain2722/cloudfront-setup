import boto3
import json
from botocore.exceptions import ClientError
def ensure_bucket(session, bucket_name, region):
    s3 = session.client('s3')
    account_id = session.client('sts').get_caller_identity()['Account']
    try:
        # Check if the bucket exists and is accessible
        s3.head_bucket(Bucket=bucket_name)
        print("Bucket already exists and is accessible.")
    except ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 403:
            raise Exception(f"Bucket '{bucket_name}' exists but is not accessible. Try a different bucket name.")
        elif error_code == 404:
            print("Bucket does not exist. Creating...")
            # Create bucket
            if region == "us-east-1":
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            print("Bucket created.")
            # Enable Object Writer (allows ACLs) for CloudFront logging
            s3.put_bucket_ownership_controls(
                Bucket=bucket_name,
                OwnershipControls={
                    'Rules': [
                        {
                            'ObjectOwnership': 'ObjectWriter'
                        },
                    ]
                }
            )
            print("S3 bucket Object Ownership set to 'Object Writer' (ACLs enabled).")
            # (Optional) Set ACL for log delivery
            s3.put_bucket_acl(Bucket=bucket_name, ACL='log-delivery-write')
            print("ACL 'log-delivery-write' applied to bucket.")
            # Add a bucket policy that allows CloudFront to write logs
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AllowCloudFrontServicePrincipal",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "cloudfront.amazonaws.com"
                        },
                        "Action": "s3:PutObject",
                        "Resource": f"arn:aws:s3:::{bucket_name}/*",
                        "Condition": {
                            "StringEquals": {
                                "AWS:SourceAccount": account_id
                            }
                        }
                    }
                ]
            }
            s3.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(policy)
            )
            print("Bucket policy added to allow CloudFront logging.")
        else:
            raise
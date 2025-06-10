from botocore.exceptions import ClientError

def ensure_bucket(session, bucket_name, region):
    s3 = session.client('s3')
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' already exists.")
    except ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            print(f"Bucket '{bucket_name}' does not exist. Creating...")
            if region == "us-east-1":
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            print("Bucket created.")
            s3.put_bucket_acl(Bucket=bucket_name, ACL='log-delivery-write')
        else:
            raise

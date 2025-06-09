import boto3
import botocore
import sys
print("Python executable:", sys.executable)
print("boto3 version:", boto3.__version__)
print("boto3 path:", boto3.__file__)
print("botocore version:", botocore.__version__)
print("botocore path:", botocore.__file__)

def select_distribution(session):
    cf = session.client('cloudfront')
    response = cf.list_distributions()
    dists = response.get('DistributionList', {}).get('Items', [])
    for idx, dist in enumerate(dists):
        print(f"[{idx}] {dist['Id']} - {dist['DomainName']}")
    choice = int(input("Select distribution by index: "))
    return dists[choice]['Id']

def enable_logging(session, distribution_id, bucket_name):
    client = session.client("cloudfront")
    dist_config = client.get_distribution_config(Id=distribution_id)
    config = dist_config["DistributionConfig"]
    etag = dist_config["ETag"]
    config["Logging"] = {
        "Enabled": True,
        "IncludeCookies": False,
        "Bucket": f"{bucket_name}.s3.amazonaws.com",
        "Prefix": "cloudfront-logs/"
        # No LogBucketOwnerFullControl here
    }
    response = client.update_distribution(
        Id=distribution_id,
        IfMatch=etag,
        DistributionConfig=config
    )
    print("Logging enabled on CloudFront distribution.")
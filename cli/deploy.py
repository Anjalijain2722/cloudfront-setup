import sys
import os
import time   # <-- import time for sleep

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli.utils import get_boto3_session, render_template, apply_terraform
from cli.cloudfront import select_distribution, enable_logging
from cli.s3 import ensure_bucket
from cli.ec2 import render_and_apply_terraform


def main():
    region = input("Enter AWS Region: ")
    session = get_boto3_session(region)
    log_dest = input("Where do you want to store logs (s3/cloudwatch/kinesis): ").strip()
    key_name = input("Enter EC2 Key Pair name: ")
    instance_type = input("Enter EC2 instance type [default: t3.medium]: ") or "t3.medium"

    distribution_id = select_distribution(session)
    bucket_name = input("Enter name for log bucket: ")
    ensure_bucket(session, bucket_name, region)

    time.sleep(5)  # <-- add delay here to ensure bucket is ready

    enable_logging(session, distribution_id, bucket_name)

    ami_id = "ami-0c02fb55956c7d316"  # Ubuntu 22.04 LTS for example (us-east-1)
    origin_domain = input("Enter S3 origin domain (e.g. bucket.s3.amazonaws.com): ")

    render_template("main.tf.j2", "../terraform/main.tf", locals())
    render_template("../templates/s3_logging.tf.j2", "../terraform/s3.tf", locals())
    render_template("../templates/ec2_opensearch.tf.j2", "../terraform/ec2.tf", locals())
    render_template("../templates/cloudfront_logging.tf.j2", "../terraform/cloudfront.tf", locals())

    apply_terraform("../terraform", bucket_name)


if __name__ == "__main__":
    main()

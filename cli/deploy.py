import sys
import os

# Add terraform directory to sys.path dynamically
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'terraform')))

from utils import get_boto3_session, ask_input, render_and_apply_terraform
from ec2 import (
    launch_ec2,
    get_existing_instance_dns, # This function needs the region string, not the session object
    setup_instance,
)
from ec2 import is_nginx_installed
from ec2 import install_nginx
from ec2 import install_opensearch_stack
# REMOVE THIS LINE: from cloudfront import create_distribution
from s3 import ensure_bucket

def main():
    region = ask_input("Enter AWS Region: ")
    session = get_boto3_session(region) # session object is correctly created here

    key_name = ask_input("Enter EC2 Key Pair name: ")
    key_path = ask_input("Enter full path to your private key file (e.g. /home/anjali/.ssh/data.pem): ")
    instance_type = ask_input("Enter EC2 instance type [default: t3.medium]: ", default="t3.medium")

    use_existing_ec2_input = ask_input("Use existing EC2 instance? (y/n): ").lower()
    use_existing_ec2 = use_existing_ec2_input == 'y'

    if use_existing_ec2:
        instance_id = ask_input("Enter existing EC2 Instance ID: ")
        # --- FIX IS HERE ---
        # Pass the 'region' string directly, as get_existing_instance_dns expects a region string
        ec2_dns = get_existing_instance_dns(region, instance_id)
        # --- END FIX ---
    else:
        instance_id, ec2_dns = launch_ec2(region, key_name, instance_type)
        print(f"Launched new EC2: {ec2_dns}")

    print(f"Using EC2 DNS: {ec2_dns}")

    use_existing_distribution_input = ask_input("Use existing CloudFront distribution? (y/n): ").lower()
    use_existing_distribution = use_existing_distribution_input == 'y'
    distribution_id_input = None

    if use_existing_distribution:
        distribution_id_input = ask_input("Enter existing CloudFront Distribution ID: ")
        print(f"Using existing CloudFront Distribution ID: {distribution_id_input}")
    else:
        print("Terraform will create a new CloudFront Distribution.")

    use_existing_bucket = ask_input("Use existing S3 bucket? (y/n): ").lower() == 'y'
    if use_existing_bucket:
        bucket_name = ask_input("Enter existing bucket name: ")
    else:
        bucket_name = ask_input("Enter new bucket name: ")
        ensure_bucket(session, bucket_name, region)

    print("Logging enabled on CloudFront distribution.")

    terraform_outputs = render_and_apply_terraform(
        region=region,
        bucket_name=bucket_name,
        key_name=key_name,
        ami_id="ami-09d56f8956ab235b3",
        instance_type=instance_type,
        ec2_instance_id=instance_id,
        use_existing_instance=use_existing_ec2,
        use_existing_cloudfront=use_existing_distribution,
        existing_cloudfront_id=distribution_id_input,
        origin_domain=ec2_dns
    )

    cloudfront_distribution_id = terraform_outputs.get('cloudfront_distribution_id', 'N/A')
    print(f"Final CloudFront Distribution ID: {cloudfront_distribution_id}")

    if not is_nginx_installed(ec2_dns, key_path):
        install_nginx(ec2_dns, key_path)

    install_opensearch_stack(ec2_dns, key_path)

    print(f"\nOpenSearch Dashboard should be available at: http://{ec2_dns}:5601")
    print(f"CloudFront URL (may take time to propagate): https://{cloudfront_distribution_id}.cloudfront.net")

if __name__ == "__main__":
    main()

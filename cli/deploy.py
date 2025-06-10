import sys
import os

# Add terraform directory to sys.path dynamically (adjust path as needed)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'terraform')))

from utils import get_boto3_session, ask_input, render_and_apply_terraform
from ec2 import get_existing_instance_dns, is_nginx_installed, install_nginx, install_opensearch_stack
from cloudfront import create_distribution
from s3 import ensure_bucket

def main():
    region = ask_input("Enter AWS Region: ")
    session = get_boto3_session(region)

    key_name = ask_input("Enter EC2 Key Pair name: ")
    key_path = ask_input("Enter full path to your private key file (e.g. /home/anjali/.ssh/data.pem): ")
    instance_type = ask_input("Enter EC2 instance type [default: t3.medium]: ", default="t3.medium")

    use_existing_ec2_input = ask_input("Use existing EC2 instance? (y/n): ").lower()
    use_existing_ec2 = use_existing_ec2_input == 'y'

    if use_existing_ec2:
        instance_id = ask_input("Enter existing EC2 Instance ID: ")
    else:
        print("Launching new EC2 not supported in current flow.")
        return

    ec2_dns = get_existing_instance_dns(session, instance_id)
    print(f"Using existing EC2 DNS: {ec2_dns}")

    use_existing_distribution = ask_input("Use existing CloudFront distribution? (y/n): ").lower() == 'y'
    if use_existing_distribution:
        distribution_id = ask_input("Enter existing CloudFront Distribution ID: ")
    else:
        distribution_id = create_distribution(session, ec2_dns)
        print(f"New CloudFront Distribution created: {distribution_id}")

    use_existing_bucket = ask_input("Use existing S3 bucket? (y/n): ").lower() == 'y'
    if use_existing_bucket:
        bucket_name = ask_input("Enter existing bucket name: ")
    else:
        bucket_name = ask_input("Enter new bucket name: ")
        ensure_bucket(session, bucket_name, region)

    print("Logging enabled on CloudFront distribution.")

    # Pass the actual boolean, not a hardcoded True
    render_and_apply_terraform(
        region=region,
        bucket_name=bucket_name,
        key_name=key_name,
        ami_id="ami-09d56f8956ab235b3",  # Example Ubuntu AMI
        instance_type=instance_type,
        ec2_instance_id=instance_id,
        use_existing_instance=use_existing_ec2,  # <-- Use actual boolean here
        cloudfront_distribution_id=distribution_id
    )

    # Now use the key_path input consistently for SSH commands
    if not is_nginx_installed(ec2_dns, key_path):
       install_nginx(ec2_dns, key_path)

    install_opensearch_stack(ec2_dns, key_path)

    print(f"\nOpenSearch Dashboard should be available at: http://{ec2_dns}:5601")

if __name__ == "__main__":
    main()

# /home/anjali/cloudfront-opensearch-automation/cli/utils.py

import os
import subprocess
import json # Import json to parse Terraform outputs
import sys

def get_boto3_session(region):
    # ... (your existing get_boto3_session code) ...
    import boto3
    return boto3.Session(region_name=region)

def ask_input(prompt, default=None):
    # ... (your existing ask_input code) ...
    if default:
        return input(f"{prompt} [default: {default}]: ") or default
    return input(f"{prompt}: ")

def render_and_apply_terraform(
    region,
    bucket_name,
    key_name,
    ami_id,
    instance_type,
    ec2_instance_id,
    use_existing_instance,
    use_existing_cloudfront, # New parameter
    existing_cloudfront_id,   # New parameter
    origin_domain             # New parameter
):
    print("Initializing the backend...")
    # Navigate to the terraform directory
    terraform_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'terraform'))
    os.chdir(terraform_dir)

    try:
        # 1. Initialize Terraform
        subprocess.run(["terraform", "init"], check=True)

        # 2. Prepare variables for Terraform
        tf_vars = {
            "region": region,
            "bucket_name": bucket_name,
            "key_name": key_name,
            "ami_id": ami_id,
            "instance_type": instance_type,
            "existing_instance_id": ec2_instance_id if use_existing_instance else "", # Pass empty string if new
            "use_existing_instance": "true" if use_existing_instance else "false",
            "log_bucket_name": bucket_name, # Assuming bucket_name is also the log_bucket_name
            "use_existing_cloudfront": "true" if use_existing_cloudfront else "false", # Pass as string
            "existing_cloudfront_id": existing_cloudfront_id if existing_cloudfront_id else "", # Pass as string
            "origin_domain": origin_domain # Pass the EC2 DNS as the origin
        }

        # Construct -var arguments
        var_args = [f"-var={key}={value}" for key, value in tf_vars.items()]

        # 3. Apply Terraform changes
        print("\nApplying Terraform configuration...")
        apply_command = ["terraform", "apply", "-auto-approve"] + var_args
        subprocess.run(apply_command, check=True)

        # 4. Get Terraform outputs
        print("\nRetrieving Terraform outputs...")
        output_command = ["terraform", "output", "-json"]
        output_result = subprocess.run(output_command, capture_output=True, text=True, check=True)
        outputs = json.loads(output_result.stdout)

        # Extract values from outputs for convenience
        cleaned_outputs = {}
        for key, value in outputs.items():
            cleaned_outputs[key] = value['value']

        return cleaned_outputs

    except subprocess.CalledProcessError as e:
        print(f"Terraform command failed: {e}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)
    finally:
        # Navigate back to the original directory (cli)
        os.chdir(os.path.dirname(__file__))
import os
import time
import paramiko
from scp import SCPClient
import boto3

# Define the directory where Docker Compose and installation scripts are located
FILES_DIR = os.path.join(os.path.dirname(__file__), "../files")

def get_ec2_client(region):
    """
    Returns a boto3 EC2 client for the specified region.
    """
    return boto3.client("ec2", region_name=region)

def launch_ec2(region, key_name, instance_type):
    """
    Launches an EC2 instance with a security group configured for OpenSearch and NGINX.

    Args:
        region (str): The AWS region to launch the instance in.
        key_name (str): The name of the EC2 key pair to use.
        instance_type (str): The desired EC2 instance type (e.g., 't2.micro').

    Returns:
        tuple: A tuple containing the instance ID and its public DNS name.
    """
    ec2 = boto3.resource('ec2', region_name=region)
    client = get_ec2_client(region)

    # Get the default VPC ID
    # This assumes there's at least one VPC. In a complex environment, you might
    # want to explicitly select a VPC.
    try:
        vpcs = client.describe_vpcs()['Vpcs']
        if not vpcs:
            raise Exception("No VPC found in the region. Please ensure a default VPC exists or specify one.")
        vpc_id = vpcs[0]['VpcId']
    except Exception as e:
        print(f"Error getting VPC ID: {e}")
        raise

    # Create a security group for OpenSearch and NGINX
    sg_id = None
    try:
        sg = client.create_security_group(
            GroupName='opensearch-sg',
            Description='Allow SSH, OpenSearch, Dashboard, and NGINX',
            VpcId=vpc_id
        )
        sg_id = sg['GroupId']

        # Authorize ingress rules
        client.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=[
            {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}, # SSH (for management)
            {'IpProtocol': 'tcp', 'FromPort': 9200, 'ToPort': 9200, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}, # OpenSearch HTTP
            {'IpProtocol': 'tcp', 'FromPort': 5601, 'ToPort': 5601, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}, # OpenSearch Dashboard (Kibana)
            {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}, # HTTP/NGINX (for CloudFront origin)
        ])
        print(f"Security Group 'opensearch-sg' created with ID: {sg_id}")
    except client.exceptions.ClientError as e:
        if "AlreadyExists" in str(e):
            print("Security Group 'opensearch-sg' already exists. Reusing it.")
            sg_id = client.describe_security_groups(GroupNames=['opensearch-sg'])['SecurityGroups'][0]['GroupId']
        else:
            raise e

    # Launch the EC2 instance
    # ami-084568db4383264d4 is a specific Ubuntu Server 20.04 LTS AMI.
    # Ensure this AMI ID is valid for your chosen AWS region.
    instances = ec2.create_instances(
        ImageId='ami-084568db4383264d4',
        InstanceType=instance_type,
        KeyName=key_name,
        MinCount=1,
        MaxCount=1,
        SecurityGroupIds=[sg_id],
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': 'OpenSearch-Instance'}]
        }]
    )

    instance = instances[0]
    print(f"Launching EC2 instance with ID: {instance.id}...")
    instance.wait_until_running() # Wait for the instance to enter 'running' state
    instance.load() # Reload instance attributes to get public_dns_name etc.
    print(f"EC2 instance {instance.id} is running.")
    return instance.id, instance.public_dns_name

def get_existing_instance_dns(region, instance_id):
    """
    Retrieves the public DNS name or public IP address of an existing EC2 instance.

    Args:
        region (str): The AWS region where the instance is located.
        instance_id (str): The ID of the EC2 instance.

    Returns:
        str: The public DNS name or public IP address of the instance.
    """
    ec2 = boto3.client('ec2', region_name=region)
    try:
        # Describe instances to get details for the specified ID
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        # Prefer PublicDnsName, fall back to PublicIpAddress if DNS is not available
        return instance.get('PublicDnsName') or instance.get('PublicIpAddress')
    except Exception as e:
        print(f"Error getting instance DNS for {instance_id}: {e}")
        return None

def connect_ssh(hostname, key_path, username='ubuntu', max_attempts=10, delay=10):
    """
    Establishes an SSH connection to the given hostname. Retries on failure.

    Args:
        hostname (str): The hostname or IP address to connect to.
        key_path (str): The path to the SSH private key file.
        username (str): The username for the SSH connection. Defaults to 'ubuntu'.
        max_attempts (int): Maximum number of connection attempts.
        delay (int): Delay in seconds between attempts.

    Returns:
        paramiko.SSHClient: An active SSH client object.
    Raises:
        Exception: If SSH connection fails after max_attempts.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Automatically add host keys

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Attempt {attempt}/{max_attempts}: Connecting to {hostname} via SSH...")
            ssh.connect(hostname, username=username, key_filename=key_path)
            print("SSH connection established.")
            return ssh
        except (paramiko.BadHostKeyException, paramiko.AuthenticationException,
                paramiko.SSHException, paramiko.buffered_pipe.PipeTimeout,
                EOFError) as e:
            print(f"SSH connection failed (attempt {attempt}): {e}")
            if attempt < max_attempts:
                print(f"Waiting {delay} seconds before retrying...")
                time.sleep(delay)
            else:
                # Raise an exception if all attempts fail
                raise Exception(f"Failed to establish SSH connection to {hostname} after {max_attempts} attempts.")

def run_commands(ssh_client, commands):
    """
    Executes a list of shell commands on the remote server via SSH.

    Args:
        ssh_client (paramiko.SSHClient): The active SSH client.
        commands (list): A list of shell commands to execute.

    Raises:
        Exception: If any command fails to execute successfully.
    """
    for cmd in commands:
        print(f"Running command: {cmd}")
        # Use get_transport().open_session() for better handling of stderr
        channel = ssh_client.get_transport().open_session()
        channel.exec_command(cmd)
        
        # Read stdout and stderr
        stdout = channel.makefile('rb', -1)
        stderr = channel.makefile_stderr('rb', -1)
        
        output = stdout.read().decode('utf-8').strip()
        error_output = stderr.read().decode('utf-8').strip()
        
        exit_status = channel.recv_exit_status() # Get the exit status

        if exit_status != 0:
            raise Exception(f"Command '{cmd}' failed with exit status {exit_status}:\n{error_output}")
        if output:
            print(f"Output: {output}")

# --- START OF MODIFIED FUNCTIONS TO FIX NameError ---

def is_nginx_installed(ec2_dns, key_path):
    """
    Checks if NGINX is installed on the remote server by establishing an SSH connection
    and executing 'nginx -v'.

    Args:
        ec2_dns (str): The public DNS name of the EC2 instance.
        key_path (str): The full path to the private key file (.pem) for SSH access.

    Returns:
        bool: True if NGINX is installed, False otherwise.
    """
    print(f"Checking if NGINX is installed on {ec2_dns}...")
    ssh_client = None # Initialize to None for robust error handling
    try:
        # Establish SSH connection
        ssh_client = connect_ssh(ec2_dns, key_path)

        # Execute the command to check NGINX version
        # 'nginx -v' typically prints version info to stderr, not stdout
        stdin, stdout, stderr = ssh_client.exec_command("nginx -v")
        error_output = stderr.read().decode().strip() # Read stderr for version info
        
        exit_status = stdout.channel.recv_exit_status() # Get the exit status

        # Check if the command exited successfully (status 0) AND if NGINX version string is found
        if exit_status == 0 and "nginx version:" in error_output.lower():
            print("NGINX is already installed.")
            return True
        else:
            print("NGINX is not installed.")
            # Optional: print more details for debugging
            # print(f"Nginx check output (stderr): {error_output}")
            # print(f"Nginx check exit status: {exit_status}")
            return False

    except Exception as e:
        print(f"An error occurred while checking NGINX installation: {e}")
        return False
    finally:
        if ssh_client and ssh_client.get_transport() and ssh_client.get_transport().is_active():
            ssh_client.close()
            print("SSH connection closed after NGINX check.")


def install_nginx(ec2_dns, key_path):
    """
    Installs and starts NGINX on the remote server by establishing an SSH connection.

    Args:
        ec2_dns (str): The public DNS name of the EC2 instance.
        key_path (str): The full path to the private key file (.pem) for SSH access.
    """
    print(f"Installing NGINX on {ec2_dns}...")
    ssh_client = None
    try:
        ssh_client = connect_ssh(ec2_dns, key_path)
        commands = [
            "sudo apt update",
            "sudo apt install -y nginx",
            "sudo systemctl enable nginx",
            "sudo systemctl start nginx"
        ]
        run_commands(ssh_client, commands)
        print("NGINX installed and started successfully.")
    except Exception as e:
        print(f"Failed to install NGINX: {e}")
        raise # Re-raise to signal failure to the caller
    finally:
        if ssh_client and ssh_client.get_transport() and ssh_client.get_transport().is_active():
            ssh_client.close()
            print("SSH connection closed after NGINX installation.")

def install_opensearch_stack(ec2_dns, key_path):
    """
    Uploads OpenSearch installation files and executes the installation script
    on the remote server by establishing an SSH connection.

    Args:
        ec2_dns (str): The public DNS name of the EC2 instance.
        key_path (str): The full path to the private key file (.pem) for SSH access.
    """
    print(f"Uploading OpenSearch installation files to {ec2_dns}...")
    ssh_client = None
    try:
        ssh_client = connect_ssh(ec2_dns, key_path)

        # Use SCPClient for file transfer
        with SCPClient(ssh_client.get_transport()) as scp:
            local_docker_compose_path = os.path.join(FILES_DIR, "docker-compose.yml")
            local_install_script_path = os.path.join(FILES_DIR, "opensearch_install.sh")
            
            # Check if files exist locally before attempting to upload
            if not os.path.exists(local_docker_compose_path):
                raise FileNotFoundError(f"Missing docker-compose.yml at: {local_docker_compose_path}")
            if not os.path.exists(local_install_script_path):
                raise FileNotFoundError(f"Missing opensearch_install.sh at: {local_install_script_path}")

            scp.put(local_docker_compose_path, "/home/ubuntu/docker-compose.yml")
            scp.put(local_install_script_path, "/home/ubuntu/opensearch_install.sh")
        print("OpenSearch installation files uploaded.")

        print("Running OpenSearch installation script...")
        commands = [
            "chmod +x /home/ubuntu/opensearch_install.sh",
            "sudo /home/ubuntu/opensearch_install.sh"
        ]
        run_commands(ssh_client, commands)
        print("OpenSearch stack installation initiated.")
    except Exception as e:
        print(f"Failed to install OpenSearch stack: {e}")
        raise # Re-raise to signal failure to the caller
    finally:
        if ssh_client and ssh_client.get_transport() and ssh_client.get_transport().is_active():
            ssh_client.close()
            print("SSH connection closed after OpenSearch installation.")

def setup_instance(hostname, key_path):
    """
    Sets up the EC2 instance by installing necessary software (NGINX, OpenSearch).
    This function now uses the new versions of is_nginx_installed, install_nginx,
    and install_opensearch_stack which handle their own SSH connections.

    Args:
        hostname (str): The public DNS name or IP address of the EC2 instance.
        key_path (str): The path to the SSH private key file.
    """
    print(f"Setting up instance at {hostname}...")
    try:
        # These functions now establish and close their own SSH connections
        if not is_nginx_installed(hostname, key_path):
            install_nginx(hostname, key_path)
        else:
            print("NGINX is already installed. Skipping installation.")

        install_opensearch_stack(hostname, key_path)

        print("Instance setup complete.")
    except Exception as e:
        print(f"An error occurred during instance setup: {e}")
        raise # Re-raise the exception to indicate failure in main script


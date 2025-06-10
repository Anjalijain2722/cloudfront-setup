import paramiko
import os

def get_existing_instance_dns(session, instance_id):
    ec2 = session.client('ec2')
    reservations = ec2.describe_instances(InstanceIds=[instance_id])['Reservations']
    if not reservations:
        raise Exception(f"No instance found with ID {instance_id}")
    instance = reservations[0]['Instances'][0]
    return instance.get('PublicDnsName') or instance.get('PublicIpAddress')

def is_nginx_installed(hostname, key_name):
    key_path = os.path.expanduser(key_name)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username="ubuntu", key_filename=key_path)
    stdin, stdout, stderr = ssh.exec_command("nginx -v")
    output = stdout.read().decode() + stderr.read().decode()
    ssh.close()
    return "nginx version" in output.lower()

def install_nginx(hostname, key_name):
    key_path = os.path.expanduser(key_name)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username="ubuntu", key_filename=key_path)
    cmds = [
        "sudo apt-get update",
        "sudo apt-get install -y nginx",
        "sudo systemctl start nginx",
        "sudo systemctl enable nginx"
    ]
    for cmd in cmds:
        ssh.exec_command(cmd)
    ssh.close()

def install_opensearch_stack(hostname, key_name):
    key_path = os.path.expanduser(key_name)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username="ubuntu", key_filename=key_path)
    cmds = [
        # Install Docker
        "sudo apt-get update",
        "sudo apt-get install -y docker.io docker-compose",
        # Pull and run OpenSearch & Dashboards
        "sudo docker pull opensearchproject/opensearch:latest",
        "sudo docker pull opensearchproject/opensearch-dashboards:latest",
        "sudo docker network create opensearch-net || true",
        # Run OpenSearch container
        "sudo docker run -d --name opensearch-node1 --network opensearch-net -p 9200:9200 -p 9600:9600 -e discovery.type=single-node opensearchproject/opensearch:latest",
        # Run Dashboards container
        "sudo docker run -d --name opensearch-dashboards --network opensearch-net -p 5601:5601 opensearchproject/opensearch-dashboards:latest"
    ]
    for cmd in cmds:
        ssh.exec_command(cmd)
    ssh.close()

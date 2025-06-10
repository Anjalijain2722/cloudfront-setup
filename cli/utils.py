import boto3
import subprocess
import os
from jinja2 import Environment, FileSystemLoader

def get_boto3_session(region=None):
    # Ideally, use environment variables or IAM role, hardcoded keys are insecure.
    return boto3.Session(region_name=region)

def ask_input(prompt, default=None):
    val = input(prompt)
    if not val and default:
        return default
    return val

def render_and_apply_terraform(**kwargs):
    # Assumes you have terraform config templates in ../terraform/templates/
    env = Environment(loader=FileSystemLoader('../templates'))
    
    # Render your main.tf or variables.tf as needed here
    # For example:
    template = env.get_template('main.tf.j2')
    rendered = template.render(kwargs)

    tf_dir = os.path.abspath('../terraform')
    tf_file_path = os.path.join(tf_dir, 'main.tf')
    
    with open(tf_file_path, 'w') as f:
        f.write(rendered)

    # Set AWS env variables (or rely on boto3 config)
    env_vars = os.environ.copy()
    env_vars["AWS_DEFAULT_REGION"] = kwargs.get('region', 'us-east-1')

    # Run terraform init & apply
    subprocess.run(["terraform", "init"], cwd=tf_dir, check=True, env=env_vars)
    subprocess.run(["terraform", "apply", "-auto-approve"], cwd=tf_dir, check=True, env=env_vars)

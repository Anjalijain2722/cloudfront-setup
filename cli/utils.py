import boto3
import subprocess
import os
from jinja2 import Environment, FileSystemLoader


def get_boto3_session(region=None):
   return boto3.Session(
       aws_access_key_id='',
       aws_secret_access_key='',
       region_name=region
   ) if region else boto3.Session(
       aws_access_key_id='',
       aws_secret_access_key=''
   )


def render_template(template_path, output_path, context):
   env = Environment(loader=FileSystemLoader(searchpath="../templates"))
   template = env.get_template(os.path.basename(template_path))
   rendered = template.render(context)
   with open(output_path, "w") as f:
       f.write(rendered)


def apply_terraform(directory, bucket_name=None):
   env = os.environ.copy()
   env["AWS_ACCESS_KEY_ID"] = ""
   env["AWS_SECRET_ACCESS_KEY"] = ""
   env["AWS_DEFAULT_REGION"] = "us-east-1"


   if bucket_name:
       env["TF_VAR_log_bucket"] = bucket_name


   try:
       subprocess.run(["terraform", "init"], cwd=directory, check=True, env=env)
       subprocess.run(["terraform", "apply", "-auto-approve"], cwd=directory, check=True, env=env)
   except subprocess.CalledProcessError as e:
       print("\nTerraform apply failed:")
       print(e.stdout)
       print(e.stderr)

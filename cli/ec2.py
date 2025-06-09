import os
from jinja2 import Environment, FileSystemLoader

def render_and_apply_terraform(region, bucket_name, key_name, ami_id, instance_type, origin_domain):
    env = Environment(loader=FileSystemLoader("templates"))
    
    variables = {
        "region": region,
        "bucket_name": bucket_name,
        "key_name": key_name,
        "ami_id": ami_id,
        "instance_type": instance_type,
        "origin_domain": origin_domain
    }

    for file in ["main.tf.j2", "s3_logging.tf.j2", "ec2_opensearch.tf.j2", "cloudfront_logging.tf.j2"]:
        template = env.get_template(file)
        output = template.render(**variables)
        with open(f"terraform/{file[:-3]}", "w") as f:
            f.write(output)

    os.chdir("terraform")
    os.system("terraform init")
    os.system("terraform apply -auto-approve")
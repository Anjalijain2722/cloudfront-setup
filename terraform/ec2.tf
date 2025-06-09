resource "aws_instance" "opensearch" {
  ami           = "ami-0c02fb55956c7d316"
  instance_type = "t3.medium"
  key_name      = "data"

  user_data = file("../files/opensearch_install.sh")

  tags = {
    Name = "OpenSearch-Instance"
  }
}
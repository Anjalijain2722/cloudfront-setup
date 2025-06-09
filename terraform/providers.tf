resource "aws_s3_bucket" "west_bucket" {
  provider = aws.us-east # refer to provider with alias "us-east"

  bucket = "bucket-in-east"
}
provider "aws" {
  alias  = "us-east"
  region = "us-east-1"

}

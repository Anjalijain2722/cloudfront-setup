# Read the existing bucket you provide via var.bucket_name
data "aws_s3_bucket" "log_bucket" {
  bucket = var.bucket_name
}

# Grant CloudFront permission to write logs into the bucket
resource "aws_s3_bucket_policy" "log_delivery_policy" {
  bucket = var.bucket_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontToWriteLogs"
        Effect    = "Allow"
        Principal = { Service = "logging.s3.amazonaws.com" }
        Action    = "s3:PutObject"
        Resource  = "arn:aws:s3:::${var.bucket_name}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })
}

variable "use_existing_distribution" {
  description = "Use existing CloudFront distribution"
  type        = bool
  default     = false
}

# Data block to read an existing distribution (only if used)
data "aws_cloudfront_distribution" "existing" {
  count = var.use_existing_distribution ? 1 : 0
  id    = var.use_existing_distribution
}

# Create CloudFront only if user chooses NOT to use existing one
resource "aws_cloudfront_distribution" "log_enabled" {
  count                = var.use_existing_distribution ? 0 : 1
  enabled              = true
  is_ipv6_enabled      = true
  comment              = "CloudFront with S3 logging"
  default_root_object  = "index.html"

  default_cache_behavior {
    target_origin_id       = "origin1"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  logging_config {
    include_cookies = false
    bucket          = "testing-bucket-for-logs-123.s3.amazonaws.com"
    prefix          = "cloudfront-logs/"
  }

  origin {
    domain_name = var.origin_domain
    origin_id   = "origin1"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1", "TLSv1.1", "TLSv1.2"]
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

# Output the actual CloudFront ID being used
output "cloudfront_distribution_id" {
  value = var.use_existing_distribution ? data.aws_cloudfront_distribution.existing[0].id : aws_cloudfront_distribution.log_enabled[0].id
}

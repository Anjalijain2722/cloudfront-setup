# /home/anjali/cloudfront-opensearch-automation/terraform/variables.tf

variable "region" {
  description = "AWS region for deployment"
  type        = string
}

variable "bucket_name" {
  description = "Name of the S3 bucket for CloudFront logs"
  type        = string
}

variable "key_name" {
  description = "EC2 Key Pair name"
  type        = string
}

variable "ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "existing_instance_id" {
  description = "ID of an existing EC2 instance to use (if any)"
  type        = string
  default     = ""
}

variable "use_existing_instance" {
  description = "Whether to use an existing EC2 instance"
  type        = bool
  default     = false
}

variable "log_bucket_name" {
  description = "S3 bucket for CloudFront access logs"
  type        = string
}

variable "use_existing_cloudfront" { # NEW variable
  description = "Whether to use an existing CloudFront distribution"
  type        = bool
  default     = false
}

variable "existing_cloudfront_id" { # NEW variable
  description = "ID of an existing CloudFront distribution to use (if use_existing_cloudfront is true)"
  type        = string
  default     = ""
}

variable "origin_domain" { # NEW variable
  description = "Domain name of the origin (EC2 instance DNS)"
  type        = string
}
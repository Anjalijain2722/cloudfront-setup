variable "region" {}
variable "bucket_name" {}
variable "key_name" {}
variable "ami_id" {}
variable "instance_type" {}
variable "origin_domain" {}
variable "log_bucket_name" {
  description = "Name of the S3 bucket used for storing logs"
  type        = string
}
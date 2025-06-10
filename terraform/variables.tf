# terraform/variables.tf
variable "region" {
  type = string
}

variable "bucket_name" {
  type = string
}

variable "log_bucket_name" {
  type = string
}

variable "key_name" {
  type = string
}

variable "ami_id" {
  type = string
}

variable "instance_type" {
  type = string
}

variable "origin_domain" {
  type = string
}

variable "use_existing_instance" {
  type = bool
}

variable "existing_instance_id" {
  type = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-north-1"
}

variable "bench_image" {
  description = "Multi-arch image tag in GHCR"
  type        = string
  default     = "ghcr.io/olexandrd/demo-bench-build-bench:latest"
}

variable "instance_types_arm" {
  description = "Instance types list ARM64 (Graviton)"
  type        = list(string)
  default     = ["t4g.xlarge"]
}

variable "instance_types_amd" {
  description = "Instance types list AMD64 (x86_64)"
  type        = list(string)
  default     = ["t3.xlarge"]
}

variable "instances_per_type" {
  description = "Number of instances per type"
  type        = number
  default     = 1
}

variable "ssh_cidr" {
  description = "CIDR for SSH (ingress)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "bucket_prefix" {
  description = "S3 bucket name prefix for results storage"
  type        = string
  default     = "arm-vs-amd64-results"
}

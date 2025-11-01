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

variable "instance_type_amd64" {
  description = "AMD64 instance type"
  type        = string
  default     = "t3.xlarge" # 4 vCPU / 16 GiB
}

variable "instance_type_arm64" {
  description = "ARM64 instance type (Graviton)"
  type        = string
  default     = "t4g.xlarge" # 4 vCPU / 16 GiB
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

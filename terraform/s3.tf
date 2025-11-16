resource "random_id" "suffix" {
  byte_length = 3
}

resource "aws_s3_bucket" "bench" {
  bucket        = "${var.bucket_prefix}-${random_id.suffix.hex}"
  force_destroy = true
  tags = {
    Project = "arm-vs-amd64"
  }
}

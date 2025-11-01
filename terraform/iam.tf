resource "aws_iam_role" "ec2_role" {
  name = "bench-ec2-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "ec2.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
  tags = { Project = "arm-vs-amd64" }
}

# дозволяємо класти файли у s3://bucket/runs/ARCH/TYPE/INSTANCE/RUN_ID/*
resource "aws_iam_role_policy" "put_results" {
  name = "bench-s3-put"
  role = aws_iam_role.ec2_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = ["s3:PutObject", "s3:AbortMultipartUpload", "s3:PutObjectAcl"],
      Resource = "${aws_s3_bucket.bench.arn}/runs/*"
    }]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "bench-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

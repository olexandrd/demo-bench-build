resource "random_uuid" "run" {}

locals {
  subnet_id = data.aws_subnets.default.ids[0]
}

# Рендеримо cloud-init через templatefile()
locals {
  user_data_rendered = templatefile("${path.module}/user_data.tpl", {
    run_id = random_uuid.run.result
    bucket = aws_s3_bucket.bench.bucket
    image  = var.bench_image
  })
}

resource "aws_instance" "amd64" {
  ami                    = data.aws_ami.ubuntu_2404_amd64.id
  instance_type          = var.instance_type_amd64
  subnet_id              = local.subnet_id
  vpc_security_group_ids = [aws_security_group.bench.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  user_data              = local.user_data_rendered

  tags = {
    Name    = "bench-amd64"
    Project = "arm-vs-amd64"
    Arch    = "amd64"
    Run     = random_uuid.run.result
  }
}

resource "aws_instance" "arm64" {
  ami                    = data.aws_ami.ubuntu_2404_arm64.id
  instance_type          = var.instance_type_arm64
  subnet_id              = local.subnet_id
  vpc_security_group_ids = [aws_security_group.bench.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  user_data              = local.user_data_rendered

  tags = {
    Name    = "bench-arm64"
    Project = "arm-vs-amd64"
    Arch    = "arm64"
    Run     = random_uuid.run.result
  }
}

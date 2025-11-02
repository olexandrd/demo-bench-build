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

/* ========================= ARM64 (Graviton) ========================= */
locals {
  arm_keys = flatten([
    for t in var.instance_types_arm : [
      for i in range(var.instances_per_type) : "${t}#${i}"
    ]
  ])
}

resource "aws_instance" "arm64" {
  for_each               = toset(local.arm_keys)
  ami                    = data.aws_ami.ubuntu_2404_arm64.id
  instance_type          = split("#", each.key)[0]
  subnet_id              = local.subnet_id
  vpc_security_group_ids = [aws_security_group.bench.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  user_data              = local.user_data_rendered

  tags = {
    Name    = "bench-arm64-${split("#", each.key)[0]}-${split("#", each.key)[1]}"
    Project = "arm-vs-amd64"
    Arch    = "arm64"
    Type    = split("#", each.key)[0]
    Run     = random_uuid.run.result
  }
}

/* ========================= AMD64 (x86_64) ========================= */

locals {
  amd_keys = flatten([
    for t in var.instance_types_amd : [
      for i in range(var.instances_per_type) : "${t}#${i}"
    ]
  ])
}

resource "aws_instance" "amd64" {
  for_each               = toset(local.amd_keys)
  ami                    = data.aws_ami.ubuntu_2404_amd64.id
  instance_type          = split("#", each.key)[0]
  subnet_id              = local.subnet_id
  vpc_security_group_ids = [aws_security_group.bench.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  user_data              = local.user_data_rendered

  tags = {
    Name    = "bench-amd64-${split("#", each.key)[0]}-${split("#", each.key)[1]}"
    Project = "arm-vs-amd64"
    Arch    = "amd64"
    Type    = split("#", each.key)[0]
    Run     = random_uuid.run.result
  }
}


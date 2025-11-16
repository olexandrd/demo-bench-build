output "run_id" {
  value = random_uuid.run.result
}

output "s3_bucket" {
  value = aws_s3_bucket.bench.bucket
}

output "s3_results_prefix" {
  value       = "s3://${aws_s3_bucket.bench.bucket}/runs/"
  description = "Корінь з усіма результатами. Дивись підпрефікси ARCH/TYPE/INSTANCE_ID/RUN_ID/"
}

output "ls_command" {
  value = "aws s3 ls s3://${aws_s3_bucket.bench.bucket}/runs/ --recursive"
}


output "arm64_instance_public_ips" {
  description = "ARM64: public IPs for key <type>#<idx>"
  value       = { for k, inst in aws_instance.arm64 : k => inst.public_ip }
}

output "amd64_instance_public_ips" {
  description = "AMD64: public IPs for key <type>#<idx>"
  value       = { for k, inst in aws_instance.amd64 : k => inst.public_ip }
}

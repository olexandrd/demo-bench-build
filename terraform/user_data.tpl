#cloud-config
package_update: true
packages:
  - docker.io
  - jq
  - awscli

write_files:
  - path: /opt/bench/run-and-upload.sh
    permissions: "0755"
    content: |
      #!/usr/bin/env bash
      set -euo pipefail
      RUN_ID="$RUN_ID"
      BUCKET="$BUCKET"
      IMAGE="$IMAGE"

      systemctl enable --now docker
      docker pull "$IMAGE"

      mkdir -p /var/log/bench

      IID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id || echo "i-unknown")
      ITYPE=$(curl -s http://169.254.169.254/latest/meta-data/instance-type || echo "t-unknown")
      ARCH=$(uname -m)
      PREFIX="runs/$${ARCH}/$${ITYPE}/$${IID}/$${RUN_ID}"

      docker run --rm --cpus=2 "$IMAGE" stress-ng --cpu 2 --cpu-method all --metrics-brief --timeout 20s \
        | tee /var/log/bench/sysbench.jsonl
      docker run --rm --cpus=2 "$IMAGE" numpy matmul 2000 \
        | tee /var/log/bench/numpy.jsonl
      docker run --rm --cpus=2 "$IMAGE" numpy elem 1000000 50 \
        | tee /var/log/bench/numpy-elem.jsonl

      aws s3 cp /var/log/bench/sysbench.jsonl   "s3://$${BUCKET}/$${PREFIX}/sysbench.jsonl"
      aws s3 cp /var/log/bench/numpy.jsonl      "s3://$${BUCKET}/$${PREFIX}/numpy.jsonl"
      aws s3 cp /var/log/bench/numpy-elem.jsonl "s3://$${BUCKET}/$${PREFIX}/numpy-elem.jsonl"

      aws s3 cp <(echo ok) "s3://$${BUCKET}/$${PREFIX}/DONE"

      shutdown -h now || true

runcmd:
  - RUN_ID='${run_id}' BUCKET='${bucket}' IMAGE='${image}' bash /opt/bench/run-and-upload.sh

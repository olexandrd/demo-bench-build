#cloud-config
package_update: true
packages:
  - docker.io
  - jq

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

      # IMDSv2-safe метадані
      TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" || true)
      HDR=()
      [ -n "$${TOKEN}" ] && HDR=(-H "X-aws-ec2-metadata-token: $${TOKEN}")
      IID=$(curl -s "$${HDR[@]}" http://169.254.169.254/latest/meta-data/instance-id || echo "i-unknown")
      ITYPE=$(curl -s "$${HDR[@]}" http://169.254.169.254/latest/meta-data/instance-type || echo "t-unknown")

      ARCH=$(uname -m)
      PREFIX="runs/$${ARCH}/$${ITYPE}/$${RUN_ID}/$${IID}"

      docker run --rm --cpus=2 \
        -e RUN_ID="$RUN_ID" \
        -e TASK="stress-ng" \
        -e DATASET="default" \
        -e INSTANCE_ID="$IID" \
        -e INSTANCE_TYPE="$ITYPE" \
        -e CLOUD_PROVIDER="AWS" \
        "$IMAGE" stress-ng --cpu 2 --cpu-method all --metrics-brief --cpu-ops 1000 --timeout 20s \
        | tee /var/log/bench/stressng.jsonl
      docker run --rm --cpus=2 \
        -e RUN_ID="$RUN_ID" \
        -e TASK="stress-ng" \
        -e DATASET="default" \
        -e INSTANCE_ID="$IID" \
        -e INSTANCE_TYPE="$ITYPE" \
        -e CLOUD_PROVIDER="AWS" \
        "$IMAGE" numpy matmul 2000 \
        | tee /var/log/bench/numpy.jsonl
      docker run --rm --cpus=2 \
        -e RUN_ID="$RUN_ID" \
        -e TASK="stress-ng" \
        -e DATASET="default" \
        -e INSTANCE_ID="$IID" \
        -e INSTANCE_TYPE="$ITYPE" \
        -e CLOUD_PROVIDER="AWS" \
        "$IMAGE" numpy elem 1000000 50 \
        | tee /var/log/bench/numpy-elem.jsonl
      docker run --rm --cpus=2 \
        -e RUN_ID="$RUN_ID" \
        -e TASK="ffmpeg" \
        -e DATASET="default" \
        -e INSTANCE_ID="$IID" \
        -e INSTANCE_TYPE="$ITYPE" \
        -e CLOUD_PROVIDER="AWS" \
        "$IMAGE" ffmpeg \
          -f lavfi \
          -i testsrc=duration=10:size=1920x1080:rate=30 \
          -c:v libx264 \
          -preset medium \
          -crf 28 \
          -an \
          -f null - \
        | tee /var/log/bench/ffmpeg.jsonl

      aws s3 cp /var/log/bench/stressng.jsonl   "s3://$${BUCKET}/$${PREFIX}/stressng.jsonl"
      aws s3 cp /var/log/bench/numpy.jsonl      "s3://$${BUCKET}/$${PREFIX}/numpy.jsonl"
      aws s3 cp /var/log/bench/numpy-elem.jsonl "s3://$${BUCKET}/$${PREFIX}/numpy-elem.jsonl"
      aws s3 cp /var/log/bench/ffmpeg.jsonl     "s3://$${BUCKET}/$${PREFIX}/ffmpeg.jsonl"
      touch DONE && aws s3 cp DONE "s3://$${BUCKET}/$${PREFIX}/DONE"

      shutdown -h now || true

runcmd:
  - snap install aws-cli --classic
  - aws --version
  - RUN_ID='${run_id}' BUCKET='${bucket}' IMAGE='${image}' bash /opt/bench/run-and-upload.sh

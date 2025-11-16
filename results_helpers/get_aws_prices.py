#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import boto3
import pandas as pd


REGION_LOCATION_MAP = {
    "eu-north-1": "EU (Stockholm)",
    "eu-central-1": "EU (Frankfurt)",
    "eu-west-1": "EU (Ireland)",
    "us-east-1": "US East (N. Virginia)",
    "us-east-2": "US East (Ohio)",
    "us-west-1": "US West (N. California)",
    "us-west-2": "US West (Oregon)",
}


def get_location_for_region(region_code: str) -> str:
    if region_code not in REGION_LOCATION_MAP:
        raise ValueError(
            f"Unknown region {region_code}. Please add it to REGION_LOCATION_MAP."
        )
    return REGION_LOCATION_MAP[region_code]


def fetch_price_for_instance(
    pricing_client, region_code: str, instance_type: str
) -> float:
    """Fetch the hourly price for an instance via the AWS Pricing API."""
    location = get_location_for_region(region_code)

    resp = pricing_client.get_products(
        ServiceCode="AmazonEC2",
        Filters=[
            {"Type": "TERM_MATCH", "Field": "instanceType", "Value": instance_type},
            {"Type": "TERM_MATCH", "Field": "location", "Value": location},
            {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": "Linux"},
            {"Type": "TERM_MATCH", "Field": "tenancy", "Value": "Shared"},
            {"Type": "TERM_MATCH", "Field": "preInstalledSw", "Value": "NA"},
            {"Type": "TERM_MATCH", "Field": "capacitystatus", "Value": "Used"},
        ],
        MaxResults=100,
    )

    if not resp["PriceList"]:
        raise RuntimeError(
            f"Could not find price for {instance_type} in {region_code} ({location})"
        )

    offer = json.loads(resp["PriceList"][0])
    terms = offer["terms"]["OnDemand"]
    term_id, term = next(iter(terms.items()))
    price_dimensions = term["priceDimensions"]
    dim_id, dim = next(iter(price_dimensions.items()))
    price_str = dim["pricePerUnit"]["USD"]

    return float(price_str)


def fetch_vcpus_for_instance(ec2_client, instance_type: str) -> int:
    """Fetch the number of vCPUs for instance_type from EC2 DescribeInstanceTypes."""
    resp = ec2_client.describe_instance_types(InstanceTypes=[instance_type])
    if not resp["InstanceTypes"]:
        raise RuntimeError(
            f"Could not find description for instance type {instance_type} in EC2"
        )
    info = resp["InstanceTypes"][0]
    return info["VCpuInfo"]["DefaultVCpus"]


def main():
    parser = argparse.ArgumentParser(
        description="Fetch AWS EC2 prices for instances from normalized_results.csv"
    )
    parser.add_argument(
        "--normalized-csv",
        default="normalized_results.csv",
        help="Path to normalized_results.csv (default: normalized_results.csv)",
    )
    parser.add_argument(
        "--region",
        required=True,
        help="AWS region code (e.g., eu-north-1, eu-central-1, us-east-1)",
    )
    parser.add_argument(
        "--output",
        default="aws_instance_prices.csv",
        help="File to save the results (default: aws_instance_prices.csv)",
    )
    args = parser.parse_args()

    region_code = args.region
    location = get_location_for_region(region_code)

    df = pd.read_csv(args.normalized_csv)

    if "instance_type" not in df.columns:
        raise SystemExit("The CSV does not contain an instance_type column.")

    aws_df = df[df["cloud_provider"].str.upper() == "AWS"].copy()
    instances = sorted(aws_df["instance_type"].unique())

    print(
        f"Fetching prices for {len(instances)} instances in region {region_code} ({location})"
    )

    # Pricing API lives in us-east-1
    pricing = boto3.client("pricing", region_name="us-east-1")
    # EC2 API is in your region
    ec2 = boto3.client("ec2", region_name=region_code)

    rows = []
    for itype in instances:
        try:
            price = fetch_price_for_instance(pricing, region_code, itype)
            vcpus = fetch_vcpus_for_instance(ec2, itype)
            print(f"{itype}: {price} USD/hour, {vcpus} vCPU")
            rows.append(
                {
                    "cloud_provider": "AWS",
                    "region": region_code,
                    "location": location,
                    "instance_type": itype,
                    "price_per_hour_usd": price,
                    "vcpus": vcpus,
                    "currency": "USD",
                }
            )
        except Exception as e:
            print(f"⚠️ Error fetching {itype}: {e}")

    if not rows:
        raise SystemExit(
            "Could not fetch any prices. Check your access to the AWS Pricing API."
        )

    out_df = pd.DataFrame(rows)
    out_df.to_csv(args.output, index=False)
    print(f"\n✅ Prices saved to {args.output}")


if __name__ == "__main__":
    main()

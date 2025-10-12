#!/usr/bin/env python3
"""빌드 시 NCP Object Storage에서 모델을 다운로드하는 스크립트."""
import argparse
import sys
import boto3
from botocore.exceptions import ClientError


def download_model(
    access_key: str,
    secret_key: str,
    endpoint: str,
    region: str,
    bucket: str,
    key: str,
    output: str
):
    """NCP Object Storage에서 모델 파일을 다운로드합니다."""
    try:
        print(f"Connecting to NCP Object Storage: {endpoint}")

        # S3 호환 클라이언트 생성
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint,
            region_name=region,
        )

        print(f"Downloading {bucket}/{key} -> {output}")

        # 파일 다운로드
        s3_client.download_file(bucket, key, output)

        print(f"✓ Model downloaded successfully: {output}")
        return 0

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        print(f"✗ Download failed (ClientError): {error_code} - {error_msg}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ Download failed: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description='Download model from NCP Object Storage')
    parser.add_argument('--access-key', required=True, help='NCP Access Key')
    parser.add_argument('--secret-key', required=True, help='NCP Secret Key')
    parser.add_argument('--endpoint', required=True, help='NCP Object Storage endpoint')
    parser.add_argument('--region', required=True, help='NCP region')
    parser.add_argument('--bucket', required=True, help='Bucket name')
    parser.add_argument('--key', required=True, help='Object key (path)')
    parser.add_argument('--output', required=True, help='Output file path')

    args = parser.parse_args()

    exit_code = download_model(
        access_key=args.access_key,
        secret_key=args.secret_key,
        endpoint=args.endpoint,
        region=args.region,
        bucket=args.bucket,
        key=args.key,
        output=args.output,
    )

    sys.exit(exit_code)


if __name__ == '__main__':
    main()

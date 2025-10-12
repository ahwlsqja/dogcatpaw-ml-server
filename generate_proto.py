"""Script to generate Python code from protobuf files."""
import subprocess
import sys
from pathlib import Path


def generate_proto_files():
    """Generate Python code from proto files."""
    proto_dir = Path("src/presentation/proto")
    proto_file = proto_dir / "nose_embedder.proto"

    if not proto_file.exists():
        print(f"Error: Proto file not found at {proto_file}")
        sys.exit(1)

    print(f"Generating Python code from {proto_file}...")

    # Generate Python code
    result = subprocess.run([
        sys.executable, "-m", "grpc_tools.protoc",
        f"-I{proto_dir}",
        "--python_out=.",
        "--grpc_python_out=.",
        str(proto_file)
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error generating proto files:")
        print(result.stderr)
        sys.exit(1)

    print("[OK] Proto files generated successfully!")
    print("  - nose_embedder_pb2.py")
    print("  - nose_embedder_pb2_grpc.py")


if __name__ == "__main__":
    generate_proto_files()

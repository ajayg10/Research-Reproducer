#!/usr/bin/env python3
"""
Simple end-to-end test script.

Usage: python scripts/test_end_to_end.py [pdf_path]
"""

import sys
import asyncio
import requests
from pathlib import Path


API_BASE = "http://localhost:8000/api"


async def test_pipeline(pdf_path: str):
    """Test complete pipeline flow."""
    print("=== End-to-End Pipeline Test ===\n")

    # 1. Upload PDF and start pipeline
    print("1. Uploading PDF and starting pipeline...")

    with open(pdf_path, 'rb') as f:
        response = requests.post(
            f"{API_BASE}/reproduce/upload",
            files={"file": f}
        )

    if response.status_code != 200:
        print(f"❌ Upload failed: {response.text}")
        return False

    data = response.json()
    pipeline_id = data["pipeline_id"]
    print(f"✓ Pipeline started: {pipeline_id}\n")

    # 2. Poll for completion
    print("2. Waiting for pipeline completion...")

    max_wait = 600  # 10 minutes
    elapsed = 0
    interval = 5

    while elapsed < max_wait:
        await asyncio.sleep(interval)
        elapsed += interval

        response = requests.get(f"{API_BASE}/pipeline/{pipeline_id}")

        if response.status_code != 200:
            print(f"❌ Status check failed: {response.text}")
            return False

        status_data = response.json()
        status = status_data["status"]

        print(f"   [{elapsed}s] Status: {status}")

        if status in ["completed", "partial", "failed"]:
            break

    if elapsed >= max_wait:
        print("❌ Pipeline timed out")
        return False

    # 3. Get full results
    print("\n3. Fetching results...")

    response = requests.get(f"{API_BASE}/pipeline/{pipeline_id}/full")

    if response.status_code != 200:
        print(f"❌ Failed to fetch results: {response.text}")
        return False

    full_state = response.json()

    # 4. Display results
    print("\n=== Results ===")
    print(f"Status: {full_state['status']}")
    print(f"Retry Count: {full_state['retry_count']}")

    if full_state.get('error'):
        print(f"Error: {full_state['error']}")

    # Parser output
    if full_state.get('parser_output'):
        parser = full_state['parser_output']
        if parser.get('specification'):
            spec = parser['specification']
            print(f"\nPaper: {spec.get('title', 'Unknown')}")
            print(f"Ambiguities: {len(spec.get('ambiguities', []))}")

    # Verifier output
    if full_state.get('verifier_output'):
        verifier = full_state['verifier_output']
        if verifier.get('report'):
            report = verifier['report']
            print(f"\nVerdict: {report['verdict']}")
            print(f"Quality Score: {report.get('reproduction_quality_score', 'N/A')}")

            if report.get('metric_comparisons'):
                print("\nMetrics:")
                for metric in report['metric_comparisons']:
                    print(f"  - {metric['metric_name']}: {metric['status']}")

    # Final status
    print("\n" + "=" * 40)

    if status == "completed":
        print("✓ Pipeline completed successfully!")
        return True
    elif status == "partial":
        print("⚠ Pipeline partially successful")
        return True
    else:
        print("❌ Pipeline failed")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_end_to_end.py <pdf_path>")
        print("\nExample:")
        print("  python scripts/test_end_to_end.py paper.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not Path(pdf_path).exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    # Check backend is running
    try:
        response = requests.get(f"{API_BASE}/../health", timeout=5)
        if response.status_code != 200:
            print("Error: Backend is not responding correctly")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("Error: Backend is not running. Start it with:")
        print("  cd backend && python main.py")
        sys.exit(1)

    # Run test
    success = asyncio.run(test_pipeline(pdf_path))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

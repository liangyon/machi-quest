"""
Test script to simulate GitHub webhook delivery

This script sends a mock GitHub push event to the local webhook endpoint
to verify end-to-end webhook processing.
"""
import requests
import json
import hmac
import hashlib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
WEBHOOK_URL = "http://localhost:8000/webhooks/github"
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "your-webhook-secret-here")

# Mock GitHub push event payload
MOCK_PAYLOAD = {
    "ref": "refs/heads/main",
    "before": "0000000000000000000000000000000000000000",
    "after": "abc123def456abc123def456abc123def456abc1",
    "repository": {
        "id": 123456789,
        "name": "test-repo",
        "full_name": "testuser/test-repo",
        "owner": {
            "login": "testuser",
            "id": 987654321
        }
    },
    "pusher": {
        "name": "testuser",
        "email": "test@example.com"
    },
    "sender": {
        "login": "testuser",
        "id": 987654321,
        "avatar_url": "https://avatars.githubusercontent.com/u/987654321"
    },
    "commits": [
        {
            "id": "abc123def456abc123def456abc123def456abc1",
            "message": "Test commit message\n\nThis is a detailed commit description.",
            "timestamp": "2025-10-26T13:00:00-07:00",
            "url": "https://github.com/testuser/test-repo/commit/abc123",
            "author": {
                "name": "Test User",
                "email": "test@example.com",
                "username": "testuser"
            },
            "committer": {
                "name": "Test User",
                "email": "test@example.com",
                "username": "testuser"
            },
            "added": ["new_file.py"],
            "removed": [],
            "modified": ["existing_file.py"]
        },
        {
            "id": "def789ghi012def789ghi012def789ghi012def7",
            "message": "Another test commit",
            "timestamp": "2025-10-26T13:05:00-07:00",
            "url": "https://github.com/testuser/test-repo/commit/def789",
            "author": {
                "name": "Test User",
                "email": "test@example.com",
                "username": "testuser"
            },
            "committer": {
                "name": "Test User",
                "email": "test@example.com",
                "username": "testuser"
            },
            "added": [],
            "removed": ["old_file.py"],
            "modified": ["another_file.py"]
        }
    ]
}


def generate_signature(payload_bytes, secret):
    """
    Generate GitHub webhook signature.
    
    GitHub uses HMAC-SHA256 to sign webhook payloads.
    """
    mac = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def send_test_webhook():
    """
    Send a test webhook to the local server.
    """
    print("=" * 60)
    print("GitHub Webhook Test Script")
    print("=" * 60)
    print(f"\nTarget URL: {WEBHOOK_URL}")
    print(f"Webhook Secret: {WEBHOOK_SECRET[:10]}... (truncated)")
    print(f"Number of commits in payload: {len(MOCK_PAYLOAD['commits'])}")
    
    # Convert payload to JSON bytes
    payload_json = json.dumps(MOCK_PAYLOAD)
    payload_bytes = payload_json.encode('utf-8')
    
    # Generate signature
    signature = generate_signature(payload_bytes, WEBHOOK_SECRET)
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "push",
        "X-GitHub-Delivery": "12345678-1234-1234-1234-123456789abc",
        "X-Hub-Signature-256": signature,
        "User-Agent": "GitHub-Hookshot/test"
    }
    
    print("\n" + "-" * 60)
    print("Sending webhook...")
    print("-" * 60)
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            data=payload_bytes,
            headers=headers,
            timeout=10
        )
        
        print(f"\n✅ Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"\nResponse Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("status") == "success":
                print("\n" + "=" * 60)
                print("✅ SUCCESS! Webhook processed successfully")
                print("=" * 60)
                print(f"Event Raw ID: {response_data.get('event_raw_id')}")
                print(f"Events Created: {response_data.get('events_created')}")
                print(f"\nYou can now check the admin endpoint:")
                print(f"  curl http://localhost:8000/admin/webhooks/raw")
                print(f"  curl http://localhost:8000/admin/webhooks/stats")
                return True
            else:
                print("\n⚠️ WARNING: Unexpected response status")
                return False
        else:
            print(f"\n❌ ERROR: Webhook failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to webhook endpoint")
        print("Make sure the backend server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def verify_in_database():
    """
    Verify the webhook was saved to the database via admin API.
    """
    print("\n" + "=" * 60)
    print("Verifying webhook in database via Admin API...")
    print("=" * 60)
    
    try:
        # Check stats
        stats_response = requests.get("http://localhost:8000/admin/webhooks/stats")
        stats = stats_response.json()
        
        print(f"\nWebhook Statistics:")
        print(f"  Total webhooks: {stats['webhooks']['total']}")
        print(f"  Processed: {stats['webhooks']['processed']}")
        print(f"  Unprocessed: {stats['webhooks']['unprocessed']}")
        print(f"  Total events: {stats['events']['total']}")
        print(f"  Events by type: {stats['events']['by_type']}")
        
        # Get raw webhooks
        raw_response = requests.get("http://localhost:8000/admin/webhooks/raw?limit=1")
        raw_data = raw_response.json()
        
        if raw_data['total'] > 0:
            latest = raw_data['events'][0]
            print(f"\nLatest Webhook:")
            print(f"  ID: {latest['id']}")
            print(f"  External ID: {latest['external_event_id']}")
            print(f"  Processed: {latest['processed']}")
            print(f"  Events Created: {latest['events_created']}")
            print(f"  Received At: {latest['received_at']}")
            return True
        else:
            print("\n⚠️ No webhooks found in database")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR verifying database: {str(e)}")
        return False


if __name__ == "__main__":
    success = send_test_webhook()
    
    if success:
        print("\n" + "-" * 60)
        verify_in_database()
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

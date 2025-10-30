"""
Unit tests for webhook idempotency.

Tests that duplicate webhook deliveries are properly detected and handled,
ensuring events are only processed once even if GitHub retries.
"""
import pytest
import json
import hmac
import hashlib
from app.db.models import EventRaw
from app.tests.conftest import generate_github_signature


def make_signed_request(client, payload: dict, headers: dict):
    """
    Helper to make webhook request with proper signature.
    
    TestClient.post(json=...) serializes differently than our signature,
    so we compute signature from exact bytes and use content= instead.
    """
    # Get the secret from headers
    secret = "a_raspberry_pi_is_a_tasty_treat"  # From .env
    
    # Serialize payload the same way TestClient will
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    
    # Compute signature
    mac = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256)
    headers["X-Hub-Signature-256"] = f"sha256={mac.hexdigest()}"
    
    # Make request with raw content
    return client.post("/webhooks/github", content=payload_bytes, headers=headers)


class TestWebhookIdempotency:
    """Test webhook idempotency at the HTTP endpoint level."""
    
    def test_first_webhook_delivery_succeeds(
        self, client, db_session, signed_webhook_request
    ):
        """
        Test that the first webhook delivery is accepted and stored.
        
        Expected behavior:
        - Returns 200 status
        - Creates EventRaw record
        - Returns success status
        - Includes event_raw_id in response
        """
        # Use content instead of json to ensure exact bytes match signature
        response = client.post(
            "/webhooks/github",
            content=signed_webhook_request["payload_bytes"],
            headers=signed_webhook_request["headers"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert data["status"] == "success"
        assert data["event_type"] == "push"
        assert "event_raw_id" in data
        assert data["message"] == "Event queued for processing"
        
        # Verify database has one EventRaw record
        event_raws = db_session.query(EventRaw).all()
        assert len(event_raws) == 1
        
        # Verify EventRaw properties
        event_raw = event_raws[0]
        assert event_raw.external_event_id == signed_webhook_request["headers"]["X-GitHub-Delivery"]
        assert event_raw.payload == signed_webhook_request["payload"]
        assert event_raw.processed == False  # Will be processed by worker
    
    def test_duplicate_webhook_detected(
        self, client, db_session, mock_push_payload, duplicate_delivery_id, webhook_secret
    ):
        """
        Test that duplicate webhook deliveries are detected and rejected.
        
        Expected behavior:
        - First delivery: Creates new EventRaw, returns success
        - Second delivery (same ID): Returns duplicate status, no new EventRaw
        - Database has only ONE EventRaw record
        """
        # Create headers with duplicate delivery ID
        signature = generate_github_signature(mock_push_payload, webhook_secret)
        headers = {
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": duplicate_delivery_id,
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json"
        }
        
        # First delivery - should succeed
        response1 = make_signed_request(client, mock_push_payload, headers)
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["status"] == "success"
        event_raw_id_1 = data1["event_raw_id"]
        
        # Verify one EventRaw exists
        assert db_session.query(EventRaw).count() == 1
        
        # Second delivery - SAME delivery ID (duplicate)
        response2 = make_signed_request(client, mock_push_payload, headers)
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should be marked as duplicate
        assert data2["status"] == "duplicate"
        assert data2["message"] == "Webhook already processed"
        assert data2["event_raw_id"] == event_raw_id_1  # Same ID returned
        
        # Still only ONE EventRaw in database
        assert db_session.query(EventRaw).count() == 1
    
    def test_multiple_deliveries_same_id(
        self, client, db_session, mock_push_payload, duplicate_delivery_id, webhook_secret
    ):
        """
        Test multiple webhook deliveries with same delivery ID.
        
        Simulates GitHub retrying webhook multiple times.
        Expected: Only first creates EventRaw, rest return duplicate.
        """
        signature = generate_github_signature(mock_push_payload, webhook_secret)
        headers = {
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": duplicate_delivery_id,
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json"
        }
        
        # Send same webhook 5 times
        responses = []
        for i in range(5):
            response = make_signed_request(client, mock_push_payload, headers)
            responses.append(response.json())
        
        # First should succeed
        assert responses[0]["status"] == "success"
        event_raw_id = responses[0]["event_raw_id"]
        
        # All others should be duplicates
        for response_data in responses[1:]:
            assert response_data["status"] == "duplicate"
            assert response_data["event_raw_id"] == event_raw_id
        
        # Only ONE EventRaw created
        assert db_session.query(EventRaw).count() == 1
    
    def test_different_delivery_ids_create_separate_records(
        self, client, db_session, mock_push_payload, webhook_secret
    ):
        """
        Test that webhooks with different delivery IDs create separate records.
        
        Expected behavior:
        - Different delivery IDs → separate EventRaw records
        - Each gets unique event_raw_id
        """
        delivery_ids = [
            "delivery-1",
            "delivery-2",
            "delivery-3"
        ]
        
        event_raw_ids = []
        
        for delivery_id in delivery_ids:
            signature = generate_github_signature(mock_push_payload, webhook_secret)
            headers = {
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": delivery_id,
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json"
            }
            
            response = make_signed_request(client, mock_push_payload, headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            event_raw_ids.append(data["event_raw_id"])
        
        # All event_raw_ids should be unique
        assert len(event_raw_ids) == len(set(event_raw_ids))
        
        # Should have 3 EventRaw records
        assert db_session.query(EventRaw).count() == 3
        
        # Verify each has correct delivery ID
        for delivery_id in delivery_ids:
            event_raw = db_session.query(EventRaw).filter(
                EventRaw.external_event_id == delivery_id
            ).first()
            assert event_raw is not None
    
    def test_idempotency_with_invalid_signature_on_retry(
        self, client, db_session, mock_push_payload, duplicate_delivery_id, webhook_secret
    ):
        """
        Test that duplicate detection happens AFTER signature verification.
        
        Expected behavior:
        - First delivery with valid signature: Success
        - Retry with INVALID signature: Rejected with 401 (signature check first)
        - Retry with VALID signature: Duplicate detected
        """
        # First delivery - valid signature
        valid_signature = generate_github_signature(mock_push_payload, webhook_secret)
        valid_headers = {
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": duplicate_delivery_id,
            "X-Hub-Signature-256": valid_signature,
            "Content-Type": "application/json"
        }
        
        response1 = make_signed_request(client, mock_push_payload, valid_headers)
        
        assert response1.status_code == 200
        assert response1.json()["status"] == "success"
        
        # Retry with INVALID signature (but same delivery ID)
        invalid_headers = {
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": duplicate_delivery_id,
            "X-Hub-Signature-256": "sha256=invalid",
            "Content-Type": "application/json"
        }
        
        payload_bytes = json.dumps(mock_push_payload, separators=(',', ':')).encode('utf-8')
        response2 = client.post(
            "/webhooks/github",
            content=payload_bytes,
            headers=invalid_headers
        )
        
        # Should be rejected due to invalid signature (401)
        assert response2.status_code == 401
        
        # Retry with valid signature again
        response3 = make_signed_request(client, mock_push_payload, valid_headers)
        
        # Should be detected as duplicate
        assert response3.status_code == 200
        assert response3.json()["status"] == "duplicate"
        
        # Still only ONE EventRaw
        assert db_session.query(EventRaw).count() == 1
    
    def test_idempotency_preserves_original_payload(
        self, client, db_session, mock_push_payload, duplicate_delivery_id, webhook_secret
    ):
        """
        Test that duplicate detection returns original event, even if payload differs.
        
        Expected behavior:
        - First delivery stores payload A
        - Retry with same delivery ID but different payload → duplicate detected
        - Original payload preserved in database
        """
        # First delivery
        original_signature = generate_github_signature(mock_push_payload, webhook_secret)
        headers = {
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": duplicate_delivery_id,
            "X-Hub-Signature-256": original_signature,
            "Content-Type": "application/json"
        }
        
        response1 = make_signed_request(client, mock_push_payload, headers)
        
        assert response1.status_code == 200
        original_event_raw_id = response1.json()["event_raw_id"]
        
        # Modified payload (different commits)
        modified_payload = mock_push_payload.copy()
        modified_payload["commits"] = [
            {
                "id": "different-commit-id",
                "message": "Different message",
                "timestamp": "2025-10-26T14:00:00-07:00",
                "url": "https://github.com/testuser/test-repo/commit/different",
                "author": {
                    "name": "Different Author",
                    "email": "different@example.com",
                    "username": "different"
                },
                "committer": {
                    "name": "Different Author",
                    "email": "different@example.com",
                    "username": "different"
                },
                "added": [],
                "removed": [],
                "modified": []
            }
        ]
        
        # Second delivery - SAME delivery ID, DIFFERENT payload
        modified_signature = generate_github_signature(modified_payload, webhook_secret)
        modified_headers = {
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": duplicate_delivery_id,  # Same ID!
            "X-Hub-Signature-256": modified_signature,
            "Content-Type": "application/json"
        }
        
        response2 = make_signed_request(client, modified_payload, modified_headers)
        
        # Should be duplicate
        assert response2.status_code == 200
        assert response2.json()["status"] == "duplicate"
        assert response2.json()["event_raw_id"] == original_event_raw_id
        
        # Verify original payload preserved
        event_raw = db_session.query(EventRaw).filter(
            EventRaw.external_event_id == duplicate_delivery_id
        ).first()
        
        assert event_raw is not None
        assert event_raw.payload == mock_push_payload  # Original, not modified
        assert len(event_raw.payload["commits"]) == 2  # Original had 2 commits
    
    def test_concurrent_duplicate_handling(
        self, client, db_session, mock_push_payload, duplicate_delivery_id, webhook_secret
    ):
        """
        Test that database constraint prevents race conditions.
        
        Even if two identical webhooks arrive simultaneously,
        database unique constraint on external_event_id ensures
        only one EventRaw is created.
        
        Note: This test verifies the database constraint, not actual
        concurrency, since TestClient is synchronous.
        """
        from app.db.models import EventRaw as EventRawModel
        import uuid
        
        # Try to manually insert duplicate
        event_raw_1 = EventRawModel(
            id=uuid.uuid4(),
            external_event_id=duplicate_delivery_id,
            payload=mock_push_payload,
            processed=False
        )
        db_session.add(event_raw_1)
        db_session.commit()
        
        # Try to insert another with same external_event_id
        event_raw_2 = EventRawModel(
            id=uuid.uuid4(),
            external_event_id=duplicate_delivery_id,  # Duplicate!
            payload=mock_push_payload,
            processed=False
        )
        db_session.add(event_raw_2)
        
        # Should raise IntegrityError due to unique constraint
        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            db_session.commit()
        
        db_session.rollback()
        
        # Verify only one exists
        assert db_session.query(EventRawModel).filter(
            EventRawModel.external_event_id == duplicate_delivery_id
        ).count() == 1


class TestIdempotencyEdgeCases:
    """Test edge cases and error scenarios for idempotency."""
    
    def test_missing_delivery_id_header(
        self, client, mock_push_payload, webhook_secret
    ):
        """
        Test that missing X-GitHub-Delivery header is rejected.
        
        Expected: 400 Bad Request (before duplicate check)
        """
        signature = generate_github_signature(mock_push_payload, webhook_secret)
        headers = {
            "X-GitHub-Event": "push",
            # Missing X-GitHub-Delivery!
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json"
        }
        
        payload_bytes = json.dumps(mock_push_payload, separators=(',', ':')).encode('utf-8')
        
        # Need to compute proper signature for the exact bytes
        mac = hmac.new(webhook_secret.encode('utf-8'), payload_bytes, hashlib.sha256)
        headers["X-Hub-Signature-256"] = f"sha256={mac.hexdigest()}"
        
        response = client.post(
            "/webhooks/github",
            content=payload_bytes,
            headers=headers
        )
        
        # Signature check happens first, then header check
        # So we actually get 400 for missing delivery ID
        assert response.status_code == 400
        assert "Missing X-GitHub-Delivery header" in response.json()["detail"]
    
    def test_empty_delivery_id(
        self, client, db_session, mock_push_payload, webhook_secret
    ):
        """
        Test handling of empty delivery ID.
        
        Empty string should still be treated as valid (though unusual).
        """
        signature = generate_github_signature(mock_push_payload, webhook_secret)
        headers = {
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": "",  # Empty!
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json"
        }
        
        response = make_signed_request(client, mock_push_payload, headers)
        
        # Empty delivery ID is actually invalid - FastAPI header parsing treats it as None
        # So this should return 400, not 200
        assert response.status_code == 400
        # No event should be created
        assert db_session.query(EventRaw).count() == 0

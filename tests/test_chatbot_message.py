"""Tests for the chatbot message endpoint's input bounds and error status.

Run with: python -m pytest tests/test_chatbot_message.py
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simple_backend import app  # noqa: E402

ENDPOINT = "/api/patient/chatbot_message"


@pytest.fixture
def client():
    return TestClient(app)


def test_a_normal_message_is_answered(client):
    response = client.post(
        ENDPOINT, json={"patient_id": "p1", "message": "I feel a bit tired today."}
    )

    assert response.status_code == 200
    assert response.json()["sender"] == "ai"


def test_critical_symptoms_are_escalated(client):
    response = client.post(
        ENDPOINT, json={"patient_id": "p1", "message": "I have chest pain"}
    )

    assert response.status_code == 200
    assert "emergency room" in response.json()["message"]


def test_an_empty_message_is_rejected(client):
    response = client.post(ENDPOINT, json={"patient_id": "p1", "message": ""})

    assert response.status_code == 422


def test_an_empty_patient_id_is_rejected(client):
    response = client.post(ENDPOINT, json={"patient_id": "", "message": "hello"})

    assert response.status_code == 422


def test_an_oversized_message_is_rejected(client):
    response = client.post(
        ENDPOINT, json={"patient_id": "p1", "message": "a" * 4001}
    )

    assert response.status_code == 422


def test_a_message_at_the_limit_is_accepted(client):
    response = client.post(
        ENDPOINT, json={"patient_id": "p1", "message": "a" * 4000}
    )

    assert response.status_code == 200


def test_a_missing_message_is_rejected(client):
    response = client.post(ENDPOINT, json={"patient_id": "p1"})

    assert response.status_code == 422


def test_a_failed_triage_is_not_reported_as_success():
    """A handler that blows up must not answer 200 with a canned reply."""
    import asyncio

    import simple_backend

    class Exploding(str):
        def lower(self):
            raise RuntimeError("boom")

    request = simple_backend.ChatbotMessageRequest(patient_id="p1", message="hi")
    object.__setattr__(request, "message", Exploding("hi"))

    result = asyncio.run(simple_backend.chatbot_message(request))

    assert result.status_code == 500

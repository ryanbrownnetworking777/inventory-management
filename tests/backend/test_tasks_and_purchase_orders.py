"""
Tests for the task and purchase order endpoints.
"""
from datetime import date, timedelta

import pytest

import main


@pytest.fixture(autouse=True)
def reset_in_memory_state():
    """Tasks and purchase orders are held in memory, so reset them between tests."""
    saved_pos = list(main.purchase_orders)
    main.tasks.clear()
    yield
    main.tasks.clear()
    main.purchase_orders[:] = saved_pos


def _future_date(days=7):
    return (date.today() + timedelta(days=days)).isoformat()


class TestTasks:
    """Test suite for /api/tasks."""

    def test_get_tasks_empty(self, client):
        """The tasks endpoint exists and starts empty."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """Creating a task returns a pending task with a string id."""
        response = client.post("/api/tasks", json={"title": "  Audit stock  ", "priority": "high", "dueDate": "2025-10-10"})
        assert response.status_code == 201

        task = response.json()
        assert task["title"] == "Audit stock"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-10-10"
        assert task["status"] == "pending"
        assert task["id"].startswith("api-")

    def test_tasks_listed_newest_first(self, client):
        """GET returns tasks in reverse creation order."""
        first = client.post("/api/tasks", json={"title": "A", "dueDate": "2025-10-10"}).json()
        second = client.post("/api/tasks", json={"title": "B", "dueDate": "2025-10-11"}).json()
        assert [t["id"] for t in client.get("/api/tasks").json()] == [second["id"], first["id"]]

    def test_toggle_task(self, client):
        """PATCH flips status between pending and completed."""
        task = client.post("/api/tasks", json={"title": "Toggle me", "dueDate": "2025-10-10"}).json()

        toggled = client.patch(f"/api/tasks/{task['id']}").json()
        assert toggled["status"] == "completed"
        assert client.patch(f"/api/tasks/{task['id']}").json()["status"] == "pending"

    def test_delete_task(self, client):
        """DELETE removes the task; ids are not reused afterwards."""
        task = client.post("/api/tasks", json={"title": "Delete me", "dueDate": "2025-10-10"}).json()
        assert client.delete(f"/api/tasks/{task['id']}").status_code == 200
        assert client.get("/api/tasks").json() == []

        new_task = client.post("/api/tasks", json={"title": "New", "dueDate": "2025-10-10"}).json()
        assert new_task["id"] != task["id"]

    def test_unknown_task_returns_404(self, client):
        assert client.patch("/api/tasks/api-999").status_code == 404
        assert client.delete("/api/tasks/api-999").status_code == 404

    @pytest.mark.parametrize("payload", [
        {"title": "   ", "dueDate": "2025-10-10"},
        {"title": "Bad date", "dueDate": "not-a-date"},
    ])
    def test_invalid_task_rejected(self, client, payload):
        assert client.post("/api/tasks", json=payload).status_code == 400

    def test_invalid_priority_rejected(self, client):
        response = client.post("/api/tasks", json={"title": "X", "priority": "urgent", "dueDate": "2025-10-10"})
        assert response.status_code == 422


class TestPurchaseOrders:
    """Test suite for /api/purchase-orders and backlog PO linkage."""

    def _payload(self, backlog_item_id="1", **overrides):
        payload = {
            "backlog_item_id": backlog_item_id,
            "supplier_name": "Acme Supply",
            "quantity": 350,
            "unit_cost": 6.4,
            "expected_delivery_date": _future_date(),
            "notes": "Rush order",
        }
        payload.update(overrides)
        return payload

    def test_create_purchase_order(self, client):
        """Creating a PO returns it with server-generated fields."""
        response = client.post("/api/purchase-orders", json=self._payload())
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["backlog_item_id"] == "1"
        assert po["status"] == "Pending"
        assert po["created_date"]

    def test_get_purchase_order_by_backlog_item(self, client):
        created = client.post("/api/purchase-orders", json=self._payload()).json()

        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_missing_purchase_order_returns_404(self, client):
        assert client.get("/api/purchase-orders/1").status_code == 404

    def test_backlog_reports_purchase_order_link(self, client):
        """GET /api/backlog exposes purchase_order_id once a PO exists."""
        backlog = {b["id"]: b for b in client.get("/api/backlog").json()}
        assert backlog["1"]["purchase_order_id"] is None
        assert backlog["1"]["has_purchase_order"] is False

        po = client.post("/api/purchase-orders", json=self._payload()).json()

        backlog = {b["id"]: b for b in client.get("/api/backlog").json()}
        assert backlog["1"]["purchase_order_id"] == po["id"]
        assert backlog["1"]["has_purchase_order"] is True

    def test_duplicate_purchase_order_rejected(self, client):
        client.post("/api/purchase-orders", json=self._payload())
        assert client.post("/api/purchase-orders", json=self._payload()).status_code == 409

    def test_unknown_backlog_item_rejected(self, client):
        assert client.post("/api/purchase-orders", json=self._payload(backlog_item_id="9999")).status_code == 404

    @pytest.mark.parametrize("overrides", [
        {"supplier_name": "  "},
        {"quantity": 0},
        {"unit_cost": -1},
        {"expected_delivery_date": "soon"},
    ])
    def test_invalid_purchase_order_rejected(self, client, overrides):
        assert client.post("/api/purchase-orders", json=self._payload(**overrides)).status_code == 400

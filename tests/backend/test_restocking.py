"""
Tests for the restocking recommendation and restock order endpoints.
"""
from datetime import datetime, timedelta

import pytest

import main


@pytest.fixture(autouse=True)
def clear_restock_orders():
    """Restock orders are held in memory, so reset them between tests."""
    main.restock_orders.clear()
    yield
    main.restock_orders.clear()


class TestRestockRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_zero_budget_returns_no_items(self, client):
        """A zero budget should not recommend anything but still report max_budget."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["max_budget"] > 0

    def test_total_cost_never_exceeds_budget(self, client):
        """Recommendations must fit within the requested budget."""
        max_budget = client.get("/api/restocking/recommendations").json()["max_budget"]

        for budget in [100, 1000, 2500, max_budget / 2, max_budget]:
            data = client.get(f"/api/restocking/recommendations?budget={budget}").json()
            assert data["total_cost"] <= budget + 0.01
            assert data["total_cost"] == pytest.approx(sum(item["subtotal"] for item in data["items"]))

    def test_excludes_items_without_demand_growth(self, client):
        """Items whose forecast does not exceed current demand are never recommended."""
        max_budget = client.get("/api/restocking/recommendations").json()["max_budget"]
        data = client.get(f"/api/restocking/recommendations?budget={max_budget}").json()

        skus = {item["item_sku"] for item in data["items"]}
        assert "MTR-304" not in skus  # decreasing demand
        for item in data["items"]:
            assert item["forecasted_demand"] > item["current_demand"]
            assert item["quantity"] == item["forecasted_demand"] - item["current_demand"]

    def test_max_budget_includes_all_candidates(self, client):
        """Spending max_budget should recommend every candidate, sorted by demand growth."""
        demand = client.get("/api/demand").json()
        growing = [d for d in demand if d["forecasted_demand"] > d["current_demand"]]

        max_budget = client.get("/api/restocking/recommendations").json()["max_budget"]
        data = client.get(f"/api/restocking/recommendations?budget={max_budget}").json()

        assert len(data["items"]) == len(growing)
        assert data["total_cost"] == pytest.approx(max_budget)
        quantities = [item["quantity"] for item in data["items"]]
        assert quantities == sorted(quantities, reverse=True)

    def test_negative_budget_rejected(self, client):
        """A negative budget is invalid input."""
        response = client.get("/api/restocking/recommendations?budget=-1")
        assert response.status_code == 400


class TestRestockOrders:
    """Test suite for POST/GET /api/restocking/orders."""

    def _order_items(self, client):
        max_budget = client.get("/api/restocking/recommendations").json()["max_budget"]
        items = client.get(f"/api/restocking/recommendations?budget={max_budget}").json()["items"]
        return [
            {key: item[key] for key in ["item_sku", "item_name", "quantity", "unit_cost", "lead_time_days"]}
            for item in items[:2]
        ]

    def test_create_and_list_order(self, client):
        """A submitted order is returned by the list endpoint with computed fields."""
        items = self._order_items(client)
        response = client.post("/api/restocking/orders", json={"items": items})
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"] == "RST-0001"
        assert order["status"] == "Submitted"
        assert order["total_value"] == pytest.approx(sum(i["quantity"] * i["unit_cost"] for i in items))

        expected_lead = max(i["lead_time_days"] for i in items)
        assert order["lead_time_days"] == expected_lead
        delivery = datetime.fromisoformat(order["expected_delivery"])
        ordered = datetime.fromisoformat(order["order_date"])
        assert delivery - ordered == timedelta(days=expected_lead)

        listed = client.get("/api/restocking/orders").json()
        assert [o["id"] for o in listed] == [order["id"]]

    def test_orders_listed_newest_first(self, client):
        """Multiple orders come back in reverse submission order."""
        items = self._order_items(client)
        client.post("/api/restocking/orders", json={"items": items})
        client.post("/api/restocking/orders", json={"items": items})

        listed = client.get("/api/restocking/orders").json()
        assert [o["order_number"] for o in listed] == ["RST-0002", "RST-0001"]

    def test_empty_order_rejected(self, client):
        """An order with no items is invalid."""
        response = client.post("/api/restocking/orders", json={"items": []})
        assert response.status_code == 400

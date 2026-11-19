from app import price_drop
from app.db import conn


def test_drop_to_targets_lowers_cheapest_offer_below_target(client):
    item = client.get("/products", params={"limit": 1}).json()["items"][0]
    best = min(o["price"] for o in item["offers"] if o["inStock"])
    target = best - 100
    store = next(o["storeId"] for o in item["offers"] if o["inStock"])
    response = client.post("/wishlist", json={"productId": item["id"], "storeId": store,
                                       "targetPrice": target, "notify": True})
    assert response.status_code in (200, 201)

    changed = price_drop.drop_to_targets()
    assert any(c["new"] <= target for c in changed)

    fresh = client.get("/products/%d" % item["id"]).json()
    assert min(o["price"] for o in fresh["offers"] if o["inStock"]) <= target
    assert price_drop.drop_to_targets() == []

    conn.execute("DELETE FROM wishlist WHERE product_id = ?", (item["id"],))

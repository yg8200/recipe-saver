def test_health_check_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200

def test_health_check_returns_correct_json(client):
    response = client.get("/health")
    data = response.get_json()
    assert data == {
        "status": "healthy",
        "service": "recipe-saver-backend"
    }
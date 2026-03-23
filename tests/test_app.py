import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities after each test to avoid state pollution"""
    from src.app import activities
    original = {k: {"participants": v["participants"].copy(), **{k2: v2 for k2, v2 in v.items() if k2 != "participants"}} 
                for k, v in activities.items()}
    yield
    # Restore original state
    for activity_name, activity_data in original.items():
        activities[activity_name]["participants"] = activity_data["participants"]


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all(self, client):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_get_activities_structure(self, client):
        """Test that activity structure is correct"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant"""
        from src.app import activities
        initial_count = len(activities["Programming Class"]["participants"])
        
        client.post(
            "/activities/Programming Class/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert len(activities["Programming Class"]["participants"]) == initial_count + 1
        assert "test@mergington.edu" in activities["Programming Class"]["participants"]
    
    def test_signup_invalid_activity(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration"""
        from src.app import activities
        initial_count = len(activities["Chess Club"]["participants"])
        existing_email = activities["Chess Club"]["participants"][0]
        
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": existing_email}
        )
        
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert len(activities["Chess Club"]["participants"]) == initial_count - 1
        assert existing_email not in activities["Chess Club"]["participants"]
    
    def test_unregister_not_registered(self, client):
        """Test unregistering a student who isn't signed up"""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_invalid_activity(self, client):
        """Test unregistering from non-existent activity"""
        response = client.delete(
            "/activities/Fake Club/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404

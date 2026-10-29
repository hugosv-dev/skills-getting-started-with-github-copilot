from src.app import activities


# --- GET / ---

def test_root_redirects_to_static_index(client):
    # Arrange
    url = "/"

    # Act
    response = client.get(url, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


# --- GET /activities ---

def test_get_activities_returns_all_activities(client):
    # Arrange
    expected_names = set(activities.keys())

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == expected_names
    assert "Chess Club" in data


def test_get_activities_includes_expected_fields(client):
    # Arrange
    expected_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    for details in response.json().values():
        assert expected_fields <= set(details.keys())
        assert isinstance(details["participants"], list)


# --- POST /activities/{activity_name}/signup ---

def test_signup_adds_participant(client):
    # Arrange
    email = "newstudent@mergington.edu"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    email = activities["Chess Club"]["participants"][0]
    count_before = len(activities["Chess Club"]["participants"])

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert len(activities["Chess Club"]["participants"]) == count_before


def test_signup_unknown_activity_returns_404(client):
    # Arrange
    email = "student@mergington.edu"

    # Act
    response = client.post("/activities/Underwater Basket Weaving/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_full_activity_returns_400(client):
    # Arrange
    activity = activities["Chess Club"]
    activity["participants"] = [
        f"student{i}@mergington.edu" for i in range(activity["max_participants"])
    ]
    participants_before = list(activity["participants"])

    # Act
    response = client.post(
        "/activities/Chess Club/signup", params={"email": "latecomer@mergington.edu"}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
    assert activity["participants"] == participants_before


# --- DELETE /activities/{activity_name}/unregister ---

def test_unregister_removes_participant(client):
    # Arrange
    email = activities["Chess Club"]["participants"][0]

    # Act
    response = client.delete("/activities/Chess Club/unregister", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_not_signed_up_returns_404(client):
    # Arrange
    email = "nobody@mergington.edu"
    participants_before = list(activities["Chess Club"]["participants"])

    # Act
    response = client.delete("/activities/Chess Club/unregister", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert activities["Chess Club"]["participants"] == participants_before


def test_unregister_unknown_activity_returns_404(client):
    # Arrange
    email = "student@mergington.edu"

    # Act
    response = client.delete("/activities/Underwater Basket Weaving/unregister", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


# --- URL encoding / special characters ---

def test_signup_and_unregister_email_with_special_characters(client):
    # Arrange
    email = "first.last+clubs@mergington.edu"
    activity_path = "/activities/Programming%20Class"

    # Act
    signup = client.post(f"{activity_path}/signup", params={"email": email})
    stored_after_signup = list(activities["Programming Class"]["participants"])
    unregister = client.delete(f"{activity_path}/unregister", params={"email": email})

    # Assert
    assert signup.status_code == 200
    assert email in stored_after_signup
    assert unregister.status_code == 200
    assert email not in activities["Programming Class"]["participants"]

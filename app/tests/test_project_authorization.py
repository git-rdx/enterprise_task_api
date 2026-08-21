def test_employee_cannot_create_project(client, employee_user, auth_header_for):

    headers = auth_header_for(employee_user)

    response = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "Unauthorized Project",
            "description": "Should not be created",
            "member_ids": [],
        },
    )

    assert response.status_code == 403


def test_manager_can_create_project(client, manager_user, auth_header_for):

    headers = auth_header_for(manager_user)

    response = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "Manager Project",
            "description": "Created by manager",
            "member_ids": [],
        },
    )

    assert response.status_code in {200, 201}

    data = response.json()

    assert data["name"] == "Manager Project"


def test_project_member_can_access_project(
    client, employee_user, project_with_member, auth_header_for
):

    headers = auth_header_for(employee_user)

    response = client.get(f"/api/v1/projects/{project_with_member.id}", headers=headers)

    assert response.status_code == 200


def test_unrelated_user_cannot_access_project(
    client, unrelated_user, project_with_member, auth_header_for
):

    headers = auth_header_for(unrelated_user)

    response = client.get(f"/api/v1/projects/{project_with_member.id}", headers=headers)

    assert response.status_code == 403

def test_assigned_employee_can_update_task(
    client, employee_user, assigned_task, task_project, auth_header_for
):
    headers = auth_header_for(employee_user)

    response = client.patch(
        (f"/projects/{task_project.id}/tasks/{assigned_task.id}"),
        headers=headers,
        json={"title": "Updated By Assignee"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated By Assignee"


def test_unassigned_employee_cannot_update_task(
    client, unrelated_user, assigned_task, task_project, auth_header_for
):
    headers = auth_header_for(unrelated_user)

    response = client.patch(
        (f"/projects/{task_project.id}/tasks/{assigned_task.id}"),
        headers=headers,
        json={"title": "Unauthorized Update"},
    )

    assert response.status_code == 403

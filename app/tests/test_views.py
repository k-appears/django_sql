import json
from datetime import datetime

import pytest
from django.db import connection
from django.urls import reverse
from rest_framework.exceptions import ErrorDetail
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)
from rest_framework.test import APIClient

from app.models import Machine, Simulation
from app.serializers import MachineSerializer


@pytest.fixture
def setup_test_data():
    with connection.cursor() as cursor:
        # Create simulation 1
        cursor.execute(
            "INSERT INTO app_simulation (name_description, status, machine_id, graph_data, creation_date) "
            "VALUES (%s, %s, %s, %s, %s)",
            [
                "Simulation 1",
                "running",
                1,
                json.dumps({"data": [{"seconds": 10, "loss": 0.8}]}),
                datetime(2011, 1, 1).strftime("%Y-%m-%d %H:%M:%S"),
            ],
        )
        simulation_1_id = cursor.lastrowid

        # Create simulation 2
        cursor.execute(
            "INSERT INTO app_simulation (name_description, status, machine_id, graph_data, creation_date) "
            "VALUES (%s, %s, %s, %s, %s)",
            [
                "Simulation 2",
                "pending",
                2,
                json.dumps({"data": [{"seconds": 20, "loss": 0.7}]}),
                datetime(2022, 1, 1).strftime("%Y-%m-%d %H:%M:%S"),
            ],
        )
        simulation_2_id = cursor.lastrowid

        # Create simulation 3
        cursor.execute(
            "INSERT INTO app_simulation (name_description, status, machine_id, graph_data, creation_date) "
            "VALUES (%s, %s, %s, %s, %s)",
            ["Simulation 3", "finished", 3, None, datetime(2003, 1, 1).strftime("%Y-%m-%d %H:%M:%S")],
        )
        simulation_3_id = cursor.lastrowid

        yield simulation_1_id, simulation_2_id, simulation_3_id


@pytest.mark.django_db
def test_list_simulations(setup_test_data):
    client = APIClient()
    response = client.get(reverse("simulations"))

    assert response.status_code == HTTP_200_OK
    simulations_data = json.loads(response.content)
    assert len(simulations_data) == 3

    assert simulations_data[0]["name_description"] == "Simulation 1"
    assert simulations_data[0]["status"] == "running"
    assert simulations_data[1]["name_description"] == "Simulation 2"
    assert simulations_data[1]["status"] == "pending"
    assert simulations_data[2]["name_description"] == "Simulation 3"
    assert simulations_data[2]["status"] == "finished"


@pytest.mark.django_db
def test_create_simulation():
    assert len(Simulation.list()) == 0
    assert len(Machine.list()) == 3

    client = APIClient()
    url = reverse("simulations")
    data = {"name_description": "Test Simulation", "machine_id": 1}
    response = client.post(url, data, format="json")

    assert response.status_code == HTTP_201_CREATED
    assert len(Machine.list()) == 3
    simulations = Simulation.list()
    assert len(simulations) == 1
    assert simulations[0].name_description == "Test Simulation"


@pytest.mark.django_db
def test_create_simulation_not_found_machine():
    assert len(Simulation.list()) == 0
    assert len(Machine.list()) == 3

    client = APIClient()
    url = reverse("simulations")
    data = {"name_description": "Test Simulation", "machine_id": 999}
    response = client.post(url, data, format="json")

    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_simulation_no_description():
    assert len(Simulation.list()) == 0
    assert len(Machine.list()) == 3

    client = APIClient()
    url = reverse("simulations")
    data = {"machine_id": 999}
    response = client.post(url, data, format="json")

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data == {"name_description": [ErrorDetail(string="This field is required.", code="required")]}


@pytest.mark.parametrize(
    "status, machine_id, simulation",
    [("running", 1, "Simulation 1"), ("pending", 2, "Simulation 2"), ("finished", 3, "Simulation 3")],
)
@pytest.mark.django_db
def test_filter_simulations_by_status(setup_test_data, status, machine_id, simulation):
    client = APIClient()
    response = client.get(reverse("simulations"), data={"status": status})

    assert response.status_code == HTTP_200_OK
    simulations_data = json.loads(response.content)
    assert len(simulations_data) == 1

    assert simulations_data[0]["name_description"] == simulation
    assert simulations_data[0]["status"] == status
    assert simulations_data[0]["machine"]["id"] == machine_id


@pytest.mark.parametrize(
    "field, expected_simulation",
    [("name_description", "Simulation 1"), ("creation_date", "Simulation 3"), ("update_date", "Simulation 1")],
)
@pytest.mark.django_db
def test_order_simulations_by_creation_date(setup_test_data, field, expected_simulation):
    client = APIClient()
    response = client.get(reverse("simulations"), data={"order_by": field})

    assert response.status_code == HTTP_200_OK
    simulations_data = json.loads(response.content)
    assert len(simulations_data) == 3
    assert simulations_data[0]["name_description"] == expected_simulation


@pytest.mark.django_db
def test_order_and_filter_simulations(setup_test_data):
    client = APIClient()
    response = client.get(reverse("simulations"), data={"order_by": "update_date", "status": "running"})

    assert response.status_code == HTTP_400_BAD_REQUEST
    [response] = json.loads(response.content)
    assert response == "Not implemented filter and order at the same time"


@pytest.mark.django_db
def test_get_details(setup_test_data):
    url = reverse("simulation-details", kwargs={"simulation_id": setup_test_data[0]})
    client = APIClient()
    response = client.get(url)
    assert response.status_code == HTTP_200_OK

    assert response.data["machine"] == {"id": 1, "description": "Machine 1"}
    assert response.data["name_description"] == "Simulation 1"
    assert response.data["status"] == "running"


@pytest.mark.django_db
def test_get_details_not_found():
    url = reverse("simulation-details", kwargs={"simulation_id": 999})
    client = APIClient()
    response = client.get(url)
    assert response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_list_machines(setup_test_data):
    client = APIClient()
    response = client.get(reverse("machines"))

    assert response.status_code == HTTP_200_OK
    machines_data = json.loads(response.content)
    assert len(machines_data) == 3

    assert response.data == MachineSerializer(instance=Machine.list(), many=True).data

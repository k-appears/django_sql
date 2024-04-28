import json
from datetime import datetime

import pytest
from django.db import connection

from app.models import Machine, Simulation


@pytest.fixture
def setup_test_data():
    with connection.cursor() as cursor:
        # 3 machines already preloaded in init script
        machine1_id = 1
        machine2_id = 2
        cursor.execute(
            "INSERT INTO app_simulation (name_description, status, machine_id, creation_date, update_date, graph_data) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            [
                "Simulation name 1",
                "pending",
                machine1_id,
                "2000-01-02",
                "2000-01-02",
                json.dumps(
                    {
                        "data": [
                            {"seconds": 10, "loss": 0.8},
                            {"seconds": 20, "loss": 0.7},
                            {"seconds": 30, "loss": 0.65},
                        ],
                    },
                ),
            ],
        )
        cursor.execute(
            "INSERT INTO app_simulation (name_description, status, machine_id, creation_date, update_date, graph_data) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            [
                "Simulation name 0",
                "running",
                machine2_id,
                "2000-01-01",
                "2000-01-01",
                json.dumps(
                    {
                        "data": [
                            {"seconds": 10, "loss": 0.61},
                            {"seconds": 50, "loss": 0.615},
                            {"seconds": 60, "loss": 0.60},
                        ],
                    },
                ),
            ],
        )


@pytest.mark.django_db
def test_list_simulations(setup_test_data):
    simulations = Simulation.list()
    assert len(simulations) == 2
    assert simulations[0].creation_date == simulations[0].update_date and isinstance(
        simulations[0].update_date,
        datetime,
    )
    assert simulations[0].name_description == "Simulation name 1"


@pytest.mark.django_db
def test_filter_simulations_by_status(setup_test_data):
    pending_simulations = Simulation.filter_by_status("pending")
    assert len(pending_simulations) == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "order_field, expected_simulation_id",
    [
        ("name_description", 2),
        ("creation_date", 2),
        ("update_date", 2),
    ],
)
def test_order_by(setup_test_data, order_field, expected_simulation_id):
    simulations_ordered_by_name = list(Simulation.order_by_field("name_description"))
    assert simulations_ordered_by_name[0].id == expected_simulation_id


def test_order_by_error():
    with pytest.raises(ValueError) as exc_info:
        Simulation.order_by_field("invalid_field")
    assert str(exc_info.value) == "Invalid field for ordering simulations."


@pytest.mark.django_db
def test_filter_error(setup_test_data):
    with pytest.raises(NotImplementedError) as exc_info:
        Simulation.objects.filter(name="Simulation 1").exists()
    assert str(exc_info.value) == "Do use ORM to query objects"


@pytest.mark.django_db
def test_get_details_db(setup_test_data):
    simulation = Simulation.get_details(simulation_id=1)
    assert simulation.name_description == "Simulation name 1"
    assert simulation.graph_data["data"][0] == {"seconds": 10, "loss": 0.8}


def test_get_details(mocker):
    simulation_data = {
        "id": 1,
        "name_description": "Simulation 1",
        "status": "pending",
        "machine_id": 1,
        "ma_description": "Machine 1",
        "graph_data": {"data": [{"seconds": 10, "loss": 0.8}]},
        "creation_date": "2021-01-01",
        "update_date": "2021-01-01",
    }
    simulation = mocker.Mock(**simulation_data)
    mocker.patch.object(Simulation.objects, "raw", return_value=[simulation])
    found_simulation = Simulation.get_details(simulation_id=1)
    assert found_simulation.name_description == simulation_data["name_description"]
    assert found_simulation.graph_data == simulation_data["graph_data"]
    assert found_simulation.machine.description == simulation_data["ma_description"]


def test_get_details_empty(mocker):
    mocker.patch.object(Simulation.objects, "raw", return_value=[])
    found_simulation = Simulation.get_details(simulation_id=1)
    assert not found_simulation


@pytest.mark.parametrize("machines", [[Machine(1, "Test Machine")], []])
def test_list_machines(machines, mocker):
    mocker.patch.object(Machine.objects, "raw", return_value=machines)
    found_machines = Machine.list()
    assert found_machines == machines
    Machine.objects.raw.assert_called_once_with("SELECT id, description FROM app_machine")


def test_get_machine(mocker):
    machine_id = 1
    machine_data = {"id": machine_id, "description": "Test Machine"}
    machine = mocker.Mock(**machine_data)
    mocker.patch.object(Machine.objects, "raw", return_value=[machine])
    found_machine = Machine.get_details(machine_id)
    assert found_machine.description == machine_data["description"]
    assert found_machine.id == machine_data["id"]
    Machine.objects.raw.assert_called_once_with(
        "SELECT id, description FROM app_machine WHERE id = %s",
        [machine_id],
    )

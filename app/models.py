from typing import List, Optional, TypeVar

from django.db import connection, models
from django.db.models import Model
from django.db.models.query import QuerySet
from django.db.models.base import ModelBase
from abc import ABCMeta

ModelT = TypeVar("ModelT", bound=Model)


class ABCModelMeta(ModelBase, ABCMeta):
    pass


class Unmanaged(models.Model, metaclass=ABCModelMeta):
    class Meta:
        abstract = True
        managed = False


class RestrictedManager(models.Manager[ModelT]):
    def get_queryset(self) -> QuerySet[ModelT]:
        return super().get_queryset()

    def all(self) -> QuerySet[ModelT]:
        raise NotImplementedError("Do use ORM to query objects")

    def get(self, *args: tuple[int | str], **kwargs: dict[str, str | int]) -> ModelT:
        raise NotImplementedError("Do use ORM to query objects")

    def filter(self, *args: tuple[int | str], **kwargs: dict[str, str | int]) -> QuerySet[ModelT]:
        raise NotImplementedError("Do use ORM to query objects")


class Machine(Unmanaged, RestrictedManager["Machine"]):
    description = models.CharField(max_length=100)

    objects = RestrictedManager()

    @staticmethod
    def list() -> list["Machine"]:
        machines = Machine.objects.raw("SELECT id, description FROM app_machine")
        return list(machines)

    @staticmethod
    def get_details(machined_id: int) -> Optional["Machine"]:
        machines = Machine.objects.raw("SELECT id, description FROM app_machine WHERE id = %s", [machined_id])
        return machines[0] if machines else None


class Simulation(Unmanaged, RestrictedManager["Simulation"]):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("finished", "Finished"),
    ]

    name_description = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, null=True, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    graph_data = models.JSONField(null=True, blank=True)

    objects = RestrictedManager()

    @staticmethod
    def filter_by_status(status: str) -> List["Simulation"]:
        raw_query_set = Simulation.objects.raw(
            "SELECT id, name_description, status FROM app_simulation WHERE status = %s",
            [status],
        )
        return list(raw_query_set)

    @staticmethod
    def order_by_field(field: str) -> List["Simulation"]:
        valid_fields = ["name_description", "creation_date", "update_date"]
        if field in valid_fields:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM app_simulation ORDER BY {field}")
                if not cursor.description:
                    return []
                simulations = [
                    Simulation(**{cursor.description[i][0]: value for i, value in enumerate(row)})
                    for row in cursor.fetchall()
                ]
                return simulations
        raise ValueError("Invalid field for ordering simulations.")

    @staticmethod
    def list() -> list["Simulation"]:
        raw_query_set = Simulation.objects.raw("SELECT id, name_description, status FROM app_simulation")
        return list(raw_query_set)

    @staticmethod
    def get_details(simulation_id: int) -> Optional["Simulation"]:
        query = """
            SELECT s.id, s.name_description, s.status, s.creation_date, s.update_date, s.graph_data, s.machine_id, ma.description as ma_description
            FROM app_simulation s
            LEFT JOIN app_machine ma ON s.machine_id = ma.id
            WHERE s.id = %s;
        """
        raw_query_set = Simulation.objects.raw(query, [simulation_id])
        for result in raw_query_set:
            return Simulation(
                id=result.id,
                name_description=result.name_description,
                status=result.status,
                machine=Machine(id=result.machine_id, description=result.ma_description) if result.machine_id else None,
                creation_date=result.creation_date,
                update_date=result.update_date,
                graph_data=result.graph_data,
            )
        return None

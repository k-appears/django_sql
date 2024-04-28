# your_app/views.py
from typing import Any

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import generics, serializers, views
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from .models import Machine, Simulation
from .serializers import (
    MachineSerializer,
    SimulationCreateSerializer,
    SimulationSerializer,
)


@extend_schema_view(
    get=extend_schema(
        summary="List Simulations",
        description="List existing Simulation runs with filtering and ordering options.",
        responses={HTTP_200_OK: SimulationSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                "status",
                location=OpenApiParameter.QUERY,
                enum=["pending", "running", "finished"],
                description="Fiter by status (pending, running, finished)",
            ),
            OpenApiParameter(
                "order_by",
                location=OpenApiParameter.QUERY,
                enum=["name_description", "creation_date", "update_date"],
                description="Order by name, creation date, or update date",
            ),
        ],
    ),
    post=extend_schema(
        summary="Create Simulation",
        description="Create a new simulation",
        request=SimulationCreateSerializer,
        responses={HTTP_201_CREATED: SimulationSerializer},
    ),
)
class SimulationCreateListView(generics.ListAPIView, generics.CreateAPIView):
    serializer_class = SimulationSerializer

    def get_queryset(self) -> list[Simulation]:
        status = self.request.query_params.get("status")
        ordering = self.request.query_params.get("order_by")
        if ordering and status:
            raise serializers.ValidationError("Not implemented filter and order at the same time")
        if ordering:
            return Simulation.order_by_field(ordering)
        if status:
            return Simulation.filter_by_status(status)

        return Simulation.list()

    def post(self, request: Request, *args: list[Any], **kwargs: dict[str, Any]) -> Response:
        serializer = SimulationCreateSerializer(data=request.data)
        if serializer.is_valid():
            if machine := Machine.get_details(machined_id=serializer.validated_data["machine_id"]):
                saved = serializer.save(machine=machine)
                return Response(SimulationSerializer(saved).data, status=HTTP_201_CREATED)
            return Response(status=HTTP_400_BAD_REQUEST, data={"message": "Machine not found"})

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class SimulationDetailsView(views.APIView):
    @extend_schema(
        summary="Get Simulation Details",
        description="Get details of a simulation by its ID",
        responses={HTTP_200_OK: SimulationSerializer},
    )
    def get(self, _: Request, simulation_id: int) -> Response:
        if simulation := Simulation.get_details(simulation_id):
            serializer = SimulationSerializer(simulation)
            return Response(serializer.data)
        return Response(status=HTTP_404_NOT_FOUND)


class MachineListView(views.APIView):
    """
    List all machines
    """

    @extend_schema(
        summary="List Machines",
        description="List all machines pre-registered in database as fixtures",
        responses={HTTP_200_OK: MachineSerializer},
        examples=[
            OpenApiExample(
                name="Example 1",
                value=[
                    {"id": 1, "description": "Machine 1"},
                    {"id": 2, "description": "Machine 2"},
                ],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        machines = Machine.list()
        serializer = MachineSerializer(machines, many=True)
        return Response(serializer.data)

# serializers.py
from typing import Any

from rest_framework import serializers  # type: ignore
from rest_framework.fields import CharField, IntegerField

from .models import Machine, Simulation


class SimulationCreateSerializer(serializers.Serializer):  # type: ignore
    machine_id = IntegerField(min_value=1)
    name_description = CharField(max_length=100)

    def create(self, validated_data: dict[str, Any]) -> Simulation:
        return Simulation.objects.create(**validated_data)


class SimulationSerializer(serializers.ModelSerializer):  # type: ignore
    class Meta:
        model = Simulation
        fields = ["id", "name_description", "status", "machine", "graph_data", "creation_date", "update_date"]
        depth = 1


class MachineSerializer(serializers.ModelSerializer):  # type: ignore
    class Meta:
        model = Machine
        fields = ["id", "description"]

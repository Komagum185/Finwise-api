from rest_framework import viewsets, permissions
from .models import InventoryItem, InventoryMovement
from .serializers import InventoryItemSerializer, InventoryMovementSerializer


class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated]


class InventoryMovementViewSet(viewsets.ModelViewSet):
    queryset = InventoryMovement.objects.all()
    serializer_class = InventoryMovementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # All authenticated users can see all inventory movements
        return super().get_queryset()



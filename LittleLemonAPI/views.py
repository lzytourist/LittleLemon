from datetime import date

from django.contrib.auth.models import User, Group
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Cart, Category, MenuItem, Order, OrderItem
from .permissions import IsManager
from .serializers import CartSerializer, CategorySerializer, MenuItemSerializer, OrderSerializer, OrderPartialUpdateSerializer


class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class MenuItemView(generics.ListCreateAPIView):
    serializer_class = MenuItemSerializer
    ordering_fields = ['price', 'category']
    search_fields = ['title', 'category__title']
    pagination_class = PageNumberPagination

    def get_queryset(self):
        queryset = MenuItem.objects.all()

        cat = self.request.query_params.get('category')
        if cat is not None:
            queryset = queryset.filter(category__title=cat)

        return queryset

    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated, IsManager]
        
        return [permission() for permission in self.permission_classes]


class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        if not self.request.method in SAFE_METHODS:
            self.permission_classes = [IsAuthenticated, IsManager]
        
        return [permission() for permission in self.permission_classes]


class ManagerGroupView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsManager]

    def list(self, request, *args, **kwargs):
        users = User.objects.filter(groups__name='Manager').all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        if not username:
            return Response({
                'username': [
                    'This field is required'
                ]
            }, status=400)
        
        user = get_object_or_404(User, username=username)
        group = get_object_or_404(Group, name='Manager')

        user.groups.add(group)
        
        return Response({'message': 'Manager added'}, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, userId):
        user = get_object_or_404(User, pk=userId)
        group = get_object_or_404(Group, name='Manager')

        user.groups.remove(group)

        return Response(status=status.HTTP_200_OK)


class DeliveryCrewGroupView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsManager]
    
    def list(self, request, *args, **kwargs):
        delivery_crews = User.objects.filter(groups__name='Delivery crew').all()
        serializer = UserSerializer(delivery_crews, many=True)

        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        if not username:
            return Response({
                'username': [
                    'This field is required'
                ]
            }, status=400)
        
        user = get_object_or_404(User, username=username)
        group = get_object_or_404(Group, name='Delivery crew')

        user.groups.add(group)
        
        return Response({'message': 'Delivery crew added'}, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, userId):
        user = get_object_or_404(User, pk=userId)
        group = get_object_or_404(Group, name='Delivery crew')

        user.groups.remove(group)

        return Response(status=status.HTTP_200_OK)
    

class CartView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer
    
    def get_queryset(self):
        return Cart.objects.select_related('menuitem').filter(user=self.request.user).all()
    
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            return Response({
                'message': 'Menu item already in the cart'
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': 'Menu item added to cart'
        }, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        Cart.objects.filter(user=request.user).all().delete()
        return Response({'message': 'Cart cleared'})
    

class OrderView(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def user_type(self, request):
        if request.user.groups.filter(name='Manager').exists():
            return 'Manager'
        elif request.user.groups.filter(name='Delivery crew').exists():
            return 'Delivery crew'
        return 'Customer'

    def get_permissions(self):
        if self.request.method == 'DELETE':
            self.permission_classes += [IsManager]
        
        return super().get_permissions()
    
    def get_queryset(self):
        queryset = self.queryset

        match self.user_type(self.request):
            case 'Customer':
                queryset = Order.objects.filter(user=self.request.user).all()
            case 'Delivery crew':
                queryset = Order.objects.filter(delivery_crew=self.request.user).all()
    
        return queryset
    
    def list(self, request, *args, **kwargs):
        return super().list(request, args, kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user=request.user).all()
        
        if cart.count() == 0:
            return Response({
                'message': 'Cart is empty'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        total_cost = 0
        for item in cart:
            total_cost += item.price
                        
        order = Order(
            user=request.user,
            total=total_cost,
            date=date.today()
        )
        order.save()

        order_items = []
        for item in cart:
            order_items.append(
                OrderItem(
                    order=order,
                    menuitem=item.menuitem,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    price=item.price
                )
            )
        
        OrderItem.objects.bulk_create(order_items)
        cart.delete()

        return Response({
            'message': 'Order placed'
        }, status=status.HTTP_201_CREATED)
    
    
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        self.serializer_class = OrderPartialUpdateSerializer

        print(self.get_serializer())
        return super().partial_update(request, args, kwargs)

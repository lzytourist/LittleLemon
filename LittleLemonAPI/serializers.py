from djoser.serializers import UserSerializer
from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Cart, Category, MenuItem, Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ['id', 'title', 'slug']


class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category', 'category_id']


class CartSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.IntegerField(write_only=True)

    def validate_menuitem_id(self, value):
        item = MenuItem.objects.filter(pk=value).exists()
        if not item:
            raise serializers.ValidationError('Invalid menuitem')
        return value

    class Meta:
        model = Cart
        fields = ['id', 'menuitem', 'menuitem_id', 'quantity', 'unit_price', 'price']
        extra_kwargs = {
            'price': {
                'read_only': True,
            },
            'unit_price': {
                'read_only': True
            }
        }
        depth = 1

    def create(self, validated_data):
        item = MenuItem.objects.get(pk=validated_data.get('menuitem_id'))
        
        validated_data['unit_price'] = item.price
        validated_data['price'] = item.price * validated_data.get('quantity')

        return super().create(validated_data)


class OrderItem(serializers.ModelSerializer):
    menuitem = MenuItemSerializer()

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'menuitem',
            'quantity',
            'unit_price',
            'price'
        ]


class OrderSerializer(serializers.ModelSerializer):
    delivery_crew = UserSerializer(read_only=True)
    delivery_crew_id = serializers.IntegerField(write_only=True)
    orderitem_set = OrderItem(many=True)

    class Meta:
        model = Order
        fields = ['id', 'delivery_crew', 'delivery_crew_id', 'status', 'total', 'date', 'orderitem_set']


# class OrderPartialUpdateSerializer(serializers.ModelSerializer):
#     delivery_crew_id = serializers.IntegerField()
#     class Meta:
#         model = Order
#         fields = ['id', 'delivery_crew_id', 'status']


class OrderPartialUpdateSerializer(serializers.ModelSerializer):
    delivery_crew_id = serializers.IntegerField()

    class Meta:
        model = Order
        fields = ['id', 'delivery_crew_id', 'status']

    
    def validate_delivery_crew_id(self, value):
        if not User.objects.filter(groups__name='Delivery crew').filter(pk=value).exists():
            raise serializers.ValidationError("Incorrect delivery crew")
        return value
    
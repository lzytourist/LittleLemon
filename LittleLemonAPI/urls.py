from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views


urlpatterns = [
    path('categories', views.CategoryView.as_view()),

    # Menu Items
    path('menu-items', views.MenuItemView.as_view()),
    path('menu-items/<int:pk>', views.SingleMenuItemView.as_view()),
    
    # Manager Group
    path('groups/manager/users', views.ManagerGroupView.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('groups/manager/users/<int:userId>', views.ManagerGroupView.as_view({
        'delete': 'destroy'
    })),

    # Delivery Crew Group
    path('groups/delivery-crew/users', views.DeliveryCrewGroupView.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('groups/delivery-crew/users/<int:userId>', views.DeliveryCrewGroupView.as_view({
        'delete': 'destroy'
    })),

    # Cart
    path('cart/menu-items', views.CartView.as_view({
        'get': 'list',
        'post': 'create',
        'delete': 'destroy'
    })),
]

router = SimpleRouter(trailing_slash=False)
router.register('orders', views.OrderView)

urlpatterns += router.urls

from django.contrib.auth.models import User
from django.db import models


class Category(models.Model):
    slug = models.SlugField()
    title = models.CharField(max_length=255, db_index=True)

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        ordering = ['id']


class MenuItem(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    price = models.DecimalField(max_digits=5, decimal_places=2, db_index=True)
    featured = models.BooleanField(db_index=True)
    category = models.ForeignKey(
        to=Category,
        on_delete=models.PROTECT
    )

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        ordering = ['id']


class Cart(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE
    )
    menuitem = models.ForeignKey(
        to=MenuItem,
        on_delete=models.CASCADE
    )
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=5, decimal_places=2)
    price = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = ('menuitem', 'user')
        ordering = ['id']


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_crew = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='delivery_crew', null=True)
    status = models.BooleanField(db_index=True, default=0)
    total = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField(db_index=True)

    class Meta:
        ordering = ['id']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=5, decimal_places=2)
    price = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = ('order', 'menuitem')
        ordering = ['id']

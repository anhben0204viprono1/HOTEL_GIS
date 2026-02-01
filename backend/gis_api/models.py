from django.db import models


class Hotel(models.Model):
    hotel_id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)

    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)

    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)

    star_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        null=True,
        blank=True
    )

    total_reviews = models.IntegerField(default=0)

    description = models.TextField(blank=True, null=True)

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)

    image_url = models.URLField(max_length=500, blank=True, null=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "hotels"
        ordering = ["-created_date"]

    def __str__(self):
        return self.name

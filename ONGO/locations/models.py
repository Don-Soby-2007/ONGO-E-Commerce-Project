from django.db import models

# Create your models here.


class PincodeLocation(models.Model):
    pincode = models.CharField(max_length=6, unique=True, db_index=True)
    district = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = "Pincode Location"
        verbose_name_plural = "Pincode Locations"
        ordering = ['pincode']

    def __str__(self):
        return f"{self.pincode} - {self.state}"

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

STATUS_CHOICES = [
    ('PENDING_OTP','Pending OTP'),
    ('ACTIVE','Active'),
    ('IN_USE','In Use'),
    ('USED','Used'),
    ('EXPIRED','Expired'),
]

class Config(models.Model):
    enable = models.BooleanField(default=True)

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    def __str__(self):
        return f"Wallet({self.user.username}): {self.balance}"

class Line(models.Model):
    name = models.CharField(max_length=200, unique=True)
    enable = models.BooleanField(default=True)
    def __str__(self):
        return self.name

class Station(models.Model):
    name = models.CharField(max_length=200, unique=True)
    def __str__(self):
        return self.name

class StationLine(models.Model):
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='station_station')
    line = models.ForeignKey(Line, on_delete=models.CASCADE, related_name='station_line')
    position = models.IntegerField(default=1)
    def __str__(self):
        return f"{self.station} ({self.line} -> {self.position})"

class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets', null=True, blank=True)
    start = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='tickets_start')
    end = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='tickets_end')
    path = models.JSONField(default=list)
    direction = models.JSONField(default=list)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return f"Ticket {self.id} ({self.start} -> {self.end})"

class PurchaseRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchase_requests')
    start_name = models.CharField(max_length=200)
    end_name = models.CharField(max_length=200)
    path = models.JSONField(default=list)
    direction = models.JSONField(default=list)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"PurchaseRequest {self.id} ({self.start_name} -> {self.end_name})"

class OTP(models.Model):
    purchase = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    def is_valid(self):
        return timezone.now() < self.expires_at

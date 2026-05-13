from django.db import models
from django.contrib.auth.models import User

class ConversionHistory(models.Model):
    """Enregistre chaque conversion effectuée."""

    user          = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    from_currency = models.CharField(max_length=3)
    to_currency   = models.CharField(max_length=3)
    amount        = models.DecimalField(max_digits=15, decimal_places=4)
    converted     = models.DecimalField(max_digits=15, decimal_places=4)
    rate          = models.DecimalField(max_digits=15, decimal_places=6)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Conversion'
        verbose_name_plural = 'Historique des conversions'

    def __str__(self):
        return f"{self.amount} {self.from_currency} → {self.converted} {self.to_currency}"
from django.db import models

class AgentLog(models.Model):
    machine_id = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    risk_score = models.FloatField()
    recommendation = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.machine_id} - {self.status}"

class SensorReading(models.Model):
    machine_id = models.CharField(max_length=100, db_index=True)
    vibration = models.FloatField()
    temperature = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['machine_id', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.machine_id} - {self.timestamp}"
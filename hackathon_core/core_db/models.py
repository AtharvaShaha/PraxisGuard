from django.db import models

class AgentLog(models.Model):
    machine_id = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    risk_score = models.FloatField()
    recommendation = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.machine_id} - {self.status}"
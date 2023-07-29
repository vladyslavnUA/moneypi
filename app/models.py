from django.db import models

class Employee(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class WorkRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(null=True, blank=True)
    date = models.DateField()
    comments = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee} - {self.date}"
        # return f"{self.employee} : {self.clock_in} - {self.clock_out}"
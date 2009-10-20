from django.db import models

class FakeImage(models.Model):
    image = models.ImageField(upload_to='fakeapp')
    misc = models.IntegerField()

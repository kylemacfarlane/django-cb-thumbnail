from django.db import models


# Needed for a ModelsTests.test_audodiscover
Model = models.Model


class FakeImage(models.Model):
    image = models.ImageField(upload_to='fakeapp')
    misc = models.IntegerField()

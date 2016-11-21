from django.db import models

# Create your models here.

class Host(models.Model):
  #ip = models.IPAddressField(unique=True)
  ip = models.GenericIPAddressField(unique=True)
  hostname = models.TextField()
  country = models.TextField()

  ports = models.CommaSeparatedIntegerField(max_length=65535)
  data = models.TextField()

  ctime = models.DateTimeField(auto_now_add=True, auto_now=False)
  mtime = models.DateTimeField(auto_now_add=False, auto_now=True)


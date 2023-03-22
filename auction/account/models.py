from django.db import models
from django.conf import settings as dj_settings


class Profile(models.Model):
    """ Additional user fields."""
    PHOTO_UPLOAD_TO = 'users/%Y/%m/%d/'

    user = models.OneToOneField(dj_settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_of_birth = models.DateField(blank=True, null=True)
    photo = models.ImageField(upload_to=PHOTO_UPLOAD_TO, blank=True)
    # TODO: add other fields: phone, different lists of lots (won, follow up, created)

    def __str__(self):
        return f'Profile of {self.user.username}'

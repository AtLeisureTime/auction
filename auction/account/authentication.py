from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.http.request import HttpRequest


class EmailAuthBackend(ModelBackend):
    """ Authentication based on using of email addresses.
        Type your email into 'email' field on your registration.
        Type your email into 'username' field in login form.
        You will be authenticated if no one but you provide the same email on registration.
    """

    def authenticate(self, request: HttpRequest, username: str = None,
                     password: str = None) -> User | None:
        try:
            user = User.objects.get(email=username)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
            return None
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            # User.email: unique=False and blank=True
            return None

    def user_can_authenticate(self, user: User) -> bool:
        """ Reject users with is_active=False."""
        is_active = getattr(user, "is_active", None)
        return is_active or is_active is None

    def get_user(self, user_id) -> User | None:
        try:
            user = User.objects.get(pk=user_id)
            return user if self.user_can_authenticate(user) else None
        except User.DoesNotExist:
            return None

# This file is a customization of django's built-in authentication. It allows users to log in w/ their email address, as opposed to using username (the default for Django) 
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class EmailAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        if not username or not password:
            return None

        try:
            user = UserModel.objects.get(email=username)  # Use email to authenticate
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce timing
            # differences between an existing and a non-existing user (#20760).
            UserModel().set_password(password)

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None

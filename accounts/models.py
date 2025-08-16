from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

from .utils import create_otp


class JTUserManager(BaseUserManager):
    """User manager that works with email‑only authentication."""
    use_in_migrations = True

    def get_queryset(self):
        print("query form manager....")
        return super().get_queryset()

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email address must be set")
        email = self.normalize_email(email)
        print("____create")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        print("create user.....")
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


AGENCY_CHOICES = (
    ("ABC", "ABC"),
    ("CBA", "CBA")
)


class JTUser(AbstractUser):
    email = models.EmailField(unique=True, null=False, blank=False)
    profile_image = models.ImageField(upload_to="profile_images/", null=True, blank=True, verbose_name='profile_images')
    # full_name = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=255, null=True, blank=True, choices=[
        ("Male", "Male"),
        ("Female", "Female"),
        ('Disabled', 'Disabled')
    ])
    agency = models.CharField(
        choices=AGENCY_CHOICES,
        null=True
    )
    age = models.IntegerField(null=True, blank=True, default=None)
    username = models.CharField(max_length=30, unique=True, null=True, blank=True)

    otp = models.CharField(default=create_otp, max_length=10)

    email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = JTUserManager()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        print("hey........")
        if not hasattr(self, 'profile_image'):
            return
        try:
            img = Image.open(self.profile_image.path)
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return
        if img.height < 300 and img.width < 300:
            if os.path.exists(self.profile_image.path):
                os.remove(self.profile_image.path)
            raise ValidationError("image minimum size must be >300x300")
        output_size = (300, 300)
        img.thumbnail(output_size)
        img.save(self.profile_image.path)
    pass


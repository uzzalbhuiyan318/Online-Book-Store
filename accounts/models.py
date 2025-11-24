from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User Model"""
    
    email = models.EmailField(unique=True, verbose_name='Email Address')
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name='Phone Number')
    full_name = models.CharField(max_length=255, verbose_name='Full Name')
    full_name_bn = models.CharField(max_length=255, null=True, blank=True, verbose_name='Full Name (Bangla)')
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True, verbose_name='Profile Image')
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return self.full_name
    
    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else self.email


class Address(models.Model):
    """User Address Model"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=255, verbose_name='Full Name')
    full_name_bn = models.CharField(max_length=255, null=True, blank=True, verbose_name='Full Name (Bangla)')
    phone = models.CharField(max_length=20, verbose_name='Phone Number')
    email = models.EmailField(verbose_name='Email Address', null=True, blank=True)
    address_line1 = models.CharField(max_length=255, verbose_name='Address Line 1')
    address_line1_bn = models.CharField(max_length=255, null=True, blank=True, verbose_name='Address Line 1 (Bangla)')
    address_line2 = models.CharField(max_length=255, null=True, blank=True, verbose_name='Address Line 2')
    address_line2_bn = models.CharField(max_length=255, null=True, blank=True, verbose_name='Address Line 2 (Bangla)')
    city = models.CharField(max_length=100, verbose_name='City')
    city_bn = models.CharField(max_length=100, null=True, blank=True, verbose_name='City (Bangla)')
    state = models.CharField(max_length=100, verbose_name='State/Division')
    state_bn = models.CharField(max_length=100, null=True, blank=True, verbose_name='State/Division (Bangla)')
    postal_code = models.CharField(max_length=20, verbose_name='Postal Code')
    country = models.CharField(max_length=100, default='Bangladesh', verbose_name='Country')
    is_default = models.BooleanField(default=False, verbose_name='Default Address')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.city}"
    
    def save(self, *args, **kwargs):
        # If this address is set as default, remove default from other addresses
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    @property
    def full_address(self):
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.extend([self.city, self.state, self.postal_code, self.country])
        return ', '.join(parts)

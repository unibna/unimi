from random import choice
from string import ascii_letters

from django.db import models
from django.utils.text import slugify

from apps.account.models import Employee


ITEM_FOLDER = 'store/item/'
ITEM_EXTRA_FOLDER = 'store/item_extra/'
LOGO_FOLDER = 'store/logo/'

DEFAULT_ITEM = 'store/item/default-item.png'
DEFAULT_EXTRA = 'store/item_extra/default-extra.png'
DEFAULT_LOGO = 'store/logo/default-logo.png'

class StoreCategory(models.Model):

    name = models.CharField(max_length=32, unique=True)
    slug = models.SlugField(max_length=32, unique=True, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        return super().save(*args, **kwargs)


class Store(models.Model):

    owner = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=64, null=True)
    email = models.EmailField(max_length=64, null=True)
    phone = models.CharField(max_length=11, null=True)
    description = models.CharField(max_length=512, null=True)
    logo = models.ImageField(upload_to=LOGO_FOLDER, default=DEFAULT_LOGO, null=True, blank=True)
    address = models.CharField(max_length=128, null=True)
    open_time = models.TimeField(null=True)
    close_time = models.TimeField(null=True)
    rating = models.FloatField(default=0, null=True)
    slug = models.SlugField(max_length=64, unique=True, null=True)
    secret_key = models.CharField(max_length=128, unique=True, null=True)
    store_category = models.ForeignKey(
        StoreCategory,
        on_delete=models.CASCADE,
        default=11,
    )
    is_valid = models.BooleanField(default=False)
    # location = PointField(null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.secret_key:
            self.secret_key = self.generate_secret_key()

        return super().save(*args, **kwargs)

    def generate_secret_key(self):
        return ''.join(choice(ascii_letters) for i in range(128))


class JoinStore(models.Model):

    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True)
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    join_date = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=False)


class Menu(models.Model):

    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    name = models.CharField(max_length=32, null=True)
    is_active = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.store} - {self.name}"


class Item(models.Model):

    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    name = models.CharField(max_length=128, null=True)
    is_active = models.BooleanField(default=False)
    image = models.ImageField(upload_to=ITEM_FOLDER, default=DEFAULT_ITEM, null=True, blank=True)
    price = models.FloatField(default=0)
    rating = models.FloatField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ItemExtraGroup(models.Model):

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    name = models.CharField(max_length=32, null=True)
    is_active = models.BooleanField(default=False)


class IteamExtra(models.Model):

    item_extra_group = models.ForeignKey(
        ItemExtraGroup,
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=64, null=True)
    value = models.CharField(max_length=128, null=True)
    price = models.FloatField(default=0)
    image = models.ImageField(upload_to=ITEM_EXTRA_FOLDER, default=DEFAULT_EXTRA, null=True, blank=True)
    is_active = models.BooleanField(default=False)

    # fix the typing error of class name
    class Meta:

        verbose_name = 'ItemExtra'
        verbose_name_plural = 'ItemExtra'

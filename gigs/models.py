# from django.db import models
# from django.conf import settings

# # Create your models here.
# class Gig(models.Model):
#     seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     title = models.CharField(max_length=200)
#     description = models.TextField()
#     price = models.DecimalField(max_digits=8, decimal_places=2)
#     image = models.ImageField(upload_to='gigs/')
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):
#         return self.title


from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Gig(models.Model):

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gigs'
    )

    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True, blank=True)

    description = models.TextField()

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    image = models.ImageField(
        upload_to='gigs/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            num = 1

            while Gig.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.seller.username}"

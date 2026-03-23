from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
# from orders.models import Order
# from django.contrib.auth.models import User
from django.db import models

# from accounts.models import SellerProfile
class User(AbstractUser):

    class Roles(models.TextChoices):
        BUYER = "buyer", "Buyer"
        SELLER = "seller", "Seller"

    role = models.CharField(
        max_length=10,
        choices=Roles.choices,
        default=Roles.BUYER,
        db_index=True
    )

    bio = models.TextField(null=True)  # null not needed for TextField
    
    profile_pic = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
class SellerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seller_profile'
    )

    skills = models.ManyToManyField(Skill,blank=True)
    experience = models.IntegerField(blank=True, null=True)
    portfolio_link = models.URLField(blank=True)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rating = models.FloatField(default=0)
    location = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"
    
class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    message = models.TextField()
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.message}"

class Profile(models.Model):

    LEVEL_CHOICES = [
        ("new", "New Seller"),
        ("level1", "Level 1 Seller"),
        ("level2", "Level 2 Seller"),
        ("level3", "Level 3 Seller"),
        ("top", "Top Rated Seller"),
    ]

    AVAILABILITY_CHOICES = [
        ("available", "Available"),
        ("busy", "Busy"),
        ("offline", "Offline"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    image = models.ImageField(
        upload_to="profiles/",
        default="profiles/default.png"
    )

    bio = models.TextField(blank=True)

    skills = models.CharField(
        max_length=300,
        blank=True,
        help_text="Example: Python, Django, HTML, CSS"
    )

    location = models.CharField(
        max_length=100,
        blank=True
    )

    level = models.CharField(
        max_length=10,
        choices=LEVEL_CHOICES,
        default="new"
    )

    availability = models.CharField(
        max_length=10,
        choices=AVAILABILITY_CHOICES,
        default="available"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
   
@receiver(post_save, sender=User)
def create_seller_profile(sender, instance, created, **kwargs):
    if created:# and instance.role == "seller":
        SellerProfile.objects.create(user=instance)


    
# =========================
# Coding Test Model
# =========================
class CodingTest(models.Model):
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    min_score = models.IntegerField(default=70)

    def __str__(self):
        return self.title


# =========================
# Questions Model
# =========================
class Question(models.Model):
    test = models.ForeignKey(CodingTest, on_delete=models.CASCADE)
    question_text = models.TextField()
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    correct_answer = models.CharField(max_length=200)

    def __str__(self):
        return self.question_text


# =========================
# Test Attempt Model
# =========================
class TestAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(CodingTest, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.test.title}"
    
# =========================
# Coding Problem Model
# =========================
class CodingProblem(models.Model):
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    problem_type = models.CharField(max_length=20,choices=[("backend", "Backend"),("frontend", "Frontend"),],default="backend")
    title = models.CharField(max_length=200)
    description = models.TextField()
    sample_input = models.TextField()
    sample_output = models.TextField()
    min_score = models.IntegerField(default=70)
    max_attempts = models.IntegerField(default=3)
    difficulty = models.CharField(max_length=10,choices=[("easy", "Easy"),("medium", "Medium"),("hard", "Hard"),],default="easy")
    language = models.CharField(max_length=20,choices=[("python", "Python"),("javascript", "JavaScript"),("cpp", "C++"),("java", "Java"),("html", "HTML"),("css", "CSS"),],default="python")
    
    def __str__(self):
        return self.title


# =========================
# Test Case Model
# =========================
class TestCase(models.Model):
    problem = models.ForeignKey(CodingProblem, on_delete=models.CASCADE)
    input_data = models.TextField()
    expected_output = models.TextField()
    is_hidden = models.BooleanField(default=True)
    
    def __str__(self):
        return f"TestCase for {self.problem.title}"
    


# =========================
# Freelancer Skill Mapping
# =========================
class FreelancerSkill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.skill.name}"

# =========================
# Submission Model
# =========================
class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey("CodingProblem", on_delete=models.CASCADE)
    code = models.TextField()
    score = models.FloatField(default=0)
    passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.problem.title}"
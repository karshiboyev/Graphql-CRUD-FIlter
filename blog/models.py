
from django.db.models import Model, ForeignKey, ManyToManyField, CASCADE
from django.db.models.fields import CharField, EmailField, TextField, DateTimeField, BooleanField, IntegerField


class Author(Model):
    name = CharField(max_length=100)
    email = EmailField()
    bio = TextField(blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Category(Model):
    name = CharField(max_length=50)
    description = TextField(blank=True)

    def __str__(self):
        return self.name


class Post(Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    title = CharField(max_length=200)
    content = TextField()
    excerpt = TextField(blank=True)
    author = ForeignKey(Author, on_delete=CASCADE, related_name='posts')
    categories = ManyToManyField(Category, blank=True)
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    featured = BooleanField(default=False)
    view_count = IntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    published_at = DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

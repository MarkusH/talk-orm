from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, related_name='books')
    authors = models.ManyToManyField(Author, through='AuthorBookThrough', related_name='books_m2m')

    def __str__(self):
        return self.title


class AuthorBookThrough(models.Model):
    author = models.ForeignKey(Author)
    book = models.ForeignKey(Book)

    class Meta:
        unique_together = (
            ('author', 'book'),
        )

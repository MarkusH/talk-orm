from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    votes = models.PositiveIntegerField()
    authors = models.ManyToManyField(
        Author, through="AuthorBookThrough", related_name="books_m2m"
    )
    genres = models.ManyToManyField("Genre", related_name="books")

    def __str__(self):
        return self.title


class AuthorBookThrough(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("author", "book"),)


class Genre(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

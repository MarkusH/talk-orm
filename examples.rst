========
Examples
========

..

    To run this file as ``doctest``, load the fixtures as stated in the
    ``README.md``. With an activated virtualenv and all dependencies
    installed::

        $ python -m doctest -o NORMALIZE_WHITESPACE -o ELLIPSIS -o IGNORE_EXCEPTION_DETAIL examples.rst


Setup
=====

Before we begin with the examples we need to do some setup: we need to "boot"
Django and configure it:

.. code:: python

    >>> import os
    >>> import django
    >>> os.environ.setdefault("DJANGO_SETTINGS_MODULE", "talk.settings")
    'talk.settings'
    >>> django.setup()

Counting objects
================

Let's start with something basic. We'll count how many records we have in the
database:

.. code:: python

    >>> from literature.models import Author, Book, Genre

    >>> Author.objects.count()
    1142
    >>> Book.objects.count()
    3578
    >>> Genre.objects.count()
    412

Fetching single objects
=======================

Great, let's fetch some random author from the database:

.. code:: python

    >>> Author.objects.get()
    Traceback (most recent call last):
      File "<console>", line 1, in <module>
      File ".../django/db/models/manager.py", line 82, in manager_method
        return getattr(self.get_queryset(), name)(*args, **kwargs)
      File ".../django/db/models/query.py", line 403, in get
        (self.model._meta.object_name, num)
    literature.models.Author.MultipleObjectsReturned: get() returned more than one Author -- it returned 1142!

Well, that obviously didn't go as planned. We got an exception that multiple
objects got returned. That's what ``get()`` is all about. It returns
**exactly** one object. Not zero, not two or more. One!

Alternatively, we could use ``first()``:

.. code:: python

    >>> Author.objects.first()
    <Author: Bill Bryson>

The difference here, ``first()`` may return ``None`` in case there is no record
to return. We can see that when we try to select me as an author:

.. code:: python

    >>> Author.objects.filter(name="Markus").first()
    >>> Author.objects.filter(name="Markus").get()
    Traceback (most recent call last):
      File "<console>", line 1, in <module>
      File ".../django/db/models/query.py", line 399, in get
        self.model._meta.object_name
    literature.models.Author.DoesNotExist: Author matching query does not exist.

While ``first()`` returned ``None``, ``get()`` raised a ``DoesNotExist``
exception.

Advanced filtering
==================

We've just seen how we can filter on the exact value of a model field when
querying the database. But there's more. For example, we can select all authors
whose name starts with ``"Lisa"``:

.. code:: python

    >>> Author.objects.filter(name__startswith="Lisa")
    <QuerySet [<Author: Lisa Unger>, <Author: Lisa Scottoline>, ...]>

Similarly, when we don't care about upper and lower case and only care if the
character sequence is part of a record, we can use ``__icontains``:

.. code:: python

    >>> Author.objects.filter(name__icontains="tom")
    <QuerySet [<Author: Robert Tombs>, <Author: Tom Barbash>, <Author: Tom Sweterlitsch>, ...]>

Following related objects
=========================

Let's say we want to print a list of all books with their corresponding author.
The first approach we will make may very well look like this:

.. code:: python

    >>> books = Book.objects.all()
    >>> for book in books:
    ...     print(f"Title: {book.title} -- Author: {book.author.name}")
    Title: ...


That works, we end up with *a lot* of database queries. Specifically, we end up
with ``1 + $number_of_books`` queries. Why is that?

First, we're selecting all the books. That's one query. Then, in the for loop,
we make *one query per book*. In case you're wondering: that is *bad*!

Sidebar: Inspecting database queries
------------------------------------

When you're developing your Django project or app, it can be helpful to check
the recent database queries quickly. For that, Django tracks them on the
database connection:

.. code:: python

    >>> from django.db import connection

    >>> connection.queries
    [...]

Following `one-to-one` and `many-to-one` relationships
------------------------------------------------------

Getting back to where we left off, we need to find a way to optimize our ``1 +
$number_of_books`` database queries. And Django has just the right tool for
that: ``select_related()``. This queryset method tells Django to fetch
*forward relationships* when making the initial query:

.. code:: python

    >>> books = Book.objects.select_related("author").all()
    >>> for book in books:
    ...     print(f"Title: {book.title} -- Author: {book.author.name}")
    Title: ...

Now we have only 1 query. Exactly what we wanted.

I wrote above that ``select_related()`` is for *forward relationships*. That
means, it only ever works when on the other end of the relationships is at most
one object. "At most," because that related object could also be ``None``,
e.g. when you have a ``ForeignKey`` with ``null=True``. In other words, you
can use ``select_related()`` when the current model has a ``ForeignKey`` or
``OneToOneField``, or if the current model is the opposite end of an
``OneToOneField``. It will **not** work for ``ManyToManyFields`` or the reverse
of a ``ForeignKey``.

Following `one-to-many` and `many-to-many` relationships
--------------------------------------------------------

When there are `one-to-one` and `many-to-one` relationships, there are probably
`one-to-many` and `many-to-many` as well. And indeed, there are. You use them
when you have ``ManyToManyFields`` or when you follow a ``ForeignKey``
backward.

Given our database schema, we have that scenario when we want to list all the
books for each author. The naïve approach will look a bit like this:

.. code:: python

    >>> authors = Author.objects.all()
    >>> for author in authors:
    ...     print(f"Author: {author.name}")
    ...     for book in author.books.all():
    ...         print(f"  - title: {book.title}")
    Author: ...

As you might imagine, this has similar problems as the example I had above. We
now have ``1 + $number_of_authors`` queries: one for the list of authors, and one
for each author to get the books. We can optimize this can to exactly two
database queries:

.. code:: python

    >>> authors = Author.objects.prefetch_related("books")
    >>> for author in authors:
    ...     print(f"Author: {author.name}")
    ...     for book in author.books.all():
    ...         print(f"  - title: {book.title}")
    Author: ...

Django will construct a *prefetch query* under the hood which pretty much
equals to:

.. code:: python

    >>> books = Book.object.filter(author_id__in=...)

The filter on ``author_id`` will automatically be populated by Django and limit
the books to the set of authors selected in the first query.

If you want to limit the books queryset further, you can do so using
``Prefetch`` objects:

.. code:: python

    >>> from django.db.models import Prefetch

    >>> prefetch_qs = Book.objects.filter(title__startswith="H")
    >>> authors = Author.objects.prefetch_related(
    ...     Prefetch("books", queryset=prefetch_qs)
    ... )

Aggregating data
================

All the things above are somewhat basic and something everybody using Django
will come across eventually. The following about data aggregation and
annotating database objects with additional information is something that's
still common, but it may take some time for this to come up in a project.

Let's ``COUNT`` again
---------------------

Let's start by counting the number of books per author:

.. code:: python

    >>> from django.db.models import Count

    >>> authors = Author.objects.annotate(book_count=Count("books"))
    >>> for author in authors:
    ...     print(f"Author: {author.name}: {author.book_count}")
    Author: ...

We get a list that looks like this::

    Author: Jen Wang: 10
    Author: Sarah MacLean: 12
    Author: Charles Soule: 12
    Author: A.S. King: 1
    Author: Jesmyn Ward: 1
    Author: Victor LaValle: 2

And at this point, it's interesting to start to look at the SQL Django
generated:

.. code:: sql

    SELECT
        "literature_author"."id",
        "literature_author"."name",
        COUNT("literature_book"."id") AS "book_count"
    FROM "literature_author"
    LEFT OUTER JOIN "literature_book"
        ON ("literature_author"."id" = "literature_book"."author_id")
    GROUP BY
        "literature_author"."id", "literature_author"."name"

The critical puzzle piece in this SQL statement is the ``JOIN`` between the
author and book tables with the ``COUNT`` in the ``SELECT`` clause. Django
shifts the entire work to calculate the sum of books per author to the
database.

Let's ``SUM`` it up
-------------------

What we have is already great. Now, let's look into finding the top five
authors with the most votes across all books:

.. code:: python

    >>> from django.db.models import Sum

    >>> authors = Author.objects.annotate(
    ...     sum_votes=Sum("books__votes")
    ... ).order_by("-sum_votes")[:5]
    >>> for author in authors:
    ...     print(f"Author: {author.name}: {author.sum_votes} votes")
    Author: J.K. Rowling: 10354107 votes
    Author: Suzanne Collins: 10270371 votes
    Author: Rick Riordan: 5860434 votes
    Author: John Green: 5694398 votes
    Author: Stephen King: 5181285 votes

Annotating "arbitrary" data
---------------------------

The annotations shown above are not the only thing Django can do. There's a lot
more:

.. code:: python

    >>> from django.db.models import CharField, Value
    >>> from django.db.models.functions import StrIndex, Substr

    >>> substr_exp = Substr(
    ...     "name",
    ...     1,
    ...     StrIndex("name", Value(" ")) - Value(1),
    ...     output_field=CharField(max_length=100),
    ... )
    >>> Author.objects.annotate(
    ...     first_name=substr_exp
    ... ).annotate(
    ...     book_count=Count("books")
    ... ).order_by("-book_count")
    <QuerySet [<Author: Stephen King>, <Author: Peter     Meredith>, ...']>

This query will count the books per author, but will also attach the "first
name" to each model instance.

If we add the ``values()`` queryset method after the first ``annotate()``
method we effectively group on the counting by the first name:

.. code:: python

    >>> Author.objects.annotate(
    ...     first_name=substr_exp
    ... ).values(
    ...     "first_name"
    ... ).annotate(
    ...     book_count=Count("books")
    ... ).order_by("-book_count")
    <QuerySet [{'first_name': 'Lisa', 'book_count': 56}, {'first_name': 'David', 'book_count': 53}, ...]>

I'm well aware that this is a lot to digest and understand. The Django
documentation has a `whole chapter on aggregations`_ that I can highly
recommend to read through and have a look at whenever you need to deal with
aggregations and annotations, because I haven't even covered half of it.

Top-k selects
=============

The last thing I want to cover is something that's generally not easy to
express in SQL and also computational wise rather heavy. It's about selecting
the *top-k* elements for something else.

The typical approach to this problem, across all databases, is the use of
*subqueries*. A subquery is a full SQL query that will run as part of a "main"
database query.

Let's start by first selecting the top three books by the number of votes per
author, and then the top three books by votes per genre.

Top three by author
-------------------

When we discussed the ``prefetch_related`` method before, we already looked
into the ``Prefetch`` object. We will leverage that here. Let's build this
query piece by piece.

We want authors and a set of books that belong to each author. For now, the
``books_qs`` won't be doing much:

.. code:: python

    >>> books_qs = Book.objects.all()
    >>> authors = Author.objects.prefetch_related(
    ...     Prefetch("books", queryset=books_qs)
    ... )

With this, we will prefetch all books that belong to an author. As a next step,
let's sort the list of books by votes in descending order:

.. code:: python

    >>> books_qs = Book.objects.order_by("-votes")

The last step is to limit the number of books to *k*. The approach everybody
takes will be this:

.. code:: python

    >>> books_qs = Book.objects.order_by("-votes")[:3]

However, this will cause Django to raise an exception:

    Cannot filter a query once a slice has been taken.

If one thinks about that, Django will take the ``book_qs`` and apply a
``filter()`` call on the ``author_id`` to limit the books to the list of
authors selected before. So, we need another approach. There's already a
`feature request ticket`_ on the Django bug tracker.

Instead, we need to look into ``Subquery`` and ``OuterRef``.

First, we'll select the primary key of the top *k* books while filtering on an
*outer reference* to a ``author_id``. This queryset will not work on its own.
It will only ever work in the context of a subquery that knows about a
``author_id``.

We then put that ``book_sub_qs`` into a subquery. With that, the inner query
"knows" about the ``author_id``. If we were to iterate over ``books_qs``, we'd
get a list of books, the first book having the most votes, and not more than 3
books per author:

.. code:: python

    >>> from django.db.models import OuterRef, Subquery

    >>> book_sub_qs = Book.objects.filter(
    ...     author_id=OuterRef("author_id")
    ... ).order_by("-votes").values_list("id", flat=True)[:3]
    >>> books_qs = Book.objects.filter(pk__in=Subquery(book_sub_qs)).order_by("-votes")

With that, we can now go back to our ``Prefetch()`` object and combine authors
and books:

.. code:: python

    >>> book_sub_qs = Book.objects.filter(
    ...     author_id=OuterRef("author_id")
    ... ).order_by("-votes").values_list("id", flat=True)[:3]
    >>> books_qs = Book.objects.filter(pk__in=Subquery(book_sub_qs)).order_by("-votes")
    >>> authors = Author.objects.prefetch_related(Prefetch("books", queryset=books_qs))
    >>> for author in authors:
    ...     print(f"Author: {author.name}")
    ...     for book in author.books.all():
    ...         print(f"  - {book.title}")
    Author: ...

.. code:: sql

    SELECT
        "literature_book"."id",
        "literature_book"."title",
        "literature_book"."author_id",
        "literature_book"."votes"
    FROM "literature_book"
    WHERE
        "literature_book"."id" IN (
            SELECT
                U0."id"
            FROM "literature_book" U0
            WHERE
                U0."author_id" = "literature_book"."author_id"
            ORDER BY
                U0."votes" DESC
            LIMIT 3
        )
        AND "literature_book"."author_id" IN (7, 16, 25, 40, ..., 18885860)
    ORDER BY
        "literature_book"."votes" DESC

Top three by genre
------------------

We can use the very same pattern we have above for top-k by an author when we
want to select the top-k by genre.

The notable difference between the Book-Author and Book-Genre relationship is
that one of them is a many-to-one (Book-Author) and the other one is
many-to-many (Book-Genre).

Due to the relationship being a many-to-many one, we need to make one change
to remove duplicate books - the ``book_qs`` gains a ``distinct()`` call:

.. code:: python

    >>> book_sub_qs = Book.objects.filter(
    ...     genres=OuterRef("genres")
    ... ).order_by("-votes").values_list("pk", flat=True)[:3]
    >>> book_qs = Book.objects.distinct().filter(pk__in=Subquery(book_sub_qs)).order_by("-votes")
    >>> genres = Genre.objects.prefetch_related(Prefetch("books", queryset=book_qs))
    >>> for genre in genres:
    ...     print(f"Genre: {genre.name}")
    ...     for book in genre.books.all():
    ...         print(f"  - {book.title}")
    Genre: ...


.. code:: sql

    SELECT DISTINCT
        "literature_book_genres"."genre_id" AS "_prefetch_related_val_genre_id",
        "literature_book"."id",
        "literature_book"."title",
        "literature_book"."author_id",
        "literature_book"."votes"
    FROM "literature_book"
    INNER JOIN "literature_book_genres"
        ON  "literature_book"."id" = "literature_book_genres"."book_id"
    INNER JOIN "literature_book_genres" T4
        ON "literature_book"."id" = T4."book_id"
    WHERE
        "literature_book"."id" IN (
            SELECT
                U0."id"
            FROM "literature_book" U0
            INNER JOIN "literature_book_genres" U1
                ON U0."id" = U1."book_id"
            WHERE
                U1."genre_id" = "literature_book_genres"."genre_id"
            ORDER BY
                U0."votes" DESC
            LIMIT 3
        )
        AND T4."genre_id" IN (1, 2, ..., 411, 412)
    ORDER BY
        "literature_book"."votes" DESC

.. _whole chapter on aggregations: https://docs.djangoproject.com/en/2.1/topics/db/aggregation/
.. _feature request ticket: https://code.djangoproject.com/ticket/26780

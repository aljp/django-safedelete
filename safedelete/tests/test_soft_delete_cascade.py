import unittest
from django.db import models
from django.test import TestCase
from safedelete import SOFT_DELETE_CASCADE, SOFT_DELETE
from safedelete.models import SafeDeleteModel
from safedelete.tests.models import Article, Author, Category


class Press(SafeDeleteModel):
    name = models.CharField(max_length=200)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)


class PressNormalModel(models.Model):
    name = models.CharField(max_length=200)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)


class CustomAbstractModel(SafeDeleteModel):
    class Meta:
        abstract = True


class ArticleView(CustomAbstractModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    article = models.ForeignKey(Article, on_delete=models.CASCADE)


class SimpleTest(TestCase):

    def setUp(self):
        self.authors = (
            Author.objects.create(),
            Author.objects.create(),
            Author.objects.create(),
        )

        self.categories = (
            Category.objects.create(name='category 0'),
            Category.objects.create(name='category 1'),
            Category.objects.create(name='category 2'),
        )

        self.articles = (
            Article.objects.create(author=self.authors[1]),
            Article.objects.create(author=self.authors[1], category=self.categories[1]),
            Article.objects.create(author=self.authors[2], category=self.categories[2]),
        )

        self.press = (
            Press.objects.create(name='press 0', article=self.articles[2])
        )

    def test_soft_delete_cascade(self):
        self.assertEqual(Author.objects.count(), 3)
        self.assertEqual(Article.objects.count(), 3)
        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(Press.objects.count(), 1)

        self.authors[2].delete(force_policy=SOFT_DELETE_CASCADE)

        self.assertEqual(Author.objects.count(), 2)
        self.assertEqual(Author.all_objects.count(), 3)
        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(Article.all_objects.count(), 3)
        self.assertEqual(Press.objects.count(), 0)
        self.assertEqual(Press.all_objects.count(), 1)

    def test_soft_delete_cascade_with_normal_model(self):
        PressNormalModel.objects.create(name='press 0', article=self.articles[2])
        self.authors[2].delete(force_policy=SOFT_DELETE_CASCADE)

        self.assertEqual(Author.objects.count(), 2)
        self.assertEqual(Author.all_objects.count(), 3)
        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(Article.all_objects.count(), 3)
        self.assertEqual(Press.objects.count(), 0)
        self.assertEqual(Press.all_objects.count(), 1)

    def test_soft_delete_cascade_with_abstract_model(self):
        ArticleView.objects.create(article=self.articles[2])

        self.articles[2].delete(force_policy=SOFT_DELETE_CASCADE)

        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(Article.all_objects.count(), 3)

        self.assertEqual(ArticleView.objects.count(), 0)
        self.assertEqual(ArticleView.all_objects.count(), 1)

    def test_undelete_with_soft_delete_cascade_policy(self):
        self.authors[2].delete(force_policy=SOFT_DELETE_CASCADE)
        self.authors[2].undelete(force_policy=SOFT_DELETE_CASCADE)

        self.assertEqual(Author.objects.count(), 3)
        self.assertEqual(Article.objects.count(), 3)
        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(Press.objects.count(), 1)


class SafeDeleteWithInOp(TestCase):

    def setUp(self):
        self.authors = (
            Author.objects.create(),
            Author.objects.create(),
            Author.objects.create(),
        )

        self.articles = (
            Article.objects.create(author=self.authors[1]),
            Article.objects.create(author=self.authors[1]),
            Article.objects.create(author=self.authors[2]),
        )

        self.press = (
            Press.objects.create(name='press 0', article=self.articles[0]),
            Press.objects.create(name='press 1', article=self.articles[1]),
            Press.objects.create(name='press 2', article=self.articles[2]),
        )

    def test_filter_with_in(self):
        """
        Issue https://github.com/makinacorpus/django-safedelete/issues/101

        Using a SafeDeleteQueryset as the argument to a filters `in` lookup only works if the queryset is
          evaluated. i.e. Press.objects.filter(article__in=list(articles))
        """
        self.articles[0].delete(force_policy=SOFT_DELETE)
        self.articles[1].delete(force_policy=SOFT_DELETE)

        articles = Article.objects.filter()
        #  press = Press.objects.filter(article__in=articles)  # This doesn't work but should
        press = Press.objects.filter(article__in=list(articles))  # This works

        self.assertEqual(press.count(), 1)

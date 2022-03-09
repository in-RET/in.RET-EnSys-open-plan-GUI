from django.test import TestCase
from django.urls import reverse
from django.conf import settings as django_settings
from django.test.client import RequestFactory
from projects.models import Project


class BasicOperationsTest(TestCase):
    fixtures = ["fixtures/benchmarks_fixture.json"]

    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        self.factory = RequestFactory()
        self.client.login(username="testUser", password="ASas12,.")

    def test_delete_project_redirects(self):
        """Make sure we are redirected to project page once deleting a project"""
        response = self.client.post(reverse("project_delete", args=[1]))
        self.assertRedirects(response, reverse("project_search"))
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Project.objects.all().count(), 0)

    def test_duplicate_project_redirects(self):
        """Make sure we are redirected to project page once duplicating a project"""
        response = self.client.post(reverse("project_duplicate", args=[1]))
        self.assertRedirects(response, reverse("project_search", args=[2]))
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Project.objects.all().count(), 2)

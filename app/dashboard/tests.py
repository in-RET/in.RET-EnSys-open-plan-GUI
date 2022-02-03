from django.test import TestCase

# import uuid
# from .models import Project, Simulation
# from io import BytesIO
# from django.urls import reverse
from .helpers import dict_keyword_mapper, nested_dict_crawler

#class SimulationServiceTest(TestCase):
#    fixtures = ['fixtures/benchmarks_fixture.json',]
#
#     @classmethod
#     def setUpTestData(cls):
#         pass
#
#     def setUp(self):
#         pass
#
#     # def test_results_assets_successfull_creation_after_file_processing(self):
#         # project = Project.objects.get(pk=1)
#         # associated_simulation = Simulation(request_id=f'{uuid.uuid4()}', project=project, status='RU')
#         # associated_simulation.save()
#         # with open('test_resources/results.xls', 'rb') as test_file:
#         #     mock_file_handler = BytesIO(test_file.read())
#         # mock_file_handler.name = "results.xls"
#         # xls_to_dict = parse_xl_file(file=mock_file_handler)
#
#         # assets_created = create_results_assets(xls_to_dict, associated_simulation)
#         # self.assertTrue(assets_created)


class TestAccessKPIs(TestCase):
    """
    KPIs are non dict variables (usually scalars, or a dict containing the keys 'unit' and 'value' only)
    which one can find at the very end path of nested dict
    """

    def test_dict_crawler(self):
        dct = dict(a=dict(a1=1, a2=2), b=dict(b1=dict(b11=11, b12=dict(b121=121))))
        self.assertDictEqual(
            {
                "a1": [("a", "a1")],
                "a2": [("a", "a2")],
                "b11": [("b", "b1", "b11")],
                "b121": [("b", "b1", "b12", "b121")],
            },
            nested_dict_crawler(dct),
        )

    def test_dict_crawler_doubled_path(self):
        """If an KPI is present at two places within the dict, the 2 paths should be returned"""
        dct = dict(a=dict(a1=1, a2=2), b=dict(b1=dict(a2=11)))
        self.assertDictEqual(
            {"a1": [("a", "a1")], "a2": [("a", "a2"), ("b", "b1", "a2")]},
            nested_dict_crawler(dct),
        )

    def test_dict_crawler_finds_non_scalar_value(self):
        """
        If a KPI valus is not a simple scalar but a dict in the format {'unit':..., 'value':...},
        the crawler should stop the path finding there and consider this last dict to be the value of the KPI
        """
        dct = dict(
            a=dict(a1=1, a2=dict(unit="EUR", value=30)),
            b=dict(b1=dict(b11=11, b12=dict(unit="kWh", value=12))),
        )
        self.assertDictEqual(
            {
                "a1": [("a", "a1")],
                "a2": [("a", "a2")],
                "b11": [("b", "b1", "b11")],
                "b12": [("b", "b1", "b12")],
            },
            nested_dict_crawler(dct),
        )

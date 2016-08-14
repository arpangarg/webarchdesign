from django.test import TestCase, Client
import os

from views import *


class TestViews(TestCase):

	DIR_PATH = os.path.dirname(os.path.abspath(__file__))


	def test_get_processed(self):
		c = Client()

		fd = open(self.DIR_PATH + '/tests/cutedog.jpg')

		response = c.post(
			'/getProcessed',
			{'user_id': 'bob', 'image': fd, 'test': 1}
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, "Image Submitted!")

		response = c.get(
			'/getProcessed',
			{'user_id': 'bob', 'image': fd, 'test': 1}
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, "Invalid Request")

		fd = open(self.DIR_PATH + '/tests/not_image.txt')
		response = c.post(
			'/getProcessed',
			{'user_id': 'bob', 'image': fd, 'test': 1}
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, "Inappropriate file type")


	def test_extract_weekly_histograms(self):
		result = extract_weekly_histograms('bob')
		self.assertIsInstance(result, list)

		if result:
			truthy = not any(
				[self.assertIsInstance(h['histogram'], list) for h in result]
			)
			self.assertTrue(truthy)


	def test_extract_median_histogram(self):
		result = extract_median_histogram()
		self.assertIsInstance(result, list)

		if result:
			self.assertEquals(len(result), 256)


	def test_get_most_similar(self):
		result = get_most_similar('bob', 1)
		assertEquals(result, [])

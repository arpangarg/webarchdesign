from django.shortcuts import render
from django.http import HttpResponse

from pymongo import MongoClient
from bson.binary import Binary

from datetime import datetime, timedelta, date, time
import numpy as np
import matplotlib.pyplot as plt
import cStringIO as StringIO
from PIL import Image
import cv2
from operator import itemgetter


client = MongoClient()
db = client.local

# home page of app, just a generic bootstrap page
def display_page(request):
	return render(request, 'index.html')


def get_processed(request):
	'''
	Native mobile client sends image as part of a POST request.
 	This method receives the image, converts image to grayscale,
 	computes histogram, stores the original image and histogram to 
 	MongoDB, and finally returns the grayscale image back to cient as
 	part of the response
	'''
	if (request.method != 'POST' or 'user_id' not in request.POST \
		or 'image' not in request.FILES):
		return HttpResponse("Invalid Request")

	if not request.FILES['image'].name.endswith((
		".jpg", ".JPG", ".jpeg", ".JPEG", ".png", ".PNG", ".bmp", ".BMP",
		".gif", ".GIF"
	)):
		return HttpResponse("Inappropriate file type")

	image_original = request.FILES['image'].read()
	pil_image = Image.open(StringIO.StringIO(image_original))
	np_image = np.array(pil_image)

	np_image_grayscale = rgb2gray(np_image)

	hist = cv2.calcHist(
		[np_image_grayscale.astype('float32')],
		[0],
		None,
		[256],
		[0,256]
	)

	if 'test' not in request.POST:
		db.images.insert_one({
			"user_id": request.POST['user_id'],
			"date": datetime.utcnow(),
			"image": Binary(image_original),
			"histogram": hist.tolist(),
			"median_histogram": float(np.median(hist))
		})

	return HttpResponse("Image Submitted!")


def rgb2gray(rgb):
	'''
	Uses a weighted average to compute the grayscale of an rgb image
	'''
	return np.dot(rgb[...,:3], [0.299, 0.587, 0.114])


def show_histogram(hist):
	'''
	Takes histogram data and displays histogram on the screen
	'''
	plt.imshow(hist, cmap = plt.get_cmap('gray'))
	plt.show()


def extract_weekly_histograms(user_id):
	'''
	Returns a list of histograms for the current week for a given user,
	assuming week starts from Monday
	'''
	today = datetime.combine(date.today(), time.min)

	results = list(db.images.find(
		{
			"user_id": user_id,
			"date": {"$gte": today - timedelta(days = today.weekday())}
		},
		{
			"histogram": 1
		}
	))

	return results


def extract_median_histogram():
	'''
	Finds the median histogram of the current day for all users
	'''
	today = datetime.combine(date.today(), time.min)

	histograms = list(db.images.find(
		{
			"date": {"$gte": today}
		},
		{
			"histogram": 1,
			"median_histogram": 1
		}
	))

	medians = [m['median_histogram'] for m in histograms]

	median = -1

	if len(medians) % 2 == 0:
		median = np.median(medians[:-1])
	else:
		median = np.median(medians)

	med_histogram = next(
		(i for i in histograms if i["median_histogram"] == median),
		None
	)

	return med_histogram['histogram']


def get_most_similar(user_id, n):
	'''
	For a particular user, returns n user id's with the most similar
	histograms

	**Problem specificiation unclear: which histogram to compare with?**
	ASSUMPTION: only one histogram per user exists in the database

	Note: To determine similarity between two histograms, the correlation
	is computed
	'''
	correlation = list()

	input_user = db.images.find_one(
		{"user_id": user_id},
		{"user_id": 1, "histogram": 1}
	)

	cursor = db.images.find(
		{"user_id": {"$ne": user_id}},
		{"user_id": 1, "histogram": 1}
	)

	for doc in cursor:
		user = doc['user_id']

		corr_val = cv2.compareHist(
			np.asarray(input_user['histogram'], dtype='float32'),
			np.asarray(doc['histogram'], dtype='float32'),
			cv2.cv.CV_COMP_CORREL
		)

		correlation.append((user, corr_val))

	correlation.sort(key = itemgetter(1), reverse=True)

	if (n > len(correlation)):
		return [u[0] for u in correlation]
	else:
		return [u[0] for u in correlation][0:n]

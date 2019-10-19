from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import numpy as np
from PIL import Image

import sys
import re
import subprocess
import math
from sklearn.cluster import KMeans
import numpy as np
import glob
import os
import shutil
import imagehash

from datetime import datetime

class imageclusterengine:
	def __init__(self):
		return

	@staticmethod
	def get_perception_hash(img, **kwargs):
		if 'hashtype' not in kwargs:
			kwargs['hashtype'] = 'phash-rgb'
		if kwargs['hashtype'] == 'imagemagick':
			i = 0
			phash = [0] * 42
			img.save("/tmp/phash.png")
			res = subprocess.run(['identify', '-verbose', '-define', 'identify:moments', '/tmp/phash.png'], stdout=subprocess.PIPE)
			for line in (res.stdout).decode('utf-8').split("\n"):
				m = re.match("^\s+PH\d:\s+(.+?),\s(.+?)$", line.rstrip())
				if m and i < 42:
					phash[i] = float(m.groups()[0])
					phash[i+1] = float(m.groups()[1])
					i = i + 2
			return { 'hashtype': kwargs['hashtype'], 'hash': phash }
		if kwargs['hashtype'] == 'phash':
			i = 0
			phash = [0] * 64
			for v in imagehash.average_hash(img).__dict__['hash']:
				for u in v:
					phash[i] = 1.0 if u else 0.0
					i = i + 1
			return { 'hashtype': kwargs['hashtype'], 'hash': phash }
		if kwargs['hashtype'] == 'phash-rgb':
			i = 0
			phash = [0] * (64 * 3)
			data = img.getdata()

			r = [(d[0], d[0], d[0]) for d in data]
			g = [(d[1], d[1], d[1]) for d in data]
			b = [(d[2], d[2], d[2]) for d in data]

			img.putdata(r)
			for v in imagehash.average_hash(img).__dict__['hash']:
				for u in v:
					phash[i] = 1.0 if u else 0.0
					i = i + 1
			img.putdata(b)
			for v in imagehash.average_hash(img).__dict__['hash']:
				for u in v:
					phash[i] = 1.0 if u else 0.0
					i = i + 1
			img.putdata(g)
			for v in imagehash.average_hash(img).__dict__['hash']:
				for u in v:
					phash[i] = 1.0 if u else 0.0
					i = i + 1
			img.putdata(data)
			return { 'hashtype': kwargs['hashtype'], 'hash': phash }
		raise Exception("Unknown hashtype format")

	@staticmethod
	def cluster_images(perhashList):
		Y = np.array([i[1]['hash'] for i in perhashList])
		X = PCA().fit_transform(X=Y)

		# Calculate the MDL Coefficient for hypothesis length
		# Calculate current best score (1 cluster)
		best = KMeans(n_clusters = 1).fit(X)
		score = best.inertia_

		# Hypothesis 1
		# Complexity of the model grows linearly
		# Found this produces too many buckets for big problems
		# mdl_coeff = score / len(X)

		# Hypothesis 2
		# Complexity of the model grows exponentially
		# Exponent base measured experimentally
		# Found this produces too many buckets
		# mdl_coeff = score**(1/float(len(X))) / 1.25

		# Hypothesis 3
		# Complexity of the model grows quadratically
		# Found this produces too many buckets
		# mdl_coeff = score / len(X) / len(X)

		# Hypothesis 4
		# Complexity of the model grows linear against len(X) * sqrt(data)
		# Constant experimentally determined
		mdl_coeff = math.sqrt(score) * 2

		# Hypothesis 5
		# Complexity of model grows in the logarithm
		# Exponent base measured experimentally
		# mdl_coeff = score / math.log(len(X))

		# Hypothesis 6
		# Must beat race against expected improvements
		# Found this produces very stable results, though too many buckets
		# start = score
		# improvement = 0.85
		# mdl_coeff = 0.0

		score = score

		# Increase the number of clusters until description length does not decrease
		buckets = 1
		best_n = 1
		while True:
			buckets = buckets + 1
			kmeans = KMeans(n_clusters = buckets).fit(X)
			totaldist = kmeans.inertia_

			# Hypothesis 1
			# tempscore = totaldist + (mdl_coeff * buckets)

			# Hypothesis 2
			# tempscore = totaldist + (math.pow(mdl_coeff, buckets))

			# Hypothesis 3
			# tempscore = totaldist + (mdl_coeff * buckets * buckets)

			# Hypothesis 4
			tempscore = totaldist + (mdl_coeff * buckets)

			# Hypothesis 5
			# tempscore = totaldist + (mdl_coeff * math.log(buckets, 1 / improvement) * buckets)

			# Hypothesis 6
			# mdl_coeff = start - (start * math.pow(improvement, buckets - 1))
			# tempscore = totaldist + mdl_coeff

			if tempscore > (score * 1.1):
				break

			if tempscore < score:
				score = tempscore
				best = kmeans
				best_n = buckets

		def norm_sort(cluster_center):
			return np.linalg.norm(cluster_center[1])

		# Create a mapping so that buckets are named consistently
		mapping = sorted([[i, best.cluster_centers_[i]] for i in range(0, len(best.cluster_centers_))], key=norm_sort)
		invmapping = [0] * len(mapping)
		for i in range(0, len(mapping)):
			invmapping[mapping[i][0]] = i

		# Output a mapping between image ids and bucket labels
		labels = [[perhashList[i][0], invmapping[best.labels_[i]]] for i in range(0, len(X))]
		return labels

# TODO if name = whatever, make this into a module
if __name__ == "__main__":
	phashlist = []

	files = glob.glob(sys.argv[1])

	for filename in files:
		phashlist.append([ filename, PerceptualClusteringEngine.get_perception_hash(Image.open(filename)) ])

	labels = PerceptualClusteringEngine.cluster_images(phashlist)

	for label in labels:
		if not os.path.exists("buckets"):
			os.mkdir("buckets")
		if not os.path.exists("buckets/{}".format(label[1])):
			os.mkdir("buckets/{}".format(label[1]))
		shutil.copy(label[0], "buckets/{}".format(label[1]))

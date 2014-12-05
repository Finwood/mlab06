#!/usr/bin/env python
# coding: utf-8

import numpy as np
import pandas as pd
from pandas.stats.moments import ewma
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

logset = [
	[
		('tek0002ALL.csv', 'Lasse: Resonanzfrequenz'),
		('tek0003ALL.csv', 'Lasse: Eigenkreisfrequenz'),
		('tek0004ALL.csv', 'Lasse: f = 0.5 Hz'),
		('tek0005ALL.csv', 'Lasse: f = 0.75 Hz'),
		('tek0006ALL.csv', 'Lasse: f = 1.0 Hz'),
		('tek0007ALL.csv', 'Lasse: f = 1.5 Hz'),
		('tek0008ALL.csv', 'Lasse: f = 2.0 Hz'),
		('tek0009ALL.csv', 'Lasse: f = 3.0 Hz'),
		('tek0011ALL.csv', 'Lasse: f = 4.0 Hz'),
		('tek0012ALL.csv', 'Lasse: f = 5.0 Hz')
	],
#	[('swl/tek00%02iALL.csv' %i, 'SWL %02i' %i) for i in range(14)],
	[
		('swl/tek0000ALL.csv', 'Sebastian: Ausschwingen'),
		('swl/tek0011ALL.csv', 'Sebastian: Kennkreisfrequenz'),
		('swl/tek0013ALL.csv', 'Sebastian: Resonanzfrequenz'),
		('swl/tek0008ALL.csv', 'Sebastian: f = 0.5 Hz'),
		('swl/tek0007ALL.csv', 'Sebastian: f = 0.7 Hz'),
		('swl/tek0006ALL.csv', 'Sebastian: f = 1.0 Hz'),
		('swl/tek0005ALL.csv', 'Sebastian: f = 1.3 Hz'),
		('swl/tek0004ALL.csv', 'Sebastian: f = 1.5 Hz'),
		('swl/tek0003ALL.csv', 'Sebastian: f = 2.0 Hz'),
		('swl/tek0002ALL.csv', 'Sebastian: f = 2.5 Hz'),
		('swl/tek0001ALL.csv', 'Sebastian: f = 3.0 Hz'),
		('swl/tek0009ALL.csv', 'Sebastian: f = 4.0 Hz'),
		('swl/tek0010ALL.csv', 'Sebastian: f = 5.0 Hz')
	]
]

def get_center_index(s):
	diff = s[valids].diff()
	i1 = list(s.ix[valids][diff > 1].index.values)
	i2 = list(s.ix[valids][diff < -1].index.values)

	if len(i1) > len(i2):
		i1 = i1[:-1]
	elif len(i2) > len(i1):
		i2 = i2[1:]

	l1, l2 = [], []

	for a, b in zip(i1, i2):
		if abs(a - b) > 2:
			l1.append(a)
			l2.append(b)

	i1 = np.array(l1)
	i2 = np.array(l2)

	return i1 + (i2 - i1) / 2

def get_max_index(s):
	s_max = s.max()
	max_area = s[s_max - s < .9]

	groups = []
	s = 0
	for i in range(len(max_area) - 1):
		if max_area.index[i+1] - max_area.index[i] > 1:
			groups.append((s, i))
			s = i + 1
	groups.append((s, len(max_area) - 1))

	max_indices = []
	for s,e in groups:
		if abs(s-e) > 2:
			max_indices.append(max_area.iloc[s:e].idxmax())

	return np.array(max_indices, dtype=np.int64)

def get_delta_phi(t_e, t_a, T):
#	return (t_e - t_a) * 2 * np.pi / T
	return (t_e - t_a) * 360. / T

log = open('delta_phi.csv', 'w')

pd.options.display.precision = 4
pd.options.display.line_width = 160

pdf = PdfPages('oszi.pdf')
for logs in logset:

	for logfile, title in logs:
		df = pd.read_csv('../res/logs/' + logfile, skiprows=14)

		valids = (df.CH1 < 5) & (df.CH1 > -.5)

		df = df.ix[valids]

		df.TIME -= df.TIME.iloc[0] # remove Offset

		idx_antrieb_max = get_center_index(df.CH1)
		t_max_i = df.TIME[idx_antrieb_max]
		T_est = np.mean(np.diff(t_max_i.values))

		# as seen at http://connor-johnson.com/2014/02/01/smoothing-with-exponentially-weighted-moving-averages/
		ewma_span = 10
		np_phi = df.CH2.values * 15.
		fwd = ewma(np_phi, span=ewma_span) # take EWMA in fwd direction
		bwd = ewma(np_phi[::-1], span=ewma_span) # take EWMA in bwd direction
		c = np.vstack(( fwd, bwd[::-1] )) # lump fwd and bwd together
		df['phi'] = np.mean( c, axis=0 ) # average

		phimax = df.phi.max()
		phimin = df.phi.min()
		amplitude = phimax - phimin

		df.phi -= (phimin + amplitude / 2.)

		idx_phi_max = get_max_index(df.phi)

#		log.write('#%s: T = %.3f\n' %(title, T_est))
#		log.write('u:\n%s\n\n' %df.TIME[idx_antrieb_max].to_string())
#		log.write('y:\n%s\n\n' %df.TIME[idx_phi_max].to_string())

#		if len(idx_phi_max) > len(idx_antrieb_max):
#			idx_phi_max = idx_phi_max[:-1]
#		elif len(idx_antrieb_max) > len(idx_phi_max):
#			idx_antrieb_max = idx_antrieb_max[:-1]


#		print get_delta_phi(df.TIME[idx_antrieb_max].values, df.TIME[idx_phi_max].values, T_est).mean()
#		print delta_phi

		fig = plt.figure()
		fig.subplots_adjust(left = 0.1, right = 0.95, bottom = 0.1, top = 0.9)
		ax = fig.add_subplot(111)
		ax.tick_params(pad=10)
		ax.plot(df.TIME, df.CH1, color='r', linestyle='-')
		ax.plot(df.TIME, df.phi, color='b', linestyle='-')
		for foo in t_max_i:
			ax.axvline(foo, color='g')
		for foo in df.TIME[idx_phi_max]:
			ax.axvline(foo, color='r')

		ax.grid(True)

		fig.suptitle(title)
		pdf.savefig(fig)

		print "%s:\tomega = %.3f/s,\tA = %.3f°" %(title, 2 * np.pi / T_est, amplitude)

pdf.close()
log.close()

#!/usr/bin/env python
# coding: utf-8

import numpy as np
import pandas as pd
from pandas.stats.moments import ewma
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

logset = [
	[
		('tek0002ALL.csv', 'Resonanzfrequenz'),
		('tek0003ALL.csv', 'Eigenkreisfrequenz'),
		('tek0004ALL.csv', 'f = 0.5 Hz'),
		('tek0005ALL.csv', 'f = 0.75 Hz'),
		('tek0006ALL.csv', 'f = 1.0 Hz'),
		('tek0007ALL.csv', 'f = 1.5 Hz'),
		('tek0008ALL.csv', 'f = 2.0 Hz'),
		('tek0009ALL.csv', 'f = 3.0 Hz'),
		('tek0011ALL.csv', 'f = 4.0 Hz'),
		('tek0012ALL.csv', 'f = 5.0 Hz')
	],
	[('swl/tek00%02iALL.csv' %i, 'SWL %02i' %i) for i in range(14)]
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

pd.options.display.precision = 4
pd.options.display.line_width = 160

pdf = PdfPages('oszi.pdf')
for logs in logset:

	for logfile, title in logs:
		df = pd.read_csv('../res/logs/' + logfile, skiprows=14)

		valids = (df.CH1 < 5) & (df.CH1 > -.5)

		df = df.ix[valids].reindex()

		df.TIME -= df.TIME.iloc[0] # remove Offset

		antrieb_max = get_center_index(df.CH1)
		t_max_i = df.TIME[antrieb_max]
		T_est = np.mean(np.diff(t_max_i.values))

		df['phi'] = df.CH2 * 15.
		phimax = ewma(df.phi, span=5).max()
		phimin = ewma(df.phi, span=5).min()
		amplitude = phimax - phimin

		df.phi -= (phimin + amplitude / 2.)

		# as seen at http://connor-johnson.com/2014/02/01/smoothing-with-exponentially-weighted-moving-averages/
		ewma_span = 5
		np_phi = df.phi.values
		fwd = ewma(np_phi, span=ewma_span)
		bwd = ewma(np_phi[::-1], span=ewma_span)
		c = np.vstack(( fwd, bwd[::-1] )) # lump fwd and bwd together
		df['phi_corr'] = np.mean( c, axis=0 ) # average

		fig = plt.figure()
		fig.subplots_adjust(left = 0.1, right = 0.95, bottom = 0.1, top = 0.9)
		ax = fig.add_subplot(111)
		ax.tick_params(pad=10)
		ax.plot(df.TIME, df.CH1, color='r', linestyle='-')
		ax.plot(df.TIME, df.phi, color='b', linestyle='-')
		ax.plot(df.TIME, df.phi_corr, color='g', linestyle='-')
		for foo in t_max_i:
			ax.axvline(foo, color='g')

		ax.grid(True)

		fig.suptitle(title)
		pdf.savefig(fig)

		print "%s:\tT = %.3fs,\tA = %.3f°" %(logfile, T_est, amplitude)

pdf.close()


#!/usr/bin/env python
# coding: utf-8

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('auswertung.csv', index_col='name')

R = .2
h = 9.4e-3
rho = 2.7e6
M = rho * np.pi * R**2 * h
J = .5 * M * R**2

omega_n = df.ix['omega_n'].omega
omega_r = df.ix['omega_r'].omega

k = J * omega_n**2 # Gleichung 33
print k
D = np.sqrt((1 - (omega_r / omega_n)**2) / 2.) # Gleichung 48
print D
d = 2 * D * k / omega_n # Gleichung 33
print d


def G(s):
	global J, d, k
	return 1 / ((J / k) * s**2 + (d / k) * s + 1)

x = np.logspace(.3, 1.6, 1000)

fig, axarr = plt.subplots(2, sharex=True)

for ax in axarr:
	ax.tick_params(pad=10)
	ax.set_xscale('log')
	ax.grid(True, which='both')
	ax.set_xlim([3, 40])

axarr[0].plot(df.omega, df.A_dB, 'o')
axarr[0].plot(x, 20*np.log10(np.absolute(G(1j * x))))
axarr[1].plot(df.omega, df.delta_phi_deg, 'o')
axarr[1].plot(x, np.angle(G(1j * x)) * 180. / np.pi)
axarr[1].set_yticks([0, -45, -90, -135, -180])

fig.savefig('bode.pdf')

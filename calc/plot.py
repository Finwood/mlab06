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

xlim = (2, 100)
x = np.logspace(np.log10(xlim[0]), np.log10(xlim[1]), 1000)

fig, axarr = plt.subplots(2, sharex=True)
fig.subplots_adjust(left = 0.11, right = 0.96, bottom = 0.1, top = 0.95)

for ax in axarr:
	ax.tick_params(pad=5)
	ax.set_xscale('log')
	ax.grid(True, which='both')
	ax.set_xlim(xlim)

axarr[0].plot(df.omega, df.A_dB, 'o')
axarr[0].plot(x, 20*np.log10(np.absolute(G(1j * x))))
dots = axarr[1].plot(df.omega, df.delta_phi_deg, 'o', label='Messpunkte')
line = axarr[1].plot(x, np.angle(G(1j * x)) * 180. / np.pi, label='berechnet')
axarr[1].set_ylim([-202.5, 22.5])
axarr[1].set_yticks([0, -45, -90, -135, -180])

axarr[1].set_xlabel(ur'$\log \, \omega$ [1/s]')
axarr[0].set_ylabel(ur'$\left| G \left( j \omega \right) \right|$ [dB]')
axarr[1].set_ylabel(ur'$\arg \left( G \left( j \omega \right) \right)$ [°]')

lines = dots + line
labels = [l.get_label() for l in lines]
axarr[1].legend(lines, labels, loc='best')

fig.savefig('bode.pdf')

import re
import string
with open('tab.tex', 'w') as f:
	df_tex = df[['omega', 'A', 'A_dB', 'delta_phi_deg']]
	preg = re.compile(ur'(?<=\\toprule\n) *o *& *do *& *Mg *& *M2 *& *Mr *& *mue *\\\\(?=\n\\midrule)', re.UNICODE)
	df_tex.columns = ['o', 'A', 'AdB', 'dphi']
	tex_string = df_tex.to_latex()
	f.write(tex_string)


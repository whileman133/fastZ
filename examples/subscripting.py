from fastz import R, L, C
from fastz.plotting import bodez

import numpy as np
import matplotlib.pyplot as plt

Z1 = ((R(v=10) // C(v=0.2e-9) // L('a', 100e-9))['p'] + L('b', 5e-9))[1]
print(Z1, Z1(10e6), Z1.breakfreq('R La'), Z1.breakfreq('R C'), Z1.breakfreq('C Lb'), sep='\n')

ff = np.logspace(6, 9, 1000)
fig, ax = bodez(Z1, ff, zlines='Zp', refzlines='R C La Lb')
plt.show()

import numpy as np

from fastz import R, L, C
from fastz.plotting import bodez

Z1 = R() // L()

Zball = (R('p',v=1.8e-3) + L('p',v=64e-12))["ball"]
Zpkg = (Zball // Zball // Zball // Zball)["pkg"]
Zin = ( Zpkg // ( C('d',v=1e-9) + R('d',v=40e-3))['die'] )['in']
Ztrg = (R('trg',v=600e-3)) ['trg']
ff = np.logspace(7, 10, 1000)
fig, ax = bodez(Zin, ff=ff, zlines='Zin:100e6 Zdie Zpkg', refzlines='Lp Cd') # Rp Rd
fig.show()

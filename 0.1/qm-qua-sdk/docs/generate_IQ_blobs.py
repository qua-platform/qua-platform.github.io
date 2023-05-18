import numpy as np
import random
import matplotlib.pyplot as plt

# angle = 0.5
angle = np.pi/2
dA = 0.8
width = 0.08
points = 5000
fidelity = 0.95
I_g = []
Q_g = []
I_e = []
Q_e = []

I_g_mean = 0.5 * np.cos(angle + dA / 2)
Q_g_mean = 0.5 * np.sin(angle + dA / 2)
I_e_mean = 0.5 * np.cos(angle - dA / 2)
Q_e_mean = 0.5 * np.sin(angle - dA / 2)

for i in range(points):
    I_g.append(random.gauss(I_g_mean, width))
    Q_g.append(random.gauss(Q_g_mean, width))

    if random.random() > (1 - fidelity):
        I_e.append(random.gauss(I_e_mean, width))
        Q_e.append(random.gauss(Q_e_mean, width))
    else:
        I_e.append(random.gauss(I_g_mean, width))
        Q_e.append(random.gauss(Q_g_mean, width))

angle_vec = np.arange(0, angle, 0.01)
angle_line_x = []
angle_line_y = []
for i in range(len(angle_vec)):
    angle_line_x.append(angle*np.cos(angle_vec[i]))
    angle_line_y.append(angle*np.sin(angle_vec[i]))

plt.plot(I_g, Q_g, '.', markersize=2, label='g', alpha=0.2)
plt.plot(I_e, Q_e, '.', markersize=2, label='e', alpha=0.2)
plt.axhline(color='k')
plt.axvline(color='k')
if angle == 0.5:
    plt.plot(angle_line_x, angle_line_y, 'k:')
    plt.plot([0, angle_line_x[-1]], [0, angle_line_y[-1]], 'k--')
    plt.text(0.25, 0.04, 'a')
plt.xlabel('I')
plt.ylabel('Q')
plt.legend()
plt.axis([-0.75, 0.75, -0.75, 0.75])

# plt.figure()
# plt.hist2d(I_g + I_e, Q_g + Q_e, range=[[-1, 1], [-1,1]], bins=100)

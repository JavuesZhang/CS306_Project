import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon

with open('./ShenzhenBorder2.txt', 'r') as f:
    content=[]
    for line in f.readlines():
        point = line.split(',')
        point = [float(point[0]), float(point[1])]
        content.append(point)
    border = np.array(content).reshape(-1,2)


city = Polygon(border)
print(city.contains(Point(113.9096, 22.5822)))
x1 = border[:, 0]
y1 = border[:, 1]
fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)
ax1.scatter(x1, y1, c='k', marker='.')
plt.show()


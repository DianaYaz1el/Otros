import numpy as np
import matplotlib.pyplot as plt

from sklearn.datasets import make_blobs
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans

X, y = make_blobs(
    n_samples=200,
    centers=2,
    cluster_std=1.3,
    random_state=7
)

modelo = LogisticRegression()
modelo.fit(X, y)

x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1

xx, yy = np.meshgrid(
    np.linspace(x_min, x_max, 300),
    np.linspace(y_min, y_max, 300)
)

grid = np.c_[xx.ravel(), yy.ravel()]

Z = modelo.predict(grid)
Z = Z.reshape(xx.shape)

kmeans = KMeans(
    n_clusters=2,
    random_state=7,
    n_init=10
)

clusters = kmeans.fit_predict(X)
centroides = kmeans.cluster_centers_

fig, ax = plt.subplots(
    1,
    2,
    figsize=(12, 5)
)

ax[0].contourf(
    xx,
    yy,
    Z,
    alpha=0.15
)

ax[0].scatter(
    X[:, 0],
    X[:, 1],
    c=y,
    s=45
)

ax[0].contour(
    xx,
    yy,
    modelo.predict_proba(grid)[:, 1].reshape(xx.shape),
    levels=[0.5],
    linewidths=2
)

ax[0].set_title("Aprendizaje supervisado")
ax[0].set_xlabel("x₁")
ax[0].set_ylabel("x₂")

ax[1].scatter(
    X[:, 0],
    X[:, 1],
    c=clusters,
    s=45
)

ax[1].scatter(
    centroides[:, 0],
    centroides[:, 1],
    marker="X",
    s=220,
    edgecolors="black"
)

ax[1].set_title("Aprendizaje no supervisado")
ax[1].set_xlabel("x₁")
ax[1].set_ylabel("x₂")

plt.tight_layout()
plt.show()
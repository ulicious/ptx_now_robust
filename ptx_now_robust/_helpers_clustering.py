import math

import pandas as pd
import numpy as np

from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances_argmin_min, silhouette_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from yellowbrick.cluster import KElbowVisualizer


def cluster_data_head_script(data, length_cluster):

    def rearrange_data():

        wind_cols = ['Wind_' + str(i) for i in range(length_cluster)]
        solar_cols = ['Solar_' + str(i) for i in range(length_cluster)]

        processed_data = pd.DataFrame(index=range(int(len(data.columns) / 2)), columns=wind_cols + solar_cols)

        for i in range(int(len(data.columns) / 2)):
            col_1 = data.columns[i * 2]
            col_2 = data.columns[i * 2 + 1]

            processed_data.loc[i, wind_cols] = data[col_1].values
            processed_data.loc[i, solar_cols] = data[col_2].values

        num_periods = len(processed_data.index)

        return processed_data, num_periods

    def apply_clustering():

        def elbow_visualizer(data_elbow, show=False):

            model = KMeans(init='k-means++', random_state=42, n_init='auto')
            visualizer = KElbowVisualizer(model, k=(2, 30), timings=True)
            visualizer.fit(data_elbow)
            if show:
                visualizer.show()

            return visualizer.elbow_value_

        # Clustering
        X_std = StandardScaler().fit_transform(rearranged_data)

        pca = PCA()
        try:
            pca.fit(X_std)
        except ValueError:  # 0 variance in data

            variances = np.var(rearranged_data, axis=0)
            not_col_0_var = list(variances[variances != 0].index)
            X_std = StandardScaler().fit_transform(rearranged_data[not_col_0_var])
            pca.fit(X_std)

        n_components = 0
        for k in range(0, len(pca.explained_variance_ratio_.cumsum())):
            if pca.explained_variance_ratio_.cumsum()[k] >= 0.8:
                n_components = k
                break

        pca = PCA(n_components=n_components)
        pca.fit(X_std)
        scores_pca = pca.transform(X_std)

        n_cluster = elbow_visualizer(scores_pca)

        # might be no elbow --> use silhouette score to determine number of clusters
        if n_cluster is None:

            silhouette_value = 0
            for n in range(2, 30):
                kmeans_pca = KMeans(n_clusters=n, init='k-means++', random_state=42, n_init='auto')
                cluster_labels = kmeans_pca.fit_predict(scores_pca)

                silhouette_avg = silhouette_score(scores_pca, cluster_labels)
                if silhouette_avg > silhouette_value:
                    silhouette_value = silhouette_avg
                    n_cluster = n

            print(n_cluster)

        kmeans_pca = KMeans(n_clusters=n_cluster, init='k-means++', random_state=42, n_init='auto')
        kmeans_pca.fit(scores_pca)

        rearranged_data.loc[:, 'cluster'] = kmeans_pca.labels_

        # create file with weighting for clusters
        weighing_df = {}
        for k in range(n_cluster):
            weighing_df[k] = kmeans_pca.labels_.tolist().count(k) / number_periods * (365 * 24 / length_cluster)

        # Create dataframe with time series of representative weeks

        # get array which is closest to center
        closest, _ = pairwise_distances_argmin_min(kmeans_pca.cluster_centers_, scores_pca)

        # create for each feature (e.g., solar and pv) one Excel file which contains the arrays
        generation_file = pd.DataFrame(index=range(n_cluster * length_cluster), columns=name_columns)
        for c in name_columns:

            first_pos = min([k for k, s in enumerate(rearranged_data.columns) if c in s])
            last_pos = first_pos + length_cluster

            value_array = []
            for k in range(n_cluster):
                value_array += rearranged_data.iloc[closest[k], first_pos:last_pos].tolist()

            generation_file.loc[:, c] = value_array

        j = 0
        for k in [*weighing_df.keys()]:
            for n in range(length_cluster):
                generation_file.loc[j, 'Weighting'] = weighing_df[k]
                j += 1

        return generation_file

    name_columns = ['Wind', 'Solar']

    successful = False
    while not successful:

        try:
            rearranged_data, number_periods = rearrange_data()
            clustered_data = apply_clustering()

            return clustered_data
        except Exception as error:
            print("An error occurred:", error)

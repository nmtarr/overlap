"""
CHECK NUMERICAL RESULTS - does it do what it should (percent overlap etc.)
"""
import repo_functions as functions
import os
import pandas as pd
import matplotlib as plt

# Wheres the project directory
projDir = "T:/Occurrence_Records/Overlap/"

# Remove existing dtabase
db = projDir + "/overlap.sqlite"
os.remove(db)

# Radii to examine (meters)
radii = (10,30,60,100,200,300,400,500,600,700,800,900,
        1000,1500,2000,3000,4000,5000,6000,7000,8000,9000,10000)
radii = (1000,)
# Minimum_overlap to examine
min_overlap = range(30,100,5)

# Paths to feature layers to use and id fields for each
layers = ['counties', 'hucs', 'ncba_blocks']
feature_layers = {"hucs":(projDir + "NChucs","HUC12RNG"),
                  "ncba_blocks":(projDir + "NCBAblocks",'BLOCK_QUAD'),
                  "counties":(projDir + "NCcounties",'OBJECTID'),
                  "points1":(projDir + "points1", 'id'),
                  "points2":(projDir + "points2", 'id')}

################################################################################
################               Run Processes              ######################
################################################################################
# Create and populate the database with tables
functions.build_tables(db, feature_layers)

# For each point in the set, buffer with each of the radii.  Save buffers as
#   geometries in columns.
for radius in radii:
    functions.buffer_points(db, "points1", radius)

# Fill out results table with proportion of points that can be attributed to
# a huc at each buffer radius - minimum overlap combination.
for layer in layers[:1]:
    for lap in min_overlap:
        for radius in radii:
            print(layer, lap, radius)
            usable = functions.summarize_by_features(overlap_db=db,
                                                     points='points1', features=layer,
                                                     IDfield=feature_layers[layer][1], radius=radius,
                                                     min_overlap=lap)
            print("\t" + str(usable))
            functions.enter_result(db=db, point_set="points1", radius=radius,
                                   min_overlap=lap, prop_usable=usable,
                                   layer=layer)

################################################################################
####################             Figures               #########################
################################################################################
# Graph results y-axis: prop_usable, x-axis: buffer, series: min_overlap
title_dict = {'hucs': "NC 12-digit HUCs",
              'counties': "NC Counties",
              'ncba_blocks': "NC Bird Atlas Blocks"}

for layer in layers:
    sql = "SELECT * FROM results WHERE layer = '{0}';".format(layer)
    curs, con = functions.spatialite(db)
    df0 = pd.read_sql(sql, con)
    df0.drop(inplace=True, axis=1, columns=['layer', 'point_set'])
    df0.set_index(inplace=True, keys=['radius', 'min_overlap'])
    df1 = df0.unstack()
    df2 = df1['prop_usable']
    print(df2)
    df3 = df2.filter([30, 50, 60, 70, 80, 95], axis=1)
    title = title_dict[layer]
    fig = df3.plot(kind='line', figsize=(6,4), legend=True,
            xlim=(0,10000), fontsize=12, title=title)
    fig.set_ylabel("Usable records (%)", fontsize=10)
    fig.set_xlabel("Locational Uncertainty (m)", fontsize=10)
    fig.legend(loc=1, title="Minimum % overlap")

"""

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

# Minimum_overlap to examine
min_overlap = range(30,100,5)

# Paths to feature layers to use and id fields for each
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
    functions.buffer_points(db, "points2", radius)

# Fill out results table with proportion of points that can be attributed to
# a huc at each buffer radius - minimum overlap combination.
for layer in ['counties', 'hucs', 'ncba_blocks']
    for lap in min_overlap:
        for radius in radii:
            print(layer, lap, radius)
            usable = functions.summarize_by_features(overlap_db=db,
                                                     points='points2', features=layer,
                                                     IDfield=feature_layers[layer][1], radius=radius,
                                                     min_overlap=lap)
            print("\t" + str(usable))
            functions.enter_result(db=db, point_set="points2", radius=radius,
                                   min_overlap=lap, prop_usable=usable,
                                   layer=layer)

################################################################################
####################             Figures               #########################
################################################################################
# Graph results y-axis: prop_usable, x-axis: buffer, series: min_overlap

sql = "SELECT * FROM results;"
curs, con = functions.spatialite(db)
df0 = pd.read_sql(sql, con)
df0.drop(inplace=True, axis=1, columns=['layer', 'point_set'])
df0.set_index(inplace=True, keys=['radius', 'min_overlap'])
df1 = df0.unstack()
df2 = df1['prop_usable']
print(df2)
df3 = df2.filter([30, 50, 70, 80, 90, 95], axis=1)
title = "12-digit Hucs"
fig = df3.plot(kind='line', figsize=(6,4), legend=True,
        xlim=(0,5000), fontsize=12, title=title)
fig.set_ylabel("Usable records (%)")
fig.set_xlabel("Radius (m)")
fig.legend(loc=1, title="Minimum overlap (%)")


fig2 = df3.plot(kind='line', figsize=(6,4), legend=True, xlim=(0,2000),
         ylim=(40,105), fontsize=12, title=title)
fig2.set_ylabel("Usable records (%)")
fig2.set_xlabel("Radius (m)")
fig2.legend(loc=0, title="")

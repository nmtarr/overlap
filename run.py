import repo_functions as functions

# Wheres the project directory
projDir = "T:/occurrence_records/Overlap/"

overlap_db = projDir + "/overlap.sqlite"

# Radii to examine (meters)
radii = (10,30,60,100,200,300,400,500,600,700,800,900,
        1000,1500,2000,3000,4000,5000,6000,7000,8000,9000,10000)

# Minimum_overlap to examine
min_overlap = range(30,100,5)

feature_layers = {"hucs":(projDir + "NChucs","HUC12RNG"),
                  "ncba_blocks":(projDir + "NCBAblocks",'BLOCK_QUAD'),
                  "counties":(projDir + "NCcounties",'OBJECTID'),
                  "points2":(projDir + "points2", 'id')}

points1 = projDir + "points1.shp"
points2 = projDir + "points2.shp"

################################################################################
################################################################################
################################################################################
# Create and populate the database with tables
functions.build_tables(overlap_db, feature_layers)

# For each point in the set, buffer with each of the radii.  Save buffers as
#   geometries in columns.
for radius in radii:
    functions.buffer_points(overlap_db, "points2", radius)

# Fill out results table with proportion of points that can be attributed to
# a huc at each buffer radius - minimum overlap combination.
for lap in min_overlap[:1]:
    for radius in radii[:1]:
        print(lap, radius)
        usable = functions.summarize_by_features(overlap_db=overlap_db,
                                                 points='points2', features='hucs',
                                                 IDfield='HUC12RNG', radius=radius,
                                                 min_overlap=lap)
        print(usable)
        functions.enter_result(point_set=points, radius=radius,
                               min_overlap=min_overlap, prop_usable=usable)

# Graph results y-axis: prop_usable, x-axis: buffer, series: min_overlap

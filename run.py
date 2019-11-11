import repo_functions as functions

overlap_db = "/Users/nmtarr/documents/overlap/overlap.sqlite"

# Radii to examine (meters)
radii = (10,30,60,100,200,300,400,500,600,700,800,900,
        1000,1500,2000,3000,4000,5000,6000,7000,8000,9000,10000)

# Minimum_overlap to examine
min_overlap = range(30,100,5)

# Wheres the project directory
projDir = "/users/nmtarr/documents/overlap/"

feature_layers = {"hucs":(projDir + "NChucs","HUC12RNG"),
                  "ncba_blocks":(projDir + "NCBAblocks",'BLOCK_QUAD'),
                  "counties":(projDir + "NCcounties",'OBJECTID'),
                  "points2":(projDir + "points2", 'id')}

points1 = "/Users/nmtarr/Documents/Overlap/points1.shp"
points2 = "/Users/nmtarr/Documents/Overlap/points2.shp"

################################################################################
################################################################################
################################################################################
# Create and populate the database with tables
functions.build_tables(overlap_db, feature_layers)

# For each point in the set, buffer with each of the radii.  Save buffers as
#   geometries in columns.
for radius in radii[:1]:
    functions.buffer_points(overlap_db, "points2", radius)

# Fill out results table with proportion of points that can be attributed to
# a huc at each buffer radius - minimum overlap combination.
for lap in min_overlap:
    radius in radii:
    print(lap, radius)
    usable = functions.summarize_by_features(points='points1', features='hucs',
                                             id='HUC12RNG', radius=radius,
                                             min_overlap=lap)

    functions.enter_result(point_set=points, radius=radius,
                           min_overlap=min_overlap, prop_usable=usable)

# Graph results y-axis: prop_usable, x-axis: buffer, series: min_overlap

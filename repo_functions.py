# Connect to the project database
def spatialite(db, init_spatial_metadata=False):
    """
    Creates a connection and cursor for sqlite db and enables
    spatialite extension and shapefile functions.

    (db) --> cursor, connection

    Arguments:
    db -- path to the db you want to create or connect to.
    """
    import os
    import sqlite3
    import platform
    connection = sqlite3.connect(db)
    cursor = connection.cursor()

    # Environment variables need to be handled
    if platform.system() == 'Windows':
        os.environ['PATH'] = os.environ['PATH'] + ';' + 'C:/Spatialite'
        os.environ['SPATIALITE_SECURITY'] = 'relaxed'

    if platform.system() == 'Darwin':
        #os.putenv('SPATIALITE_SECURITY', 'relaxed')
        os.environ['SPATIALITE_SECURITY'] = 'relaxed'

    connection.enable_load_extension(True)
    cursor.execute('SELECT load_extension("mod_spatialite");')
    if init_spatial_metadata == True:
        cursor.execute('SELECT InitSpatialMetadata(1);')
    return cursor, connection

# Build necessary tables in database (load shapefiles)
def build_tables(db, feature_layers):
    """
    Builds the necessary tables.

    Arguments:
    db -- STRING; path to database to connect to/create.
    feature_layers -- DICTIONARY of STRING:TUPLEs ; layers to process with
    layer name to be used as table name as keys and paths to the layer and
    layer's unique ID field as items 0 and 1 in a tuple of strings, respectively.

    NOTE:
    Tables must be in SRID 5070 projection.
    """
    cursor, connection = spatialite(db, init_spatial_metadata=True)

    # Results table
    sql = """
    /* Create tables */
    CREATE TABLE results (point_set	 TEXT,
                          radius INTEGER,
                          min_overlap INTEGER,
                          prop_usable INTEGER,
                          layer TEXT);"""
    try:
        cursor.executescript(sql)
    except Exception as e:
        print(e)

    # Feature shapefiles
    for item in list(feature_layers.keys()):
        table_name = item
        path = feature_layers[item][0]
        IDfield = feature_layers[item][1]
        print(table_name)
        print(path)
        print(IDfield)
        sql = """SELECT ImportSHP('{0}', '{1}', 'utf-8', 5070, 'geom_5070', '{2}', 'POLYGON');
              """.format(path, table_name, IDfield)
        try:
            cursor.executescript(sql)
        except Exception as e:
            print(e)

    connection.commit()
    connection.close()
    return

# Buffer xy points
def buffer_points(db, points, radius):
    """
    Buffers the points with the given radius (m).

    Arguments:
    db -- STRING; path to database.
    points -- STRING; a point set identifier from the database.
    radius -- INTEGER; a radius to use when buffering in meters.
    """
    import os
    import sqlite3
    connection = sqlite3.connect(db)
    cursor = connection.cursor()
    os.putenv('SPATIALITE_SECURITY', 'relaxed')
    connection.enable_load_extension(True)
    cursor.execute('SELECT load_extension("mod_spatialite");')
    strRadius = str(radius)

    print(strRadius)

    # Buffers and put in new column
    sql = """
    ALTER TABLE {0} ADD COLUMN buffer{1} BLOB;

    UPDATE {0} SET buffer{1} = Buffer(geom_5070, {1});

    SELECT RecoverGeometryColumn('{0}', 'buffer{1}', 5070, 'POLYGON', 'XY');
    """.format(points, radius)
    try:
        cursor.executescript(sql)
    except Exception as e:
        print(e)

# Perform summaries of records within feature polygons
def summarize_by_features(overlap_db, points, features, IDfield, radius, min_overlap):
    """
    Returns the proportion of points that can be attributed to a feature from
    the feature layer with the stated buffer radii (m) and minimum overlap (%).

    Arguments:
    overlap_db -- STRING; path to the overlap project database.
    points -- STRING; identifier of the point set from the point_sets table.
    features -- STRING; name of feature layer table, as saved in the project db.
    IDfield -- STRING; unique ID field of the feature.
    radius -- INTEGER; radius to buffer points, in meters.
    min_overlap -- INTEGER; minimum percent overlap to use in overlap evaluations,
                    as a proportion (i.e. 90).
    """
    import sqlite3
    import os

    # Connect to range evaluation database.
    cursor, conn = spatialite(overlap_db)

    # Get the total number of points
    n_points = cursor.execute("""SELECT count(id)
                                 FROM {0}""".format(points)).fetchone()[0]

    # How many records can be used?
    sql = """
    /* Intersect occurrence circles with features */
    CREATE TABLE leaf AS
                 SELECT occs.id as point_id, layer.{2} as feature_id,
                 CastToMultiPolygon(Intersection(layer.geom_5070, occs.buffer{3})) AS geom
                 FROM {1} as layer, {0} AS occs
                 WHERE Intersects(layer.geom_5070, occs.buffer{3});

    SELECT RecoverGeometryColumn('leaf', 'geom', 5070, 'MULTIPOLYGON', 'XY');

    /* Select records with area greater or equal to the minimum overlap  */
    CREATE TABLE bulb AS
                 SELECT occs.id as point_id, occs.geom_5070,
                 100 * (Area(leaf.geom) / Area(occs.buffer{3})) AS proportion_circle
                 FROM leaf
                    LEFT JOIN {0} AS occs
                    ON leaf.point_id = occs.id
                 WHERE proportion_circle >= {4};
    """.format(points, features, IDfield, radius, min_overlap)
    try:
        cursor.executescript(sql)
    except Exception as e:
        print(e)

    sql = """SELECT count(point_id) FROM (SELECT point_id FROM bulb GROUP BY point_id)"""
    try:
        usable_points = cursor.execute(sql).fetchone()[0]
    except Exception as e:
        print(e)

    cursor.executescript("""DROP TABLE leaf; DROP TABLE bulb;""")
    conn.commit()
    conn.close()

    answer = 100*(usable_points/n_points)
    return(answer)

# Put value in correct cell
def enter_result(db, point_set, radius, min_overlap, prop_usable, layer):
    """
    Enters value into the results table.

    Arguments:
    db -- path to database.
    point_set -- name of the set of random points the value corresponds to.
    radius -- buffer radius explored when gettting the value.
    min_overlap -- minimum overlap explored when getting the value.
    prop_usable -- percent of points useable with the buffer radius and min_overlap.
    layer -- feature layer assessed (e.g. huc).
    """

    sql = """
    INSERT INTO results (point_set, radius, min_overlap, prop_usable, layer)
    VALUES ('{0}', '{1}', '{2}', '{3}', '{4}');
    """.format(point_set, radius, min_overlap, prop_usable, layer)

    cursor, conn = spatialite(db)
    cursor.execute(sql)
    conn.commit()
    conn.close()
    return

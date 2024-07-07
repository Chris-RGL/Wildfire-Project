"""Geographic clustering of historical wildfire data
CS 210, University of Oregon
Christopher Gallinger-Long
Credits: Moses Moon
"""
import doctest
import csv
import config
import graphics.utm_plot
import random

def main():
    """the 'beginning of the program'"""
    doctest.testmod()
    fire_map = make_map()
    points = get_fires_utm(config.FIRE_DATA_PATH)

    #Creates fire symbols
    plot_points(fire_map, points, color=config.FIRE_SYMBOL_COLOR)

    # Initial random assignment
    partition = assign_random(points, config.N_CLUSTERS)
    centroids = cluster_centroids(partition)
    centroid_symbols = plot_points(fire_map, centroids, size_px=10, color=config.CENTROID_COLOR)

    # Continue improving assignment until assignment doesn't change
    for i in range(config.MAX_ITERATIONS):
        old_partition = partition
        partition = assign_closest(points, centroids)
        if partition == old_partition:
            # No change ... this is "convergence"
            break
        centroids = cluster_centroids(partition)
        move_points(fire_map, centroids, centroid_symbols)

    # Show connections at end
    show_clusters(fire_map, centroid_symbols, partition)

    input("Press enter to quit")

def make_map() -> graphics.utm_plot.Map:
    """Create and return a basemap display"""
    map = graphics.utm_plot.Map(config.BASEMAP_PATH,
                                config.BASEMAP_SIZE,
                                (config.BASEMAP_ORIGIN_EASTING, config.BASEMAP_ORIGIN_NORTHING),
                                (config.BASEMAP_EXTENT_EASTING, config.BASEMAP_EXTENT_NORTHING))
    return map

def get_fires_utm(path: str) -> list[tuple[int, int]]:
    """Read CSV file specified by path, returning a list
    of (easting, northing) coordinate pairs within the
    study area.

    >>> get_fires_utm("data/test_locations_utm.csv")
    [(442151, 4729315), (442151, 5071453), (914041, 4729315), (914041, 5071453)]
    """
    with open(path, newline="", encoding="utf-8") as source_file:
        reader = csv.DictReader(source_file)
        result_row = []
        #creates cords
        for row in reader:
            easting = int(row["Easting"])
            northing = int(row["Northing"])
            if in_bounds(easting, northing):
                result_row.append((easting,northing))
        return result_row

def in_bounds(easting: float, northing: float) -> bool:
    """Is the UTM value within bounds of the map?"""
    if (easting < config.BASEMAP_ORIGIN_EASTING
            or easting > config.BASEMAP_EXTENT_EASTING
            or northing < config.BASEMAP_ORIGIN_NORTHING
            or northing > config.BASEMAP_EXTENT_NORTHING):
        return False
    return True

def plot_points(fire_map: graphics.utm_plot.Map,
                points:  list[tuple[int, int]],
                size_px: int = config.FIRE_SYMBOL_SIZE,
                color: str = config.FIRE_SYMBOL_COLOR) -> list:
    """Plot all the points and return a list of handles that
    can be used for moving them.
    """
    symbols = []
    for point in points:
        easting, northing = point
        symbol = fire_map.plot_point(easting, northing,
                                     size_px=size_px, color=color)
        symbols.append(symbol)
    return symbols

def assign_random(points: list[tuple[int, int]], n: int) -> list[list[tuple[int, int]]]:
    """Returns a list of n lists of coordinate pairs.
    The i'th list is the points assigned randomly to the i'th cluster.
    """
    # Initially the assignments is a list of n empty lists
    assignments = []
    for i in range(n):
        assignments.append([])
    # Then we randomly assign points to lists
    for point in points:
        choice = random.randrange(n)
        assignments[choice].append(point)
    return assignments

def centroid(points: list[tuple[int, int]]) -> tuple[int, int]:
    """The centroid of a set of points is the mean of x and mean of y"""
    if points == []:
        return (0,0)
    else:
        x = [x[0] for x in points]
        y = [x[1] for x in points]
        total_x = sum(x) // len(x)
        total_y = sum(y) // len(y)
        return [total_x, total_y]


def cluster_centroids(clusters: list[list[tuple[int,int]]]) -> list[tuple[int,int]]:
    """Return a list containing the centroid corresponding to each assignment of
    points to a cluster.
    """
    centroids = []
    for cluster in clusters:
        centroids.append(centroid(cluster))
    return centroids

def sq_dist(p1: tuple[int, int], p2: tuple[int, int]) -> int:
    """Square of Euclidean distance between p1 and p2

    >>> sq_dist([2, 3], [3, 5])
    5
    """
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    return dx*dx + dy*dy

def closest_index(point: tuple[int, int], centroids: list[tuple[int, int]]) -> int:
    """Returns the index of the centroid closest to point

    >>> closest_index((5, 5), [(3, 2), (4, 5), (7, 1)])
    1
    """

    #Default closest point is the first centroid
    closest = sq_dist(point, centroids[0])
    closest_centroid = 0

    #loop through centroids to determine if any are closer than the default
    for i in range(len(centroids)):
        if sq_dist(point, centroids[i]) < closest:
            closest = sq_dist(point, centroids[i])
            closest_centroid = i
    return closest_centroid

def assign_closest(points: list[tuple[int,int]],
                   centroids: list[tuple[int, int]]
                   ) -> list[list[int, int]]:
    """Returns a list of lists.  The i'th list contains the points
    assigned to the i'th centroid.  Each point is assigned to the
    centroid it is closest to.

    >>> assign_closest([(1, 1), (2, 2), (5, 5)], [(4, 4), (2, 2)])
    [[(5, 5)], [(1, 1), (2, 2)]]
    """
    # Initially the assignments is a list of n empty lists
    assignments = []
    for i in range(len(centroids)):
        assignments.append([])

    for i in range(len(points)):
        closest = closest_index(points[i], centroids)
        assignments[closest].append(points[i])
    return assignments

def move_points(fire_map: graphics.utm_plot.Map,
                points:  list[tuple[int, int]],
                symbols: list):
    """Move a set of symbols to new points"""
    for i in range(len(points)):
        fire_map.move_point(symbols[i], points[i])

def show_clusters(fire_map: graphics.utm_plot.Map,
                  centroid_symbols: list,
                  assignments: list[list[tuple[int, int]]]):
    """Connect each centroid to all the points in its cluster"""
    for i in range(len(centroid_symbols)):
        fire_map.connect_all(centroid_symbols[i], assignments[i])

if __name__ == "__main__":
    main()

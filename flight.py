import pandas as pd
import networkx as nx
from geopy.distance import great_circle
import plotly.graph_objects as go

# 1. Load airport and route data
airports_url = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
routes_url = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat"

airports = pd.read_csv(airports_url, header=None)
routes = pd.read_csv(routes_url, header=None)

# 2. Clean and extract relevant columns
airports = airports[[0, 1, 2, 3, 4, 6, 7]]
airports.columns = ["AirportID", "Name", "City", "Country", "IATA", "Latitude", "Longitude"]
airports = airports[airports["IATA"].apply(lambda x: isinstance(x, str) and len(x) == 3)]

routes = routes[[2, 4]]  # Source and Destination IATA codes
routes.columns = ["Source", "Destination"]

# 3. Map airport IATA to coordinates
airport_coords = {
    row["IATA"]: (row["Latitude"], row["Longitude"]) 
    for _, row in airports.iterrows()
}

# 4. Function to compute great-circle distance
def get_distance(source_code, dest_code):
    if source_code in airport_coords and dest_code in airport_coords:
        return great_circle(airport_coords[source_code], airport_coords[dest_code]).km
    return None

# 5. Build the graph
G = nx.DiGraph()
for _, row in routes.iterrows():
    src, dst = row["Source"], row["Destination"]
    dist = get_distance(src, dst)
    if dist:
        G.add_edge(src, dst, weight=dist)

# 6. Function to find all best routes from all airport pairs
def get_airports_by_city(city_name):
    return airports[airports["City"].str.lower() == city_name.lower()]["IATA"].tolist()

def find_all_routes(source_city, dest_city):
    source_airports = get_airports_by_city(source_city)
    dest_airports = get_airports_by_city(dest_city)
    
    all_routes = []

    for src in source_airports:
        for dst in dest_airports:
            try:
                path = nx.dijkstra_path(G, source=src, target=dst, weight='weight')
                dist = nx.dijkstra_path_length(G, source=src, target=dst, weight='weight')
                all_routes.append((src, dst, path, dist))
            except nx.NetworkXNoPath:
                continue
    
    return all_routes

# 7. Plot all routes
def plot_all_routes(routes):
    fig = go.Figure()
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'cyan', 'magenta']
    
    for idx, (_, _, path, dist) in enumerate(routes):
        lats, lons = zip(*[airport_coords[code] for code in path])
        fig.add_trace(go.Scattergeo(
            lon=lons,
            lat=lats,
            mode='lines+markers',
            name=f"{' → '.join(path)} ({dist:.1f} km)",
            line=dict(width=2, color=colors[idx % len(colors)])
        ))

    fig.update_layout(
        title='All Possible Routes Between Selected Cities',
        geo_scope='world'
    )
    fig.show()

# 8. User Input
print("✈️  Welcome to the Flight Route Optimizer!")
print(" Find the shortest route between two cities (based on real airport data).")
print(" Example cities: Mumbai, Delhi, New York, London, Tokyo")

source_city = input("Enter Source City Name: ")
destination_city = input("Enter Destination City Name: ")

routes_found = find_all_routes(source_city, destination_city)

if routes_found:
    # Sort by distance (optional, best route first)
    routes_found.sort(key=lambda x: x[3])
    
    print(f"\n✅ Found {len(routes_found)} possible route(s):\n")
    for idx, (src, dst, path, dist) in enumerate(routes_found):
        print(f"{idx + 1}. Route: {' → '.join(path)} | Distance: {dist:.2f} km")
    
    plot_all_routes(routes_found)
else:
    print("❌ No valid routes found between these cities.")

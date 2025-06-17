pfrom arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
import pyproj
import pandas as pd

# Autenticación
gis = GIS("https://www.arcgis.com", username=os.environ["coellop_gadmriobamba"], password=os.environ["S0l0Y0paola2837"])

# Obtener ítem
item = gis.content.get("3fa2bcad8ee34479ada0fec1dd4cabf3")
layer = item.layers[0]

# Consultar registros pendientes
query = layer.query(
    where="utm_x IS NOT NULL AND utm_y IS NOT NULL AND (geopoint_final IS NULL OR geopoint_final = '')",
    out_fields="objectid, utm_x, utm_y",
    return_geometry=False
)

df = pd.DataFrame.from_records([f.attributes for f in query.features])

if df.empty:
    print("No hay registros pendientes.")
else:
    print(f"{len(df)} registros encontrados para transformar.")

    # Transformación EPSG:32717 -> EPSG:4326
    transformer = pyproj.Transformer.from_crs("EPSG:32717", "EPSG:4326", always_xy=True)

    def transform_coords(row):
        easting = row['utm_x']
        northing = row['utm_y']
        lon, lat = transformer.transform(easting, northing)
        return lat, lon

    df['lat'], df['lon'] = zip(*df.apply(transform_coords, axis=1))

    features_to_update = []
    for _, row in df.iterrows():
        feature = {
            "attributes": {
                "objectid": row['objectid']
            },
            "geometry": {
                "x": row['lon'],
                "y": row['lat'],
                "spatialReference": {"wkid": 4326}
            }
        }
        features_to_update.append(feature)

    result = layer.edit_features(updates=features_to_update)
    print("Actualización completada:", result)

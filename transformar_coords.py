from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
import pyproj
import pandas as pd
import os

def main():
    # Autenticación
    gis = GIS("https://www.arcgis.com", username=os.environ["GIS_USER"], password=os.environ["GIS_PASS"])

    # Obtener ítem
    item = gis.content.get("8dcb434e6bce4584abf28bc94a82b68a")
    if item is None:
        print("Error: No se encontró el ítem con ese ID.")
        return

    layer = item.layers[0]

    # Consulta para obtener registros con coordenadas UTM sin transformar
    query = layer.query(
        where="utm_x IS NOT NULL AND utm_y IS NOT NULL", 
        out_fields="objectid, utm_x, utm_y", 
        return_geometry=False
    )

    # Convertir resultado a DataFrame
    df = pd.DataFrame.from_records([f.attributes for f in query.features])

    if df.empty:
        print("No hay registros pendientes.")
        return
    else:
        print(f"{len(df)} registros encontrados para transformar.")

    # Definir transformación UTM 17S (EPSG:32717) a WGS84 (EPSG:4326)
    transformer = pyproj.Transformer.from_crs("EPSG:32717", "EPSG:4326", always_xy=True)

    # Función para transformar coordenadas
    def transform_coords(row):
        easting = row['utm_x']
        northing = row['utm_y']
        lon, lat = transformer.transform(easting, northing)
        return lat, lon

    # Aplicar transformación y agregar columnas lat y lon
    df['lat'], df['lon'] = zip(*df.apply(transform_coords, axis=1))

    # Preparar lista de features para actualizar geometría
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

    # Actualizar las geometrías en el Feature Layer
    result = layer.edit_features(updates=features_to_update)
    print("Actualización completada:", result)

if __name__ == "__main__":
    main()

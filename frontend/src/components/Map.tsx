import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, Circle } from "react-leaflet";
import { apiGet } from "../api/client";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Fix Leaflet default icon issue
import icon from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

type MapFeature = {
  type: string;
  geometry: {
    type: string;
    coordinates: [number, number];
  };
  properties: {
    id: number;
    name: string;
    level: string;
    risk_prob: number;
    risk_score: number;
    confidence: number;
    trend: string;
    is_anomaly: boolean;
  };
};

type MapData = {
  type: string;
  features: MapFeature[];
};

export default function MapView() {
  const [mapData, setMapData] = useState<MapData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const data = await apiGet<MapData>("/territories/map?tenant_id=1");
        setMapData(data);
      } catch (e: any) {
        setError(e?.message ?? "Error loading map");
      }
    })();
  }, []);

  if (error) {
    return <div className="p-4 bg-red-100 text-red-800 rounded">{error}</div>;
  }

  if (!mapData || mapData.features.length === 0) {
    return (
      <div className="p-4 bg-yellow-100 text-yellow-800 rounded">
        No hay territorios con coordenadas disponibles. Agrega territorios desde el panel de configuración.
      </div>
    );
  }

  // Calcular centro del mapa
  const center: [number, number] =
    mapData.features.length > 0
      ? [
          mapData.features[0].geometry.coordinates[1],
          mapData.features[0].geometry.coordinates[0],
        ]
      : [-33.4489, -70.6693]; // Default: Santiago

  const getRiskColor = (prob: number) => {
    if (prob >= 0.7) return "#ef4444"; // red-500
    if (prob >= 0.5) return "#f59e0b"; // amber-500
    if (prob >= 0.3) return "#eab308"; // yellow-500
    return "#10b981"; // green-500
  };

  return (
    <div className="h-[600px] rounded-2xl overflow-hidden shadow-lg">
      <MapContainer center={center} zoom={6} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {mapData.features.map((feature) => {
          const [lon, lat] = feature.geometry.coordinates;
          const { name, risk_prob, risk_score, confidence, trend, is_anomaly } =
            feature.properties;

          return (
            <React.Fragment key={feature.properties.id}>
              <Marker position={[lat, lon]}>
                <Popup>
                  <div className="text-sm">
                    <div className="font-semibold text-lg mb-1">{name}</div>
                    <div className="space-y-1">
                      <div>
                        <span className="font-medium">Probabilidad: </span>
                        <span
                          className="font-bold"
                          style={{ color: getRiskColor(risk_prob) }}
                        >
                          {(risk_prob * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div>
                        <span className="font-medium">Confianza: </span>
                        {(confidence * 100).toFixed(1)}%
                      </div>
                      <div>
                        <span className="font-medium">Score: </span>
                        {risk_score.toFixed(2)}
                      </div>
                      <div>
                        <span className="font-medium">Tendencia: </span>
                        <span
                          className={
                            trend === "rising"
                              ? "text-red-600"
                              : trend === "falling"
                              ? "text-green-600"
                              : "text-gray-600"
                          }
                        >
                          {trend === "rising" ? "↗️ Subiendo" : trend === "falling" ? "↘️ Bajando" : "→ Estable"}
                        </span>
                      </div>
                      {is_anomaly && (
                        <div className="text-red-600 font-bold">⚠️ Anomalía detectada</div>
                      )}
                    </div>
                  </div>
                </Popup>
              </Marker>
              <Circle
                center={[lat, lon]}
                radius={risk_prob * 50000} // Radio proporcional al riesgo (max 50km)
                pathOptions={{
                  color: getRiskColor(risk_prob),
                  fillColor: getRiskColor(risk_prob),
                  fillOpacity: 0.2,
                }}
              />
            </React.Fragment>
          );
        })}
      </MapContainer>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, GeoJSON, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";

function MapClickHandler({ onMapClick }: { onMapClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click: (e) => onMapClick(e.latlng.lat, e.latlng.lng),
  });
  return null;
}

export default function Map() {
  // THE TYPESCRIPT FIXES: Added <any> and the coordinate types
  const [routeData, setRouteData] = useState<any>(null);
  const [startCoords, setStartCoords] = useState<{lat: number, lng: number} | null>(null);
  
  const [displayDistance, setDisplayDistance] = useState("5.00");
  const [unit, setUnit] = useState("km"); 
  const [terrain, setTerrain] = useState("road"); 
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  const [routeStats, setRouteStats] = useState({ actualDistance: 0, ascent: 0 });

  useEffect(() => {
    if (!startCoords) return;
    const parsedDistance = parseFloat(displayDistance.toString()) || 0;
    if (parsedDistance <= 0) return;

    const targetMeters = Math.round(parsedDistance * (unit === "km" ? 1000 : 1609.34));

    const timer = setTimeout(() => {
      setLoading(true);
      setErrorMsg(null); 
      
      fetch(`https://run-generator.onrender.com/api/route?distance=${targetMeters}&lat=${startCoords.lat}&lon=${startCoords.lng}&terrain=${terrain}`)
        .then(async (res) => {
          if (!res.ok) {
            const errorData = await res.json().catch(() => ({}));
            throw new Error(errorData.detail || "Backend routing failed.");
          }
          return res.json();
        })
        .then((data) => {
          if (data && data.features && data.features.length > 0) {
            setRouteData(data);
            const summary = data.features[0].properties.summary;
            setRouteStats({
              actualDistance: summary.distance || 0,
              ascent: summary.ascent || 0
            });
          } else {
            throw new Error("Received invalid map data from the server.");
          }
          setLoading(false);
        })
        .catch((err) => {
           console.error("Error:", err);
           setErrorMsg(err.message); 
           setRouteData(null);
           setLoading(false); 
        });
    }, 500);

    return () => clearTimeout(timer);
  }, [startCoords, displayDistance, unit, terrain]); 

  // THE GPX GENERATOR
  const downloadGPX = () => {
    if (!routeData) return;
    
    const coords = routeData.features[0].geometry.coordinates;
    let gpx = '<?xml version="1.0" encoding="UTF-8"?>\n';
    gpx += '<gpx version="1.1" creator="RouteGenerator">\n  <trk>\n    <trkseg>\n';
    
    coords.forEach((coord: number[]) => {
      const ele = coord[2] ? `\n        <ele>${coord[2]}</ele>\n      ` : '';
      gpx += `      <trkpt lat="${coord[1]}" lon="${coord[0]}">${ele}</trkpt>\n`;
    });
    
    gpx += '    </trkseg>\n  </trk>\n</gpx>';
    
    const blob = new Blob([gpx], { type: 'application/gpx+xml' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `run-${parseFloat(displayDistance.toString()).toFixed(1)}${unit}.gpx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const actualDistanceDisplay = unit === "km" 
    ? (routeStats.actualDistance / 1000).toFixed(2)
    : (routeStats.actualDistance / 1609.34).toFixed(2);
    
  const elevationDisplay = unit === "km"
    ? Math.round(routeStats.ascent)
    : Math.round(routeStats.ascent * 3.28084); 
    
  const elevationUnit = unit === "km" ? "m" : "ft";

  return (
    <div className="h-screen w-full relative">
      <div className="absolute top-4 left-4 z-[1000] bg-white p-4 rounded-xl shadow-xl w-80 space-y-4">
        <div className="flex justify-between items-center">
          <h1 className="font-bold text-lg text-gray-800">Route Generator</h1>
          
          <button 
            onClick={() => {
              const current = parseFloat(displayDistance.toString()) || 0;
              if (unit === "km") {
                setDisplayDistance((current * 0.621371).toFixed(2));
                setUnit("mi");
              } else {
                setDisplayDistance((current * 1.60934).toFixed(2));
                setUnit("km");
              }
            }}
            className="text-xs font-bold bg-gray-100 hover:bg-gray-200 text-gray-800 px-2 py-1 rounded transition-colors"
          >
            Switch to {unit === "km" ? "Miles" : "KM"}
          </button>
        </div>
        
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Target Distance</label>
            
            <div className="flex items-center space-x-1">
              <input
                type="number"
                step="0.01"
                value={displayDistance}
                onChange={(e) => setDisplayDistance(e.target.value)}
                className="w-20 text-right bg-gray-50 border border-gray-200 rounded p-1 text-sm font-bold text-black focus:outline-none focus:ring-1 focus:ring-black"
              />
              <span className="text-sm font-bold text-black w-6">{unit}</span>
            </div>
          </div>
          
          <input
            type="range"
            min={unit === "km" ? 2 : 1}
            max={unit === "km" ? 30 : 20}
            step="0.1"
            value={parseFloat(displayDistance.toString()) || 0}
            onChange={(e) => setDisplayDistance(e.target.value)}
            className="w-full accent-black cursor-pointer"
          />
        </div>

        <div className="mt-2">
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider block mb-1">Terrain</label>
          <select 
            value={terrain} 
            onChange={(e) => setTerrain(e.target.value)}
            className="w-full bg-gray-50 border border-gray-200 rounded p-2 text-sm font-bold text-black focus:outline-none focus:ring-1 focus:ring-black cursor-pointer"
          >
            <option value="road">Strictly Paved (Roads & Sidewalks)</option>
            <option value="trail">Nature & Dirt (Trails & Parks)</option>
          </select>
        </div>

        {errorMsg && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-3 rounded-lg mt-2">
            <strong>Error:</strong> {errorMsg}
          </div>
        )}

        {routeData && !errorMsg && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Actual Route Stats</h2>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-gray-50 p-2 rounded-lg">
                <p className="text-xs text-gray-500">Distance</p>
                <p className="font-bold text-black text-lg">
                  {actualDistanceDisplay} <span className="text-sm font-normal text-gray-500">{unit}</span>
                </p>
              </div>
              <div className="bg-gray-50 p-2 rounded-lg">
                <p className="text-xs text-gray-500">Elevation Gain</p>
                <p className="font-bold text-black text-lg">
                  {elevationDisplay} <span className="text-sm font-normal text-gray-500">{elevationUnit}</span>
                </p>
              </div>
            </div>
            
            <button
              onClick={downloadGPX}
              className="w-full bg-black hover:bg-gray-800 text-white font-bold py-2 px-4 rounded-lg text-sm transition-colors"
            >
              Download GPX for Watch
            </button>
          </div>
        )}

        <p className="text-xs text-gray-400 italic">Tip: Click anywhere on the map to change your starting point.</p>
      </div>

      {loading && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-[1000] bg-black text-white px-6 py-2 rounded-full font-bold shadow-lg text-sm">
          Calculating Route...
        </div>
      )}
      
      <MapContainer center={[50.885, -1.246]} zoom={13} className="h-full w-full z-0">
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapClickHandler onMapClick={(lat, lng) => setStartCoords({ lat, lng })} />
        
        {routeData && !errorMsg && (
          <GeoJSON 
            data={routeData} 
            // THE TYPESCRIPT FIX: Added question marks here
            key={`${startCoords?.lat}-${startCoords?.lng}-${routeStats.actualDistance}`} 
            style={{
              color: '#FC4C02', 
              weight: 5,
              opacity: 0.8,
              lineCap: 'round',
              lineJoin: 'round'
            }}
          />
        )}
      </MapContainer>
    </div>
  );
}
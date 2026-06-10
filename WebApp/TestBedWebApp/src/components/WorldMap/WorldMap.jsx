import React, { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import terminator from '@joergdietrich/leaflet.terminator';
import styles from './WorldMap.module.css';

import EARTHMAP from '../../assets/world.jpg';
const IMAGE_URL = 'textures/sat.png';

const IMAGE_ASPECT_RATIO = 1434 / 751;
const IMAGE_SIZE_PROPORTION = 0.9;

const BOUNDS = [
  [-90, -180],
  [90, 180],
];

export default function WorldMap() {
  const satLon = useSelector((state) => state.sat.longitude);
  const satLat = useSelector((state) => state.sat.latitude);
  const simTime = useSelector((state) => state.sat.time);

  const [terminatorLayerState, setTerminatorLayerState] = useState(null);
  const mapRef = useRef(null);
  const imageOverlayRef = useRef(null);
  const mapInstanceRef = useRef(null);

  useEffect(() => {
    if (mapInstanceRef.current) return;

    console.log('Initializing map with settings:', {
      center: [0, 0],
      zoom: 1,
      dragging: false,
    });

    const map = L.map(mapRef.current, {
      center: [0, 0],
      zoom: 1,
      layers: [L.imageOverlay(EARTHMAP, BOUNDS)],
      dragging: false,
      touchZoom: false,
      scrollWheelZoom: false,
      doubleClickZoom: false,
      boxZoom: false,
      zoomControl: false,
      attributionControl: false,
    });

    mapInstanceRef.current = map;

    let terminatorLayer = terminator().addTo(map);
    console.log('Terminator layer initialized:', terminatorLayer);
    setTerminatorLayerState(terminatorLayer);

    return () => {
      console.log('Cleaning up map instance');
      map.remove();
    };
  }, []);

  useEffect(() => {
    if (!mapInstanceRef.current || !terminatorLayerState) return;

    const date = new Date(simTime * 1000);
    console.log('Updating terminator with:', {
      simTime: simTime,
      date: date.toUTCString(),
      terminatorLayer: terminatorLayerState,
    });

    terminatorLayerState.setTime(date);
  }, [satLat, satLon]);

  useEffect(() => {
    if (!mapInstanceRef.current) return;

    const map = mapInstanceRef.current;

    const centerLat = satLat;
    const centerLon = satLon;
    const halfHeight = 12 * IMAGE_SIZE_PROPORTION;
    const halfWidth = halfHeight * IMAGE_ASPECT_RATIO;

    console.log('Image overlay calculations:', {
      centerLat,
      centerLon,
      halfHeight,
      halfWidth,
      imageAspectRatio: IMAGE_ASPECT_RATIO,
      sizeProportion: IMAGE_SIZE_PROPORTION,
    });

    const latLngBounds = [
      [
        centerLat - halfHeight,
        centerLon - halfWidth / Math.cos(centerLat * (Math.PI / 180)),
      ],
      [
        centerLat + halfHeight,
        centerLon + halfWidth / Math.cos(centerLat * (Math.PI / 180)),
      ],
    ];

    console.log('Calculated bounds:', latLngBounds);

    if (!imageOverlayRef.current) {
      const overlay = L.imageOverlay(IMAGE_URL, latLngBounds, {
        opacity: 1,
        zIndex: 1000,
      }).addTo(map);
      imageOverlayRef.current = overlay;
      console.log('Created new image overlay');
    } else {
      imageOverlayRef.current.setBounds(latLngBounds);
      console.log('Updated existing image overlay bounds');
    }
  }, [satLon, satLat]);

  return <div className={styles.map2D} ref={mapRef}></div>;
}

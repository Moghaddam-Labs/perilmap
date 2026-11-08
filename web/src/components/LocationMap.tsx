"use client";

import "maplibre-gl/dist/maplibre-gl.css";
import type { Map as MapLibreMap, Marker } from "maplibre-gl";
import { useEffect, useRef } from "react";
import { LONDON_BOUNDARY, type Position } from "@/lib/geo";
import { MAP_BOUNDS, MAP_STYLES, MAP_WORKER_PATH, STREET_ZOOM } from "@/lib/map";
import { onPrintPrepare } from "@/lib/print";
import styles from "./LocationMap.module.css";

interface LocationMapProps {
  start: Position;
  pin: Position;
  onPinChange: (pin: Position) => void;
  onUnavailable: () => void;
}

const BOUNDARY = "london-boundary";
const KEY_STEP_PIXELS = 10;
const ARROWS: Record<string, [number, number]> = {
  ArrowUp: [0, -1],
  ArrowDown: [0, 1],
  ArrowLeft: [-1, 0],
  ArrowRight: [1, 0],
};
const SVG = "http://www.w3.org/2000/svg";

function prefersDark() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

/** Printing forces the light colours, so the map's boundary line follows the page, not the device. */
function lightPage() {
  return document.documentElement.getAttribute("data-theme") === "light" || !prefersDark();
}

/** Waits until the map has finished drawing, or gives up after a few seconds. */
function whenIdle(map: MapLibreMap, timeoutMs = 4000) {
  return new Promise<void>((resolve) => {
    const timer = setTimeout(resolve, timeoutMs);
    map.once("idle", () => {
      clearTimeout(timer);
      resolve();
    });
  });
}

function svgElement(tag: string, attributes: Record<string, string>) {
  const element = document.createElementNS(SVG, tag);
  for (const [name, value] of Object.entries(attributes)) {
    element.setAttribute(name, value);
  }
  return element;
}

/** The pin is a real button, so it can be reached and moved with a keyboard. */
function createPinButton() {
  const button = document.createElement("button");
  button.type = "button";
  button.className = styles.pin ?? "";
  button.setAttribute("aria-label", "Pin marking the home. Use the arrow keys to move it.");
  const icon = svgElement("svg", {
    viewBox: "0 0 32 40",
    "aria-hidden": "true",
    focusable: "false",
  });
  icon.append(
    svgElement("path", {
      d: "M16 38.5S29 25.4 29 15.5a13 13 0 0 0-26 0C3 25.4 16 38.5 16 38.5Z",
      class: styles.pinBody ?? "",
    }),
    svgElement("circle", { cx: "16", cy: "15.5", r: "5", class: styles.pinHole ?? "" }),
  );
  button.append(icon);
  return button;
}

function addBoundary(map: MapLibreMap) {
  if (!map.getSource(BOUNDARY)) {
    map.addSource(BOUNDARY, { type: "geojson", data: LONDON_BOUNDARY });
  }
  if (!map.getLayer(BOUNDARY)) {
    map.addLayer({
      id: BOUNDARY,
      type: "line",
      source: BOUNDARY,
      paint: {
        "line-color": lightPage() ? "#12332b" : "#eef6f2",
        "line-width": 2,
        "line-dasharray": [2, 2],
      },
    });
  }
}

const PIN_PATH = "M16 38.5S29 25.4 29 15.5a13 13 0 0 0-26 0C3 25.4 16 38.5 16 38.5Z";

/**
 * A still image of the map with the pin drawn on, for printing. A live map doesn't print reliably,
 * because it redraws when the page changes size for paper.
 */
function snapshot(map: MapLibreMap, marker: Marker) {
  const source = map.getCanvas();
  const copy = document.createElement("canvas");
  copy.width = source.width;
  copy.height = source.height;
  const context = copy.getContext("2d");
  if (!context || !source.clientWidth) return null;
  context.drawImage(source, 0, 0);
  const scale = source.width / source.clientWidth;
  const point = map.project(marker.getLngLat());
  context.translate(point.x * scale, point.y * scale);
  // The pin on screen is 44 px tall for a 40 unit drawing, with its tip at the bottom.
  context.scale(1.1 * scale, 1.1 * scale);
  context.translate(-16, -40);
  context.lineWidth = 2;
  context.fillStyle = "#ff7f6e";
  context.strokeStyle = "#12332b";
  const body = new Path2D(PIN_PATH);
  context.fill(body);
  context.stroke(body);
  context.beginPath();
  context.arc(16, 15.5, 5, 0, Math.PI * 2);
  context.fillStyle = "#ffffff";
  context.fill();
  context.lineWidth = 1.5;
  context.stroke();
  return copy.toDataURL("image/png");
}

/** The map, loaded only when needed because MapLibre is large. */
export function LocationMap({ start, pin, onPinChange, onUnavailable }: LocationMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markerRef = useRef<Marker | null>(null);
  const snapshotRef = useRef<HTMLImageElement>(null);
  const styleRef = useRef<string>(MAP_STYLES.light);
  const callbacks = useRef({ onPinChange, onUnavailable });
  useEffect(() => {
    callbacks.current = { onPinChange, onUnavailable };
  });

  useEffect(() => {
    let cancelled = false;
    let cleanup = () => {};

    (async () => {
      let maplibre: typeof import("maplibre-gl");
      try {
        maplibre = await import("maplibre-gl");
      } catch {
        callbacks.current.onUnavailable();
        return;
      }
      if (cancelled || !containerRef.current) return;
      maplibre.setWorkerUrl(MAP_WORKER_PATH);

      let map: MapLibreMap;
      try {
        map = new maplibre.Map({
          container: containerRef.current,
          style: (styleRef.current = prefersDark() ? MAP_STYLES.dark : MAP_STYLES.light),
          center: [start.longitude, start.latitude],
          zoom: STREET_ZOOM,
          minZoom: 9,
          maxBounds: MAP_BOUNDS,
          dragRotate: false,
          pitchWithRotate: false,
          touchPitch: false,
          cooperativeGestures: true,
          attributionControl: { compact: false },
          // Keeps the last drawn map available, so it can be copied into an image for printing.
          canvasContextAttributes: { preserveDrawingBuffer: true },
        });
      } catch {
        callbacks.current.onUnavailable();
        return;
      }
      mapRef.current = map;
      map.touchZoomRotate.disableRotation();
      map.keyboard.disableRotation();
      map.addControl(new maplibre.NavigationControl({ showCompass: false }), "top-right");

      let loaded = false;
      map.on("load", () => {
        loaded = true;
      });
      map.on("style.load", () => addBoundary(map));
      map.on("error", () => {
        // Missing tiles after loading only leave gaps. Failing before it means there's no map.
        if (!loaded) {
          callbacks.current.onUnavailable();
        }
      });

      const element = createPinButton();
      const marker = new maplibre.Marker({ element, anchor: "bottom", draggable: true })
        .setLngLat([start.longitude, start.latitude])
        .addTo(map);
      markerRef.current = marker;

      const report = () => {
        const { lat, lng } = marker.getLngLat();
        callbacks.current.onPinChange({ latitude: lat, longitude: lng });
      };
      marker.on("dragend", report);
      map.on("click", (event) => {
        marker.setLngLat(event.lngLat);
        report();
      });
      element.addEventListener("keydown", (event) => {
        const direction = ARROWS[event.key];
        if (!direction) return;
        event.preventDefault();
        const step = event.shiftKey ? KEY_STEP_PIXELS * 5 : KEY_STEP_PIXELS;
        const point = map.project(marker.getLngLat());
        const moved = map.unproject([point.x + direction[0] * step, point.y + direction[1] * step]);
        marker.setLngLat(moved);
        if (!map.getBounds().contains(moved)) {
          map.panTo(moved);
        }
        report();
      });

      const scheme = window.matchMedia("(prefers-color-scheme: dark)");
      const changeScheme = () => {
        styleRef.current = scheme.matches ? MAP_STYLES.dark : MAP_STYLES.light;
        map.setStyle(styleRef.current);
      };
      scheme.addEventListener("change", changeScheme);

      cleanup = () => {
        scheme.removeEventListener("change", changeScheme);
        map.remove();
        mapRef.current = null;
        markerRef.current = null;
      };
    })();

    return () => {
      cancelled = true;
      cleanup();
    };
  }, [start.latitude, start.longitude]);

  // Follows changes made outside the map, such as moving the pin back to the postcode's centre.
  useEffect(() => {
    const marker = markerRef.current;
    const map = mapRef.current;
    if (!marker || !map) return;
    const current = marker.getLngLat();
    if (current.lat !== pin.latitude || current.lng !== pin.longitude) {
      marker.setLngLat([pin.longitude, pin.latitude]);
      map.easeTo({ center: [pin.longitude, pin.latitude] });
    }
  }, [pin.latitude, pin.longitude]);

  useEffect(
    () =>
      onPrintPrepare(async ({ canWait }) => {
        const map = mapRef.current;
        const marker = markerRef.current;
        const image = snapshotRef.current;
        if (!map || !marker || !image) return;
        let undo: (() => void) | undefined;
        // A dark map wastes ink and is hard to read on paper, so the print button switches to the
        // light map first, waits for it to draw, and switches back afterwards.
        if (canWait && styleRef.current === MAP_STYLES.dark) {
          const drawn = whenIdle(map);
          map.setStyle(MAP_STYLES.light);
          await drawn;
          undo = () => {
            if (styleRef.current === MAP_STYLES.dark) map.setStyle(MAP_STYLES.dark);
          };
        }
        try {
          const source = snapshot(map, marker);
          if (source) image.src = source;
        } catch {
          // Without an image, the printout still has the location in words.
        }
        return undo;
      }),
    [],
  );

  return (
    <>
      <div ref={containerRef} className={`${styles.map} no-print`} />
      <figure className={`print-only ${styles.printMap}`}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img ref={snapshotRef} alt="Map of the area, with the pin on the home" data-map-snapshot />
        <figcaption>
          Map: OpenFreeMap © OpenMapTiles, data from OpenStreetMap © OpenStreetMap contributors.
        </figcaption>
      </figure>
    </>
  );
}

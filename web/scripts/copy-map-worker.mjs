// MapLibre runs part of its work in a separate worker file. Serving it from the site itself keeps
// the content security policy strict, and copying it on each build keeps it matched to the library.
import { copyFileSync, mkdirSync } from "node:fs";

const source = new URL("../node_modules/maplibre-gl/dist/maplibre-gl-worker.mjs", import.meta.url);
const folder = new URL("../public/vendor/", import.meta.url);

mkdirSync(folder, { recursive: true });
copyFileSync(source, new URL("maplibre-gl-worker.mjs", folder));

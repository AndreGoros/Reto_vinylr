import { loadFont as loadArchivo } from "@remotion/google-fonts/ArchivoBlack";
import { loadFont as loadNewsreader } from "@remotion/google-fonts/Newsreader";

// Fuentes cargadas dentro de Remotion (delayRender interno): el render espera a que estén listas.
const archivo = loadArchivo("normal", { weights: ["400"], subsets: ["latin"] });
const newsreader = loadNewsreader("italic", { weights: ["400", "500"], subsets: ["latin"] });

export const FONT_SANS = `${archivo.fontFamily}, "Arial Black", "Helvetica Neue", sans-serif`;
export const FONT_SERIF = `${newsreader.fontFamily}, Georgia, "Times New Roman", serif`;

// BRAND_GUIDE.md — 90% blanco/negro/gris + 10% color.
export const C = {
  black: "#050505",
  white: "#F5F5F3",
  gray: "#777777",
  dark: "#202020",
  blue: "#4263FF",
  magenta: "#C73E7D",
};

// Igual que country_accents en duelo_template_split.html.j2
export const COUNTRY_ACCENTS: Record<string, string> = {
  Mexico: "#16855B",
  Argentina: "#36C5F0",
  Colombia: "#F4C430",
  Chile: "#E63946",
};

export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;

// Zonas que tapa la UI de Instagram Reels (nombre de cuenta, caption, botones).
export const SAFE_TOP = 250;
export const SAFE_BOTTOM = 1540;

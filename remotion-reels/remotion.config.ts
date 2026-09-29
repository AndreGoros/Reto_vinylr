import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setCodec("h264");
// Instagram Reels / TikTok aceptan h264 + aac; crf 18 = buena calidad sin pesar de más.
Config.setCrf(18);

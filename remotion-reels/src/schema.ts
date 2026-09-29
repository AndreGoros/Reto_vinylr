import { z } from "zod";

// Mismos nombres de campo que el JSON del pipeline Python (cover_url, artists, country)
// => el "hueco" se llena con el dict de build_duels() sin mapear nada.
export const albumSchema = z.object({
  name: z.string(),
  artists: z.array(z.string()),
  cover_url: z.string(),
  country: z.string().optional(),
});

export const dueloSchema = z.object({
  albumA: albumSchema,
  albumB: albumSchema,
  kicker: z.string(),
  headline: z.string(),
  turnHeadline: z.string(),
  cta: z.string(),
  year: z.string(),
});

export const top10Schema = z.object({
  countryName: z.string(),
  accentPrimary: z.string(),
  accentSecondary: z.string(),
  featuredCoverUrl: z.string(),
  items: z.array(z.object({ rank: z.number(), artist: z.string(), title: z.string() })).min(3).max(10),
  secondsPerItem: z.number(),
  cta: z.string(),
  year: z.string(),
});

export type Album = z.infer<typeof albumSchema>;
export type DueloProps = z.infer<typeof dueloSchema>;
export type Top10Props = z.infer<typeof top10Schema>;

import React from "react";
import { Composition } from "remotion";
import { DueloReel } from "./compositions/DueloReel";
import { TOP10_INTRO, TOP10_OUTRO, Top10Reel } from "./compositions/Top10Reel";
import { dueloSchema, top10Schema } from "./schema";
import { FPS, HEIGHT, WIDTH } from "./theme";

import dueloSample from "../props/duelo.sample.json";
import top10Sample from "../props/top10.sample.json";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="DueloReel"
      component={DueloReel}
      schema={dueloSchema}
      defaultProps={dueloSample}
      durationInFrames={330}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
    <Composition
      id="Top10Reel"
      component={Top10Reel}
      schema={top10Schema}
      defaultProps={top10Sample}
      durationInFrames={510}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
      // La duración se ajusta sola al número de canciones que traiga la API.
      calculateMetadata={({ props }) => ({
        durationInFrames: TOP10_INTRO + props.items.length * Math.round(props.secondsPerItem * FPS) + TOP10_OUTRO,
      })}
    />
  </>
);

import React from "react";
import { Composition } from "remotion";
import { Short } from "./Short";
import narration from "./narration.json";
export const Root: React.FC = () => (
  <Composition id="Short" component={Short} width={1080} height={1920} fps={30}
    durationInFrames={Math.ceil((narration.duration + 0.15 + 1.0) * 30)} />
);

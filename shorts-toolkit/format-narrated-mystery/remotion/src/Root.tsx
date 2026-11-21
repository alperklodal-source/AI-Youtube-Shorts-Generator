import React from "react";
import { Composition } from "remotion";
import { Short } from "./Short";
import { Cover } from "./Cover";
import narration from "./narration.json";
export const Root: React.FC = () => (
  <>
  <Composition id="Cover" component={Cover} width={1080} height={1920} fps={30} durationInFrames={1} defaultProps={{ v: "a" as const }} />
  <Composition id="Short" component={Short} width={1080} height={1920} fps={30}
    durationInFrames={Math.ceil((narration.duration + 0.15 + 1.0) * 30)} />
  </>
);

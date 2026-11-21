import React from "react";
import { Composition } from "remotion";
import { Short, TOTAL_S } from "./Short";
export const Root: React.FC = () => (
  <Composition id="Short" component={Short} width={1080} height={1920} fps={30} durationInFrames={Math.ceil(TOTAL_S * 30)} defaultProps={{}} />
);

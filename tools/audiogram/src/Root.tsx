import React from "react";
import { Composition } from "remotion";
import { AudiogramComposition } from "./Audiogram/Main";
import { defaultAudiogramProps, AudiogramProps } from "./types";

export const RemotionRoot: React.FC = () => {
  const fps = 30;

  return (
    <>
      {/* 1:1 正方形 (X / Twitter, Instagram用) */}
      <Composition<any, AudiogramProps>
        id="AudiogramSquare"
        component={AudiogramComposition}
        durationInFrames={300} // デフォルト10秒 (calculateMetadataで動的調整)
        fps={fps}
        width={1080}
        height={1080}
        defaultProps={defaultAudiogramProps}
        calculateMetadata={({ props }) => {
          const duration = typeof props.durationInSeconds === "number" ? props.durationInSeconds : 10;
          return {
            durationInFrames: Math.max(1, Math.ceil(duration * fps)),
            props,
          };
        }}
      />

      {/* 9:16 縦型 (TikTok / YouTube Shorts / Reels用) */}
      <Composition<any, AudiogramProps>
        id="AudiogramVertical"
        component={AudiogramComposition}
        durationInFrames={300}
        fps={fps}
        width={1080}
        height={1920}
        defaultProps={defaultAudiogramProps}
        calculateMetadata={({ props }) => {
          const duration = typeof props.durationInSeconds === "number" ? props.durationInSeconds : 10;
          return {
            durationInFrames: Math.max(1, Math.ceil(duration * fps)),
            props,
          };
        }}
      />

      {/* 16:9 横型 (YouTube / Web用) */}
      <Composition<any, AudiogramProps>
        id="AudiogramHorizontal"
        component={AudiogramComposition}
        durationInFrames={300}
        fps={fps}
        width={1920}
        height={1080}
        defaultProps={defaultAudiogramProps}
        calculateMetadata={({ props }) => {
          const duration = typeof props.durationInSeconds === "number" ? props.durationInSeconds : 10;
          return {
            durationInFrames: Math.max(1, Math.ceil(duration * fps)),
            props,
          };
        }}
      />
    </>
  );
};

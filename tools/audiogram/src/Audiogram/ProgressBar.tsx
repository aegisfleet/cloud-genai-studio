import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";

interface ProgressBarProps {
  primaryColor?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  primaryColor = "#38bdf8",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const progress = Math.min(1, Math.max(0, frame / (durationInFrames - 1)));
  const currentSec = Math.floor(frame / fps);
  const totalSec = Math.floor(durationInFrames / fps);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 12,
        width: "100%",
        padding: "0 8px",
      }}
    >
      <div
        style={{
          width: "100%",
          height: 6,
          borderRadius: 999,
          backgroundColor: "rgba(255, 255, 255, 0.12)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${progress * 100}%`,
            background: `linear-gradient(90deg, ${primaryColor}, #818cf8)`,
            borderRadius: 999,
            boxShadow: `0 0 12px ${primaryColor}`,
            transition: "width 0.1s linear",
          }}
        />
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 16,
          fontFamily: "'Inter', 'Segoe UI', -apple-system, sans-serif",
          color: "rgba(255, 255, 255, 0.6)",
          fontWeight: 500,
        }}
      >
        <span>{formatTime(currentSec)}</span>
        <span style={{ color: "rgba(255, 255, 255, 0.4)" }}>
          {formatTime(totalSec)}
        </span>
      </div>
    </div>
  );
};

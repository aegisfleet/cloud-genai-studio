import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

interface BackgroundProps {
  primaryColor?: string;
  secondaryColor?: string;
}

export const Background: React.FC<BackgroundProps> = ({
  primaryColor = "#38bdf8",
  secondaryColor = "#818cf8",
}) => {
  const frame = useCurrentFrame();

  // オーブの浮遊アニメーション
  const orb1Y = interpolate(Math.sin(frame * 0.03), [-1, 1], [-40, 40]);
  const orb1X = interpolate(Math.cos(frame * 0.02), [-1, 1], [-30, 30]);

  const orb2Y = interpolate(Math.cos(frame * 0.025), [-1, 1], [30, -30]);
  const orb2X = interpolate(Math.sin(frame * 0.035), [-1, 1], [40, -40]);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundColor: "#090d16",
        overflow: "hidden",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* グリッドメッシュパターン */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `
            linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px)
          `,
          backgroundSize: "40px 40px",
          opacity: 0.8,
        }}
      />

      {/* 発光オーブ 1 (左上) */}
      <div
        style={{
          position: "absolute",
          width: 600,
          height: 600,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${primaryColor} 0%, transparent 70%)`,
          filter: "blur(90px)",
          opacity: 0.28,
          top: "5%",
          left: "10%",
          transform: `translate(${orb1X}px, ${orb1Y}px)`,
        }}
      />

      {/* 発光オーブ 2 (右下) */}
      <div
        style={{
          position: "absolute",
          width: 700,
          height: 700,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${secondaryColor} 0%, transparent 70%)`,
          filter: "blur(110px)",
          opacity: 0.22,
          bottom: "0%",
          right: "5%",
          transform: `translate(${orb2X}px, ${orb2Y}px)`,
        }}
      />

      {/* ビネット（周辺減光） */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "radial-gradient(circle at center, transparent 40%, rgba(5, 7, 13, 0.7) 100%)",
        }}
      />
    </div>
  );
};

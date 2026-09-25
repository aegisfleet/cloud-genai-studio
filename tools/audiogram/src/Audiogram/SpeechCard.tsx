import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";

interface SpeechCardProps {
  speaker: string;
  speakerRole: string;
  speechText: string;
  tag?: string;
  primaryColor?: string;
  secondaryColor?: string;
}

export const SpeechCard: React.FC<SpeechCardProps> = ({
  speaker,
  speakerRole,
  speechText,
  tag = "QWEN3-TTS 1.7B",
  primaryColor = "#38bdf8",
  secondaryColor = "#818cf8",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // カードの登場アニメーション（スプリングで滑らかにポップ）
  const cardScale = spring({
    frame,
    fps,
    config: {
      damping: 15,
      stiffness: 90,
      mass: 0.8,
    },
  });

  const cardOpacity = spring({
    frame,
    fps,
    config: {
      damping: 20,
    },
  });

  return (
    <div
      style={{
        width: "90%",
        maxWidth: 900,
        backgroundColor: "rgba(15, 23, 42, 0.65)",
        backdropFilter: "blur(24px)",
        WebkitBackdropFilter: "blur(24px)",
        borderRadius: 24,
        padding: "36px 40px",
        boxSizing: "border-box",
        border: "1px solid rgba(255, 255, 255, 0.12)",
        boxShadow: `
          0 20px 50px rgba(0, 0, 0, 0.5),
          0 0 30px rgba(56, 189, 248, 0.08),
          inset 0 1px 1px rgba(255, 255, 255, 0.2)
        `,
        transform: `scale(${cardScale})`,
        opacity: cardOpacity,
        display: "flex",
        flexDirection: "column",
        gap: 24,
        zIndex: 10,
      }}
    >
      {/* ヘッダー: 話者情報 & チップタグ */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          paddingBottom: 20,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          {/* 話者アバターアイコン */}
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: "50%",
              background: `linear-gradient(135deg, ${primaryColor} 0%, ${secondaryColor} 100%)`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: `0 0 16px ${primaryColor}66`,
            }}
          >
            {/* 音声波形SVGアイコン */}
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 3v18M8 8v8M4 11v2M16 8v8M20 11v2"
                stroke="#ffffff"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </svg>
          </div>

          <div>
            <div
              style={{
                color: "#ffffff",
                fontSize: 24,
                fontWeight: 700,
                letterSpacing: "-0.02em",
                fontFamily: "'Segoe UI', 'Hiragino Sans', 'Meiryo', sans-serif",
              }}
            >
              {speaker}
            </div>
            <div
              style={{
                color: "rgba(203, 213, 225, 0.75)",
                fontSize: 14,
                fontWeight: 500,
                marginTop: 2,
                fontFamily: "'Segoe UI', 'Hiragino Sans', sans-serif",
              }}
            >
              {speakerRole}
            </div>
          </div>
        </div>

        {/* チップタグ */}
        <div
          style={{
            background: "rgba(30, 41, 59, 0.8)",
            border: `1px solid ${primaryColor}66`,
            borderRadius: 20,
            padding: "6px 16px",
            color: primaryColor,
            fontSize: 13,
            fontWeight: 700,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            boxShadow: `0 0 12px ${primaryColor}22`,
          }}
        >
          {tag}
        </div>
      </div>

      {/* セリフ本文 */}
      <div
        style={{
          position: "relative",
          padding: "8px 12px",
        }}
      >
        {/* 開始クォート装飾 */}
        <span
          style={{
            position: "absolute",
            top: -24,
            left: -8,
            fontSize: 60,
            color: `${primaryColor}33`,
            fontFamily: "serif",
            userSelect: "none",
          }}
        >
          “
        </span>

        <p
          style={{
            margin: 0,
            color: "#f8fafc",
            fontSize: 28,
            lineHeight: 1.6,
            fontWeight: 600,
            letterSpacing: "0.02em",
            fontFamily: "'Meiryo', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', sans-serif",
            textShadow: "0 2px 10px rgba(0, 0, 0, 0.4)",
          }}
        >
          {speechText}
        </p>
      </div>
    </div>
  );
};

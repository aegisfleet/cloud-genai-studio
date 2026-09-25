import React from "react";
import { Audio, staticFile } from "remotion";
import { Background } from "./Background";
import { SpeechCard } from "./SpeechCard";
import { WaveformVisualizer } from "./WaveformVisualizer";
import { ProgressBar } from "./ProgressBar";
import { AudiogramProps } from "../types";

export const AudiogramComposition: React.FC<AudiogramProps> = ({
  audioSrc,
  title,
  speaker,
  speakerRole,
  speechText,
  tag,
  primaryColor = "#38bdf8",
  secondaryColor = "#818cf8",
}) => {
  // audioSrc が http や staticFile 形式か、そのまま渡されたものかをハンドリング
  const resolvedAudioSrc = audioSrc.startsWith("http") || audioSrc.startsWith("data:")
    ? audioSrc
    : staticFile(audioSrc);

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "60px 48px 48px 48px",
        boxSizing: "border-box",
        fontFamily: "'Segoe UI', 'Hiragino Sans', 'Noto Sans JP', sans-serif",
      }}
    >
      {/* リッチなアンビエント背景 */}
      <Background primaryColor={primaryColor} secondaryColor={secondaryColor} />

      {/* 音声再生コンポーネント */}
      {audioSrc && <Audio src={resolvedAudioSrc} />}

      {/* ヘッダーブランドバー */}
      <div
        style={{
          zIndex: 10,
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "8px 24px",
          borderRadius: 999,
          backgroundColor: "rgba(15, 23, 42, 0.4)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          backdropFilter: "blur(12px)",
        }}
      >
        <div
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            backgroundColor: primaryColor,
            boxShadow: `0 0 10px ${primaryColor}`,
          }}
        />
        <span
          style={{
            color: "rgba(255, 255, 255, 0.9)",
            fontSize: 16,
            fontWeight: 700,
            letterSpacing: "0.06em",
          }}
        >
          {title}
        </span>
      </div>

      {/* メイン: セリフカード */}
      <div
        style={{
          zIndex: 10,
          width: "100%",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          flex: 1,
          margin: "24px 0",
        }}
      >
        <SpeechCard
          speaker={speaker}
          speakerRole={speakerRole}
          speechText={speechText}
          tag={tag}
          primaryColor={primaryColor}
          secondaryColor={secondaryColor}
        />
      </div>

      {/* 下部: 波形ビジュアライザー & プログレスバー */}
      <div
        style={{
          zIndex: 10,
          width: "100%",
          maxWidth: 900,
          display: "flex",
          flexDirection: "column",
          gap: 20,
          padding: "24px 28px",
          backgroundColor: "rgba(15, 23, 42, 0.5)",
          borderRadius: 20,
          border: "1px solid rgba(255, 255, 255, 0.08)",
          backdropFilter: "blur(16px)",
        }}
      >
        <WaveformVisualizer
          audioSrc={resolvedAudioSrc}
          primaryColor={primaryColor}
          secondaryColor={secondaryColor}
          numberOfBars={64}
          height={100}
        />
        <ProgressBar primaryColor={primaryColor} />
      </div>
    </div>
  );
};

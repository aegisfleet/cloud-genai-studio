import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { useAudioData, visualizeAudio } from "@remotion/media-utils";

interface WaveformVisualizerProps {
  audioSrc: string;
  numberOfBars?: 32 | 64 | 128;
  primaryColor?: string;
  secondaryColor?: string;
  height?: number;
}

export const WaveformVisualizer: React.FC<WaveformVisualizerProps> = ({
  audioSrc,
  numberOfBars = 64,
  primaryColor = "#38bdf8",
  secondaryColor = "#818cf8",
  height = 120,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const audioData = useAudioData(audioSrc);

  let frequencies: number[] = [];

  if (audioData) {
    frequencies = visualizeAudio({
      fps,
      frame,
      audioData,
      numberOfSamples: numberOfBars,
      smoothing: true,
    });
  } else {
    // 音声データ未ロード時、または無音時の微細なアンビエント揺らぎ
    frequencies = Array.from({ length: numberOfBars }, (_, i) => {
      return (Math.sin(frame * 0.12 + i * 0.25) * 0.5 + 0.5) * 0.05;
    });
  }

  // 左右対称（シンメトリック）マッピング:
  // 中央に声のエネルギーが集まる帯域（低中音）を配置し、外側に向けて高音を広げる
  const half = Math.floor(numberOfBars / 2);
  const mirroredFrequencies: number[] = new Array(numberOfBars).fill(0);

  for (let i = 0; i < half; i++) {
    // i: 0(外側・左端) -> half-1(中央)
    const ratioToCenter = i / (half - 1); // 0 (外側) -> 1 (中央)
    // 中央ほどエネルギーの大きい低周波(インデックス0付近)、外側ほど高周波
    const freqIdx = Math.min(
      frequencies.length - 1,
      Math.floor((1 - ratioToCenter) * 22)
    );
    const rawVal = frequencies[freqIdx] || 0;

    // 中央部によりリッチなふくらみを持たせる
    const centerBoost = 0.4 + ratioToCenter * 0.6;
    const finalVal = rawVal * centerBoost;

    mirroredFrequencies[i] = finalVal; // 左側
    mirroredFrequencies[numberOfBars - 1 - i] = finalVal; // 右側（完全対称）
  }

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 5,
        width: "100%",
        height,
        padding: "0 10px",
        boxSizing: "border-box",
      }}
    >
      {mirroredFrequencies.map((val, idx) => {
        // 人間の聴覚特性（対数・平方根近似）に合わせた非線形スケーリング
        const scaledVal = Math.pow(Math.max(0, val), 0.5) * 190;
        const barHeight = Math.max(6, Math.min(100, scaledVal));

        const isSpeaking = barHeight > 18;

        return (
          <div
            key={idx}
            style={{
              flex: 1,
              maxWidth: 8,
              height: `${barHeight}%`,
              background: `linear-gradient(to top, ${primaryColor} 0%, ${secondaryColor} 100%)`,
              borderRadius: 6,
              boxShadow: isSpeaking
                ? `0 0 12px ${primaryColor}aa, 0 0 20px ${secondaryColor}66`
                : "none",
              transition: "height 0.05s ease-out",
              position: "relative",
            }}
          >
            {/* ピーク時のハイライトドット */}
            {barHeight > 35 && (
              <div
                style={{
                  position: "absolute",
                  top: -2,
                  left: "50%",
                  transform: "translateX(-50%)",
                  width: 3.5,
                  height: 3.5,
                  borderRadius: "50%",
                  backgroundColor: "#ffffff",
                  boxShadow: `0 0 6px #ffffff, 0 0 10px ${primaryColor}`,
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
};

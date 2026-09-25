export type AudiogramProps = {
  audioSrc: string;
  title: string;
  speaker: string;
  speakerRole: string;
  speechText: string;
  tag: string;
  durationInSeconds: number;
  primaryColor?: string;
  secondaryColor?: string;
  accentGlow?: string;
  [key: string]: unknown;
};

export const defaultAudiogramProps: AudiogramProps = {
  audioSrc: "",
  title: "Qwen3-TTS 日本語音声合成",
  speaker: "Ono Anna (小野 アンナ)",
  speakerRole: "AI音声キャラクター / 日本語ネイティブ話者",
  speechText: "初めまして。Qwen3-TTSの日本語音声モデル検証へようこそ。Google CloudのL4インスタンスで快適に動作しています。",
  tag: "QWEN3-TTS 1.7B",
  durationInSeconds: 10,
  primaryColor: "#38bdf8", // Sky blue
  secondaryColor: "#818cf8", // Indigo
  accentGlow: "rgba(56, 189, 248, 0.5)",
};

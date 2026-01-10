"use client";

import React, { useRef, useState } from "react";
import { Mic, Square } from "lucide-react";
import { useTranslations, useLocale } from 'next-intl';

type Props = {
  onTranscribed: (text: string, language?: string) => void;
  onError?: (err: string) => void;
  onProcessingChange?: (isProcessing: boolean) => void;
};

export default function VoiceRecorder({ onTranscribed, onError, onProcessingChange }: Props) {
  const [recording, setRecording] = useState(false);
  const t = useTranslations('Chat');
  const locale = useLocale(); // Get current locale
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      mediaRef.current = mr;
      chunksRef.current = [];

      mr.ondataavailable = (e: BlobEvent) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };

      mr.onstop = async () => {
        onProcessingChange?.(true); // Start processing indicator
        try {
          const blob = new Blob(chunksRef.current, { type: mediaRef.current?.mimeType || "audio/webm" });
          const fd = new FormData();
          fd.append("file", blob, "voice.webm");
          fd.append("locale", locale); // Send user's language preference

          const token = localStorage.getItem("token");

          const res = await fetch("/api/transcribe", {
            method: "POST",
            headers: {
              'Authorization': `Bearer ${token}`
            },
            body: fd,
          });

          if (!res.ok) {
            if (res.status === 401) {
              window.location.href = "/login";
              return;
            }
            const txt = await res.text();
            onError?.(`Upload error: ${res.status} ${txt}`);
            onProcessingChange?.(false);
            return;
          }

          const json = await res.json();
          onTranscribed(json.text, json.language);

          // 🔊 Auto-play TTS if available
          if (json.audio_url) {
            const audio = new Audio(json.audio_url);
            audio.play().catch((err) =>
              console.error("Audio playback failed:", err)
            );
          }
        } catch (err: unknown) {
          if (err instanceof Error) {
            onError?.(err.message || "Upload failed");
          } else {
            onError?.("Upload failed");
          }
        } finally {
          onProcessingChange?.(false); // End processing indicator
        }
      };

      mr.start();
      setRecording(true);
    } catch (err: unknown) {
      if (err instanceof Error) {
        onError?.(err.message || "Microphone not accessible");
      } else {
        onError?.("Microphone not accessible");
      }
    }
  }

  function stopRecording() {
    if (mediaRef.current && mediaRef.current.state !== "inactive") {
      mediaRef.current.stop();
      mediaRef.current.stream.getTracks().forEach((t) => t.stop());
    }
    setRecording(false);
  }

  return (
    <button
      onClick={() => (recording ? stopRecording() : startRecording())}
      className={`p-3.5 transition-all duration-300 flex items-center justify-center group ${recording
        ? "bg-red-500 text-white animate-pulse"
        : "bg-white text-[#3A5A40] hover:bg-[#3A5A40] hover:text-white"
        }`}
      style={{
        borderRadius: recording 
          ? '50%' 
          : '255px 15px 225px 15px/15px 225px 15px 255px',
        border: recording 
          ? '3px solid #ef4444' 
          : '3px solid #3A5A40',
        boxShadow: recording 
          ? '0 0 0 4px rgba(239, 68, 68, 0.2)' 
          : '5px 5px 0px rgba(0, 0, 0, 0.2)',
        transform: recording ? 'scale(1)' : 'scale(1)',
      }}
      onMouseEnter={(e) => {
        if (!recording) {
          e.currentTarget.style.transform = 'translate(-2px, -2px)';
          e.currentTarget.style.boxShadow = '7px 7px 0px rgba(0, 0, 0, 0.2)';
        }
      }}
      onMouseLeave={(e) => {
        if (!recording) {
          e.currentTarget.style.transform = 'translate(0, 0)';
          e.currentTarget.style.boxShadow = '5px 5px 0px rgba(0, 0, 0, 0.2)';
        }
      }}
      title={recording ? t('stopRecording') : t('speakQuery')}
    >
      {recording ? (
        <Square className="w-5 h-5 fill-current" />
      ) : (
        <Mic className="w-6 h-6" />
      )}
    </button>
  );
}
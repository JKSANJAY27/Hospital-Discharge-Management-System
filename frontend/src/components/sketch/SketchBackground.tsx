'use client';
import React from 'react';

export default function SketchBackground() {
  return (
    <>
      {/* Comic dots background */}
      <div className="fixed inset-0 comic-dots pointer-events-none" />
      
      {/* Hand-drawn doodles floating around */}
      <svg className="fixed inset-0 w-full h-full pointer-events-none" style={{ zIndex: 1 }}>
        {/* Floating medical cross doodle */}
        <g className="float-sketch" style={{ transformOrigin: '15% 20%' }}>
          <path
            d="M 100 80 L 100 50 L 80 50 L 80 30 L 120 30 L 120 50 L 100 50 M 100 80 L 80 80 L 80 60 L 60 60 L 60 100 L 80 100 L 80 80 M 100 80 L 120 80 L 120 60 L 140 60 L 140 100 L 120 100 L 120 80"
            fill="none"
            stroke="#3A5A40"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity="0.3"
            style={{
              strokeDasharray: '1000',
              strokeDashoffset: '0',
              filter: 'url(#pencil-texture)'
            }}
          />
        </g>

        {/* Floating heart doodle */}
        <g className="doodle-heart" style={{ transformOrigin: '85% 25%' }}>
          <path
            d="M 1400 150 C 1400 130, 1385 120, 1370 120 C 1355 120, 1345 130, 1340 145 C 1335 130, 1325 120, 1310 120 C 1295 120, 1280 130, 1280 150 C 1280 175, 1340 220, 1340 220 C 1340 220, 1400 175, 1400 150 Z"
            fill="none"
            stroke="#A3B18A"
            strokeWidth="3"
            strokeLinecap="round"
            opacity="0.25"
          />
        </g>

        {/* Pill/capsule doodle */}
        <g className="wiggle-sketch" style={{ transformOrigin: '80% 70%' }}>
          <ellipse
            cx="1350"
            cy="550"
            rx="25"
            ry="50"
            fill="none"
            stroke="#588157"
            strokeWidth="3"
            strokeLinecap="round"
            opacity="0.2"
            transform="rotate(-25 1350 550)"
          />
          <line
            x1="1330"
            y1="530"
            x2="1370"
            y2="570"
            stroke="#588157"
            strokeWidth="2"
            opacity="0.2"
          />
        </g>

        {/* Stethoscope doodle */}
        <g className="float-sketch" style={{ transformOrigin: '10% 75%' }}>
          <path
            d="M 120 600 Q 150 620, 180 600 Q 190 590, 200 580"
            fill="none"
            stroke="#3A5A40"
            strokeWidth="3"
            strokeLinecap="round"
            opacity="0.15"
          />
          <circle
            cx="200"
            cy="580"
            r="15"
            fill="none"
            stroke="#3A5A40"
            strokeWidth="3"
            opacity="0.15"
          />
        </g>

        {/* Star sparkles */}
        {[...Array(6)].map((_, i) => (
          <g
            key={i}
            className="doodle-star"
            style={{
              transformOrigin: `${20 + i * 15}% ${15 + i * 12}%`,
              animationDelay: `${i * 0.3}s`
            }}
          >
            <path
              d={`M ${200 + i * 250} ${100 + i * 80} l 5 15 l 15 5 l -15 5 l -5 15 l -5 -15 l -15 -5 l 15 -5 Z`}
              fill="#A3B18A"
              opacity="0.2"
            />
          </g>
        ))}

        {/* Pencil texture filter for hand-drawn effect */}
        <defs>
          <filter id="pencil-texture">
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.8"
              numOctaves="4"
              result="noise"
            />
            <feDisplacementMap
              in="SourceGraphic"
              in2="noise"
              scale="2"
              xChannelSelector="R"
              yChannelSelector="G"
            />
          </filter>
          
          {/* Rough sketch filter */}
          <filter id="rough">
            <feTurbulence baseFrequency="0.05" numOctaves="2" result="turbulence" />
            <feDisplacementMap in="SourceGraphic" in2="turbulence" scale="3" />
          </filter>
        </defs>
      </svg>

      {/* Comic book "POW" style elements */}
      <div className="fixed top-20 right-10 pointer-events-none opacity-10 rotate-12">
        <div className="text-6xl font-black text-[#3A5A40] sketch-shadow">
          <span style={{
            fontFamily: 'Impact, sans-serif',
            WebkitTextStroke: '2px #3A5A40',
            WebkitTextFillColor: 'transparent',
            letterSpacing: '3px'
          }}>
            HEALTH
          </span>
        </div>
      </div>
    </>
  );
}

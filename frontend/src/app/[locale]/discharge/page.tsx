"use client";

import { useState, useRef } from 'react';
import { Upload, FileText, AlertTriangle, Calendar, Volume2, CheckCircle2, Copy, Download, ShieldCheck, Activity, Camera, Image as ImageIcon, X } from 'lucide-react';
import MetricCard from '@/components/discharge/MetricCard';
import ActionTimeline from '@/components/discharge/ActionTimeline';
import SketchBackground from '@/components/sketch/SketchBackground';
import '@/styles/sketch.css';

export default function DischargePage() {
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [speaking, setSpeaking] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [uploadMode, setUploadMode] = useState<'file' | 'image' | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [showCamera, setShowCamera] = useState(false);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // File Upload Handler (PDF/DOCX)
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setText("");
      setUploadMode('file');
      setImagePreview(null);
    }
  };

  // Image Upload Handler (JPG/PNG)
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setText("");
      setUploadMode('image');
      
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(selectedFile);
    }
  };

  // Trigger camera capture
  const handleCameraClick = async () => {
    try {
      // For desktop: open webcam interface
      setShowCamera(true);
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } 
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (error) {
      console.error('Camera access error:', error);
      // Fallback to file input
      if (cameraInputRef.current) {
        cameraInputRef.current.click();
      }
    }
  };

  // Capture photo from webcam
  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      if (context) {
        context.drawImage(video, 0, 0);
        canvas.toBlob((blob) => {
          if (blob) {
            const file = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' });
            setFile(file);
            setUploadMode('image');
            setImagePreview(canvas.toDataURL('image/jpeg'));
            closeCamera();
          }
        }, 'image/jpeg', 0.95);
      }
    }
  };

  // Close camera
  const closeCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setShowCamera(false);
  };

  // Trigger image upload
  const handleImageUploadClick = () => {
    if (imageInputRef.current) {
      imageInputRef.current.click();
    }
  };

  // Submit Handler
  const handleSubmit = async () => {
    if (!file && !text) {
      setError("Please provide a file, image, or text.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    
    // If image mode, use the new image extraction endpoint
    if (uploadMode === 'image' && file) {
      try {
        formData.append("file", file);
        
        const token = localStorage.getItem('token');
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/extract/prescription`, {
          method: "POST",
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData,
        });

        if (!response.ok) {
          throw new Error("Failed to extract prescription from image.");
        }

        const data = await response.json();
        
        // Format the extracted prescription data to match discharge format
        const formattedResult = {
          simplified_summary: `Prescription extracted successfully!\n\n**Patient:** ${data.data.patient || 'N/A'}\n**Doctor:** ${data.data.doctor || 'N/A'}\n**Date:** ${data.data.date || 'N/A'}\n\n**Medications:**\n${data.data.medicines?.map((med: any) => 
            `- ${med.name}: ${med.dosage} (${med.frequency}) - ${med.duration}`
          ).join('\n') || 'No medications found'}\n\n**Notes:** ${data.data.notes || 'None'}`,
          action_plan: data.data.medicines?.map((med: any, idx: number) => ({
            day: `Medicine ${idx + 1}`,
            tasks: [`Take ${med.name} - ${med.dosage}`, `Timing: ${med.timing?.instruction || 'As prescribed'}`],
            medications: [med.name]
          })) || [],
          danger_signs: ["Consult doctor if symptoms worsen", "Follow prescription exactly as shown"],
          medication_list: data.data.medicines?.map((med: any) => 
            `${med.name} - ${med.dosage} - ${med.frequency} (${med.duration})`
          ) || [],
          extracted_data: data.data
        };
        
        setResult(formattedResult);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
      return;
    }

    // Original PDF/text processing
    if (file) {
      formData.append("file", file);
    } else {
      formData.append("text", text);
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch("/api/discharge/simplify", {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to process discharge instructions.");
      }

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Text-to-Speech Handler
  const handleReadAloud = async () => {
    if (!result || !result.simplified_summary) return;

    if (speaking && audioUrl) {
      const audio = document.getElementById('tts-audio') as HTMLAudioElement;
      if (audio) {
        audio.pause();
        setSpeaking(false);
      }
      return;
    }

    setSpeaking(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch("/api/tts", {
        method: "POST",
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          text: result.simplified_summary,
          language_code: "en-IN" // Default to Indian English context
        }),
      });

      if (!response.ok) throw new Error("TTS failed");

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);

      const audio = new Audio(url);
      audio.id = 'tts-audio';
      audio.onended = () => setSpeaking(false);
      audio.play();
    } catch (err) {
      console.error("TTS Error:", err);
      setSpeaking(false);
    }
  };

  // Download ICS
  const handleDownloadCalendar = () => {
    if (!result?.ics_content) return;

    const blob = new Blob([result.ics_content], { type: 'text/calendar' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'recovery_schedule.ics';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="min-h-screen bg-[#FDFCF8] font-sans text-stone-800 pb-20 relative">
      <SketchBackground />

      {/* Camera Modal */}
      {showCamera && (
        <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-4 max-w-2xl w-full">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-purple-900">Take Photo</h3>
              <button
                onClick={closeCamera}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            <div className="relative bg-black rounded-lg overflow-hidden mb-4">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                className="w-full h-auto"
              />
            </div>
            <div className="flex gap-4">
              <button
                onClick={capturePhoto}
                className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <Camera className="h-5 w-5" />
                Capture Photo
              </button>
              <button
                onClick={closeCamera}
                className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hidden canvas for photo capture */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Hero Header */}
      <div className="bg-[#3A5A40] border-b-4 border-stone-800 py-12 px-4 relative overflow-hidden">
        <div className="absolute inset-0 comic-dots opacity-20"></div>
        <div className="max-w-4xl mx-auto text-center space-y-4 relative z-10">
          <h1 
            className="text-4xl md:text-5xl font-bold text-white tracking-tight"
            style={{
              fontFamily: '"Comic Sans MS", "Chalkboard SE", "Comic Neue", cursive',
              textShadow: '4px 4px 0px rgba(0, 0, 0, 0.3)'
            }}
          >
            Simplify Your Hospital Discharge
          </h1>
          <p className="text-lg md:text-xl text-emerald-100 max-w-2xl mx-auto leading-relaxed font-medium">
            Understand your care plan instantly. We translate complex medical jargon into clear, actionable steps for a safer recovery.
          </p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 -mt-8 relative z-10">
        {/* Input Section */}
        <div 
          className="bg-white p-6 md:p-8"
          style={{
            borderRadius: '255px 25px 225px 25px/25px 225px 25px 255px',
            border: '4px solid #3A5A40',
            boxShadow: '8px 8px 0px rgba(58, 90, 64, 0.2), -2px -2px 0px rgba(163, 177, 138, 0.3)'
          }}
        >
          <div className="space-y-6">

            {/* Upload Options */}
            <div className="grid md:grid-cols-3 gap-4">
              
              {/* PDF/Document Upload */}
              <label className={`
                border-4 border-dashed p-6 text-center transition-all cursor-pointer block group
                ${file && uploadMode === 'file' ? 'border-[#3A5A40] bg-[#A3B18A]/10' : 'border-stone-300 hover:border-[#3A5A40] hover:bg-stone-50'}
              `}
              style={{
                borderRadius: '225px 15px 225px 15px/15px 255px 15px 225px'
              }}
              >
                <input 
                  ref={fileInputRef}
                  type="file" 
                  accept=".pdf,.txt,.docx" 
                  onChange={handleFileUpload} 
                  className="hidden" 
                />
                <div className="flex flex-col items-center gap-3">
                  <div 
                    className={`p-3 ${file && uploadMode === 'file' ? 'bg-[#3A5A40] text-white' : 'bg-stone-100 text-stone-400 group-hover:text-[#3A5A40] transition-colors'}`}
                    style={{
                      borderRadius: '255px 15px 225px 15px/15px 225px 15px 255px',
                      border: '3px solid currentColor'
                    }}
                  >
                    <FileText className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-sm font-black text-stone-700">
                      {file && uploadMode === 'file' ? file.name : "Upload PDF"}
                    </p>
                    {(!file || uploadMode !== 'file') && <p className="text-xs text-stone-500 mt-1">Document</p>}
                  </div>
                </div>
              </label>

              {/* Camera Capture */}
              <button
                type="button"
                onClick={handleCameraClick}
                className={`
                  border-4 border-dashed p-6 text-center transition-all group
                  ${file && uploadMode === 'image' ? 'border-[#3A5A40] bg-[#A3B18A]/10' : 'border-stone-300 hover:border-[#3A5A40] hover:bg-stone-50'}
                `}
                style={{
                  borderRadius: '15px 225px 15px 225px/225px 15px 255px 15px'
                }}
              >
                <input 
                  ref={cameraInputRef}
                  type="file" 
                  accept="image/*" 
                  capture="environment"
                  onChange={handleImageUpload} 
                  className="hidden" 
                />
                <div className="flex flex-col items-center gap-3">
                  <div 
                    className={`p-3 ${file && uploadMode === 'image' ? 'bg-[#3A5A40] text-white' : 'bg-stone-100 text-stone-400 group-hover:text-[#3A5A40] transition-colors'}`}
                    style={{
                      borderRadius: '15px 225px 15px 225px/225px 15px 255px 15px',
                      border: '3px solid currentColor'
                    }}
                  >
                    <Camera className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-sm font-black text-stone-700">
                      Take Photo
                    </p>
                    <p className="text-xs text-stone-500 mt-1">Camera</p>
                  </div>
                </div>
              </button>

              {/* Image Upload */}
              <button
                type="button"
                onClick={handleImageUploadClick}
                className={`
                  border-4 border-dashed p-6 text-center transition-all group
                  ${file && uploadMode === 'image' ? 'border-[#3A5A40] bg-[#A3B18A]/10' : 'border-stone-300 hover:border-[#3A5A40] hover:bg-stone-50'}
                `}
                style={{
                  borderRadius: '225px 15px 225px 15px/15px 255px 15px 225px'
                }}
              >
                <input 
                  ref={imageInputRef}
                  type="file" 
                  accept="image/jpeg,image/jpg,image/png" 
                  onChange={handleImageUpload} 
                  className="hidden" 
                />
                <div className="flex flex-col items-center gap-3">
                  <div 
                    className={`p-3 ${file && uploadMode === 'image' ? 'bg-[#3A5A40] text-white' : 'bg-stone-100 text-stone-400 group-hover:text-[#3A5A40] transition-colors'}`}
                    style={{
                      borderRadius: '225px 15px 225px 15px/15px 255px 15px 225px',
                      border: '3px solid currentColor'
                    }}
                  >
                    <ImageIcon className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-sm font-black text-stone-700">
                      Upload Image
                    </p>
                    <p className="text-xs text-stone-500 mt-1">JPG, PNG</p>
                  </div>
                </div>
              </button>
            </div>

            {/* Image Preview */}
            {imagePreview && uploadMode === 'image' && (
              <div 
                className="relative p-4 bg-stone-50"
                style={{
                  borderRadius: '15px 225px 15px 225px/225px 15px 255px 15px',
                  border: '3px solid #A3B18A'
                }}
              >
                <img 
                  src={imagePreview} 
                  alt="Preview" 
                  className="w-full h-auto max-h-64 object-contain rounded-lg"
                />
                <button
                  onClick={() => {
                    setFile(null);
                    setImagePreview(null);
                    setUploadMode(null);
                  }}
                  className="absolute top-2 right-2 bg-red-500 text-white p-2 rounded-full hover:bg-red-600 transition-colors"
                  style={{
                    border: '2px solid white',
                    boxShadow: '2px 2px 0px rgba(0,0,0,0.2)'
                  }}
                >
                  ✕
                </button>
              </div>
            )}

            {/* Manual Text Option */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center" aria-hidden="true">
                <svg className="w-full h-1" style={{ overflow: 'visible' }}>
                  <path
                    d="M 0 0 Q 100 -2, 200 0 T 400 0 T 600 0 T 800 0"
                    fill="none"
                    stroke="#d6d3d1"
                    strokeWidth="2"
                    strokeLinecap="round"
                    style={{ strokeDasharray: '8,5' }}
                  />
                </svg>
              </div>
              <div className="relative flex justify-center">
                <span 
                  className="bg-white px-3 text-sm text-stone-700 font-black uppercase tracking-widest"
                  style={{
                    border: '2px solid #d6d3d1',
                    borderRadius: '15px 5px 15px 5px/5px 15px 5px 15px',
                    padding: '6px 16px'
                  }}
                >Or paste text</span>
              </div>
            </div>

            <textarea
              className="w-full p-4 outline-none transition-all placeholder:text-stone-400 text-base font-medium"
              style={{
                border: '3px solid #d6d3d1',
                borderRadius: '15px 225px 15px 225px/225px 15px 255px 15px',
                boxShadow: 'inset 2px 2px 4px rgba(0,0,0,0.05)'
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#3A5A40';
                e.target.style.boxShadow = '0 0 0 3px rgba(58, 90, 64, 0.1), inset 2px 2px 4px rgba(0,0,0,0.05)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#d6d3d1';
                e.target.style.boxShadow = 'inset 2px 2px 4px rgba(0,0,0,0.05)';
              }}
              rows={3}
              placeholder="Paste the text from your discharge papers here..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={!!file}
            ></textarea>

            {/* Action Button */}
            <button
              onClick={handleSubmit}
              disabled={loading || (!file && !text)}
              className={`
                w-full py-4 font-black text-lg transition-all flex items-center justify-center gap-3 uppercase tracking-wide
                ${loading || (!file && !text)
                  ? 'bg-stone-200 text-stone-400 cursor-not-allowed'
                  : 'bg-[#3A5A40] text-white hover:bg-[#2F4A33]'}
              `}
              style={{
                borderRadius: '15px 225px 15px 225px/225px 15px 255px 15px',
                border: '3px solid rgba(0,0,0,0.1)',
                boxShadow: loading || (!file && !text) ? 'none' : '5px 5px 0px rgba(0, 0, 0, 0.2)'
              }}
              onMouseEnter={(e) => {
                if (!loading && (file || text)) {
                  e.currentTarget.style.transform = 'translate(-2px, -2px)';
                  e.currentTarget.style.boxShadow = '7px 7px 0px rgba(0, 0, 0, 0.2)';
                }
              }}
              onMouseLeave={(e) => {
                if (!loading && (file || text)) {
                  e.currentTarget.style.transform = 'translate(0, 0)';
                  e.currentTarget.style.boxShadow = '5px 5px 0px rgba(0, 0, 0, 0.2)';
                }
              }}
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white/30 border-t-white"></div>
                  Analyzing & Simplifying...
                </>
              ) : (
                <>
                  <FileText className="w-5 h-5" />
                  Generate My Recovery Plan
                </>
              )}
            </button>

            {error && (
              <div className="p-4 bg-red-50 text-red-700 rounded-xl flex items-center gap-3 border border-red-100 animate-in slide-in-from-top-2">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <p>{error}</p>
              </div>
            )}

            {/* Blockchain Badge */}
            <div className="flex justify-center items-center gap-2 text-xs text-stone-400 pt-2">
              <ShieldCheck className="w-3 h-3" />
              <span>Secured & Audited via Blockchain</span>
            </div>
          </div>
        </div>

        {/* Results Section */}
        {result && (
          <div className="mt-12 space-y-12 pb-20 animate-in fade-in slide-in-from-bottom-8 duration-700">

            {/* 1. Evaluation Cards */}
            {result.evaluation && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard
                  label="Readability"
                  value={result.evaluation.readability_score?.toFixed(1) || "N/A"}
                  subtext="Grade Level"
                  color="blue"
                  icon={<FileText className="w-4 h-4" />}
                />
                <MetricCard
                  label="Safety Check"
                  value={result.evaluation.safety_warnings_present ? "Pass" : "Review"}
                  subtext="Warnings Found"
                  color={result.evaluation.safety_warnings_present ? "green" : "amber"}
                  icon={<ShieldCheck className="w-4 h-4" />}
                />
                <MetricCard
                  label="Completeness"
                  value={Object.values(result.evaluation.completeness).filter(Boolean).length}
                  subtext="Checks Passed"
                  color="stone"
                  icon={<CheckCircle2 className="w-4 h-4" />}
                />
                <MetricCard
                  label="Blockchain"
                  value="Verified"
                  subtext="Audit Logged"
                  color="amber" // Gold for premium/blockchain
                  icon={<Activity className="w-4 h-4" />}
                />
              </div>
            )}

            {/* 2. Critical Alerts */}
            {result.danger_signs && result.danger_signs.length > 0 && (
              <div className="bg-red-50 border-l-4 border-red-500 p-6 md:p-8 rounded-r-xl shadow-sm">
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-white rounded-full text-red-500 shadow-sm shrink-0">
                    <AlertTriangle className="w-8 h-8" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-red-900 mb-2">Warning Signs</h3>
                    <p className="text-red-800 mb-4 font-medium">If you experience any of these symptoms, call your doctor or 911 immediately:</p>
                    <div className="grid md:grid-cols-2 gap-3">
                      {result.danger_signs.map((sign: string, i: number) => (
                        <div key={i} className="flex items-center gap-2 bg-white/60 p-2 rounded text-red-900 font-semibold border border-red-100">
                          <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                          {sign}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 3. Simplified Summary with Voice */}
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-stone-200">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-serif font-bold text-stone-900">Summary</h2>
                <button
                  onClick={handleReadAloud}
                  className={`flex items-center gap-2 px-4 py-2 rounded-full font-medium transition-all ${speaking ? 'bg-teal-100 text-teal-700 animate-pulse' : 'bg-stone-100 text-stone-600 hover:bg-teal-50 hover:text-teal-600'}`}
                >
                  <Volume2 className="w-4 h-4" />
                  {speaking ? "Listening..." : "Read Aloud"}
                </button>
              </div>
              <div className="prose prose-lg text-stone-700 leading-relaxed font-normal">
                {result.simplified_summary}
              </div>
            </div>

            {/* 4. Action Plan Timeline */}
            <div className="bg-[#fffefe] p-8 rounded-2xl shadow-sm border border-stone-200">
              <div className="flex flex-col md:flex-row justify-between md:items-center mb-8 gap-4">
                <div className="flex items-center gap-3">
                  <div className="p-2bg-teal-100 rounded-lg text-teal-700">
                    <Calendar className="w-8 h-8 text-teal-600" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-serif font-bold text-stone-900">Recovery Action Plan</h2>
                    <p className="text-stone-500">Your day-by-day guide to recovery</p>
                  </div>
                </div>

                {result.ics_content && (
                  <button
                    onClick={handleDownloadCalendar}
                    className="flex items-center gap-2 bg-stone-900 hover:bg-stone-800 text-white px-5 py-3 rounded-xl transition-all shadow-md active:scale-95"
                  >
                    <Download className="w-4 h-4" />
                    Add to Calendar
                  </button>
                )}
              </div>

              <ActionTimeline plan={result.action_plan || []} />
            </div>

            {/* 5. Additional Info Grid */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Lifestyle Changes */}
              {result.lifestyle_changes && (
                <div className="bg-emerald-50/50 p-6 rounded-2xl border border-emerald-100">
                  <h3 className="text-xl font-bold text-emerald-900 mb-4 flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    Healthy Habits
                  </h3>
                  <div className="text-emerald-800/90 leading-relaxed">
                    {Array.isArray(result.lifestyle_changes) ? (
                      <ul className="space-y-2">
                        {result.lifestyle_changes.map((item: string, i: number) => (
                          <li key={i} className="flex gap-2">
                            <span className="mt-2 w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    ) : <p>{result.lifestyle_changes}</p>}
                  </div>
                </div>
              )}

              {/* Restrictions */}
              {result.activity_restrictions && (
                <div className="bg-amber-50/50 p-6 rounded-2xl border border-amber-100">
                  <h3 className="text-xl font-bold text-amber-900 mb-4 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-600" />
                    Important Restrictions
                  </h3>
                  <div className="text-amber-800/90 leading-relaxed">
                    {Array.isArray(result.activity_restrictions) ? (
                      <ul className="space-y-2">
                        {result.activity_restrictions.map((item: string, i: number) => (
                          <li key={i} className="flex gap-2">
                            <span className="mt-2 w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    ) : <p>{result.activity_restrictions}</p>}
                  </div>
                </div>
              )}
            </div>

          </div>
        )}
      </div>
    </div>
  );
}

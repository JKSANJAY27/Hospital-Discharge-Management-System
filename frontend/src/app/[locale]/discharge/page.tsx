"use client";

import { useState } from 'react';
import { Upload, FileText, AlertTriangle, Calendar, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';
import { useTranslations } from 'next-intl';

export default function DischargePage() {
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setText(""); // Clear text if file selected
    }
  };

  const handleSubmit = async () => {
    if (!file && !text) {
      setError("Please provide a file or text.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
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

  return (
    <div className="min-h-screen bg-[#FDFCF8] p-4 md:p-8 font-sans text-stone-800">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-serif font-bold text-primary-dark">Discharge Simplifier</h1>
          <p className="text-stone-600">Upload your hospital discharge summary to get a simple, day-by-day action plan.</p>
        </div>

        {/* Input Section */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-stone-200">
            <div className="space-y-4">
                <div className="border-2 border-dashed border-stone-300 rounded-lg p-8 text-center hover:border-primary transition-colors cursor-pointer relative">
                    <input 
                        type="file" 
                        accept=".pdf" 
                        onChange={handleFileUpload} 
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    <Upload className="mx-auto h-12 w-12 text-stone-400 mb-2" />
                    <p className="font-medium text-stone-700">{file ? file.name : "Drop PDF here or click to upload"}</p>
                </div>
                
                <div className="relative flex items-center gap-2 my-4">
                    <div className="h-px bg-stone-200 flex-1"></div>
                    <span className="text-sm text-stone-400 font-medium">OR PASTE TEXT</span>
                    <div className="h-px bg-stone-200 flex-1"></div>
                </div>

                <textarea
                    className="w-full border border-stone-300 rounded-lg p-3 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                    rows={4}
                    placeholder="Paste discharge text here..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    disabled={!!file}
                ></textarea>

                <button 
                  onClick={handleSubmit} 
                  disabled={loading}
                  className="w-full bg-primary hover:bg-primary-dark text-white font-bold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      Simplifying...
                    </>
                  ) : (
                    <>
                      <FileText className="w-5 h-5" />
                      Generate Action Plan
                    </>
                  )}
                </button>

                {error && (
                    <div className="p-3 bg-red-50 text-red-700 rounded-lg flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5" />
                        {error}
                    </div>
                )}
            </div>
        </div>

        {/* Results Section */}
        {result && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            
            {/* Danger Signs Alert */}
            {result.danger_signs && result.danger_signs.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-6">
                    <h3 className="text-xl font-bold text-red-700 flex items-center gap-2 mb-4">
                        <AlertTriangle className="w-6 h-6" />
                        Ref Flags - Call Doctor Immediately
                    </h3>
                    <ul className="space-y-2">
                        {result.danger_signs.map((sign: string, i: number) => (
                            <li key={i} className="flex items-start gap-2 text-red-800 font-medium">
                                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-red-600 shrink-0"></span>
                                {sign}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Simplified Summary */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-stone-200">
                <h2 className="text-2xl font-serif font-bold text-stone-800 mb-4">Summary</h2>
                <div className="bg-blue-50 p-4 rounded-lg text-stone-800 leading-relaxed text-lg">
                    {result.simplified_summary}
                </div>
            </div>

            {/* Action Plan Timeline */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-stone-200">
                <h2 className="text-2xl font-serif font-bold text-stone-800 mb-6 flex items-center gap-2">
                    <Calendar className="w-6 h-6 text-primary" />
                    Action Plan
                </h2>
                
                <div className="space-y-8 relative before:absolute before:left-4 before:top-2 before:bottom-2 before:w-0.5 before:bg-stone-200">
                    {result.action_plan?.map((day: any, i: number) => (
                        <div key={i} className="relative pl-12">
                            <div className="absolute left-1.5 top-1.5 w-5 h-5 rounded-full border-4 border-white bg-primary shadow-sm"></div>
                            <h3 className="text-lg font-bold text-stone-800 mb-2">{day.day}</h3>
                            <div className="space-y-3">
                                {day.tasks.map((task: string, j: number) => (
                                    <div key={j} className="flex items-start gap-3 bg-stone-50 p-3 rounded-lg border border-stone-100">
                                        <div className="w-5 h-5 rounded border-2 border-stone-300 mt-0.5" />
                                        <span className="text-stone-700 font-medium">{task}</span>
                                    </div>
                                ))}
                                {day.medications && day.medications.length > 0 && (
                                    <div className="bg-blue-50/50 p-3 rounded-lg border border-blue-100 mt-2">
                                        <p className="text-xs font-bold text-blue-600 uppercase tracking-wide mb-1">Medications</p>
                                        <ul className="list-disc list-inside text-sm text-blue-900">
                                            {day.medications.map((med: string, k: number) => (
                                                <li key={k}>{med}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Follow Up */}
            {result.follow_up_schedule && result.follow_up_schedule.length > 0 && (
                <div className="bg-white p-6 rounded-xl shadow-sm border border-stone-200">
                     <h2 className="text-2xl font-serif font-bold text-stone-800 mb-4">Follow-Up Appointments</h2>
                     <div className="grid gap-4 md:grid-cols-2">
                        {result.follow_up_schedule.map((appt: any, i: number) => (
                            <div key={i} className="p-4 bg-amber-50 rounded-lg border border-amber-100">
                                <p className="font-bold text-amber-900 text-lg">{appt.specialist}</p>
                                <p className="text-amber-800 font-medium mt-1">{appt.when}</p>
                                <p className="text-amber-700 text-sm mt-2">{appt.purpose}</p>
                            </div>
                        ))}
                     </div>
                </div>
            )}
            
          </div>
        )}
      </div>
    </div>
  );
}

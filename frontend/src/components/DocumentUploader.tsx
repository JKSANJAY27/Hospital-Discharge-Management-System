"use client";

import { useState, useEffect, useRef } from 'react';
import { Upload, FileText, X, CheckCircle, AlertCircle, Camera, Image as ImageIcon } from 'lucide-react';
import { getValidToken } from '../lib/firebase-client';

interface UploadedDocument {
  id: string;
  file_name: string;
  upload_date: string;
  num_pages?: number;
  analysis?: {
    document_type?: string;
    summary?: string;
    medications?: string[];
    diagnoses?: string[];
  };
}

interface DocumentUploaderProps {
  onExtractComplete?: (data: any) => void;
}

export default function DocumentUploader({ onExtractComplete }: DocumentUploaderProps) {
  const [uploading, setUploading] = useState(false);
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [extractedData, setExtractedData] = useState<any>(null);
  const [documentType, setDocumentType] = useState<'prescription' | 'discharge' | 'lab-report'>('prescription');
  const [recoveryPlan, setRecoveryPlan] = useState<any>(null);
  
  // Camera state
  const [showCamera, setShowCamera] = useState(false);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  // Load documents on mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  // Cleanup camera stream
  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [stream]);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const token = await getValidToken();
      if (!token) return;

      const response = await fetch('/api/documents', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents || []);
      }
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are supported');
      return;
    }

    // Check file size (Vercel serverless functions have a 4.5MB body limit)
    const maxSize = 4.5 * 1024 * 1024; // 4.5MB in bytes
    if (file.size > maxSize) {
      setError(`File too large. Maximum size is 4.5MB for serverless upload (${(file.size / 1024 / 1024).toFixed(2)}MB provided). Please compress your PDF or contact support for alternatives.`);
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      const token = await getValidToken();
      if (!token) {
        setError('Not authenticated. Please log in again.');
        setUploading(false);
        return;
      }

      console.log('Extracting from PDF:', file.name, 'Size:', (file.size / 1024).toFixed(2), 'KB', 'Type:', documentType);

      const formData = new FormData();
      formData.append('file', file);

      // Use extraction endpoint based on document type
      const endpoint = `/api/extract/${documentType}`;
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      console.log('Extraction response status:', response.status);

      if (response.ok) {
        const result = await response.json();
        console.log('Extraction result:', result);

        if (result.data) {
          setExtractedData(result.data);
          
          // Handle recovery plan for discharge summaries
          if (result.recovery_plan) {
            setRecoveryPlan(result.recovery_plan);
          }
          
          const docTypeLabel = documentType === 'prescription' ? 'Prescription' : 
                              documentType === 'discharge' ? 'Discharge Summary' : 'Lab Report';
          setSuccess(`✅ ${docTypeLabel} extracted successfully from PDF!`);
          
          // Pass data to parent (chat) for integration
          if (onExtractComplete) {
            onExtractComplete({
              ...result.data,
              recovery_plan: result.recovery_plan,
              document_type: documentType
            });
          }
        } else {
          setError('No data could be extracted from the PDF. Please ensure it contains medical information.');
        }
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('Extraction failed:', errorData);
        setError(errorData.detail || 'Extraction failed. Please try again.');
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError('Network error during upload');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm('Delete this document?')) return;

    try {
      const token = await getValidToken();
      const response = await fetch(`/api/documents/${docId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Document deleted');
        setError(null);
        await fetchDocuments();
      } else {
        setError(data.detail || 'Failed to delete document');
        console.error('Delete failed:', data);
      }
    } catch (err) {
      console.error('Delete error:', err);
      setError('Failed to delete document');
    }
  };

  // Camera functions
  const startCamera = async () => {
    try {
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
      setError('Could not access camera. Please check permissions.');
      setShowCamera(false);
    }
  };

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      if (context) {
        context.drawImage(video, 0, 0);
        const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
        setImagePreview(dataUrl);
        closeCamera();
      }
    }
  };

  const closeCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setShowCamera(false);
  };

  // Image upload handler
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    setSuccess(null);
    setExtractedData(null);

    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  // Extract data from image (prescription/discharge/lab report)
  const handleExtractFromImage = async () => {
    if (!imagePreview) return;

    setUploading(true);
    setError(null);
    setSuccess(null);
    setExtractedData(null);

    try {
      const token = await getValidToken();
      if (!token) {
        setError('Not authenticated. Please log in again.');
        setUploading(false);
        return;
      }

      // Convert data URL to blob
      const blob = await (await fetch(imagePreview)).blob();
      const formData = new FormData();
      formData.append('file', blob, 'capture.jpg');

      console.log('Sending extraction request...');
      const endpoint = `/api/extract/${documentType}`;
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      console.log('Extraction response status:', response.status);

      if (response.ok) {
        const result = await response.json();
        console.log('Extraction result:', result);
        
        // Check if extraction returned data
        if (result.data) {
          setExtractedData(result.data);
          
          // Handle recovery plan for discharge summaries
          if (result.recovery_plan) {
            setRecoveryPlan(result.recovery_plan);
          }
          
          const docTypeLabel = documentType === 'prescription' ? 'Prescription' : 
                              documentType === 'discharge' ? 'Discharge Summary' : 'Lab Report';
          setSuccess(`✅ ${docTypeLabel} extracted successfully!`);
          
          // Pass data to parent (chat) for integration
          if (onExtractComplete) {
            onExtractComplete({
              ...result.data,
              recovery_plan: result.recovery_plan,
              document_type: documentType
            });
          }
        } else {
          setError('No data could be extracted from the image. Please ensure the image is clear and contains medical information.');
        }
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('Extraction failed:', errorData);
        setError(errorData.detail || 'Extraction failed. Please try again.');
      }
    } catch (err: any) {
      console.error('Extraction error:', err);
      setError(`Network error: ${err.message || 'Please check your connection and try again.'}`);
    } finally {
      setUploading(false);
    }
  };

  const clearImagePreview = () => {
    setImagePreview(null);
    setExtractedData(null);
  };

  return (
    <div className="space-y-4">
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

      {/* Image Preview */}
      {imagePreview && (
        <div className="border-2 border-purple-300 rounded-lg p-4 bg-purple-50">
          <div className="flex justify-between items-start mb-3">
            <h3 className="font-semibold text-purple-900">Captured Image</h3>
            <button
              onClick={clearImagePreview}
              className="text-gray-500 hover:text-gray-700"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <img src={imagePreview} alt="Preview" className="w-full rounded-lg mb-3" />
          <button
            onClick={handleExtractFromImage}
            disabled={uploading}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50"
          >
            {uploading ? 'Extracting...' : 'Extract Medical Data'}
          </button>
        </div>
      )}

      {/* Extracted Data Display */}
      {extractedData && (
        <div className="border-2 border-green-300 rounded-lg p-4 bg-green-50">
          <h3 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
            <CheckCircle className="h-5 w-5" />
            Extracted Information
          </h3>
          <div className="space-y-2 text-sm">
            {extractedData.patient_name && (
              <div>
                <span className="font-semibold">Patient:</span> {extractedData.patient_name}
              </div>
            )}
            {extractedData.doctor_name && (
              <div>
                <span className="font-semibold">Doctor:</span> {extractedData.doctor_name}
              </div>
            )}
            {extractedData.date && (
              <div>
                <span className="font-semibold">Date:</span> {extractedData.date}
              </div>
            )}
            {extractedData.medications && extractedData.medications.length > 0 && (
              <div>
                <span className="font-semibold">Medications:</span>
                <ul className="ml-4 mt-1 list-disc">
                  {extractedData.medications.map((med: any, idx: number) => (
                    <li key={idx}>{med.name} - {med.dosage}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Recovery Action Plan Display */}
      {recoveryPlan && (
        <div className="border-2 border-blue-300 rounded-lg p-6 bg-gradient-to-br from-blue-50 to-purple-50">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold text-purple-900 flex items-center gap-2">
                📋 {recoveryPlan.title}
              </h2>
              <p className="text-sm text-stone-600 mt-1">{recoveryPlan.subtitle}</p>
            </div>
          </div>

          {/* Daily Plans */}
          <div className="space-y-4 mb-6">
            {recoveryPlan.daily_plans && recoveryPlan.daily_plans.map((day: any, idx: number) => (
              <div key={idx} className="bg-white rounded-lg p-4 shadow-sm border border-stone-200">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-full bg-purple-600 text-white flex items-center justify-center text-sm font-bold">
                    {idx + 1}
                  </div>
                  <h3 className="font-semibold text-lg text-purple-900">{day.day}</h3>
                </div>
                
                {/* Tasks */}
                <div className="space-y-2 mb-3">
                  {day.tasks && day.tasks.map((task: any, taskIdx: number) => (
                    <label key={taskIdx} className="flex items-start gap-2 cursor-pointer hover:bg-stone-50 p-2 rounded">
                      <input 
                        type="checkbox" 
                        defaultChecked={task.completed}
                        className="mt-1 h-4 w-4 text-purple-600 rounded border-stone-300"
                      />
                      <span className="text-sm text-stone-700">{task.task}</span>
                    </label>
                  ))}
                </div>

                {/* Medications to Take */}
                {day.medications_to_take && day.medications_to_take.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-stone-200">
                    <p className="text-xs font-semibold text-purple-700 mb-1">MEDICATIONS TO TAKE:</p>
                    <div className="flex flex-wrap gap-2">
                      {day.medications_to_take.map((med: string, medIdx: number) => (
                        <span key={medIdx} className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">
                          💊 {med}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Healthy Habits & Restrictions Grid */}
          <div className="grid md:grid-cols-2 gap-4 mb-4">
            {/* Healthy Habits */}
            {recoveryPlan.healthy_habits && recoveryPlan.healthy_habits.length > 0 && (
              <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                <h4 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
                  ✅ Healthy Habits
                </h4>
                <ul className="space-y-1 text-sm text-green-800">
                  {recoveryPlan.healthy_habits.map((habit: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span>•</span>
                      <span>{habit}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Important Restrictions */}
            {recoveryPlan.important_restrictions && recoveryPlan.important_restrictions.length > 0 && (
              <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                <h4 className="font-semibold text-orange-900 mb-2 flex items-center gap-2">
                  ⚠️ Important Restrictions
                </h4>
                <ul className="space-y-1 text-sm text-orange-800">
                  {recoveryPlan.important_restrictions.map((restriction: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span>•</span>
                      <span>{restriction}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Emergency Signs */}
          {recoveryPlan.emergency_signs && recoveryPlan.emergency_signs.length > 0 && (
            <div className="bg-red-50 rounded-lg p-4 border border-red-200">
              <h4 className="font-semibold text-red-900 mb-2 flex items-center gap-2">
                🚨 Seek Medical Help If You Experience:
              </h4>
              <ul className="space-y-1 text-sm text-red-800">
                {recoveryPlan.emergency_signs.map((sign: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span>•</span>
                    <span>{sign}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Upload Section */}
      <div className="border-2 border-dashed border-stone-300 rounded-lg p-6 text-center hover:border-primary transition-colors">
        {/* Document Type Selector */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-stone-700 mb-2">Document Type</label>
          <div className="flex gap-2 justify-center">
            <button
              onClick={() => setDocumentType('prescription')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                documentType === 'prescription' 
                  ? 'bg-purple-600 text-white' 
                  : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
              }`}
            >
              💊 Prescription
            </button>
            <button
              onClick={() => setDocumentType('discharge')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                documentType === 'discharge' 
                  ? 'bg-purple-600 text-white' 
                  : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
              }`}
            >
              🏥 Discharge Summary
            </button>
            <button
              onClick={() => setDocumentType('lab-report')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                documentType === 'lab-report' 
                  ? 'bg-purple-600 text-white' 
                  : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
              }`}
            >
              🔬 Lab Report
            </button>
          </div>
        </div>

        {/* Three Upload Options */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          {/* PDF Upload */}
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleUpload}
              disabled={uploading}
              className="hidden"
              id="document-upload"
            />
            <label 
              htmlFor="document-upload" 
              className="cursor-pointer block p-4 border-2 border-stone-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all"
            >
              <FileText className={`mx-auto h-8 w-8 mb-2 ${uploading ? 'text-primary animate-pulse' : 'text-stone-400'}`} />
              <p className="text-xs font-medium text-stone-600">Upload PDF</p>
            </label>
          </div>

          {/* Camera Capture */}
          <button
            onClick={startCamera}
            disabled={uploading}
            className="p-4 border-2 border-stone-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all disabled:opacity-50"
          >
            <Camera className="mx-auto h-8 w-8 mb-2 text-stone-400" />
            <p className="text-xs font-medium text-stone-600">Take Photo</p>
          </button>

          {/* Image Upload */}
          <div>
            <input
              ref={imageInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              disabled={uploading}
              className="hidden"
              id="image-upload"
            />
            <label
              htmlFor="image-upload"
              className="cursor-pointer block p-4 border-2 border-stone-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all"
            >
              <ImageIcon className="mx-auto h-8 w-8 mb-2 text-stone-400" />
              <p className="text-xs font-medium text-stone-600">Upload Image</p>
            </label>
          </div>
        </div>

        <p className="text-xs text-stone-500">
          Upload prescriptions, discharge summaries, or lab reports
        </p>
      </div>

      {/* Old upload UI */}
      <div className="border-2 border-dashed border-stone-300 rounded-lg p-6 text-center hover:border-primary transition-colors hidden">
        <input
          type="file"
          accept=".pdf"
          onChange={handleUpload}
          disabled={uploading}
          className="hidden"
          id="document-upload"
        />
        <label htmlFor="document-upload" className="cursor-pointer">
          <Upload className={`mx-auto h-12 w-12 mb-3 ${uploading ? 'text-primary animate-pulse' : 'text-stone-400'}`} />
          <p className="text-sm text-stone-600 mb-1">
            {uploading ? 'Uploading & analyzing...' : 'Click to upload PDF'}
          </p>
          <p className="text-xs text-stone-500">
            Lab reports, prescriptions, medical records
          </p>
        </label>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 p-3 bg-green-50 text-green-700 rounded-lg text-sm">
          <CheckCircle className="h-4 w-4" />
          {success}
        </div>
      )}

      {/* Documents List */}
      {loading ? (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="text-sm text-stone-500 mt-2">Loading documents...</p>
        </div>
      ) : documents.length > 0 ? (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-stone-700">Uploaded Documents</h3>
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="flex items-start justify-between p-3 bg-stone-50 rounded-lg hover:bg-stone-100 transition-colors"
            >
              <div className="flex items-start gap-3 flex-1">
                <FileText className="h-5 w-5 text-primary mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-stone-900 truncate">
                    {doc.file_name}
                  </p>
                  <p className="text-xs text-stone-500">
                    {new Date(doc.upload_date).toLocaleDateString()} • {doc.num_pages || 0} pages
                  </p>
                  {doc.analysis?.summary && (
                    <p className="text-xs text-stone-600 mt-1 line-clamp-2">
                      {doc.analysis.summary}
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={() => handleDelete(doc.id)}
                className="text-stone-400 hover:text-red-600 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-stone-500">
          <FileText className="mx-auto h-12 w-12 text-stone-300 mb-2" />
          <p className="text-sm">No documents uploaded yet</p>
        </div>
      )}
    </div>
  );
}

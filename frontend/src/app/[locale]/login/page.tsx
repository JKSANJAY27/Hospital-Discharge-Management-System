"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Leaf, Lock, Mail, Loader2, ArrowRight } from "lucide-react";
import { signInWithPopup } from "firebase/auth";
import { authInstance as auth } from "../../../lib/firebase-client";
import { GoogleAuthProvider } from "firebase/auth";
const googleProvider = new GoogleAuthProvider();
import { useTranslations } from 'next-intl';
import LanguageSwitcher from '@/components/LanguageSwitcher';
import SketchBackground from '@/components/sketch/SketchBackground';
import '@/styles/sketch.css';

export default function LoginPage() {
    const t = useTranslations('Login');
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isGoogleLoading, setIsGoogleLoading] = useState(false);
    const [error, setError] = useState("");

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError("");

        try {
            const formData = new FormData();
            formData.append("username", email);
            formData.append("password", password);

            const res = await fetch("/api/auth/login", {
                method: "POST",
                body: formData,
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Login failed");
            }

            const data = await res.json();
            localStorage.setItem("token", data.access_token);
            router.push("/");
        } catch (err: unknown) {
            if (err instanceof Error) {
                setError(err.message);
            } else {
                setError("Login failed");
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleGoogleSignIn = async () => {
        setIsGoogleLoading(true);
        setError("");

        // Check if Firebase is initialized
        if (!auth || !googleProvider) {
            setError("Firebase is not configured. Please contact the administrator.");
            setIsGoogleLoading(false);
            console.error("Firebase auth or googleProvider is undefined. Check your .env file.");
            return;
        }

        try {
            const result = await signInWithPopup(auth, googleProvider);
            const user = result.user;

            // Get Firebase ID token
            const idToken = await user.getIdToken();

            // Send to backend for verification and session creation
            const res = await fetch("/api/auth/firebase-login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    idToken,
                    email: user.email,
                    displayName: user.displayName,
                    photoURL: user.photoURL
                }),
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Google sign-in failed");
            }

            const data = await res.json();
            localStorage.setItem("token", data.access_token);
            router.push("/");
        } catch (err: any) {
            console.error("Google sign-in error:", err);
            setError(err.message || "Failed to sign in with Google");
        } finally {
            setIsGoogleLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#FDFCF8] p-4 font-sans relative overflow-hidden">
            
            {/* Sketch background with doodles */}
            <SketchBackground />

            {/* Large blob backgrounds with sketch effect */}
            <div className="absolute top-0 left-0 w-64 h-64 bg-[#3A5A40]/5 blur-3xl -translate-x-1/2 -translate-y-1/2 float-sketch"></div>
            <div className="absolute bottom-0 right-0 w-96 h-96 bg-[#A3B18A]/10 blur-3xl translate-x-1/3 translate-y-1/3 wiggle-sketch"></div>

            <div className="absolute top-4 right-4 z-20">
                <LanguageSwitcher />
            </div>

            <div className="w-full max-w-md z-10" style={{ animation: 'bounce-in 0.8s ease-out' }}>
                {/* Header Logo Area with comic style */}
                <div className="flex flex-col items-center mb-8">
                    <div 
                        className="w-20 h-20 bg-[#3A5A40] flex items-center justify-center shadow-lg mb-6 relative wiggle-sketch"
                        style={{
                            borderRadius: '255px 15px 225px 15px/15px 225px 15px 255px',
                            border: '4px solid #2F4A33',
                            boxShadow: '5px 5px 0px rgba(0,0,0,0.2), -2px -2px 0px rgba(255,255,255,0.5)'
                        }}
                    >
                        <Leaf className="w-10 h-10 text-[#F2E8CF]" strokeWidth={3} />
                        {/* Hand-drawn circle accent */}
                        <div 
                            className="absolute -top-2 -right-2 w-6 h-6 bg-[#A3B18A] rounded-full"
                            style={{
                                border: '2px solid #588157',
                                animation: 'pulse-sketch 2s ease-in-out infinite'
                            }}
                        />
                    </div>
                    <h1 
                        className="text-4xl font-bold text-stone-800 text-center relative"
                        style={{
                            fontFamily: '"Comic Sans MS", "Chalkboard SE", "Comic Neue", cursive',
                            letterSpacing: '0.5px',
                            textShadow: '4px 4px 0px rgba(163, 177, 138, 0.4), 2px 2px 0px rgba(58, 90, 64, 0.2)',
                            transform: 'rotate(-1deg)'
                        }}
                    >
                        {t('welcome')}
                        {/* Comic underline */}
                        <svg className="absolute -bottom-2 left-0 w-full h-2" style={{ overflow: 'visible' }}>
                            <path
                                d="M 0 2 Q 50 0, 100 2 T 200 2"
                                fill="none"
                                stroke="#3A5A40"
                                strokeWidth="3"
                                strokeLinecap="round"
                                opacity="0.4"
                                style={{
                                    strokeDasharray: '5,3'
                                }}
                            />
                        </svg>
                    </h1>
                    <p className="text-stone-600 mt-4 text-center font-medium">{t('subtitle')}</p>
                </div>

                {/* Login Card with sketch border */}
                <div 
                    className="bg-white p-8 relative"
                    style={{
                        borderRadius: '255px 25px 225px 25px/25px 225px 25px 255px',
                        border: '4px solid #3A5A40',
                        boxShadow: '8px 8px 0px rgba(58, 90, 64, 0.2), -2px -2px 0px rgba(163, 177, 138, 0.3)',
                        background: 'linear-gradient(135deg, #ffffff 0%, #fdfcf8 100%)'
                    }}
                >
                    <form onSubmit={handleLogin} className="space-y-6">
                        {error && (
                            <div 
                                className="bg-red-50 border-4 text-red-700 p-4 text-sm text-center font-bold relative"
                                style={{
                                    borderRadius: '25px 255px 15px 225px/255px 15px 225px 25px',
                                    borderColor: '#dc2626',
                                    boxShadow: '3px 3px 0px rgba(220, 38, 38, 0.3)'
                                }}
                            >
                                {error}
                            </div>
                        )}

                        <div className="space-y-2">
                            <label className="text-sm font-black text-stone-800 ml-1 uppercase tracking-wide">{t('email')}</label>
                            <div className="relative group">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-stone-400 group-focus-within:text-[#3A5A40] transition-colors z-10" />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full bg-white py-4 pl-12 pr-4 text-stone-800 placeholder-stone-400 focus:outline-none font-medium relative"
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
                                    placeholder="you@example.com"
                                    required
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-black text-stone-800 ml-1 uppercase tracking-wide">{t('password')}</label>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-stone-400 group-focus-within:text-[#3A5A40] transition-colors z-10" />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full bg-white py-4 pl-12 pr-4 text-stone-800 placeholder-stone-400 focus:outline-none font-medium relative"
                                    style={{
                                        border: '3px solid #d6d3d1',
                                        borderRadius: '225px 15px 225px 15px/15px 255px 15px 225px',
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
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-[#3A5A40] hover:bg-[#2F4A33] text-white font-black py-4 uppercase tracking-wider transition-all flex items-center justify-center gap-2 group relative overflow-hidden"
                            style={{
                                borderRadius: '15px 225px 15px 225px/225px 15px 255px 15px',
                                border: '3px solid #2F4A33',
                                boxShadow: '5px 5px 0px rgba(0, 0, 0, 0.2)',
                                fontSize: '1.1rem'
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = 'translate(-2px, -2px)';
                                e.currentTarget.style.boxShadow = '7px 7px 0px rgba(0, 0, 0, 0.2)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = 'translate(0, 0)';
                                e.currentTarget.style.boxShadow = '5px 5px 0px rgba(0, 0, 0, 0.2)';
                            }}
                        >
                            {isLoading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <>
                                    {t('signIn')}
                                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>

                        {/* Divider with comic style */}
                        <div className="relative my-8">
                            <div className="absolute inset-0 flex items-center">
                                <svg className="w-full h-1" style={{ overflow: 'visible' }}>
                                    <path
                                        d="M 0 0 Q 50 -2, 100 0 T 200 0 T 300 0 T 400 0"
                                        fill="none"
                                        stroke="#d6d3d1"
                                        strokeWidth="3"
                                        strokeLinecap="round"
                                        style={{
                                            strokeDasharray: '8,5'
                                        }}
                                    />
                                </svg>
                            </div>
                            <div className="relative flex justify-center">
                                <span 
                                    className="px-4 bg-white text-stone-700 font-black uppercase tracking-wide text-xs"
                                    style={{
                                        border: '2px solid #d6d3d1',
                                        borderRadius: '15px 5px 15px 5px/5px 15px 5px 15px',
                                        padding: '6px 16px'
                                    }}
                                >
                                    {t('orContinue')}
                                </span>
                            </div>
                        </div>

                        {/* Google Sign In Button with sketch style */}
                        <button
                            type="button"
                            onClick={handleGoogleSignIn}
                            disabled={isGoogleLoading}
                            className="w-full bg-white hover:bg-stone-50 text-stone-800 font-black py-4 uppercase tracking-wide transition-all flex items-center justify-center gap-3 group relative"
                            style={{
                                borderRadius: '225px 15px 225px 15px/15px 255px 15px 225px',
                                border: '3px solid #d6d3d1',
                                boxShadow: '5px 5px 0px rgba(0, 0, 0, 0.1)',
                                fontSize: '1rem'
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = 'translate(-2px, -2px)';
                                e.currentTarget.style.boxShadow = '7px 7px 0px rgba(0, 0, 0, 0.1)';
                                e.currentTarget.style.borderColor = '#3A5A40';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = 'translate(0, 0)';
                                e.currentTarget.style.boxShadow = '5px 5px 0px rgba(0, 0, 0, 0.1)';
                                e.currentTarget.style.borderColor = '#d6d3d1';
                            }}
                        >
                            {isGoogleLoading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <>
                                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                                    </svg>
                                    {t('signInGoogle')}
                                </>
                            )}
                        </button>
                    </form>
                </div>

                {/* Footer with comic style */}
                <div className="mt-8 text-center">
                    <p className="text-stone-600 font-medium">
                        {t('noAccount')}{" "}
                        <Link 
                            href="/signup" 
                            className="text-[#3A5A40] font-black hover:text-[#2F4A33] transition-colors relative inline-block"
                            style={{
                                textDecoration: 'none'
                            }}
                            onMouseEnter={(e) => {
                                const underline = e.currentTarget.querySelector('.underline-sketch');
                                if (underline) {
                                    (underline as HTMLElement).style.strokeDashoffset = '0';
                                }
                            }}
                            onMouseLeave={(e) => {
                                const underline = e.currentTarget.querySelector('.underline-sketch');
                                if (underline) {
                                    (underline as HTMLElement).style.strokeDashoffset = '100';
                                }
                            }}
                        >
                            {t('startJourney')}
                            <svg className="absolute -bottom-1 left-0 w-full h-2" style={{ overflow: 'visible' }}>
                                <path
                                    className="underline-sketch"
                                    d="M 0 1 Q 25 -1, 50 1 T 100 1"
                                    fill="none"
                                    stroke="#3A5A40"
                                    strokeWidth="3"
                                    strokeLinecap="round"
                                    style={{
                                        strokeDasharray: '100',
                                        strokeDashoffset: '100',
                                        transition: 'stroke-dashoffset 0.5s ease'
                                    }}
                                />
                            </svg>
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
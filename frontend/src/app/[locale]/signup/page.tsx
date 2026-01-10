"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Leaf, Lock, Mail, User, Loader2, ArrowRight, CheckCircle2 } from "lucide-react";
import { useTranslations } from 'next-intl';
import SketchBackground from '@/components/sketch/SketchBackground';
import '@/styles/sketch.css';

export default function SignupPage() {
    const t = useTranslations('Signup');
    const router = useRouter();
    const [fullName, setFullName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");

    const handleSignup = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError("");

        if (password !== confirmPassword) {
            setError(t('passMismatch'));
            setIsLoading(false);
            return;
        }

        try {
            const res = await fetch("/api/auth/signup", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: fullName,
                    email: email,
                    password: password
                }),
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || t('failed'));
            }

            const data = await res.json();
            localStorage.setItem("token", data.access_token);
            router.push("/");
        } catch (err: unknown) {
            if (err instanceof Error) {
                setError(err.message);
            } else {
                setError(t('failed'));
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#FDFCF8] p-4 font-sans relative overflow-hidden">
            
            {/* Sketch background with doodles */}
            <SketchBackground />

            {/* Large blob backgrounds with sketch effect */}
            <div className="absolute top-0 right-0 w-80 h-80 bg-[#3A5A40]/5 blur-3xl translate-x-1/4 -translate-y-1/4 wiggle-sketch"></div>
            <div className="absolute bottom-0 left-0 w-96 h-96 bg-[#A3B18A]/10 blur-3xl -translate-x-1/4 translate-y-1/4 float-sketch"></div>

            <div className="w-full max-w-md z-10 my-8" style={{ animation: 'bounce-in 0.8s ease-out' }}>
                {/* Header with comic style */}
                <div className="flex flex-col items-center mb-6">
                    <div 
                        className="w-20 h-20 bg-[#3A5A40] flex items-center justify-center shadow-lg mb-4 relative wiggle-sketch"
                        style={{
                            borderRadius: '255px 15px 225px 15px/15px 225px 15px 255px',
                            border: '4px solid #2F4A33',
                            boxShadow: '5px 5px 0px rgba(0,0,0,0.2), -2px -2px 0px rgba(255,255,255,0.5)'
                        }}
                    >
                        <Leaf className="w-9 h-9 text-[#F2E8CF]" strokeWidth={3} />
                    </div>
                    <h1 
                        className="text-4xl font-bold text-stone-800 text-center relative mb-2"
                        style={{
                            fontFamily: '"Comic Sans MS", "Chalkboard SE", "Comic Neue", cursive',
                            letterSpacing: '0.5px',
                            textShadow: '4px 4px 0px rgba(163, 177, 138, 0.4), 2px 2px 0px rgba(58, 90, 64, 0.2)',
                            transform: 'rotate(-1deg)'
                        }}
                    >
                        {t('title')}
                    </h1>
                    <p className="text-stone-600 text-center text-sm font-medium">{t('subtitle')}</p>
                </div>

                {/* Signup Card with sketch border */}
                <div 
                    className="bg-white p-8 relative"
                    style={{
                        borderRadius: '255px 25px 225px 25px/25px 225px 25px 255px',
                        border: '4px solid #3A5A40',
                        boxShadow: '8px 8px 0px rgba(58, 90, 64, 0.2), -2px -2px 0px rgba(163, 177, 138, 0.3)',
                        background: 'linear-gradient(135deg, #ffffff 0%, #fdfcf8 100%)'
                    }}
                >
                    <form onSubmit={handleSignup} className="space-y-5">
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

                        {/* Full Name */}
                        <div className="space-y-2">
                            <label className="text-sm font-black text-stone-800 ml-1 uppercase tracking-wide">{t('fullName')}</label>
                            <div className="relative group">
                                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-stone-400 group-focus-within:text-[#3A5A40] transition-colors z-10" />
                                <input
                                    type="text"
                                    value={fullName}
                                    onChange={(e) => setFullName(e.target.value)}
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
                                    placeholder="John Doe"
                                    required
                                />
                            </div>
                        </div>

                        {/* Email */}
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
                                    placeholder="you@example.com"
                                    required
                                />
                            </div>
                        </div>

                        {/* Password */}
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
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        </div>

                        {/* Confirm Password */}
                        <div className="space-y-2">
                            <label className="text-sm font-black text-stone-800 ml-1 uppercase tracking-wide">{t('confirmPassword')}</label>
                            <div className="relative group">
                                <CheckCircle2 className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-stone-400 group-focus-within:text-[#3A5A40] transition-colors z-10" />
                                <input
                                    type="password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
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
                            className="w-full mt-2 bg-[#3A5A40] hover:bg-[#2F4A33] text-white font-black py-4 uppercase tracking-wider transition-all flex items-center justify-center gap-2 group relative overflow-hidden"
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
                                    {t('createAccount')}
                                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>
                </div>

                {/* Footer with comic style */}
                <div className="mt-8 text-center pb-4">
                    <p className="text-stone-600 text-sm font-medium">
                        {t('alreadyMember')}{" "}
                        <Link 
                            href="/login" 
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
                            {t('signIn')}
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
import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

// Configure body size limit for this route if needed
export const runtime = 'nodejs';
export const maxDuration = 60; // 60 seconds timeout

export async function POST(request: NextRequest) {
    try {
        const token = request.headers.get('authorization');

        if (!token) {
            return NextResponse.json(
                { detail: 'Authorization required' },
                { status: 401 }
            );
        }

        // Get form data
        const formData = await request.formData();

        console.log('Proxying discharge simplification request...');

        const response = await fetch(`${API_URL}/discharge/simplify`, {
            method: 'POST',
            headers: {
                'Authorization': token,
                'ngrok-skip-browser-warning': 'true',
                // Note: Do NOT set Content-Type for FormData, fetch sets it automatically with boundary
            },
            body: formData,
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Backend error:', response.status, errorText);
            try {
                const errorJson = JSON.parse(errorText);
                return NextResponse.json(errorJson, { status: response.status });
            } catch {
                return NextResponse.json(
                    { detail: errorText || 'Failed to process discharge instructions' },
                    { status: response.status }
                );
            }
        }

        const data = await response.json();
        return NextResponse.json(data, { status: response.status });
    } catch (error) {
        console.error('Proxy error:', error);
        return NextResponse.json(
            { detail: 'Internal server error during proxying' },
            { status: 500 }
        );
    }
}

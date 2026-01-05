import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest, { params }: { params: Promise<{ sessionId: string }> }) {
    try {
        const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
        const token = req.headers.get('authorization');
        const { sessionId } = await params;

        const response = await fetch(`${backendUrl}/sessions/${sessionId}/history`, {
            headers: {
                'Authorization': token || '',
                'ngrok-skip-browser-warning': 'true'
            },
        });

        if (!response.ok) {
            return NextResponse.json({ detail: 'Failed to fetch history' }, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch {
        return NextResponse.json({ detail: "Failed to fetch history" }, { status: 500 });
    }
}

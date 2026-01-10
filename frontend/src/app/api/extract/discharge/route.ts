// API Route: /api/extract/discharge
// Proxies discharge summary extraction requests to Python backend

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const token = request.headers.get('authorization');
    
    if (!token) {
      return NextResponse.json(
        { detail: 'No authorization token provided' },
        { status: 401 }
      );
    }

    // Get the form data from the request
    const formData = await request.formData();
    
    // Forward to Python backend
    const backendResponse = await fetch(`${BACKEND_URL}/extract/discharge`, {
      method: 'POST',
      headers: {
        'Authorization': token,
      },
      body: formData,
    });

    const data = await backendResponse.json();

    if (!backendResponse.ok) {
      return NextResponse.json(
        data,
        { status: backendResponse.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Discharge extraction proxy error:', error);
    return NextResponse.json(
      { detail: 'Failed to extract discharge data' },
      { status: 500 }
    );
  }
}

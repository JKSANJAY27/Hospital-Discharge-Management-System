// API Route: /api/recovery-plans
// Fetch recovery plans for the current user

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    const token = request.headers.get('authorization');
    
    if (!token) {
      return NextResponse.json(
        { detail: 'No authorization token provided' },
        { status: 401 }
      );
    }

    const backendResponse = await fetch(`${BACKEND_URL}/recovery-plans`, {
      method: 'GET',
      headers: {
        'Authorization': token,
      },
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
    console.error('Recovery plans fetch error:', error);
    return NextResponse.json(
      { detail: 'Failed to fetch recovery plans' },
      { status: 500 }
    );
  }
}

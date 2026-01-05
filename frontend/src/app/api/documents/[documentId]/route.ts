import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

// DELETE /api/documents/[documentId]
export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ documentId: string }> }
) {
  try {
    const token = request.headers.get('authorization');
    
    if (!token) {
      return NextResponse.json(
        { detail: 'Authorization required' },
        { status: 401 }
      );
    }
    
    const { documentId } = await context.params;
    
    console.log('Deleting document:', documentId);
    
    const response = await fetch(`${API_URL}/documents/${documentId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': token,
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend document delete error:', response.status, errorText);
      try {
        const errorJson = JSON.parse(errorText);
        return NextResponse.json(errorJson, { status: response.status });
      } catch {
        return NextResponse.json(
          { detail: errorText || 'Failed to delete document' },
          { status: response.status }
        );
      }
    }

    const data = await response.json();
    console.log('Delete response:', data);
    
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Document delete proxy error:', error);
    return NextResponse.json(
      { detail: 'Failed to delete document' },
      { status: 500 }
    );
  }
}

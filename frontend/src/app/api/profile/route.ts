export async function GET(request: Request) {
  try {
    const authHeader = request.headers.get('authorization');
    if (!authHeader) {
      return Response.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/auth/me`, {
      headers: {
        'Authorization': authHeader,
        'ngrok-skip-browser-warning': 'true',
      },
    });

    if (!response.ok) {
      return Response.json({ detail: 'Failed to fetch profile' }, { status: response.status });
    }

    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error('Profile fetch error:', error);
    return Response.json(
      { detail: 'Failed to fetch profile' },
      { status: 500 }
    );
  }
}

export async function PUT(request: Request) {
  try {
    const authHeader = request.headers.get('authorization');
    if (!authHeader) {
      return Response.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    const body = await request.json();
    const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    
    const response = await fetch(`${backendUrl}/users/profile`, {
      method: 'PUT',
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('Profile update error:', error);
      return Response.json({ detail: 'Failed to update profile' }, { status: response.status });
    }

    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error('Profile update error:', error);
    return Response.json(
      { detail: 'Failed to update profile' },
      { status: 500 }
    );
  }
}

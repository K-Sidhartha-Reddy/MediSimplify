// Quick diagnostic for login issues
export async function testLogin() {
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: 'browsertest@example.com',
        password: 'testpass123'
      })
    });
    
    console.log('Response status:', response.status);
    console.log('Response OK:', response.ok);
    console.log('Response headers:', Object.fromEntries(response.headers));
    
    if (!response.ok) {
      const error = await response.text();
      console.error('Error response:', error);
      return { error: `HTTP ${response.status}: ${error}` };
    }
    
    const data = await response.json();
    console.log('Success! Data:', data);
    return data;
  } catch (error) {
    console.error('Fetch error:', error);
    return { error: String(error) };
  }
}

if (typeof window !== 'undefined') {
  (window as unknown as Record<string, unknown>).testLogin = testLogin;
}


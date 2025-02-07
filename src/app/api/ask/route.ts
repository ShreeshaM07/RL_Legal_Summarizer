export async function POST(req: Request) {
    try {
      const { question } = await req.json();
      if (!question) return Response.json({ error: "Question is required" }, { status: 400 });
  
      // Simulate AI Response (Replace this with Python API Call)
      const answer = `AI Response for: "${question}"`;
  
      return Response.json({ answer });
    } catch (error) {
      return Response.json({ error: "Server error" }, { status: 500 });
    }
  }
  
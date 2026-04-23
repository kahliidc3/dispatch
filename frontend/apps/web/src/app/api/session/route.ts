import { NextResponse } from "next/server";
import type { SessionResponse } from "@/types/api";

export function GET() {
  const payload: SessionResponse = {
    session: null,
  };

  return NextResponse.json(payload);
}

export function POST() {
  return NextResponse.json(
    {
      message: "Session mutations are not implemented in Sprint 00.",
    },
    { status: 501 },
  );
}

export function DELETE() {
  return NextResponse.json(
    {
      message: "Session mutations are not implemented in Sprint 00.",
    },
    { status: 501 },
  );
}

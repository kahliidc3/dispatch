import { NextResponse } from "next/server";
import type { HealthResponse } from "@/types/api";

export function GET() {
  const payload: HealthResponse = {
    service: "web",
    status: "ok",
  };

  return NextResponse.json(payload);
}

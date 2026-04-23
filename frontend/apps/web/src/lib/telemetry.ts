export type TelemetryEvent = {
  event: string;
  props?: Record<string, string | number | boolean | null>;
};

export function track(event: TelemetryEvent) {
  return event;
}

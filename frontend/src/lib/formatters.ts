export function formatTimestamp(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function maskEmailAddress(value: string) {
  const [localPart, domain] = value.split("@");

  if (!localPart || !domain) {
    return value;
  }

  const visiblePrefix = localPart.slice(0, 2);
  const maskedLength = Math.max(localPart.length - visiblePrefix.length, 2);

  return `${visiblePrefix}${"*".repeat(maskedLength)}@${domain}`;
}

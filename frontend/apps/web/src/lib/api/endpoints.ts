export const apiEndpoints = {
  internal: {
    health: "/api/health",
    session: "/api/session",
  },
  auth: {
    login: "/auth/login",
    logout: "/auth/logout",
    verifyMfa: "/auth/mfa/verify",
    apiKeys: "/auth/api-keys",
    apiKeyById: (id: string) => `/auth/api-keys/${id}`,
  },
  users: {
    list: "/users",
    self: "/users/me",
    byId: (id: string) => `/users/${id}`,
    resetMfa: (id: string) => `/users/${id}/reset-mfa`,
  },
  domains: {
    list: "/domains",
    byId: (id: string) => `/domains/${id}`,
    create: "/domains",
    verify: (id: string) => `/domains/${id}/verify`,
    health: (id: string) => `/domains/${id}/health`,
    retire: (id: string) => `/domains/${id}/retire`,
  },
  senderProfiles: {
    list: "/sender-profiles",
    byId: (id: string) => `/sender-profiles/${id}`,
    create: "/sender-profiles",
    delete: (id: string) => `/sender-profiles/${id}`,
  },
  contacts: {
    list: "/contacts",
    byId: (id: string) => `/contacts/${id}`,
    bulkImport: "/contacts/bulk-import",
  },
  lists: {
    list: "/lists",
    members: (id: string) => `/lists/${id}/members`,
  },
  segments: {
    list: "/segments",
    evaluate: (id: string) => `/segments/${id}/evaluate`,
  },
  templates: {
    list: "/templates",
    versions: (id: string) => `/templates/${id}/versions`,
    publishVersion: (id: string, version: string) =>
      `/templates/${id}/versions/${version}/publish`,
  },
  campaigns: {
    list: "/campaigns",
    byId: (id: string) => `/campaigns/${id}`,
    launch: (id: string) => `/campaigns/${id}/launch`,
    pause: (id: string) => `/campaigns/${id}/pause`,
    resume: (id: string) => `/campaigns/${id}/resume`,
    analytics: (id: string) => `/campaigns/${id}/analytics`,
  },
  suppression: {
    list: "/suppression",
    byEmail: (email: string) => `/suppression/${encodeURIComponent(email)}`,
  },
  analytics: {
    overview: "/analytics/overview",
    domains: "/analytics/domains",
    reputation: "/analytics/reputation",
  },
} as const;

export function isInternalApiRoute(path: string) {
  return path.startsWith("/api/");
}

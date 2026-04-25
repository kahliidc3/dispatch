# Dispatch Technical Explanation

This document is a brief technical explanation of the whole Dispatch project so that any technical person can understand what the system is, how it runs, how it deploys, and how the main external services fit together.

## Brief Recap

### Project

Dispatch is an internal email platform for sending large campaigns safely through AWS SES, with contacts, templates, campaigns, analytics, suppression, warmup, throttling, and circuit breakers.

### Docker

Docker is used, but local dev does not have to be fully Docker-only.

You can run:

```text
Frontend: pnpm dev
Backend: uvicorn
```

But Docker is useful for services like:

- Postgres
- Redis
- LocalStack
- MailHog
- Workers

### Deployment

Production is planned around Docker containers on AWS:

```text
Backend/API/workers -> ECS Fargate
Database -> RDS PostgreSQL
Redis -> ElastiCache
Email -> AWS SES
Secrets -> AWS Secrets Manager
```

### Cloudflare

Cloudflare is not for sending emails.

Cloudflare is for DNS automation:

- SPF
- DKIM
- DMARC
- MAIL FROM
- SES verification records

Dispatch can call Cloudflare API to create those records automatically.

### Cloudflare Account/API Key

Yes, to automate DNS with Cloudflare you need:

- Cloudflare account
- Domain using Cloudflare DNS
- Cloudflare API token with DNS edit permission

Without Cloudflare, records can be added manually or through another provider like Route 53.

### Domain Managed In Cloudflare DNS

You do not need to buy domains from Cloudflare.

You can buy from Namecheap/GoDaddy/etc, then change the domain's nameservers to Cloudflare.

### Nameservers

Nameservers tell the internet where your DNS records are managed.

Example:

```text
Buy domain at Namecheap
Set nameservers to Cloudflare
Now Cloudflare controls the DNS records
```

### Env/API Keys

The project is hybrid:

```text
App-created API keys -> stored hashed in database
Infrastructure secrets -> env vars / AWS Secrets Manager
```

Docker does not remove the need for env vars.

```text
Docker contains the app.
Env vars configure the app.
```

## High-Level Architecture

<figure aria-label="Dispatch high-level architecture diagram">
  <svg viewBox="0 0 960 420" role="img" aria-labelledby="architecture-title architecture-desc" xmlns="http://www.w3.org/2000/svg">
    <title id="architecture-title">Dispatch high-level architecture</title>
    <desc id="architecture-desc">Operator dashboard calls the frontend, frontend calls the FastAPI backend, backend uses PostgreSQL, Redis, workers, AWS SES, Cloudflare DNS, and a webhook receiver.</desc>
    <defs>
      <marker id="arrow-architecture" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
        <path d="M0,0 L10,4 L0,8 Z" fill="#4f5d75" />
      </marker>
      <style>
        .diagram-bg { fill: #f5f5f5; }
        .node { fill: #ffffff; stroke: #2d3142; stroke-width: 1.2; rx: 6; }
        .node-soft { fill: #f0f1f3; stroke: #4f5d75; stroke-width: 1; rx: 6; }
        .node-focus { fill: rgba(235,108,54,0.08); stroke: #eb6c36; stroke-width: 1.4; rx: 6; }
        .label { fill: #2d3142; font-family: Geist, Arial, sans-serif; font-size: 14px; font-weight: 600; }
        .sub { fill: #4f5d75; font-family: "Geist Mono", Consolas, monospace; font-size: 11px; }
        .line { stroke: #4f5d75; stroke-width: 1.2; fill: none; marker-end: url(#arrow-architecture); }
      </style>
    </defs>
    <rect class="diagram-bg" x="0" y="0" width="960" height="420" rx="8" />

    <rect class="node-soft" x="36" y="156" width="132" height="72" />
    <text class="label" x="102" y="185" text-anchor="middle">Operator</text>
    <text class="sub" x="102" y="204" text-anchor="middle">dashboard user</text>

    <rect class="node" x="228" y="156" width="148" height="72" />
    <text class="label" x="302" y="185" text-anchor="middle">Next.js Frontend</text>
    <text class="sub" x="302" y="204" text-anchor="middle">operator console</text>

    <rect class="node-focus" x="444" y="156" width="156" height="72" />
    <text class="label" x="522" y="185" text-anchor="middle">FastAPI Backend</text>
    <text class="sub" x="522" y="204" text-anchor="middle">business rules</text>

    <rect class="node" x="688" y="42" width="136" height="64" />
    <text class="label" x="756" y="70" text-anchor="middle">PostgreSQL</text>
    <text class="sub" x="756" y="88" text-anchor="middle">system data</text>

    <rect class="node" x="688" y="128" width="136" height="64" />
    <text class="label" x="756" y="156" text-anchor="middle">Redis</text>
    <text class="sub" x="756" y="174" text-anchor="middle">cache/queues</text>

    <rect class="node-focus" x="688" y="214" width="136" height="64" />
    <text class="label" x="756" y="242" text-anchor="middle">Celery Workers</text>
    <text class="sub" x="756" y="260" text-anchor="middle">send/process</text>

    <rect class="node" x="688" y="300" width="136" height="64" />
    <text class="label" x="756" y="328" text-anchor="middle">Webhook App</text>
    <text class="sub" x="756" y="346" text-anchor="middle">SES events</text>

    <rect class="node-soft" x="852" y="214" width="84" height="64" />
    <text class="label" x="894" y="242" text-anchor="middle">SES</text>
    <text class="sub" x="894" y="260" text-anchor="middle">email</text>

    <rect class="node-soft" x="852" y="128" width="84" height="64" />
    <text class="label" x="894" y="156" text-anchor="middle">DNS</text>
    <text class="sub" x="894" y="174" text-anchor="middle">Cloudflare</text>

    <path class="line" d="M168 192 H228" />
    <path class="line" d="M376 192 H444" />
    <path class="line" d="M600 172 C636 120 652 74 688 74" />
    <path class="line" d="M600 184 C636 168 652 160 688 160" />
    <path class="line" d="M600 206 C636 230 652 246 688 246" />
    <path class="line" d="M824 246 H852" />
    <path class="line" d="M894 278 C894 318 856 332 824 332" />
    <path class="line" d="M688 332 C640 332 612 286 568 228" />
    <path class="line" d="M600 184 C668 154 780 160 852 160" />
  </svg>
</figure>

The frontend is the operator console. The backend owns the business rules. Workers handle slow or retryable work like sending email, processing events, importing CSV files, and checking domain health.

## Email Domain Setup Flow

<figure aria-label="Email domain setup sequence diagram">
  <svg viewBox="0 0 960 520" role="img" aria-labelledby="domain-flow-title domain-flow-desc" xmlns="http://www.w3.org/2000/svg">
    <title id="domain-flow-title">Email domain setup flow</title>
    <desc id="domain-flow-desc">Operator adds a domain, Dispatch asks AWS SES for identity records, writes DNS records through Cloudflare or Route53, checks verification, then marks the domain ready.</desc>
    <defs>
      <marker id="arrow-sequence" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
        <path d="M0,0 L10,4 L0,8 Z" fill="#4f5d75" />
      </marker>
      <style>
        .seq-bg { fill: #f5f5f5; }
        .actor { fill: #ffffff; stroke: #2d3142; stroke-width: 1.1; rx: 6; }
        .actor-focus { fill: rgba(235,108,54,0.08); stroke: #eb6c36; stroke-width: 1.3; rx: 6; }
        .actor-label { fill: #2d3142; font-family: Geist, Arial, sans-serif; font-size: 14px; font-weight: 600; }
        .life { stroke: rgba(45,49,66,0.22); stroke-width: 1; stroke-dasharray: 4 4; }
        .msg { stroke: #4f5d75; stroke-width: 1.2; fill: none; marker-end: url(#arrow-sequence); }
        .msg-focus { stroke: #eb6c36; stroke-width: 1.4; fill: none; marker-end: url(#arrow-sequence); }
        .msg-text { fill: #2d3142; font-family: "Geist Mono", Consolas, monospace; font-size: 11px; }
      </style>
    </defs>
    <rect class="seq-bg" x="0" y="0" width="960" height="520" rx="8" />

    <rect class="actor" x="52" y="32" width="128" height="56" />
    <text class="actor-label" x="116" y="66" text-anchor="middle">Operator</text>
    <rect class="actor-focus" x="292" y="32" width="136" height="56" />
    <text class="actor-label" x="360" y="66" text-anchor="middle">Dispatch API</text>
    <rect class="actor" x="532" y="32" width="128" height="56" />
    <text class="actor-label" x="596" y="66" text-anchor="middle">AWS SES</text>
    <rect class="actor" x="760" y="32" width="148" height="56" />
    <text class="actor-label" x="834" y="66" text-anchor="middle">Cloudflare/Route53</text>

    <line class="life" x1="116" y1="88" x2="116" y2="476" />
    <line class="life" x1="360" y1="88" x2="360" y2="476" />
    <line class="life" x1="596" y1="88" x2="596" y2="476" />
    <line class="life" x1="834" y1="88" x2="834" y2="476" />

    <path class="msg" d="M116 128 H360" />
    <text class="msg-text" x="150" y="118">add sending domain</text>

    <path class="msg" d="M360 184 H596" />
    <text class="msg-text" x="386" y="174">create SES identity</text>

    <path class="msg" d="M596 240 H360" />
    <text class="msg-text" x="398" y="230">return DKIM + verification records</text>

    <path class="msg-focus" d="M360 296 H834" />
    <text class="msg-text" x="446" y="286">write SPF, DKIM, DMARC, MAIL FROM</text>

    <path class="msg" d="M360 352 H596" />
    <text class="msg-text" x="408" y="342">check verification status</text>

    <path class="msg" d="M596 408 H360" />
    <text class="msg-text" x="430" y="398">domain verified</text>

    <path class="msg-focus" d="M360 456 H116" />
    <text class="msg-text" x="150" y="446">domain ready for sending</text>
  </svg>
</figure>

If Cloudflare is not connected, Dispatch can still show the DNS records and an operator can add them manually.

## Runtime And Secrets Model

<figure aria-label="Runtime and secrets ownership diagram">
  <svg viewBox="0 0 920 360" role="img" aria-labelledby="secrets-title secrets-desc" xmlns="http://www.w3.org/2000/svg">
    <title id="secrets-title">Runtime and secrets model</title>
    <desc id="secrets-desc">Environment variables and AWS Secrets Manager configure containers. Application API keys are hashed in the database. Provider secrets stay outside the app database.</desc>
    <defs>
      <marker id="arrow-secrets" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
        <path d="M0,0 L10,4 L0,8 Z" fill="#4f5d75" />
      </marker>
      <style>
        .sec-bg { fill: #f5f5f5; }
        .sec-node { fill: #ffffff; stroke: #2d3142; stroke-width: 1.1; rx: 6; }
        .sec-focus { fill: rgba(235,108,54,0.08); stroke: #eb6c36; stroke-width: 1.3; rx: 6; }
        .sec-store { fill: rgba(45,49,66,0.05); stroke: #4f5d75; stroke-width: 1.1; rx: 6; }
        .sec-safe { fill: #eef6ee; stroke: #6a8f6a; stroke-width: 1.1; rx: 6; }
        .sec-secret { fill: #fff3e8; stroke: #c77b30; stroke-width: 1.1; rx: 6; }
        .sec-label { fill: #2d3142; font-family: Geist, Arial, sans-serif; font-size: 14px; font-weight: 600; }
        .sec-sub { fill: #4f5d75; font-family: "Geist Mono", Consolas, monospace; font-size: 11px; }
        .sec-line { stroke: #4f5d75; stroke-width: 1.2; fill: none; marker-end: url(#arrow-secrets); }
      </style>
    </defs>
    <rect class="sec-bg" x="0" y="0" width="920" height="360" rx="8" />

    <rect class="sec-secret" x="48" y="72" width="196" height="72" />
    <text class="sec-label" x="146" y="101" text-anchor="middle">Env / Secrets Manager</text>
    <text class="sec-sub" x="146" y="120" text-anchor="middle">DB, Redis, AWS, DNS</text>

    <rect class="sec-focus" x="348" y="72" width="176" height="72" />
    <text class="sec-label" x="436" y="101" text-anchor="middle">App Containers</text>
    <text class="sec-sub" x="436" y="120" text-anchor="middle">API, webhook, workers</text>

    <rect class="sec-store" x="648" y="72" width="176" height="72" />
    <text class="sec-label" x="736" y="101" text-anchor="middle">Database</text>
    <text class="sec-sub" x="736" y="120" text-anchor="middle">business records</text>

    <rect class="sec-safe" x="348" y="224" width="176" height="72" />
    <text class="sec-label" x="436" y="253" text-anchor="middle">Dispatch API Keys</text>
    <text class="sec-sub" x="436" y="272" text-anchor="middle">hashed in DB</text>

    <rect class="sec-secret" x="48" y="224" width="196" height="72" />
    <text class="sec-label" x="146" y="253" text-anchor="middle">Provider Secrets</text>
    <text class="sec-sub" x="146" y="272" text-anchor="middle">AWS, Cloudflare, Google</text>

    <path class="sec-line" d="M244 108 H348" />
    <path class="sec-line" d="M524 108 H648" />
    <path class="sec-line" d="M524 260 C584 260 600 144 648 120" />
    <path class="sec-line" d="M244 260 H348" />
    <path class="sec-line" d="M146 224 V144" />
  </svg>
</figure>

Dispatch-created API keys belong to the application and are stored in the database as hashes plus safe metadata.

Infrastructure secrets belong outside the app database. In local development they live in `.env` files. In production they should come from AWS Secrets Manager or ECS task environment injection.

## Local Development Shape

```text
Frontend dev server -> http://localhost:3000
Backend API        -> http://localhost:8000
Webhook app        -> http://localhost:8001
Postgres           -> localhost:5432
Redis              -> localhost:6379
LocalStack         -> localhost:4566
MailHog            -> localhost:8025
```

Local development can mix direct processes and Docker containers. A common setup is to run Postgres/Redis/LocalStack/MailHog through Docker and run frontend/backend directly from the terminal.

## Production Shape

```text
Frontend       -> web hosting or container deployment
Backend API    -> ECS Fargate container
Webhook app    -> ECS Fargate container
Workers        -> ECS Fargate containers
Postgres       -> RDS PostgreSQL
Redis          -> ElastiCache Redis
Email sending  -> AWS SES
DNS automation -> Cloudflare API or Route53
Secrets        -> AWS Secrets Manager
```

The production goal is to run the application as containers, while managed AWS services provide database, cache, email, secrets, and infrastructure reliability.

## Core Safety Idea

Dispatch is designed to protect deliverability.

That means the system should avoid sending when something looks unsafe:

- Suppressed or unsubscribed contacts must not receive email.
- Warmup limits protect new sending domains.
- Throttles limit sending speed per domain.
- Circuit breakers pause sending when bounce or complaint rates become risky.
- Webhook events from SES feed analytics and reputation decisions.

In short: Dispatch is built to send email at scale, but only when the platform believes sending is safe.

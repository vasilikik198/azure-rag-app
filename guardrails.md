[ User Query ]
      │
      ▼
┌────────────────────────────────────────────────────────┐
│ 1. INPUT GUARDRAILS                                    │
│  - Prompt Injection & Jailbreak Defense                 │
│  - Input PII Masking / Anonymization                   │
│  - Intent & Non-Medical Topic Routing                  │
│  - [NEW] Rate Limiting & DDoS Safeguards (C6.3)        │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│ 2. RETRIEVAL GUARDRAILS                                │
│  - Tenant / User RBAC Isolation                        │
│  - Context Poisoning & Indirect Injection Scrubbing     │
│  - Context PII & Sensitive Data Scrubbing              │
│  - [NEW] Vector Store Query Density & Coverage Check   │
│          (C6.5)                                        │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│ 3. IN-BETWEEN / EXECUTION GUARDRAILS                   │
│  - Minimum Vector Relevance / Distance Thresholding    │
│  - Tool Parameter & Schema Sanitization                │
│  - [NEW] Context Compression & Density Guardrail       │
│          (C3.5)                                        │
│  - [NEW] Prompt Parameterization (SQL-Style Injection  │
│          Defense) (C3.6)                               │
│  - [NEW] Semantic Caching & Latency Interceptor        │
│          (C5.2)                                        │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│ 4. GENERATOR GUARDRAILS                                │
│  - [NEW] Token-Level Constrained Decoding (LMQL/Type)  │
│          (C3.10)                                       │
│  - Logit Bias & Structured Constraints                 │
│  - System Prompt Alignment & Temperature Control       │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│ 5. OUTPUT GUARDRAILS                                   │
│  - Output PII Anonymization                            │
│  - Medical Recommendation Disclaimer / Deflection      │
│  - Faithfulness / Grounding Verification               │
│  - Schema & Structural RAIL Validation                 │
│  - [NEW] Context Relevance & Alignment Verifier        │
│          (C6.6)                                        │
│  - [NEW] Response Relevancy & Sentiment Monitor        │
│          (C6.7)                                        │
│  - [NEW] Demographic Fairness & Toxicity Evaluator     │
│          (C6.9)                                        │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│ 6. POST-DEPLOYMENT & CONTINUOUS OBSERVABILITY GUARDRAILS│
│  - [NEW] Model & Concept Drift Monitoring (C6.4)       │
│  - [NEW] Refusal Metric & Content Update Trigger       │
│          (C6.8)                                        │
│  - [NEW] Latency & Token Resource Usage Monitor (C6.2, │
│          C6.10)                                        │
│  - [NEW] User Feedback (Implicit/Explicit) Collector   │
│          (C6.11)                                       │
└────────────────────────────────────────────────────────┘

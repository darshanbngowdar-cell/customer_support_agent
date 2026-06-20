```mermaid
graph TB
  subgraph Frontend
    U[User] --> UI[Streamlit/CLI]
  end
  UI -->|sanitized| PD[Persona Detection]
  PD --> QO[Query Optimization]
  QO --> HR[Hybrid Retrieval]
  HR --> CV[Context Validation]
  CV --> RG[Response Generation]
  RG --> CE[Confidence Evaluation]
  CE --> ED[Escalation Decision]
  ED --> HO[Human Handoff]
  HO --> MS[Conversation Memory]
# Workflow Diagram

```mermaid
graph TD
    A[User Input] --> B[Persona Detection]
    B --> C[Query Optimization]
    C --> D[Hybrid Retrieval]
    D --> E[Context Validation]
    E --> F[Response Generation]
    F --> G[Confidence Evaluation]
    G --> H[Escalation Decision]
    H --> I[Human Handoff / Final Response]
    I --> J[Conversation Memory]
    J --> A
```
```

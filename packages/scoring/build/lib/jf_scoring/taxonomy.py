"""Skill taxonomy used by the scoring engine.

Each category maps to the *canonical* terms and keyword aliases that JobForge
recognizes. Keyword matching is case-insensitive and substring-safe (word
boundaries). This taxonomy powers job keyword extraction, matched/missing
skill detection, and the default scoring weights.
"""

from __future__ import annotations

# canonical skill -> aliases / related tokens.
# Lowercased matching over the normalized job description.
SKILL_TAXONOMY: dict[str, list[str]] = {
    # AI / LLM
    "LLM applications": ["llm", "large language model", "langchain", "llamaindex"],
    "RAG": ["rag", "retrieval augmented", "vector database", "embeddings", "semantic search"],
    "Prompt security": ["prompt injection", "prompt security", "prompt engineering", "agent security", "llm security"],
    "AI security": ["ai security", "genai security", "ml security", "adversarial"],
    "LLMOps": ["llmops", "llm ops", "model serving", "model deployment", "fine tuning", "fine-tun"],
    "AI red teaming": ["red team", "red-teaming", "ai red team"],
    "Machine Learning": ["machine learning", "ml", "scikit", "tensorflow", "pytorch", "openai api", "transformer"],
    # DevSecOps
    "Git": ["git", "version control", "github", "gitlab"],
    "GitHub Actions": ["github actions", "gha", "workflow", "actions"],
    "CI/CD": ["ci/cd", "cicd", "cd pipeline", "continuous integration", "continuous delivery", "continuous deployment", "jenkins", "build pipeline"],
    "Docker": ["docker", "containerization", "containerised", "containerized", "container workloads", "containers"],
    "Kubernetes": ["kubernetes", "k8s", "orchestration", "helm", "eks", "gke", "aks", "argo"],
    "Terraform": ["terraform", "iac", "infrastructure as code", "infrastructure-as-code", "pulumi", "cloudformation"],
    "Linux": ["linux", "unix", "bash", "shell scripting", "system administration"],
    "Trivy": ["trivy", "vulnerability scanner", "container security scan"],
    "Bandit": ["bandit", "static analysis", "saast security"],
    "Secrets detection": ["secret scanning", "secrets detection", "gitleaks", "trufflehog", "secret management", "vault", "aws secrets"],
    "Secure SDLC": ["secure sdlc", "security sdlc", "shift left", "code review", "security review", "sdlc"],
    # Security
    "OWASP": ["owasp", "top 10", "web application security"],
    "Application security": ["application security", "appsec", "web security", "api security"],
    "Vulnerability assessment": ["vulnerability assessment", "vulnerability management", "penetration", "pentest", "pen test"],
    "Network security": ["network security", "firewall", "zero trust", "vpn", "waf", "ids", "siem"],
    "Ethical hacking": ["ethical hacking", "offensive security", "exploitation", "metasploit", "burp"],
    "Kali Linux": ["kali", "kalilinux", "nmap", "wireshark", "hydra"],
    "Threat modeling": ["threat modeling", "threat model", "stride"],
    "Security scanning": ["security scanning", "vulnerability scanning", "vuln scanning", "container scanning", "scanning"],
    "Secure coding": ["secure coding", "security best practices", "secure development"],
    "Zero trust": ["zero trust", "zero-trust"],
    "Identity & Access": ["iam", "identity and access", "access control", "rbac", "sso", "oidc", "oauth", "mfa", "authentication"],
    "Endpoint security": ["endpoint security", "edr", "antivirus", "windows defender"],
    # Cloud
    "AWS": ["aws", "amazon web services", "ec2", "lambda", "cloudfront", "route53"],
    "EC2": ["ec2", "elastic compute"],
    "S3": ["s3", "s3 buckets", "object storage"],
    "IAM": ["iam", "identity and access", "access control", "principle of least privilege", "least privilege"],
    "Cloud security": ["cloud security", "cloud sec", "guardduty", "security groups", "identity provider", "cloud posture", "cspm"],
    # Development
    "Python": ["python", "fastapi", "django", "flask", "pytest"],
    "FastAPI": ["fastapi", "starlette"],
    "JavaScript": ["javascript", "typescript", "js", "ts/"],
    "React": ["react", "next.js", "nextjs", "frontend framework"],
    "Next.js": ["next.js", "nextjs"],
    "Node.js": ["node.js", "nodejs", "node"],
    "PostgreSQL": ["postgresql", "postgres", "sql", "relational database"],
    "Supabase": ["supabase"],
}

# Category groups used by the scoring weights. Each group aggregates the
# taxonomy categories above (by canonical skill name).
WEIGHT_CATEGORIES: dict[str, list[str]] = {
    "ai_llm": ["LLM applications", "RAG", "Prompt security", "AI security", "LLMOps", "AI red teaming", "Machine Learning"],
    "devsecops": ["Git", "GitHub Actions", "CI/CD", "Docker", "Kubernetes", "Terraform", "Linux", "Trivy", "Bandit", "Secrets detection", "Secure SDLC"],
    "security": ["OWASP", "Application security", "Vulnerability assessment", "Network security", "Ethical hacking", "Kali Linux", "Threat modeling", "Cloud security", "Security scanning", "Secure coding", "Zero trust", "Identity & Access", "Endpoint security"],
    "cloud": ["AWS", "EC2", "S3", "IAM", "Cloud security"],
    "python_development": ["Python", "FastAPI", "JavaScript", "React", "Next.js", "Node.js", "PostgreSQL", "Supabase"],
    "containers": ["Docker", "Kubernetes", "Terraform", "Linux"],
}

# category name used to classify a *candidate's* proficiency claim
CANONICAL_CATEGORY_LABELS: dict[str, str] = {
    "ai_llm": "AI / LLM",
    "devsecops": "DevSecOps",
    "security": "Security",
    "cloud": "Cloud",
    "python_development": "Development",
    "containers": "Containers & Infra",
}

# Keywords that signal remote/international suitability in a job.
REMOTE_HINTS = ["remote", "fully remote", "work from home", "distributed team", "100% remote"]
HYBRID_HINTS = ["hybrid", "remote-friendly", "flexible work"]
ONSITE_HINTS = ["on-site", "onsite", "in-office", "relocation required"]

# Keyword bank for experience-level heuristics.
SENIOR_HINTS = ["senior", "lead", "principal", "staff", "architect", "4+ years", "5+ years", "6+ years", "7+ years", "8+ years"]
MID_HINTS = ["2+ years", "3+ years", "mid", "mid-level", "experienced"]
JUNIOR_HINTS = ["junior", "entry", "graduate", "1+ years", "0-2"]
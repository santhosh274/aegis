export type Severity = "critical" | "high" | "medium" | "low";
export type NodeStatus = "idle" | "running" | "success" | "failed";
export type LogLevel = "INFO" | "WARN" | "ERROR" | "SUCCESS";

export interface Vulnerability {
  id: string;
  severity: Severity;
  plugin: string;
  host: string;
  port: number;
  title: string;
  proof: string;
  remediation: string;
}

export interface PipelineStage {
  id: string;
  name: string;
  modules: string[];
  status: NodeStatus;
  duration: number | null;
  latency: number;
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  source: string;
}

export interface ModuleConfig {
  id: string;
  name: string;
  file: string;
  stage: string;
  enabled: boolean;
  description: string;
}

export const pipelineStages: PipelineStage[] = [
  {
    id: "stage-1",
    name: "Scanners",
    modules: ["nmap_scanner", "service_discovery"],
    status: "success",
    duration: 12400,
    latency: 340,
  },
  {
    id: "stage-2",
    name: "Exploits",
    modules: ["hydra", "metasploit", "sqlmap"],
    status: "running",
    duration: null,
    latency: 890,
  },
  {
    id: "stage-3",
    name: "Corroboration",
    modules: [
      "weak_credentials",
      "privilege_escalation",
      "rce_validation",
      "data_exposure",
    ],
    status: "idle",
    duration: null,
    latency: 0,
  },
  {
    id: "stage-4",
    name: "Post-Exploitation",
    modules: ["persistence", "lateral_movement"],
    status: "idle",
    duration: null,
    latency: 0,
  },
  {
    id: "stage-5",
    name: "Reporting",
    modules: ["generator"],
    status: "idle",
    duration: null,
    latency: 0,
  },
];

export const vulnerabilities: Vulnerability[] = [
  {
    id: "VULN-001",
    severity: "critical",
    plugin: "plugins.exploits.metasploit",
    host: "10.0.0.15",
    port: 445,
    title: "EternalBlue SMB RCE (MS17-010)",
    proof:
      "Metasploit exploit/windows/smb/ms17_010_eternalblue returned meterpreter session on port 445. SYSTEM shell obtained.",
    remediation:
      "Apply MS17-010 patch immediately. Disable SMBv1. Segment legacy hosts on isolated VLAN.",
  },
  {
    id: "VULN-002",
    severity: "critical",
    plugin: "plugins.corroboration.rce_validation",
    host: "10.0.0.22",
    port: 8080,
    title: "Apache Struts RCE via OGNL Injection",
    proof:
      "Nonce token 'aegis-9f3c' confirmed in /tmp/proof.txt after crafted Content-Type header injection. RCE validated.",
    remediation:
      "Upgrade Apache Struts to 2.5.30+. Deploy WAF rule to block OGNL expression payloads in Content-Type headers.",
  },
  {
    id: "VULN-003",
    severity: "high",
    plugin: "plugins.corroboration.weak_credentials",
    host: "10.0.0.8",
    port: 22,
    title: "SSH Weak Credential — admin:admin",
    proof:
      "Fresh login with admin:admin succeeded. Session established. /etc/shadow readable without sudo.",
    remediation:
      "Enforce password complexity policy. Implement key-based auth. Deploy fail2ban for brute-force protection.",
  },
  {
    id: "VULN-004",
    severity: "high",
    plugin: "plugins.exploits.hydra",
    host: "10.0.0.12",
    port: 3306,
    title: "MySQL Default Root Password",
    proof:
      "Hydra brute-force completed in 4.2s. Root:root login successful. Full database dump accessible.",
    remediation:
      "Change MySQL root password. Bind to localhost only. Remove anonymous MySQL accounts.",
  },
  {
    id: "VULN-005",
    severity: "medium",
    plugin: "plugins.corroboration.privilege_escalation",
    host: "10.0.0.5",
    port: 80,
    title: "Sudo misconfiguration — NOPASSWD",
    proof:
      "User 'webdev' has NOPASSWD sudo for /usr/bin/vim. Container breakout to host shell confirmed.",
    remediation:
      "Remove NOPASSWD from sudoers. Restrict vim to specific paths. Audit all sudo entries quarterly.",
  },
  {
    id: "VULN-006",
    severity: "medium",
    plugin: "plugins.corroboration.data_exposure",
    host: "10.0.0.18",
    port: 443,
    title: "TLS Certificate Exposes Internal Hostnames",
    proof:
      "Certificate SAN contains: internal-api.corp.local, db-primary.corp.local, staging-01.corp.local",
    remediation:
      "Regenerate certificate with minimal SAN. Remove internal hostnames from public-facing certificates.",
  },
  {
    id: "VULN-007",
    severity: "low",
    plugin: "plugins.scanners.nmap_scanner",
    host: "10.0.0.3",
    port: 80,
    title: "HTTP Server Header Disclosure",
    proof:
      "Server: Apache/2.4.41 (Ubuntu). X-Powered-By: PHP/7.4.3. Version info aids targeted exploit selection.",
    remediation:
      "Suppress Server and X-Powered-By headers. Use security-focused reverse proxy configuration.",
  },
];

export const logEntries: LogEntry[] = [
  {
    timestamp: "14:32:01.003",
    level: "INFO",
    source: "run_pipeline",
    message: "Pipeline initialized. Target scope: 10.0.0.0/24 (lab mode)",
  },
  {
    timestamp: "14:32:01.045",
    level: "INFO",
    source: "core.executor",
    message: "Scope validation passed. Lab mode: ENABLED",
  },
  {
    timestamp: "14:32:02.112",
    level: "INFO",
    source: "nmap_scanner",
    message: "Starting nmap SYN scan on 10.0.0.0/24 (top 1000 ports)",
  },
  {
    timestamp: "14:32:08.441",
    level: "SUCCESS",
    source: "nmap_scanner",
    message: "Scan complete. 47 hosts up, 189 open ports discovered",
  },
  {
    timestamp: "14:32:09.002",
    level: "INFO",
    source: "service_discovery",
    message: "Service fingerprinting 189 endpoints...",
  },
  {
    timestamp: "14:32:14.783",
    level: "SUCCESS",
    source: "service_discovery",
    message: "Service enumeration complete. 12 unique services identified",
  },
  {
    timestamp: "14:32:15.101",
    level: "INFO",
    source: "core.planner",
    message: "Utility ranking: hydra-ssh (U=0.82) > metasploit-smb (U=0.79) > sqlmap-web (U=0.71)",
  },
  {
    timestamp: "14:32:15.443",
    level: "INFO",
    source: "hydra",
    message: "Brute-force SSH on 10.0.0.8:22 (wordlist: rockyou-top1000)",
  },
  {
    timestamp: "14:32:19.667",
    level: "WARN",
    source: "hydra",
    message: "Weak credential found: admin:admin on 10.0.0.8:22",
  },
  {
    timestamp: "14:32:20.012",
    level: "INFO",
    source: "core.executor",
    message: "Dispatching metasploit module: exploit/windows/smb/ms17_010_eternalblue",
  },
  {
    timestamp: "14:32:28.891",
    level: "ERROR",
    source: "metasploit",
    message: "MSF RPC connection timeout. Retrying (attempt 2/3)...",
  },
  {
    timestamp: "14:32:33.224",
    level: "SUCCESS",
    source: "metasploit",
    message: "Meterpreter session opened on 10.0.0.15:445 -> SYSTEM",
  },
  {
    timestamp: "14:32:34.001",
    level: "INFO",
    source: "sqlmap",
    message: "Testing SQLi on http://10.0.0.22:8080/api/users?id=1",
  },
  {
    timestamp: "14:32:41.556",
    level: "WARN",
    source: "sqlmap",
    message: "Union-based injection confirmed. Extracting database schema...",
  },
  {
    timestamp: "14:32:48.903",
    level: "SUCCESS",
    source: "sqlmap",
    message: "SQLi validated. Database: production_db, 23 tables, 142K rows",
  },
  {
    timestamp: "14:32:49.100",
    level: "INFO",
    source: "devils_advocate",
    message: "Corroborating 4 findings via independent validation...",
  },
  {
    timestamp: "14:32:52.441",
    level: "SUCCESS",
    source: "rce_validation",
    message: "RCE nonce aegis-9f3c confirmed on 10.0.0.22:8080",
  },
  {
    timestamp: "14:32:55.112",
    level: "INFO",
    source: "confidence_engine",
    message: "Confidence assessment: 2 CONFIRMED, 1 SUSPECTED, 1 NEEDS_HUMAN_REVIEW",
  },
];

export const modules: ModuleConfig[] = [
  {
    id: "nmap",
    name: "Nmap Scanner",
    file: "nmap_scanner.py",
    stage: "Service Scanning",
    enabled: true,
    description: "SYN/ACK port scanning with OS fingerprinting",
  },
  {
    id: "svc-disc",
    name: "Service Discovery",
    file: "service_discovery.py",
    stage: "Service Scanning",
    enabled: true,
    description: "Service version detection and banner grabbing",
  },
  {
    id: "hydra",
    name: "Hydra",
    file: "hydra.py",
    stage: "Initial Exploitation",
    enabled: true,
    description: "Credential brute-force for SSH, FTP, HTTP",
  },
  {
    id: "msf",
    name: "Metasploit",
    file: "metasploit.py",
    stage: "Initial Exploitation",
    enabled: true,
    description: "MSF RPC exploit module dispatcher",
  },
  {
    id: "sqlmap",
    name: "SQLMap",
    file: "sqlmap.py",
    stage: "Initial Exploitation",
    enabled: true,
    description: "Automated SQL injection detection & exploitation",
  },
  {
    id: "weak-creds",
    name: "Weak Credentials",
    file: "weak_credentials.py",
    stage: "Corroboration",
    enabled: true,
    description: "Fresh-session credential validation",
  },
  {
    id: "privesc",
    name: "Privilege Escalation",
    file: "privilege_escalation.py",
    stage: "Corroboration",
    enabled: false,
    description: "Role/sudo misconfiguration corroboration",
  },
  {
    id: "rce-val",
    name: "RCE Validation",
    file: "rce_validation.py",
    stage: "Corroboration",
    enabled: true,
    description: "Benign nonce predicate for RCE confirmation",
  },
  {
    id: "data-exp",
    name: "Data Exposure",
    file: "data_exposure.py",
    stage: "Corroboration",
    enabled: true,
    description: "Schema-match data leakage corroboration",
  },
  {
    id: "persist",
    name: "Persistence",
    file: "persistence.py",
    stage: "Post-Exploitation",
    enabled: false,
    description: "Backdoor installation & persistence mechanisms",
  },
  {
    id: "lateral",
    name: "Lateral Movement",
    file: "lateral_movement.py",
    stage: "Post-Exploitation",
    enabled: false,
    description: "Network pivot & credential reuse propagation",
  },
  {
    id: "report",
    name: "Report Generator",
    file: "generator.py",
    stage: "Report Generation",
    enabled: true,
    description: "Markdown/HTML vulnerability report renderer",
  },
];

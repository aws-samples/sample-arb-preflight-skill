# AWS Landing Zone Baseline

Status: `[DEFAULT — CONFIRM]` — owned by Cloud Platform Engineering.

Mandatory platform constraints for any workload deployed into the organisation's AWS
estate. Clauses are referenced by ID from `rubric/platform.md`. Replace the defaults
with your actual control tower / organisation design; the shape matters more than the
specific values.

## Accounts and organisation

| ID | Clause | Default |
|---|---|---|
| `LZB-ACC-01` | Every workload runs in dedicated accounts per environment. No shared prod/non-prod account. | `[DEFAULT — CONFIRM]` |
| `LZB-ACC-02` | Accounts are placed in the OU matching data classification and environment. Production sits under the `Workloads/Prod` OU. | `[DEFAULT — CONFIRM]` |
| `LZB-ACC-03` | Accounts are vended only through the account factory, with cost centre, data classification, criticality tier and owner captured at vend time. | `[DEFAULT — CONFIRM]` |
| `LZB-ACC-04` | Service control policies applying to the target OU are not to be bypassed. A design that requires an SCP exception needs platform sign-off before the ARB, not after. | `[DEFAULT — CONFIRM]` |
| `LZB-ACC-05` | Root user credentials unused, hardware MFA enrolled, no root access keys. | `[DEFAULT — CONFIRM]` |

`[TBD]` — paste the effective SCP list and what each denies. This is what lets the
reviewer catch a design that cannot deploy as drawn.

## Regions and residency

| ID | Clause | Default |
|---|---|---|
| `LZB-REG-01` | Approved regions only. Primary `[TBD]`, secondary `[TBD]`. All other regions denied by SCP. | `[TBD]` |
| `LZB-REG-02` | Data may not leave the jurisdiction of the owning legal entity without a documented transfer basis. Includes backups, logs, telemetry, and support tooling. | `[DEFAULT — CONFIRM]` |
| `LZB-REG-03` | Global services with a control plane outside the approved regions (IAM, CloudFront, Route 53, some AI/ML endpoints) require explicit residency assessment. | `[DEFAULT — CONFIRM]` |
| `LZB-REG-04` | Cross-region replication targets must be within the approved secondary region and the same jurisdiction unless a transfer basis exists. | `[DEFAULT — CONFIRM]` |

## Network

| ID | Clause | Default |
|---|---|---|
| `LZB-NET-01` | Workload VPCs attach to the central transit gateway. No workload-to-workload VPC peering outside the hub. | `[DEFAULT — CONFIRM]` |
| `LZB-NET-02` | No internet gateway in a workload VPC. All egress routes through the central inspection VPC. | `[DEFAULT — CONFIRM]` |
| `LZB-NET-03` | All ingress from the internet terminates at the central edge (WAF, DDoS protection, TLS termination) before reaching a workload. No workload-owned public ALB or public API endpoint. | `[DEFAULT — CONFIRM]` |
| `LZB-NET-04` | Compute and data resources sit in private subnets with no public IP. | `[DEFAULT — CONFIRM]` |
| `LZB-NET-05` | AWS service access uses VPC endpoints or PrivateLink rather than public service endpoints. | `[DEFAULT — CONFIRM]` |
| `LZB-NET-06` | Third-party and partner connectivity terminates in the shared partner-connectivity zone, never directly into a workload VPC. | `[DEFAULT — CONFIRM]` |
| `LZB-NET-07` | CIDR ranges are allocated by the central IPAM. No self-assigned or overlapping ranges. | `[DEFAULT — CONFIRM]` |
| `LZB-NET-08` | DNS resolves through the central resolver. Private hosted zones are registered centrally. | `[DEFAULT — CONFIRM]` |
| `LZB-NET-09` | Security groups reference other security groups or prefix lists, not wide CIDRs. `0.0.0.0/0` inbound is prohibited. | `[DEFAULT — CONFIRM]` |
| `LZB-NET-10` | On-premises connectivity via the existing Direct Connect / VPN hub only. | `[DEFAULT — CONFIRM]` |

`[TBD]` — attach the reference network topology diagram so the reviewer can compare the
submitted deployment view against it.

## Encryption and keys

| ID | Clause | Default |
|---|---|---|
| `LZB-KMS-01` | Encryption at rest is mandatory for every data store, using customer-managed KMS keys. AWS-managed keys are not sufficient for confidential or restricted data. | `[DEFAULT — CONFIRM]` |
| `LZB-KMS-02` | Key policies grant use, not administration, to the workload. Key administration stays with the platform or security function. Separation is a segregation-of-duties control. | `[DEFAULT — CONFIRM]` |
| `LZB-KMS-03` | Automatic key rotation enabled. | `[DEFAULT — CONFIRM]` |
| `LZB-KMS-04` | TLS 1.2 minimum in transit, 1.3 preferred, including inside the VPC and between internal services. | `[DEFAULT — CONFIRM]` |
| `LZB-KMS-05` | Certificates issued from the organisation's PKI or ACM with automated renewal. No self-signed or manually renewed certificates. | `[DEFAULT — CONFIRM]` |
| `LZB-KMS-06` | Restricted data classes requiring key custody outside AWS use CloudHSM or external key store. | `[TBD]` |

## Guardrails and logging

| ID | Clause | Default |
|---|---|---|
| `LZB-GRD-01` | Platform guardrails are not to be disabled: CloudTrail (organisation trail), AWS Config, GuardDuty, Security Hub, IAM Access Analyzer, EBS/S3 default encryption, S3 public access block. | `[DEFAULT — CONFIRM]` |
| `LZB-GRD-02` | Logs ship to the central log archive account. The workload account cannot delete them. Retention `[TBD]`, minimum 12 months hot for tier 1 and 2. | `[DEFAULT — CONFIRM]` |
| `LZB-GRD-03` | Security findings route to the SOC. New detection requirements must be agreed with the SOC before go-live, not discovered after. | `[DEFAULT — CONFIRM]` |
| `LZB-GRD-04` | Mandatory tags on every resource: `Owner`, `CostCentre`, `Application`, `Environment`, `DataClassification`, `CriticalityTier`. | `[DEFAULT — CONFIRM]` |

## Provisioning and change

| ID | Clause | Default |
|---|---|---|
| `LZB-PRV-01` | All infrastructure is provisioned as code through the approved pipeline. Console changes in production are limited to break-glass, and are logged and reviewed. | `[DEFAULT — CONFIRM]` |
| `LZB-PRV-02` | No human standing access to production. Access is time-bound and approved, through the privileged access path. | `[DEFAULT — CONFIRM]` |
| `LZB-PRV-03` | Pipeline deploys via a role in the target account. No long-lived IAM user access keys anywhere, including for third-party tooling. | `[DEFAULT — CONFIRM]` |
| `LZB-PRV-04` | Break-glass access is pre-approved, alerting, and reviewed after every use. | `[DEFAULT — CONFIRM]` |
| `LZB-PRV-05` | Container images come from the organisation's central registry, built from approved base images, scanned before promotion. | `[DEFAULT — CONFIRM]` |

## Notes for the reviewer

- These clauses describe the platform the workload lands on. A design silent on them is
  usually assumed to inherit them, which is exactly the assumption to test: ask whether
  the design *depends* on an exception. Silence plus a dependency on an exception is the
  dangerous combination, because it surfaces during deployment, after the board approved.
- The most expensive late-discovered breaches are `LZB-NET-02`, `LZB-NET-03` and
  `LZB-REG-01`. Network topology and region choice are close to unchangeable once built.

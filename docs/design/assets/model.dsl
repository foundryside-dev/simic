// Simic architecture model — Structurizr DSL.
//
// This file is a TRANSCRIPTION of the canonical architecture, not a second
// architecture. Sources: docs/design/04-architecture.md (§7.1 logical
// architecture, §7.5 control hierarchy, §10 end-to-end flow) and the domain
// chapters under docs/design/domains/. If this model and a chapter disagree,
// the chapter wins and this file is wrong — fix it here.
//
// tools/wiki/stage.py enforces one direction of that rule mechanically: the
// build fails if the container identifiers below stop matching the canonical
// domain set (docs/design/domains/*.md).
//
// Compiled to SVGs by tools/wiki/build.sh (Structurizr CLI -> PlantUML); the
// wiki surfaces them on a generated reference page. Never hand-edit the SVGs.

workspace "Simic" "Counterfactual Generative Morphogenesis — the fourteen-domain architecture (HLD v4.1, Namespec 1.0)" {

    !impliedRelationships false

    model {
        operator = person "Operator" "Reads the account through Oona; owns escalations. Never a control-path participant."

        dataStream = softwareSystem "Task and Data Stream" "The host's training task: minibatches, splits and evaluation data." "External"

        simic = softwareSystem "Simic" "Lifecycle-driven neural training system: growth is generated from live host state, QA-tested counterfactually, adjudicated against no-op, embodied reversibly under warrant, and eventually retired." {

            // ---- Infrastructure (prepositions) ----------------------------
            leyline = container "Leyline" "Contracts, schema versions, grammar profiles, compatibility, policy record formats and ordering invariants. Imports nothing from subsystems." "src/simic/leyline/" "Infrastructure" {
                resolver = component "Request Resolver" "Pure deterministic contract assembly: (GrowthIntent, StrategicEnvelope, RegionContract, GrammarProfile) -> one canonical GrowthRequest. Fails closed on incompatibility. Not a fifteenth agent: no diagnosis, no learned policy."
            }
            tolaria = container "Tolaria" "The single training/execution substrate: host training, snapshots, deterministic replay, matched common-future branches and rollback. Applies no candidate utility weights; issues no verdicts." "src/simic/tolaria/" "Infrastructure"
            sarpadia = container "Sarpadia" "Append-only history: lineages, reference ancestry, outcomes, failures, rejected pools, no-op wins and split-safe datasets. Never winners-only." "src/simic/sarpadia/" "Infrastructure"

            // ---- Agents (verbs) -------------------------------------------
            nissa = container "Nissa" "Observes and reports. Publishes one canonical ablated observation identity directly to its consumers. Never emits should_grow." "src/simic/nissa/" "Agent"
            tamiyo = container "Tamiyo" "Plans. Strategic budgets, regional priorities, exploration quotas, cooldowns and long-horizon risk. Never issues local transitions." "src/simic/tamiyo/" "Agent"
            narset = container "Narset" "Commissions and acts. Tactical commissioning and pre-commit lifecycle actions only. Sends the assignment brief, never the photograph." "src/simic/narset/" "Agent"
            momir = container "Momir" "Designs. Raw candidate topology, parameters, mutation and recombination. No timing, approval, testing or admission authority." "src/simic/momir/" "Agent" {
                momirEvidence = component "Evidence Intake" "Consumes Nissa's canonical diagnostic evidence (TelemetryEnvelope) directly, with preserved provenance."
                momirRequest = component "Request Intake" "Consumes the independently resolved GrowthRequest as operational constraints; rejects calls whose observation, snapshot, region or compatibility identifiers do not reconcile."
                momirAncestry = component "Ancestry Channel" "Optional Sarpadian ancestry or retrieval context through a separate provenance-bearing channel. Output must remain valid when ancestry is null."
                momirGenerator = component "Candidate Generator" "Designs raw candidate graphs and birth parameters: reference reconstruction, bounded mutation, lineage recombination, de novo; deterministic or stochastic best-of-K."
                momirAssembler = component "Proposal Assembler" "Binds provenance, generation uncertainty and measured spend to every proposal in the batch."
            }
            elesh = container "Elesh" "Conforms. Static verification, canonicalisation, semantic hashing and structural legality. Simplifies only where semantic equivalence is established." "src/simic/elesh/" "Agent"
            tezzeret = container "Tezzeret" "Compiles. Lowering, kernel selection, fusion, memory planning. Preserves semantics; compilation success implies neither runtime validity nor admission." "src/simic/tezzeret/" "Agent"
            urabrask = container "Urabrask" "Tests the compiled result in Tolaria. Certifies evidence; never issues verdicts, warrants or lifecycle tokens." "src/simic/urabrask/" "Agent" {
                uraPlanner = component "Test Planner" "Constructs blinded, versioned TestPlan records. Mandatory tests cannot be weakened after viewing a candidate's result."
                uraConformance = component "Conformance Verifier" "Verifies the compiled artefact against the canonical specification at runtime: reference outputs, gradient agreement, zero-influence behaviour, numerical stability."
                uraBranch = component "Branch Measurement" "Requests deterministic replay and matched common-future branches in Tolaria; measures immediate and multi-horizon trajectories, integration shock, latency and spend."
                uraCertifier = component "Evidence Certifier" "Quantifies uncertainty and evidence completeness, classifies hard defects and soft warnings, and signs the QualityReport — measurements, never a verdict."
            }
            augustin = container "Augustin" "Judges the resulting evidence under Leyline. Provider-blind, lexicographic adjudication against mandatory no-op; issues warrants." "src/simic/augustin/" "Agent" {
                augEligibility = component "Eligibility Gate" "Stage 1 — hard eligibility: identity, compilation conformance, runtime and gradient checks, determinism, evidence completeness for the assurance class, budget."
                augTailVeto = component "Tail-Risk Veto" "Stage 2 — vetoes any candidate whose intervention-outcome tail estimate breaches the threshold. Adjudicated before any utility comparison; never tradeable against measured benefit (INV-45). No-op never faces it."
                augUtility = component "Utility Competition" "Stage 3 — u_admit ranks survivors against mandatory no-op, whose policy utility is exactly zero. Returns ADMIT, NO_OP, REJECT, DEFER or REQUIRE_RETEST."
                augTenancy = component "Tenancy Adjudicator" "Continued-tenancy adjudication: u_retain under a versioned hysteresis band strictly below the admission threshold (ADR-0005, INV-33)."
                augWarrants = component "Warrant Issuer" "Issues admission and maintenance warrants, each bound to a specific evidence digest, semantic hash, envelope and policy version."
            }
            kasmina = container "Kasmina" "Embodies the admitted growth. Host model, insertion regions, slots, gradient routing, maturation, blending and physical lifecycle — only under a valid warrant." "src/simic/kasmina/" "Agent"
            emrakul = container "Emrakul" "Destroys what no longer earns continued tenancy. Post-commit sedation, decay, consolidation and lysis under maintenance warrants. Post-commit only." "src/simic/emrakul/" "Agent"
            oona = container "Oona" "Reveals the account. Event projections, flight recorder, operator surfaces and audit bundles. Read-only: disconnecting Oona cannot change training." "src/simic/oona/" "Agent"
        }

        // ==== System-level relationships (context view only) ===============
        // Implied relationships are off, so these must be stated explicitly;
        // they never render in container or component views.
        dataStream -> simic "Supplies the task and data stream"
        operator -> simic "Reads the account through Oona; owns escalations"

        // ==== Container-level relationships (transcribed from §7.1) ========

        // Training substrate and observation
        dataStream -> tolaria "Supplies the task and data stream"
        tolaria -> kasmina "Executes host forward/backward passes and optimiser steps"
        kasmina -> nissa "Exposes host state for canonical ablated diagnostic observation"

        // Direct evidence publication (the newsroom rule)
        nissa -> tamiyo "Permitted coarse summary"
        nissa -> narset "TelemetryEnvelope O (same observation identity)"
        nissa -> momir "TelemetryEnvelope O (same observation identity)"

        // Strategic loop and request resolution
        tamiyo -> narset "StrategicEnvelope"
        narset -> leyline "GrowthIntent — assignment brief only"
        tamiyo -> leyline "Authorised StrategicEnvelope"
        kasmina -> leyline "RegionContract"
        leyline -> momir "Resolved canonical GrowthRequest"

        // Core growth flow
        sarpadia -> momir "Optional precedents / BootstrapAncestryContext (bootstrap curriculum)"
        momir -> elesh "RawGrowthGraph"
        elesh -> tezzeret "CanonicalGrowthSpec"
        tezzeret -> urabrask "ExecutableGrowthArtifact"

        // QA and adjudication
        urabrask -> tolaria "TestPlan: candidate branches + controls + mandatory no-op"
        tolaria -> urabrask "BranchResults and runtime evidence"
        urabrask -> augustin "QualityReport (blinded)"
        tamiyo -> augustin "Strategic limits"
        leyline -> augustin "Resolved request context"
        augustin -> narset "AdmissionDecision or NO_OP"

        // Embodiment and maintenance
        narset -> kasmina "LifecycleCommand plus admission warrant"
        kasmina -> emrakul "Ownership of committed growth transfers at COMMIT"
        emrakul -> urabrask "Maintenance QA request"
        augustin -> emrakul "MaintenanceDecision plus maintenance warrant"
        emrakul -> kasmina "Sedate / decay / lyse command under maintenance warrant"

        // Archival ingestion (append-only, failures included)
        nissa -> sarpadia "Append-only observation record"
        leyline -> sarpadia "Resolved request record"
        momir -> sarpadia "Raw candidates, lineages and rejected pools"
        elesh -> sarpadia "Structural reports, including failures"
        tezzeret -> sarpadia "Compilation manifests"
        tolaria -> sarpadia "Snapshots and branch traces"
        urabrask -> sarpadia "Test plans and quality reports"
        augustin -> sarpadia "Decisions, including no-op wins and abstentions"
        kasmina -> sarpadia "Lifecycle traces"
        emrakul -> sarpadia "Maintenance actions"

        // Witness projections (read-only surface)
        nissa -> oona "Event projection"
        tamiyo -> oona "Event projection"
        narset -> oona "Event projection"
        momir -> oona "Event projection"
        elesh -> oona "Event projection"
        tezzeret -> oona "Event projection"
        tolaria -> oona "Event projection"
        urabrask -> oona "Event projection"
        augustin -> oona "Event projection"
        kasmina -> oona "Event projection"
        sarpadia -> oona "Event projection"
        emrakul -> oona "Event projection"
        operator -> oona "Reads the account"

        // ==== Component-level relationships =================================
        // (implied relationships are OFF, so these never duplicate the
        //  container-level edges above; each view renders only its own level)

        // Request resolution (Leyline)
        narset -> resolver "GrowthIntent"
        tamiyo -> resolver "StrategicEnvelope"
        kasmina -> resolver "RegionContract"
        resolver -> momir "Canonical GrowthRequest"
        resolver -> augustin "Resolved request context"

        // Momir internals
        nissa -> momirEvidence "TelemetryEnvelope O"
        leyline -> momirRequest "Resolved GrowthRequest"
        sarpadia -> momirAncestry "BootstrapAncestryContext | null; ordinary retrieval where enabled"
        momirEvidence -> momirGenerator "Diagnostic evidence"
        momirRequest -> momirGenerator "Operational constraints"
        momirAncestry -> momirGenerator "Ancestry / retrieval context"
        momirGenerator -> momirAssembler "Raw candidate graphs and birth parameters"
        momirAssembler -> elesh "RawGrowthGraph batch with provenance"

        // Urabrask internals
        tezzeret -> uraConformance "ExecutableGrowthArtifact"
        uraPlanner -> tolaria "Blinded TestPlan"
        tolaria -> uraBranch "BranchResults and runtime evidence"
        uraConformance -> uraCertifier "Conformance measurements and defects"
        uraBranch -> uraCertifier "Branch measurements"
        uraPlanner -> uraCertifier "Test-plan version and evidence digest"
        uraCertifier -> augustin "Signed QualityReport (blinded)"

        // Augustin internals
        urabrask -> augEligibility "QualityReport (blinded)"
        tamiyo -> augEligibility "Active StrategicEnvelope"
        leyline -> augEligibility "Resolved request context"
        augEligibility -> augTailVeto "Eligible candidates"
        augTailVeto -> augUtility "Veto survivors"
        augUtility -> augWarrants "ADMIT / NO_OP / REJECT / DEFER / REQUIRE_RETEST"
        augWarrants -> narset "AdmissionDecision plus admission warrant"
        urabrask -> augTenancy "Maintenance QualityReport (blinded)"
        augTenancy -> augWarrants "MaintenanceDecision"
        augWarrants -> emrakul "MaintenanceDecision plus maintenance warrant"
    }

    views {
        systemContext simic "SimicContext" "Simic in context: the task it trains against and the operator who reads the account." {
            include *
            autoLayout tb
        }

        container simic "SimicContainers" "The full fourteen-domain map, including archival and witness edges — the honest hairball. The focused views below are subsets." {
            include *
            autoLayout tb
        }

        container simic "CoreGrowthFlow" "Observation to embodiment: the core growth loop without archival and witness noise." {
            include nissa tamiyo narset leyline momir elesh tezzeret urabrask augustin kasmina tolaria sarpadia
            exclude "* -> sarpadia"
            autoLayout tb
        }

        container simic "QaAdjudication" "QA and adjudication: Urabrask certifies evidence from matched branches; Augustin judges it provider-blind against no-op." {
            include tezzeret urabrask tolaria augustin tamiyo leyline narset
            exclude "tamiyo -> narset"
            exclude "narset -> leyline"
            exclude "tamiyo -> leyline"
            exclude "* -> sarpadia"
            autoLayout tb
        }

        container simic "MaintenanceLoop" "Post-commit tenancy: Emrakul requests review, Urabrask certifies counterfactual evidence, Augustin decides, Emrakul executes through Kasmina." {
            include emrakul urabrask augustin kasmina tolaria
            exclude "* -> sarpadia"
            autoLayout tb
        }

        container simic "ArchiveIngestion" "Sarpadia archival ingestion: every producer appends, failures and no-op wins included; nothing is winners-only." {
            include nissa leyline momir elesh tezzeret tolaria urabrask augustin kasmina emrakul sarpadia
            exclude "* -> *"
            include "* -> sarpadia"
            autoLayout tb
        }

        component leyline "RequestResolution" "Deterministic request resolution: four immutable records in, one canonical GrowthRequest out. No diagnosis, no learned policy." {
            include *
            autoLayout tb
        }

        component momir "MomirComponents" "Momir internals: independent evidence, constraint and ancestry intakes feeding the generator; provenance bound to every proposal." {
            include *
            autoLayout tb
        }

        component urabrask "UrabraskComponents" "Urabrask internals: blinded planning, runtime conformance, branch measurement, and certification without verdicts." {
            include *
            autoLayout tb
        }

        component augustin "AugustinComponents" "Augustin internals: the lexicographic admission order (ADR-0004) — eligibility, then the untradeable tail-risk veto, then utility against no-op." {
            include *
            autoLayout tb
        }

        styles {
            element "Infrastructure" {
                background #115e59
                color #ffffff
                shape RoundedBox
            }
            element "Agent" {
                background #0d9488
                color #ffffff
            }
            element "External" {
                background #64748b
                color #ffffff
            }
            element "Component" {
                background #99f6e4
                color #042f2e
            }
            element "Person" {
                background #334155
                color #ffffff
                shape Person
            }
        }
    }
}

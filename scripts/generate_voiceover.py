"""
GraphSRE: Kokoro TTS Audio Voiceover Generator
File: scripts/generate_voiceover.py

Generates professional, high-fidelity AI narration audio tracks for the
FalkorDB + WeMakeDevs GraphHacks Hackathon demonstration video.
"""
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import numpy as np
import soundfile as sf
from kokoro import KPipeline

AUDIO_DIR = os.path.join("demo_video", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# 7 Complete Script Sections
SECTIONS = [
    {
        "id": "01_hook_and_problem",
        "title": "Act 0: The 3:00 AM Outage & Why Vector RAG Fails",
        "visual_cue": "Open with high-stakes Sev-1 outage alert storm. Cut to architecture diagram contrasting Vector RAG / conversational rings with FalkorDB Blackboard.",
        "text": (
            "At three AM, a Tier 1 payment microservice collapses under cascading HTTP 504 errors. "
            "Within ninety seconds, hundreds of dependent alerts flood the on-call engineer. "
            "Modern AI solutions attempt to solve this with Vector RAG and conversational agent loops. "
            "But in distributed systems, this fails deterministically. "
            "Metric vector spaces are symmetric and blind to directed causality. "
            "And multi-agent chat loops suffer from quadratic token bloat and hallucination cascades. "
            "Meet GraphSRE: an autonomous SRE and code intelligence platform powered by FalkorDB."
        )
    },
    {
        "id": "02_blackboard_architecture",
        "title": "Act 1A: The FalkorDB Central ACID Blackboard",
        "visual_cue": "Show Next.js War Room at clean baseline. Pan over healthy microservices in Cytoscape canvas and zoom into docked Cypher Console showing GraphBLAS badges.",
        "text": (
            "GraphSRE discards conversational text passing in favor of a Central ACID Blackboard. "
            "FalkorDB maintains an immutable, persistent property graph unifying runtime telemetry, "
            "microservice topologies, Abstract Syntax Trees, and Git commit history into a single knowledge base. "
            "Notice our healthy baseline monitoring five microservices across three tiers. "
            "At the bottom of the war room, our docked Cypher Console streams live OpenCypher queries "
            "executed by FalkorDB's GraphBLAS linear algebra engine in under one millisecond."
        )
    },
    {
        "id": "03_act2_chaos_and_rca",
        "title": "Act 2: Chaos Fault Injection & Cross-Layer Causal Walk",
        "visual_cue": "Click [Inject Chaos Fault]. PaymentService pulses red. Causal tracer lights up in glowing amber across 5 layers down to commit c3d9a107 (Alice Chen).",
        "text": (
            "Now, let's inject a real-world chaos fault: an unbounded socket read timeout in our PaymentService. "
            "Instantly, cascading HTTP 504 alerts fire. "
            "The Triage Agent runs Community Detection via Label Propagation in FalkorDB, "
            "clustering them into a single incident and calculating a 3-hop blast radius across upstream callers. "
            "Next, our Root Cause Analysis Agent traverses five heterogeneous graph layers: "
            "from the alerted service, through endpoint /charge, into AST function call_stripe_webhook, "
            "and terminates directly at commit c3d9a107 authored by Alice Chen. "
            "If an agent hypothesizes a cause with no directed topological path in FalkorDB, "
            "it is mathematically rejected as a hallucination."
        )
    },
    {
        "id": "04_act3_quorum_and_sandbox",
        "title": "Act 3: Multi-Agent Quorum & Sub-15ms GRAPH.COPY Sandboxing",
        "visual_cue": "Focus on Quorum Consensus Meter reaching 0.88. Click [Fork Sandbox Sim], then click [1-Click Approve Canary Revert]. Node returns to healthy green.",
        "text": (
            "Multi-agent coordination occurs directly on the graph. "
            "The Memory Agent queries FalkorDB's embedded HNSW vector index using vecf32, "
            "retrieving a historical postmortem with point nine four cosine similarity. "
            "Agents cast weighted votes persisted to the graph, reaching a Verified Composite Confidence of point eight eight, "
            "exceeding our strict point seven five anti-hallucination threshold. "
            "Before mutating production, the Remediation Agent calls FalkorDB's GRAPH.COPY command, "
            "cloning the production graph in under eight milliseconds into an isolated sandbox to verify counterfactual blast radius safety. "
            "With the canary simulation passed, a single click approves the revert, resolving the Sev-1 incident in 78 seconds."
        )
    },
    {
        "id": "05_act4_shortcut_net",
        "title": "Act 4: Closed-Loop O(1) Shortcut Net with Bayesian Dynamics",
        "visual_cue": "Show radiant emerald shortcut edge appearing on canvas. Click [Test Repeat Outage]. Instant 0.18s resolution banner pops up.",
        "text": (
            "Upon resolution, GraphSRE compiles continuous organizational memory. "
            "Instead of burying postmortems in static wikis, it synthesizes an emerald O(1) shortcut edge "
            "directly from the service to the culprit root cause function. "
            "When the identical fault recurs in the future, the triage engine queries the shortcut edge first, "
            "bypassing multi-hop diagnosis entirely and resolving the incident in just point one eight seconds—"
            "a ninety-nine point eight percent reduction in MTTR. "
            "These shortcut edges are living entities: they strengthen with Bayesian reinforcement on repeat hits, "
            "decay with a 30-day exponential half-life, and automatically invalidate by 70 percent whenever Git code modifications occur."
        )
    },
    {
        "id": "06_act5_cicd_blast_gate",
        "title": "Act 5: Shift-Left CI/CD Blast Gate",
        "visual_cue": "Navigate to /cicd-blast-gate. Select PR #412 (Blocked, SRI 0.88). Switch to PR #413 (Passed, SRI 0.12). Show live interactive diff editor.",
        "text": (
            "GraphSRE also shifts left into the developer lifecycle. "
            "On the CI/CD Blast Gate page, developers evaluate pull requests before merging. "
            "Here, Pull Request 412 removes a socket timeout. "
            "The AST Code Ingestion Engine parses the patch, traverses the 4-hop call hierarchy in FalkorDB, "
            "calculates a Structural Risk Index of point eight eight, and blocks the merge by policy. "
            "Conversely, Pull Request 413 introduces an adaptive circuit breaker; "
            "the Blast Gate evaluates the safe diff and passes it with a risk score of point one two."
        )
    },
    {
        "id": "07_conclusion_and_vision",
        "title": "Act 6: The Unfair Advantage of FalkorDB",
        "visual_cue": "Show full platform architecture, live Cypher queries streaming in docked console, and multi-track hackathon summary.",
        "text": (
            "By uniting GraphBLAS sparse matrix traversals, embedded HNSW vector memory, "
            "zero-cost GRAPH.COPY sandboxing, and closed-loop shortcut learning, "
            "GraphSRE transforms reactive firefighting into deterministic, autonomous infrastructure intelligence. "
            "Connected data, institutional memory, and a permanent company brain. "
            "This is GraphSRE, powered by FalkorDB."
        )
    }
]


def generate_audio_tracks(voice: str = "af_heart", speed: float = 1.05):
    print("=" * 70)
    print(" [KOKORO TTS] GRAPHSRE NARRATION GENERATOR")
    print(f" Voice: {voice} | Speed: {speed}x | Lang: American English")
    print(f" Target Directory: {AUDIO_DIR}")
    print("=" * 70)

    print("\nLoading Kokoro 82M Pipeline...")
    start_load = time.time()
    pipeline = KPipeline(lang_code="a")
    print(f"[OK] Pipeline loaded in {time.time() - start_load:.2f}s\n")

    generated_tracks = []
    master_audio_chunks = []
    sample_rate = 24000
    pause_between_sections = np.zeros(int(sample_rate * 0.8), dtype=np.float32)  # 800ms silence

    for idx, sec in enumerate(SECTIONS, 1):
        sec_id = sec["id"]
        sec_title = sec["title"]
        sec_text = sec["text"]
        out_filename = f"{sec_id}.wav"
        out_path = os.path.join(AUDIO_DIR, out_filename)

        print(f"[{idx}/{len(SECTIONS)}] Synthesizing: {sec_title}...")
        t0 = time.time()

        generator = pipeline(sec_text, voice=voice, speed=speed, split_pattern=r'\n+')
        audio_chunks = []
        for gs, ps, audio in generator:
            audio_chunks.append(audio)

        if not audio_chunks:
            print(f"⚠️ Warning: No audio produced for {sec_id}")
            continue

        sec_audio = np.concatenate(audio_chunks)
        duration_sec = len(sec_audio) / sample_rate

        sf.write(out_path, sec_audio, sample_rate)
        gen_time = time.time() - t0
        print(f"   -> Saved: {out_filename} ({duration_sec:.2f}s, generated in {gen_time:.2f}s)")

        generated_tracks.append({
            **sec,
            "filename": out_filename,
            "filepath": out_path,
            "duration_sec": duration_sec
        })

        master_audio_chunks.append(sec_audio)
        if idx < len(SECTIONS):
            master_audio_chunks.append(pause_between_sections)

    # Master Concatenated Audio
    master_path = os.path.join(AUDIO_DIR, "graphsre_master_voiceover.wav")
    master_audio = np.concatenate(master_audio_chunks)
    master_duration = len(master_audio) / sample_rate
    sf.write(master_path, master_audio, sample_rate)
    print("\n" + "=" * 70)
    print(f" [SUCCESS] MASTER VOICEOVER COMPLETE: {master_path}")
    print(f" Total Master Narration Duration: {master_duration:.2f} seconds ({master_duration / 60:.2f} minutes)")
    print("=" * 70)

    # Write Markdown Narration & Video Alignment Guide
    guide_path = os.path.join(AUDIO_DIR, "NARRATION_GUIDE.md")
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write("# GraphSRE Official Video Narration & Visual Alignment Guide\n\n")
        f.write("> **Generated using Kokoro 82M TTS** (`voice: " + voice + "`, `speed: " + str(speed) + "`)\n")
        f.write("> **Master Audio File:** [`graphsre_master_voiceover.wav`](file:///" + os.path.abspath(master_path).replace("\\", "/") + ")\n")
        f.write(f"> **Total Spoken Duration:** {master_duration:.2f} seconds ({int(master_duration // 60)}m {int(master_duration % 60)}s)\n\n")
        f.write("---\n\n")

        running_time = 0.0
        for track in generated_tracks:
            start_m = int(running_time // 60)
            start_s = int(running_time % 60)
            end_time = running_time + track["duration_sec"]
            end_m = int(end_time // 60)
            end_s = int(end_time % 60)

            f.write(f"## {track['title']}\n")
            f.write(f"- **Audio File:** [`{track['filename']}`](file:///" + os.path.abspath(track['filepath']).replace("\\", "/") + ")\n")
            f.write(f"- **Segment Duration:** {track['duration_sec']:.2f} seconds\n")
            f.write(f"- **Suggested Video Timecode:** `{start_m:02d}:{start_s:02d}` - `{end_m:02d}:{end_s:02d}`\n")
            f.write(f"- **Visual Cue / Screen to Show:**\n  *{track['visual_cue']}*\n\n")
            f.write("### Spoken Script:\n")
            f.write(f"> \"{track['text']}\"\n\n")
            f.write("---\n\n")
            running_time = end_time + 0.8  # include inter-act pause

    print(f"\n[OK] Video Synchronization Guide written to: {guide_path}")


if __name__ == "__main__":
    v = "af_heart"
    if len(sys.argv) > 1:
        v = sys.argv[1]
    generate_audio_tracks(voice=v)

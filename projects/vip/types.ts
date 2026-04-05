// --- Video Discovery Types ---

export interface DirectVideoResult {
  type: 'video';
  title: string;
  url: string;
  videoId?: string;
  description: string;
  thumbnail_url: string;
  channelTitle: string;
  channelUrl: string;
  duration?: string;
  viewCount?: string;
  uploadDate?: string;
}

export interface DirectPlaylistResult {
  type: 'playlist';
  title: string;
  url: string;
  playlistId?: string;
  thumbnail_url: string;
  channelTitle: string;
  channelUrl: string;
}

export type StagedItem = DirectVideoResult | DirectPlaylistResult;

export type GeminiModel =
  | 'gemini-flash-lite-latest'
  | 'gemini-flash-latest'
  | 'gemini-2.5-pro'
  | 'gemini-2.0-flash'
  | 'gemini-2.0-flash-lite'
  | 'learnlm-2.0-flash-experimental';

export type LogLevel = 'info' | 'warn' | 'error';

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
}

export type LogCallback = (level: LogLevel, message: string) => void;

// FIX: Added missing type definitions
export interface Filters {
  uploadDate: 'any' | 'today' | 'week' | 'month' | 'year';
  duration: 'any' | 'short' | 'medium' | 'long';
  type: 'video' | 'channel' | 'playlist';
}

export type ViewMode = 'list' | 'card';

export interface Video {
  id: string;
  title: string;
  description: string;
  thumbnailUrl: string;
  channelTitle: string;
  hasCC: boolean;
}


// --- Analysis Report Types ---

// Part A: The WHY
export interface StrategicFramework {
  "💡 The Big Ideas: Core Principles & Mental Models"?: string[];
  "Where This Fits In: Industry Context"?: string;
  "Why It Matters: The Business Impact"?: string;
  "Security & Compliance Concerns"?: string[];
  "⚠️ What to Watch Out For: Biases & Blind Spots"?: string[];
  "Clearing Up Confusion: Common Mistakes & Misconceptions"?: string[];
  "Design Choices: Functional Analysis of the UI/UX"?: string[];
}
export interface ConceptualFramework {
    "School of Thought & Intellectual Lineage"?: string[];
    "Core Problem or Question Addressed"?: string;
    "Key Theories & Hypotheses Presented"?: string[];
    "Intended Audience & Level of Discourse"?: string;
    "Contrasting or Competing Views"?: string[];
    "Real-World Implications & Applications"?: string[];
}

// Part B: Distilled Mental Model
export interface DistilledMentalModel {
  "The Core Analogy"?: string;
  "Key Laws or Rules"?: string[];
  "Visual Metaphor"?: string;
}

// Part C: The WHAT
export interface OperationalBlueprint {
  "Tools & Technologies"?: string[];
  "Inputs/Prerequisites"?: string[];
  "Parameters & Settings"?: { [key: string]: string };
  "Outputs"?: string[];
  "Decision Logic"?: string[];
  "Limitations"?: string[];
}
export interface ArgumentStructure {
    "Central Thesis/Hypothesis"?: string;
    "Main Supporting Arguments"?: string[];
    "Evidence Presented (e.g., data, examples, anecdotes)"?: string[];
    "Counterarguments or Nuances Addressed"?: string[];
    "Key Takeaways/Conclusions"?: string[];
}

// Part D: Diagrams (Mermaid.js string)
export type ProcessFlowDiagram = string;
export type ConceptualMap = string;

// Part E: Glossary
export interface TerminologyGlossary {
  [term: string]: string;
}

// Part F: Timestamped Digest
export interface Speaker {
    identity: string;
    confidence: number;
}
export interface DigestEntry {
  synthesis: string;
  speaker: Speaker;
  audio_points: string[];
  visual_points: string[];
}
export interface TimestampedDigest {
  [timestampRangeAndTitle: string]: DigestEntry;
}

// Part G: Code Artifacts
export interface CodeArtifact {
  filename: string;
  content: string;
  language?: string;
}

// Part H: The HOW
export type ImplementationChecklist = string[];
export type KeyDiscussionPoints = string[];

// Part I: Quick Reference
export interface CheatSheet {
  [topic: string]: string[] | { [subtopic: string]: string };
}
export type KeyTakeaways = string[];

// Part J: Best Practices / Strengths & Weaknesses
export interface BestPracticeEntry {
  category: string;
  best_practice: string;
  anti_pattern: string;
}
export interface StrengthWeaknessEntry {
    category: string;
    strength: string;
    weakness: string;
}

// Part K: Troubleshooting / Misconceptions
export interface TroubleshootingEntry {
  problem: string;
  solution: string;
}
export interface MisconceptionEntry {
    misconception: string;
    clarification: string;
}

// Part L: Resources
export type KeyResources = string[];

// Part M: Unanswered Questions
export interface UnansweredQuestion {
  question: string;
  speculative_answer: string;
}

// Part N: Risk Assessment
export interface RiskAssessment {
  "Scalability Risks"?: string;
  "Maintenance Traps"?: string;
  "\"Bus Factor\" / Key Person Dependencies"?: string;
  "Risk of Misinterpretation"?: string;
  "Risk of Oversimplification"?: string;
  "Potential for Unintended Consequences"?: string;
}

// Part O: Comparative Analysis
export interface ComparativeAnalysisEntry {
  feature: string;
  video_method: string;
  alternative_method: string;
  trade_offs: string;
}

// Part P: Readiness / Further Research
export interface ProductionReadiness {
  "Code & Configuration Hardening"?: string[];
  "Dependency & Security Audit"?: string[];
  "Testing Strategy"?: string[];
  "Observability & Monitoring Plan"?: string[];
}
export interface FurtherResearch {
    "Foundational Texts & Thinkers"?: string[];
    "Contrarian or Critical Viewpoints"?: string[];
    "Practical Case Studies or Experiments"?: string[];
}

// Part Q: Executive Briefing
export interface ExecutiveBriefing {
    "Title"?: string;
    "Key Finding"?: string;
    "Recommendation"?: string;
    "Supporting Points"?: string[];
    "Potential ROI/Impact"?: string;
}

// --- Educator's Guide Types ---
export interface VideoMetadata {
    title?: string;
    presenter?: string;
    publishedDate?: string;
    duration?: string;
}

export interface EducationalSummary {
    coreThesis?: string;
    learningObjectives?: string[];
    targetAudience?: string;
    prerequisiteKnowledge?: string[];
}

export interface KeyConcept {
    term?: string;
    definition?: string;
    timestamp?: string;
}

export interface ContentAnalysis {
    keyConceptsAndVocabulary?: KeyConcept[];
    argumentStructure?: string;
}

export interface ClassroomIntegration {
    discussionQuestions?: string[];
    potentialActivities?: string[];
    connectionsToCurriculum?: string;
}

export interface CriticalEvaluation {
    presenterBiasAndPerspective?: string;
    strengthsAndLimitations?: string;
}

export interface AnalysisReport {
    part_a_strategic_framework?: StrategicFramework;
    part_a_conceptual_framework?: ConceptualFramework;
    part_b_distilled_mental_model?: DistilledMentalModel;
    part_c_operational_blueprint?: OperationalBlueprint;
    part_c_conceptual_argument_structure?: ArgumentStructure;
    part_d_process_flow_diagram?: ProcessFlowDiagram;
    part_d_conceptual_map?: ConceptualMap;
    part_e_key_terminology_glossary?: TerminologyGlossary;
    part_f_comprehensive_timestamped_digest?: TimestampedDigest[];
    part_g_key_file_recreations?: CodeArtifact[];
    part_h_interactive_implementation_checklist?: ImplementationChecklist;
    part_h_conceptual_discussion_points?: KeyDiscussionPoints;
    part_i_quick_reference_cheat_sheet?: CheatSheet;
    part_i_conceptual_key_takeaways?: KeyTakeaways;
    part_j_best_practices?: BestPracticeEntry[];
    part_j_conceptual_argument_strengths_weaknesses?: StrengthWeaknessEntry[];
    part_k_troubleshooting_guide?: TroubleshootingEntry[];
    part_k_conceptual_common_misconceptions?: MisconceptionEntry[];
    part_l_key_resources_mentioned?: KeyResources;
    part_m_unanswered_questions?: UnansweredQuestion[];
    part_n_risk_assessment?: RiskAssessment;
    part_o_comparative_analysis?: ComparativeAnalysisEntry[];
    part_p_production_readiness?: ProductionReadiness;
    part_p_conceptual_further_research?: FurtherResearch;
    part_q_executive_briefing?: ExecutiveBriefing;

    // Educator's Guide Fields
    videoMetadata?: VideoMetadata;
    educationalSummary?: EducationalSummary;
    contentAnalysis?: ContentAnalysis;
    classroomIntegration?: ClassroomIntegration;
    criticalEvaluation?: CriticalEvaluation;

    error?: string;
}

export type BatchReportValue = {
    status: 'detecting' | 'profile_detected' | 'loading' | 'completed' | 'error';
    report?: AnalysisReport;
    error?: string;
    detectedSections?: string[];
};

import type { AnalysisReport, BestPracticeEntry, CodeArtifact, ComparativeAnalysisEntry, MisconceptionEntry, StrengthWeaknessEntry, TimestampedDigest, TroubleshootingEntry, UnansweredQuestion } from '../types';

export const sanitizeFilename = (name: string): string => {
    // Remove invalid characters and limit length
    return name.replace(/[<>:"/\\|?*]/g, '').replace(/\s+/g, '_').substring(0, 100);
};

export const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
};

export const formatPromptKey = (key: string) => {
    return key
        .replace(/^(part_[a-z]_|persona_|directive_)/, '')
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
};

const formatObject = (obj: Record<string, any> | undefined): string => {
    if (!obj) return '';
    return Object.entries(obj)
        .map(([key, value]) => {
            if (!value) return '';
            let formattedValue = '';
            if (Array.isArray(value)) {
                formattedValue = `\n${value.map(item => `  - ${item}`).join('\n')}`;
            } else if (typeof value === 'object' && value !== null) {
                formattedValue = `\n${Object.entries(value).map(([sk, sv]) => `  - **${sk}:** ${sv}`).join('\n')}`;
            }
             else {
                formattedValue = String(value);
            }
            return `**${key}:** ${formattedValue}`;
        })
        .filter(Boolean)
        .join('\n\n');
};

const formatTable = (headers: string[], data: Record<string, any>[]): string => {
    const headerLine = `| ${headers.join(' | ')} |`;
    const separatorLine = `|${headers.map(() => '---').join('|')}|`;
    const bodyLines = data.map(row => {
        const rowData = headers.map(h => {
             const key = Object.keys(row).find(k => k.toLowerCase() === h.toLowerCase().replace(/ /g, '_'));
             const cellData = key ? row[key] : '';
             return ` ${String(cellData).replace(/\n/g, '<br/>')} `;
        });
        return `|${rowData.join('|')}|`;
    }).join('\n');
    return `${headerLine}\n${separatorLine}\n${bodyLines}`;
};

export const jsonToMarkdown = (report: AnalysisReport, title: string): string => {
    let md = `# Analysis Report: ${title}\n\n`;

    const sections: { title: string, content: string | undefined }[] = [
        { title: 'Executive Briefing', content: report.part_q_executive_briefing ? formatObject(report.part_q_executive_briefing) : undefined },
        { title: 'Strategic Framework', content: report.part_a_strategic_framework ? formatObject(report.part_a_strategic_framework) : undefined },
        { title: 'Conceptual Framework', content: report.part_a_conceptual_framework ? formatObject(report.part_a_conceptual_framework) : undefined },
        { title: 'Distilled Mental Model', content: report.part_b_distilled_mental_model ? formatObject(report.part_b_distilled_mental_model) : undefined },
        { title: 'Operational Blueprint', content: report.part_c_operational_blueprint ? formatObject(report.part_c_operational_blueprint) : undefined },
        { title: 'Argument Structure', content: report.part_c_conceptual_argument_structure ? formatObject(report.part_c_conceptual_argument_structure) : undefined },
        { title: 'Process Flow Diagram', content: report.part_d_process_flow_diagram ? `\`\`\`mermaid\n${report.part_d_process_flow_diagram}\n\`\`\`` : undefined },
        { title: 'Conceptual Map', content: report.part_d_conceptual_map ? `\`\`\`mermaid\n${report.part_d_conceptual_map}\n\`\`\`` : undefined },
        { title: 'Key Terminology Glossary', content: report.part_e_key_terminology_glossary ? Object.entries(report.part_e_key_terminology_glossary).map(([term, def]) => `**${term}**: ${def}`).join('\n') : undefined },
        { title: 'Timestamped Digest', content: report.part_f_comprehensive_timestamped_digest ? report.part_f_comprehensive_timestamped_digest.map((digest: TimestampedDigest) => {
            const [key, entry] = Object.entries(digest)[0];
            return `### ${key}\n**Synthesis:** ${entry.synthesis}\n\n**Speaker:** ${entry.speaker.identity} (Confidence: ${entry.speaker.confidence * 100}%)\n\n**Audio Points:**\n${entry.audio_points.map(p => ` - ${p}`).join('\n')}\n\n**Visual Points:**\n${entry.visual_points.map(p => ` - ${p}`).join('\n')}`;
        }).join('\n\n---\n') : undefined },
        { title: 'Code Artifacts', content: report.part_g_key_file_recreations && report.part_g_key_file_recreations.length > 0 ? report.part_g_key_file_recreations.map((artifact: CodeArtifact) => `### \`${artifact.filename}\`\n\`\`\`${artifact.language || ''}\n${artifact.content}\n\`\`\``).join('\n\n') : undefined },
        { title: 'Implementation Checklist', content: report.part_h_interactive_implementation_checklist ? report.part_h_interactive_implementation_checklist.map(item => `- [ ] ${item}`).join('\n') : undefined },
        { title: 'Discussion Points', content: report.part_h_conceptual_discussion_points ? report.part_h_conceptual_discussion_points.map(item => `- ${item}`).join('\n') : undefined },
        { title: 'Quick Reference Cheat Sheet', content: report.part_i_quick_reference_cheat_sheet ? formatObject(report.part_i_quick_reference_cheat_sheet) : undefined },
        { title: 'Key Takeaways', content: report.part_i_conceptual_key_takeaways ? report.part_i_conceptual_key_takeaways.map(item => `- ${item}`).join('\n') : undefined },
        { title: 'Best Practices', content: report.part_j_best_practices && report.part_j_best_practices.length > 0 ? formatTable(['Category', 'Best Practice', 'Anti Pattern'], report.part_j_best_practices) : undefined },
        { title: 'Strengths & Weaknesses', content: report.part_j_conceptual_argument_strengths_weaknesses && report.part_j_conceptual_argument_strengths_weaknesses.length > 0 ? formatTable(['Category', 'Strength', 'Weakness'], report.part_j_conceptual_argument_strengths_weaknesses) : undefined },
        { title: 'Troubleshooting Guide', content: report.part_k_troubleshooting_guide && report.part_k_troubleshooting_guide.length > 0 ? report.part_k_troubleshooting_guide.map(item => `**Problem:** ${item.problem}\n\n**Solution:** ${item.solution}`).join('\n\n---\n') : undefined },
        { title: 'Common Misconceptions', content: report.part_k_conceptual_common_misconceptions && report.part_k_conceptual_common_misconceptions.length > 0 ? report.part_k_conceptual_common_misconceptions.map(item => `**Misconception:** ${item.misconception}\n\n**Clarification:** ${item.clarification}`).join('\n\n---\n') : undefined },
        { title: 'Key Resources Mentioned', content: report.part_l_key_resources_mentioned && report.part_l_key_resources_mentioned.length > 0 ? report.part_l_key_resources_mentioned.map(item => `- ${item}`).join('\n') : undefined },
        { title: 'Unanswered Questions', content: report.part_m_unanswered_questions && report.part_m_unanswered_questions.length > 0 ? report.part_m_unanswered_questions.map((q: UnansweredQuestion) => `**❓ Question:** ${q.question}\n\n**Speculative Answer:** ${q.speculative_answer}`).join('\n\n---\n\n') : undefined },
        { title: 'Risk Assessment', content: report.part_n_risk_assessment ? formatObject(report.part_n_risk_assessment) : undefined },
        { title: 'Comparative Analysis', content: report.part_o_comparative_analysis && report.part_o_comparative_analysis.length > 0 ? formatTable(['Feature', 'Video Method', 'Alternative Method', 'Trade Offs'], report.part_o_comparative_analysis) : undefined },
        { title: 'Production Readiness', content: report.part_p_production_readiness ? formatObject(report.part_p_production_readiness) : undefined },
        { title: 'Further Research', content: report.part_p_conceptual_further_research ? formatObject(report.part_p_conceptual_further_research) : undefined },
    ];

    sections.forEach(section => {
        if (section.content) {
            md += `## ${section.title}\n\n${section.content}\n\n---\n\n`;
        }
    });

    return md;
};

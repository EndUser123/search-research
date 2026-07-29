---
source_id: "18c91da3-b5c4-46c4-8ccd-ecfc9da8fe93"
title: "SurveyGen-I: Consistent Scientific Survey Generation with Evolving Plans and Memory-Guided Writing - ACL Anthology"
notebook_id: 88c3ce70-351f-43c6-9e64-6db421c911d4
url: https://aclanthology.org/2025.ijcnlp-long.193.pdf
type: pdf
exported: 2026-07-28
---

# SurveyGen-I: Consistent Scientific Survey Generation with Evolving Plans and Memory-Guided Writing - ACL Anthology
 

 

SurveyGen-I: Consistent Scientific Survey Generation with Evolving Plans and Memory-Guided Writing 

Jing Chen1,2* , Zhiheng Yang1*† , Yixian Shen1, Jie Liu1, Adam Belloum1, Paola Grosso1, Chrysa Papagianni1 † 

1University of Amsterdam, the Netherlands 2Vrije Universiteit Amsterdam, the Netherlands 

j.chen12@student.vu.nl {z.yang, y.shen, j.liu5, a.s.z.belloum, p.grosso, c.papagianni}@uva.nl 

Abstract 

Survey papers play a critical role in scien-tific communication by consolidating progress across a field. Recent advances in Large Lan-guage Models (LLMs) offer a promising so-lution by automating key steps in the survey-generation pipeline, such as retrieval, struc-turing, and summarization. However, ex-isting LLM-based approaches often struggle with maintaining coherence across long, multi-section surveys and providing comprehensive citation coverage. To address these limita-tions, we introduce SurveyGen-I, an automatic survey generation framework that combines coarse-to-fine retrieval, adaptive planning, and memory-guided generation. SurveyGen-I per-forms survey-level retrieval to construct the initial outline and writing plan, then dynam-ically refines both during generation through a memory mechanism that stores previously written content and terminology, ensuring co-herence across subsections. When the sys-tem detects insufficient context, it triggers fine-grained subsection-level retrieval. During gen-eration, SurveyGen-I leverages this memory mechanism to maintain coherence across sub-sections. Experiments across six scientific domains demonstrate that SurveyGen-I con-sistently outperforms previous works in con-tent quality, consistency, and citation cover-age. The code is available at https://github. com/SurveyGens/SurveyGen-I. 

1 Introduction 

The exponential expansion of scholarly literature, with thousands of new papers published daily, presents significant challenges for researchers to efficiently acquire and synthesize comprehensive knowledge. Consequently, writing survey papers requires substantial expertise and time commitment from researchers, as it traditionally involves an iter-

* Equal contribution. † Corresponding author. 

ative and labor-intensive process of reading, note-taking, clustering, and synthesis (Carrera-Rivera et al., 2022). Recent advances in Large Language Models (LLMs) offer a promising solution to this bottleneck by enabling the automation of key steps in the survey-writing pipeline, such as retrieving, organizing, and summarizing large volumes of pa-pers (Wang et al., 2024; Liang et al., 2025; Yan et al., 2025; Agarwal et al., 2024, 2025). 

Despite recent advances, current LLM-based sur-vey generation frameworks remain limited in sev-eral key aspects. First, literature retrieval scope and depth remain limited. Most systems rely on embedding-based similarity search over a fixed lo-cal paper database (Wang et al., 2024; Yan et al., 2025). While efficient, such surface-level match-ing often fails to identify important papers with different terminology or at a more conceptual level, resulting in incomplete or biased coverage. Sec-ond, lack of cross-subsection consistency. Most systems generate all subsections in parallel as iso-lated units without modeling dependencies across subsections (Wang et al., 2024; Liang et al., 2025; Yan et al., 2025). This often leads to redundant content, inconsistent terminology, and fragmented discourse. Moreover, they always follow a static, once-for-all outline that cannot adapt to newly gen-erated content, making it difficult to maintain con-tent coherence or integrate emerging insights. Fi-nally, indirect citations are often left unresolved. Retrieval-augmented generation (RAG) typically extracts passages from retrieved papers to support writing. These passages often include indirect cita-tions such as "[23]" and "Smith et al., 2022", which refer to influential prior work not present in the retrieval results. Without tracing these references, the system may miss influential papers, leading to incomplete citation coverage and broken linkage between ideas and their original sources. 

To address these limitations, we introduce SurveyGen-I, an end-to-end framework for gen-

3687

erating academic surveys with consistent content and comprehensive literature coverage. First, SurveyGen-I performs coarse-to-fine literature re-trieval at both the survey and subsection levels, augmented with citation expansion and LLM-based relevance scoring. This retrieval strategy substan-tially enhances literature coverage and topical rele-vance. Second, SurveyGen-I introduces PlanEvo, a dynamic planning mechanism powered by an evolving memory that continuously accumulates terminology and content from earlier generated subsections. This memory is used to construct the outline and a dependency-aware writing plan that captures the logical and conceptual relation-ships between subsections, allowing foundational topics to be generated before more advanced or derivative ones. As writing progresses, both the outline and plan are continually refined based on the updated memory, ensuring consistent terminol-ogy and coherent content flow across the survey. Finally, SurveyGen-I introduces CaM-Writing, which combines a citation-tracing module that de-tects indirect references in retrieved passages and resolves them back to their original source papers, with memory-guided generation that uses the evolv-ing memory to maintain coherent terminology and content across the survey. 

Extensive results highlight the strengths of SurveyGen-I across multiple dimensions of aca-demic survey generation. Compared to the strongest baseline, SurveyGen-I yields an 8.5% im-provement in content quality, a 27% increase in citation density, and more than twice as many dis-tinct references, while also demonstrating signifi-cantly better citation recency. These improvements show the effectiveness of the system in enabling high-quality and consistent survey generation. 

Our contributions are summarized as follows: 

 We propose SurveyGen-I, a novel framework 

for high-quality, reference-rich, and consistent survey generation. 

 We design a coarse-to-fine Literature Re-trieval pipeline that combines keyword search, citation expansion, and LLM-based fil-tering to construct comprehensive paper sets at both survey and subsection levels. 

 We introduce PlanEvo, a dynamic planning mechanism that constructs and continuously refines the outline and writing plan based on inter-subsection dependencies and evolving memory, ensuring coherent survey generation. 

 We develop a CaM-Writing pipeline that 

combines citation tracing and memory-guided generation to improve reference coverage and ensure consistent, well-structured writing. 

2 Related work 

Component-Oriented and Hybrid Approaches. A longstanding approach to assisting literature sur-veys has been to tackle the problem in stages, where components handle retrieval, structuring, or writ-ing, etc., independently (Susnjak et al., 2025; Lai et al., 2024; Li et al., 2025). Early systems orga-nized citation sentences through clustering or clas-sification (Nanba et al., 2000; Wang et al., 2018), employed rule-based content models (Hoang and Kan, 2010), or optimization-based extractive frame-work for related work generation (Hu and Wan, 2014). These systems often relied on static heuris-tics or surface-level topic associations, making them difficult to generalize across domains or main-tain narrative coherence. 

The rise of LLMs brought a wave of hybrid de-signs that integrated neural summarization with structured control (Fok et al., 2025; An et al., 2024; Zhang et al., 2024). Template-based gen-eration (Sun and Zhuge, 2019) and extractive-abstractive hybrids (Shinde et al., 2022) introduced more fluent synthesis but retain rigid structures. Meanwhile, RAG-based methods (Lewis et al., 2020; Ali et al., 2024; Agarwal et al., 2024) en-hanced retrieval fidelity (Gao et al., 2023), and agent-driven systems like the framework proposed by Brett and Myatt (2025), RAAI (Pozzobon and Pinheiro, 2024) and AutoSurveyGPT (Xiao, 2023) broke down the pipeline into stages such as re-trieval, filtration, and generation. More recent works emphasize pre-writing planning, such as COI-Agent (Li et al., 2024b), which organizes ref-erences into conceptual chains to enhance topic coverage. 

However, these designs remain fundamentally decomposed: content selection and writing are planned in isolation, and their execution often lacks global coordination across stages. 

End-to-End Automated Literature Review/Sur-vey Generation. With increasing demand for scalability and consistency, end-to-end frame-works have emerged to streamline the full pipeline from retrieval to synthesis. Multi-agent architec-tures (Sami et al., 2024; Rouzrokh and Shariat-nia, 2025) have been widely used, and decom-pose the pipeline into specialized agent roles, mim-

3688

icking human editorial workflows. Representa-tively, AutoSurvey (Wang et al., 2024) introduces a retrieval-outline-generation sequence that produces entire surveys via section-wise prompting. Survey-Forge (Yan et al., 2025) extends this with memory modules and outline heuristics, aiming to enforce consistency across segments. SurveyX (Liang et al., 2025) scales this further by relying on larger mod-els and a more complex pipeline, producing more robust and strict step-by-step outputs. 

Despite these advances, many systems adopt a static and compartmentalized approach. Outlines are typically fixed in advance, with no capacity to revise structure based on intermediate content. Subsections are often generated in parallel, lack-ing shared context, which weakens narrative flow and increases repetition or terminology drift. Cita-tion usage often lacks depth and evidential ground-ing, with models prone to hallucinations and miss-ing fine-grained details (Kasanishi et al., 2023). In response, our work views survey writing as a dynamic process, one that requires adaptive plan-ning, context-aware memory, and citation-traced retrieval. By continuously refining structural plans, maintaining cross-section consistency, and ground-ing generation in citation chains, we move toward producing more coherent and adaptive surveys. 

3 Methodology 

In this section, we propose SurveyGen-I, a novel framework for automatic survey generation. As shown in Figure 1, it consists of three key stages: (1) Literature Retrieval (LR) performs coarse-to-fine literature retrieval at both survey and subsec-tion levels; (2) Structure Planning with Dynamic Outline Evolution (PlanEvo) generates a hierar-chical outline and a dependency-aware writing plan, and dynamically updates both during generation to ensure cross-subsection consistency; (3) CaM-Writing generates each subsection with high con-tent consistency and rich citation coverage, combin-ing a citation-tracing mechanism to recover influen-tial references, memory-guided skeleton planning for content consistency, and 

best-of-N 

draft selec-tion to ensure high-quality generation. 

3.1 LR: Literature Retrieval 

To ensure that the generated survey is grounded with the most relevant and comprehensive research, our system adopts a coarse-to-fine literature re-trieval strategy that operates at both the survey and 

subsection levels. As shown in Figure 1, this re-trieval process provides the reference foundation for both structure planning (SDP; see Sec 3.2.1) and writing (CaM-Writing; see Section 3.3). The overall workflow is shown in Figure 2; implemen-tation details are provided in Appendix B.1. 

3.1.1 Survey-Level Retrieval for Structure Planning 

For survey-level literature retrieval, an LLM is first prompted to generate a keyword set K based on the input topic 

T 

and its description 

E 

(see prompt in Figure 13). These keywords are used to query Se-mantic Scholar (Ammar et al., 2018), producing an initial set of papers Pinit. While keyword-based re-trieval offers broad initial coverage, it may include irrelevant papers. To enhance topical precision, a semantic filtering step is applied. Specifically, both the input 

(T,E) 

and each paper abstract 

ai 

are em-bedded using the all-mpnet-base-v2 sentence transformer (Song et al., 2020). Candidate papers with high cosine similarity to the input 

(T,E) 

are retained, yielding a refined set Psem: 

Psem = 

{pi ∈ 

Pinit | 

cos(eT,E , eai) ≥ θ}. 

(1) 

To improve coverage and avoid missing influ-ential work, we perform a citation expansion step. Specifically, we select the top-10 papers from Psem and retrieve both their references and citations us-ing the Semantic Scholar API, forming the ex-panded candidate set Pexp. We then remove du-plicates and re-rank all papers by topical relevance, first using semantic similarity, followed by LLM-based relevance scoring with respect to 

(T,E). 

Fi-nally, the top 30 papers are retained as the final survey-level literature set P∗ to support outline generation (see prompt in Figure 16). 

Full texts are retrieved based on the access in-formation contained in the Semantic Scholar API metadata. We prioritize the openAccessPdf fields from the metadata or arXiv ID when available, and fall back to DOI links otherwise. 

3.1.2 Subsection-Level Retrieval for Writing In addition to survey-level retrieval for structure planning, subsection-level retrieval is optionally triggered during writing. For each subsection 

si 

with its description 

di, 

the subsection-level pa-per set 

Pi 

is constructed using the same retrieval pipeline as above, with 

(si, di) 

as input. Whether this step is performed is controlled by a retrieval flag 

ri 

in the dependency-aware writing plan (see 

3689

https://lh3.googleusercontent.com/notebooklm/AKYWMX_U1f10i9gKrpFBYwO0Xo59YZWDMWV1ODr-ulJ6BgsDyVBQU2hI12Eduqx8lTVJqqpi1PMN0JkKb99OKaVMVfcJxrnshJBI7gtmGB-fUhY2NkRLZIVGmyT4Fo0UIb3XeXfprKYs=w512-h512-v0

fbefee64-ffa3-4694-9c08-5ded0942b0fe

https://lh3.googleusercontent.com/notebooklm/AKYWMX9KqHrtyueD_vRnlwbw3G87N8sG5IdYoatya3hKSmImGfB16HbUDUsY9IbA-MR-48sNe6zCde2DhVzrl1v2255qHMwbdeUf0TTtGW4I-Fs8pmpuOE8FvKmBS415i_PyIaO3Jr9w=w512-h512-v0

5de9b6b5-3c7c-4827-a0a9-5a73f1997f92

https://lh3.googleusercontent.com/notebooklm/AKYWMX9Gq2wkCtGfPv-Oy5Eiv9ASvnYYjhNAjVXJmvD5cAnm8KpwvzG42PyeK_3XmxHxUs8ZudcFoprsAI4t46ZaI-QkmtHXgtZ8Nm_SFmiTA8oIlnQf3_JVknnBu0xlBMf8Gl0t0Z0kJg=w512-h512-v0

62f0255a-41f5-41ea-8df7-9a435ad35267

https://lh3.googleusercontent.com/notebooklm/AKYWMX8E29eSJWBVz6xsZhlP9bQO7HGF3EcFSSPfV66lEQ1QiTkdR8jRZa8xXLOpvFbspRcbsdhJoA-BUi9Kk7NBl9y98ggPW46NWPcnz6a1EHkLiiNmDQed0dfKrAWhPCYrABWKRt8z=w512-h512-v0

f59604d2-4e7a-47a7-b89f-66a149b9d625

https://lh3.googleusercontent.com/notebooklm/AKYWMX8aTDRBZzGHwd8By1xkANjwkPWscQXyVkML697eN_oJpP8GTKH7dKG8gh6nfByssocP6tfiULq-VLrNsi35RblvV7cFkwfju5nienqeOL0PbDwxVGtmycib9FaLRjj7eBu7Z1cMLw=w512-h512-v0

ce3daaba-5103-40cd-94ce-155639179c30

https://lh3.googleusercontent.com/notebooklm/AKYWMX8mwRZpLWv7cFhF45GVZxPZacnx-PqldSdRXds8nnCfF0T3If7zdg2KgGjyaXGHDK-k9pNGWKRo_D1nd-kYIXyTv_eR9pphT9wezpxAJPAzIcH4ccT7-LJal1tSdjpS9CE1Kflr=w512-h512-v0

4f36c278-a319-4002-9010-e7fa48b0ff5d

https://lh3.googleusercontent.com/notebooklm/AKYWMX9L9aI3iV2O8wgeT14CVemc6BoQ8nWcXOktSm3Ebvhv23tHIM9SoXYGjZGcBNkj_ngyNkbgyJ-sMEFaRzoFx1Be-LewJRNrVrNNI3Km1cdqYZ5fBVfw52sPw7t_meg1BWzaaN0GGw=w512-h512-v0

7a023c91-011c-415a-a534-3193ed3d6be7

https://lh3.googleusercontent.com/notebooklm/AKYWMX9aWZI_3zqQT2MgjqEqlCxJvZY8FpG7zHg-WBRrOUOmX3AvCr2tBQXlrdNE4v_Z6XhzNOi5XRFmbEaJXZAZT54C8gbGDDaAZ-Idi-a0QGEM8lIj_WFe0MJ96Cxz_DM6KYM2qAtR=w512-h512-v0

565ff677-5434-4c85-a4ec-86f2816698a3

https://lh3.googleusercontent.com/notebooklm/AKYWMX9bnpX084UuzlvbXG2IlrlVufSEz8md_hBKx8ITXARhswnvJjhYd5fnpfYsDaanFk1OToSX_8AB00lyIVkVApH51Y-6OgniQ5s8DUHO1PUIoHu72JlhO4qotO4ADzP-UiXkL6g-gA=w512-h512-v0

c1ef6806-7ae9-466f-bad3-4f8d62f60b3a

https://lh3.googleusercontent.com/notebooklm/AKYWMX-D6NaGEKU2c7x-5_HKFOy64uaRB4hXxy2zejP8OmtUw8fQl_IkP_XkXvVK4mcROGdV5tRAl5tjBe66t3nGWbGnEaPU5uj44RBRSyDItdyqTMPm0VBggK0A0bP9Q3xd58TsQkAqSA=w512-h512-v0

34e9bae3-dd42-4409-a946-5de2d96bdc8c

https://lh3.googleusercontent.com/notebooklm/AKYWMX-3lyVGFG5lxXsNupBFXn8os0wRz5v6d_jF_SOAptM1muCJoUFce-gX53TJHKdIgQS9CiMWklyvNtsZR1KySKlgy3FIOZN3C6VVSpwSRDSQj0CR2EEOimvt2XyApKf1Hg0h4m-qNg=w512-h512-v0

40330df8-2d94-4037-9025-b38c1f5959bb

https://lh3.googleusercontent.com/notebooklm/AKYWMX_x2u5_t1arOyocHARLs_rbTFztIyl_04U6QpOfHphZzrinQtwS30mh5tgvIhQE0ghe4oZ4B-2c_OScHOw5VWGp69Law0-d1oH9RiKeAZs2eEnR1OKTzkesYdo8iSMnN8W1y-Mz=w512-h512-v0

3ba4f64d-3be1-4c58-a640-003eae8a44e2

https://lh3.googleusercontent.com/notebooklm/AKYWMX-skxh4RIzoRH1qLXRNHcqLCL4CXP7lIVz6djuf3pHK2gTnv2D3vVJcSQmSiblzd0cuhPFoDx2okKC1ux9huKQ_wIey4m-PkM9tTjCwfG2Vjsrkq7Zrj9lV07iTrZ1VXrEPfKRKNg=w512-h512-v0

35df373b-2bfb-446e-b660-d2accd73754f

Final Refinement 

Current Stage:        (Next Stage:   ) 

SAWC: Structure-Aware Writing Controller 

CaM-Writing 

LR: Literature Retrieval (Survey) SDP: Structure-Driven Planner 

Subsection : Subsection : 

Dispatch all 

LR: Literature Retrieval (Subsection) 

LR: Literature Retrieval (Subsection) 

If If 

MGSR 

Trig ger re 

plan ( 

) 

 replan ( 

) 

m em 

ory 

Memory 

If 

Subsection : 

Final Survey 

Table Generation 

Input 

Update Memory: 

1 2 

3 

4 

5 

6 

7 

9 

10 

All subsections in Stage t finished 

8 

0 

11 

12 

13 

Loop                   until all stages complete 

3 10 

Legend: : Subsection description  : Retrieval flag  : Table flag  

: Stage index (parallel writing)  : Structure memory (drafts, 

terminology) 

Key: 

Subsections with same  are processed in parallel per stage. 

Steps 3–10 repeat until all stages complete. 

Memory, outline and plan dynamically updated after each stage. 

Table generation/global refinement triggered after writing finishes. 

Best-of-N Drafting & Multi-Stage Refinement 

Citation Traced Retrieval (RAG + Citation Trace) 

Memory-Guided Skeleton Gen 

Figure 1: Overview of the SurveyGen-I pipeline for automatic academic survey generation. The system comprises three stages: (1) coarse-to-fine Literature Retrieval (LR); (2) PlanEvo, a structure planning module integrating SDP (planning), SAWC (scheduling), and MGSR (dynamic replanning); (3) CaM-Writing for citation-aware subsection generation. Final refinement and table generation are performed after writing. Memory M accumulates writing content and terminology across stages to guide planning and ensure consistency. 

Section 3.2.1). The final global literature set P∗ 

i 

used for writing each subsection is the combination of the survey-level set P∗ and the subsection-level set 

Pi. 

This paper set captures both the global scope of the survey and the specific focus of each subsection. 

3.2 PlanEvo: Structure Planning with Dynamic Outline Evolution 

We introduce PlanEvo, a planning-centric frame-work for scalable and coherent survey outline gen-eration and writing plan construction. PlanEvo consists of three tightly integrated components: the Structure-Driven Planner (SDP), the Structure-Aware Writing Controller (SAWC), and the Memory-Guided Structure Replanner (MGSR). De-tailed designs for each component are presented in Section 3.2.1, Section 3.2.2, and Section 3.2.3. 

3.2.1 SDP: Structure-Driven Planner 

The SDP module serves as the entry point of PlanEvo, transforming a specific research topic 

(T,E) 

into a structured, executable plan that guides the full survey generation process. The overall 

workflow is shown in Figure 2. 

Reference-Grounded Outline Generation. A literature-grounded outline is essential for generat-ing a coherent and well-structured survey. To build such an outline, the system first identifies review articles within the survey-level literature set P∗ by analyzing metadata such as publication type. The structural outlines of these reviews R are then ex-tracted from their full texts using LLMs and used as representative structural patterns to inspire the design of new outlines. The system then collects titles and abstracts of non-review papers in P∗ to form the abstract-level content set Cabs, which is then combined with R into a composite context C. Given C and 

(T,E), 

an LLM is prompted to generate an initial outline O0: 

O0 = 

{(si, di)}Ni=1 

(2) 

where each subsection heading 

si 

is paired with a brief description 

di 

to provide more detailed guid-ance for writing subsections. To improve coher-ence and reduce redundancy, the initial outline O0 

is refined by an LLM, obtaining the final outline O. 

3690

https://lh3.googleusercontent.com/notebooklm/AKYWMX-6klzLgeHzVJYBiAFUT3pb8HF83Q-aVVVhs49w1bttSpaRzpntA8-ltGS_zgKcDHmHSfdyaSe3Xrc2yyqi7AiLDGKDee1UdhiZlaYluQtUuEiWB7Sk2YWN_3mccFf10th2T_nxIQ=w615-h502-v0

3fb30221-d1dc-4c60-9f0b-6a02c958bea9

https://lh3.googleusercontent.com/notebooklm/AKYWMX94k-TI4oN5U0eaW64L-MZgqMHKF1cSMrUBMOEJE74oTxkmYbEoDb10n6cct1dU-6reX59fYtaRywJes76EEIkm3o9ptm2HR9IOTxMiDPaQF8bS5qq244mstODCHG6lxGn80S-5gw=w512-h512-v0

040e3fab-52c9-4c94-93b9-ca8e9cf24013

https://lh3.googleusercontent.com/notebooklm/AKYWMX-_T8RnPE7FuiLI9J3GyRe_zV2FOyJcnPYQSfZ6rRx746FdUVinMiE13nK1JRhjMhWC_3WFDRHkt7Wsc9DOY7KSFHy_agxuYArgi8b4Gp5VVLpiMR-Cl3Q3qADEFuksbng69oumHg=w1024-h720-v0

bac1e05d-10c2-4c1c-aaca-12a16969179c

https://lh3.googleusercontent.com/notebooklm/AKYWMX_Ltmr6snXq3YT9RYIcS0koBObYF8ENNpCkPpXAm7z6a4gY2Kao2bL1DMtTjpzUGZjFmddHnUkYDdrdogGEWEEG6FNKEY_LvYg-GDFUw2TctQxiqyW_TCm9SFeOVy0gvZSQn7lszg=w512-h512-v0

8e9828fb-20ab-474d-80bf-ef1b4b89ad2e

https://lh3.googleusercontent.com/notebooklm/AKYWMX88rp5ZIJsbd8Af_N4GktqAWszTNDaR74YerPZmx8yejequgj3nhDo7OzC-70Fd9jO30Sk0LE7a352osEZch_U3M9NE8lWlsoikAM_vwhm-3UINfpJgY6Nw0nSoZ4KWU0mnPJ7a=w512-h512-v0

efcd959f-e878-4fcf-b97a-831b3f3e8116

https://lh3.googleusercontent.com/notebooklm/AKYWMX976uYFNQM5qEPMLy52Ox7AiiFBkvPxJz1Vrv9-vSz2Ejuue6ZxZLTb7cOS0KZfIHtMAfOvg1nldu63cDFmnkvVjqiu_bKxHCfJz0q1L6UUcglfZ20uflAgJemCaX9C421oT5mB=w512-h512-v0

ca88a6fb-b7fa-4df4-a014-e33eda72751f

https://lh3.googleusercontent.com/notebooklm/AKYWMX_E37PLx0B7m6L2Wq9IuimoLDnK9Pd3lZZqLhitRf-nuApx0xXHlGemNByuR2HwzgrUPuVNdWrsphH9tgCZzmGcJtaKJJH0t_752_wIWxsrZKsyuX5EfWVM8tqcRhcIQgv2c_ogsw=w512-h512-v0

edca5ba5-a83e-40c4-8f97-d7b4d168b2be

https://lh3.googleusercontent.com/notebooklm/AKYWMX_9oCIujj5MWPysol9IlZWxNRCknOM3wG1ukpUvLERK76uuablmlK_fnEAjVQrVJUO3fOoDyE2YzqFUsWKIJ8f7iuPWfR2DG_JPoQY-0oCb0AqgIZBuhQFYKA5BilEarYMyhhwABw=w512-h512-v0

1ef83779-26e6-4f81-bd5f-30370d95d8dc

https://lh3.googleusercontent.com/notebooklm/AKYWMX_K6_fY7IjDDOJTknm_J9I2tJzUG_G32y2rtPA2Pq4VOPVMdjYcLBb8Mjc3jaJh93PHK4WtWCzRWhMS_8-SF9_0QNL-xcPfVmP25OXhLZ9_cRppLrxc4AapNvorsxkuT-alka00eQ=w512-h512-v0

f6a45708-74bd-46fb-a3d2-bf1833e77d89

https://lh3.googleusercontent.com/notebooklm/AKYWMX8ALjj-G9zxanopO1Z_vmLHfMBqGH-aHweGwkWX8oFJYmkuwaJiuxd-I3WPj4aYXuOY3HK9EJnKoXPw2ax5XynGQFP5hi3AMcZ2CdUhB-mfJwUEoRfT_KHK4XCQcDSVWC0ZzcNG=w512-h512-v0

a53b649c-7e2e-4aa5-a63b-2b8a7a3797fe

https://lh3.googleusercontent.com/notebooklm/AKYWMX-BvbRgbgSEMm_c1b94wdmXUVFAqEcHsSptJR8HfdPg3DXN7jcuwaI_9j2X11tw7ZaJi-jG4JcqVjSzP--cYHxE0qpYIBj1mWdHoI_Pqq59L-rNMunEDmc_47CGgebRm5Sw69FE5w=w512-h512-v0

aa478dfc-ccb3-4694-8e68-e83b1b6bcb3e

https://lh3.googleusercontent.com/notebooklm/AKYWMX8MRXCb-30MR1JWCjUjZA_2waBmC8Pu-WKokyZUsVoxamvAYMRxjW_kwI8lUUEk5QoWXxceaTjhnGfZ1b5krOMcdNyVuXhao9w69_w0VikDo4zn4-wuyetraJYW4Hyx_5_RWg4oMA=w512-h512-v0

3e4db470-f21a-4657-80ff-2485f432d1cb

https://lh3.googleusercontent.com/notebooklm/AKYWMX8MthBEMotEbpO1fThAJ7c_U0wBZFrwLvkachGzPwsYk4G1H60U1Ya_cbyjf5WJBiIy-m1Ky9XvTYV29w0W5mPvQ-sYJdPEYcUx_dq3gI9hSoTcuwVzzDDIcyynHpyvTbcPtFIgWw=w512-h512-v0

0720b840-ca34-4175-9623-456b9e494ef5

https://lh3.googleusercontent.com/notebooklm/AKYWMX-CMQO-qMGf7B9gsVXYkyFvXvBBhdCYKIEMxFixKdz24QSTGogdUP0QdfEwtViCW1OeZsGtQ4Srif6PfEALrPe0cT2UMs8JR7Kqba2R1eZOXPxQFNQt9pgfwxGI3jj8CttfUwQZ=w512-h512-v0

9017d38e-4c47-4717-91b1-feef8a105578

https://lh3.googleusercontent.com/notebooklm/AKYWMX8TaERW2MdHBaRyVIdzN7Ilo-rlwGQRYde4tffmIwhAFtTc76ONx8hdIi-WELTgJJ5Vdi8Y_EsWoOBSRkdLHisjOQEJhKjmLR3oDXUDkGG4OD1_btBxC3BK24S63uZHJISd1S4ENw=w512-h512-v0

5edcb407-0789-4be1-89bc-f9e84608f878

https://lh3.googleusercontent.com/notebooklm/AKYWMX8_b4AqerrUZitNOY4kq6S5ix3VQnLHwj7Jod_3WBzziK7krFn7ynIKnMSWTQTqPv5qdMKdVdBJJy_3qLMyzrIlLvVSbZ98XjQeaiajNjBbWxO-oQtqePS-dLlbo4w4kX8buU4IFA=w512-h512-v0

2186fa92-16d6-4d4a-ba75-ecc4cac04ec5

https://lh3.googleusercontent.com/notebooklm/AKYWMX-ozV92Soqx0ktPAI-gEiqlvR4zfltWYR1FKTLhE94l_j0IIQkKWE3Cxq6g_VxMH5uuzYEhMTMdOPuhkhEXAtSBUdPzerm0JLRaUHrTsEZt-nelop2nkD3Obtzx-ht87BWNpf4nUA=w512-h512-v0

334454e4-8209-4d78-a3e7-65b85b809c2d

SDP: Structure-Driven Planner LR: Literature Retrieval 

Keyword Gen 

Search 

Semantic Filter 

Citation Expansion 

LLM Relevance Rerank 

Subsection Input: 

Global Literature Set 

Step 2: Dependency-Aware Writing Plan 

Input Papers:  

Extract Review Papers 

Topic Input: T, E Step 1: Reference-Grounded Outline Generation 

Extract Non-Review Papers 

Generate Outline Refine Outline  Outline (Example) 

1. Intro 1.1 History 1.2 Motivation ... 

2. Theory 

Survey-Level Literature Set  

Sam e Pipeline 

Initial Plan Example for 

Subsection Title : Motivation Subsection description : ... Generate Table : False subsection Retrieval : True 

Remove Cycles 

Dependency (Example) 

 A: depends on B B: depends on C C: depends on D D: depends on B 

Identify Dependency 

Final Plan Example for 

Subsection Title : Motivation Subsection description : ... Generate Table : False subsection Retrieval : True 

Stage Index τ( 

): 1 

Initial Plan 

Input Outline:  

Topological Sort 

and Final Plan 

A B 

CD 

A B 

CD 

DAG 

Figure 2: Details of the Literature Retrieval and Structure-Driven Planner components in SurveyGen-I. 

An example of the generated outline is provided in Appendix B.2. 

Dependency-Aware Writing Plan. To enable logically coherent and coordinated writing across subsections, we construct a dependency-aware writ-ing plan Pdep based on the survey outline O. 

First, an initial plan Praw is generated by prompt-ing an LLM with O. For each subsection 

si 

with its description 

di, 

the plan specifies two control signals: whether additional literature retrieval is re-quired 

(ri), 

and whether a comparative table should be generated 

(ti). 

These signals guide downstream tasks in subsection-level literature retrieval and ta-ble generation. Each subsection takes the form: 

Praw[si] 

= 

(di, ri, ti), 

(3) 

Next, to ensure logical dependency alignment across subsections, we construct a structural depen-dency graph Graw = 

(V, 

E). Each node 

si ∈ 

V represents a subsection, and a directed edge 

(si → sj) ∈ 

E indicates that subsection 

si 

is an essential prerequisite for writing 

sj 

. 

To infer these prerequisite relations, we prompt an LLM to analyze the outline O and identify, for each subsection, which earlier subsections it de-pends on (see prompt in Figure 16). The LLM assigns a dependency score from 1 to 5, where 5 denotes that the prior subsection is absolutely essential for writing the current one. Only depen-dencies with a score of 5 are retained as edges in 

E . If cycles are detected, we remove one edge per cycle, obtaining a Directed Acyclic Graph (DAG) G that captures the constraints among subsections. 

Based on this dependency graph G, we derive the writing order of all subsections with topological sorting. Each subsection 

s 

is assigned a stage in-dex 

τ(s), 

representing the depth of its dependency chain: 

τ(s) 

= 

   0 if 

In(s) 

= 

∅, 

max 

s′∈In(s) τ(s′) 

+ 1 

otherwise. 

(4) 

Finally, the dependency-aware plan Pdep extends Praw by attaching the stage index 

τ(si) 

to each subsection: 

Pdep[si] 

= 

(di, ri, ti, τ(si)). 

(5) 

Subsections assigned the same stage index can be written in parallel, while respecting the dependency constraints imposed by G. An example of the gen-erated dependency-aware writing plan is provided in Appendix B.2. 

3.2.2 SAWC: Structure-Aware Writing Controller 

The SAWC module serves as the central orchestra-tion engine across the entire writing process in the SurveyGen-I pipeline. Rather than being a single step, SAWC coordinates a sequence of interdepen-dent modules, including writing stage scheduling (Step 4), subsection-level literature retrieval (Step 

3691

https://lh3.googleusercontent.com/notebooklm/AKYWMX9hhVgfOAwqr9rNxfYZoWZzLTUb_tYSU04SoKLrTvFf9DJrURqjufc026rnnvv6LBIsZm-1kKcm3l9wMKRIRTZJ8twq53LcW5ha9cQUU2rK7o6R3onxKK5wxqxzgd99cLl8_WT6=w626-h328-v0

54de137d-d3b8-4286-a4a9-9fb8f0bbecb7

5), citation-aware writing (Step 6), memory updat-ing (Step 7), dynamic structure replanning (Steps 9–10), final refinement (Step 11), and table gen-eration (Step 12). Its control flow is illustrated throughout the center path of Figure 1. 

Parallel Subsection Execution. SAWC executes the dependency-aware writing plan Pdep by acti-vating all subsections with the same writing stage index 

τ(si) 

in parallel (Step 4). For each active sub-section 

si, 

SAWC first checks the retrieval control flag 

ri 

in 

Pdep[si]. 

If retrieval is required, SAWC triggers subsection-level literature retrieval (Step 5; see Section 3.1.2). The resulting paper set P∗ 

i 

is passed to the writing module (Step 6; see Sec-tion 3.3) for citation-aware subsection generation. 

Memory Mechanism for Global Consistency. To ensure structural coherence and terminologi-cal consistency across the survey, SAWC main-tains a dynamic structure memory M through-out writing. After each subsection 

si 

is written (Step 6), the system extracts key domain-specific terminology using LLMs, and stores both the ter-minology and the draft content into M (Step 7). This accumulated memory is then used to (1) guide subsequent subsection writing by enforcing con-sistency (see Section 3.3.2), and (2) provide feed-back for dynamic updates of the outline O and writing plan Pdep during structure replanning (see Section 3.2.3). 

Dynamic Structure Refinement. At the end of each writing stage, which corresponds to the com-pletion of all subsections 

si 

with the same stage index 

τ(si), 

SAWC triggers the Memory-Guided Structure Replanner (MGSR; see Section 3.2.3) to revise the outline and the writing plan based on the accumulated memory M (Step 9–10). This stage-wise feedback loop ensures that structural adjustments are continuously informed by prior writing outputs before the next stage begins. 

Final Refinement and Table Generation. Af-ter all subsections are written, SAWC performs a final refinement step to improve global coherence (Step 11). An LLM analyzes the full draft to detect logical contradictions, redundancy, and terminolog-ical/style inconsistencies. Based on this diagnosis, the system rewrites the relevant subsections to en-sure consistency. Then, for each subsection with the table flag 

ti 

enabled in 

Pdep[si], 

SAWC gener-ates a structured table based on the retrieved paper set (Step 12). See Appendix D for details. 

3.2.3 MGSR: Memory-Guided Structure Replanner 

After each writing stage, the MGSR module per-forms dynamic refinement of the outline and writ-ing plan based on the accumulated memory M and the current outline O. MGSR prompts an LLM (see prompt in Figure 15) to analyze redundancy, missing conceptual gaps, or suboptimal ordering within the unwritten subsections. It produces a set of structured revision actions (merge, delete, rename, reorder, add) applied to the remaining out-line. The updated writing plan P ′ 

dep is then derived from the revised outline O′ through the same plan-ning method used in the initial plan Pdep (see Sec-tion 3.2.1). This enables memory-guided structural evolution throughout writing, ensuring that later sections are adaptively optimized based on prior content while maintaining global consistency. 

3.3 CaM-Writing: Citation-Aware Subsection Writing with Memory Guidance 

This section introduces CaM-Writing, a citation-aware, memory-guided writing pipeline for generat-ing each survey subsection. The pipeline integrates a citation-tracing mechanism to enhance literature coverage and citation diversity, skeleton-based gen-eration guided by the memory M to ensure content consistency, and multi-stage refinement to improve clarity, coherence, and citation integrity. 

3.3.1 Context Construction with Citation Tracing 

To construct a rich and contextually relevant ev-idence set for writing each subsection 

si 

with description 

di, 

a RAG step is first applied over the global literature set P∗ 

i 

, which includes both survey-level and subsection-specific literature. Top-ranked passages are selected to form the initial writ-ing context 

Crag,i. 

However, the retrieved passages from academic papers often contain indirect cita-tions such as "[23]" and "Ge et al., 2023". These citations typically refer to influential prior work that is not directly included in the retrieved litera-ture. If the system relies solely on these secondary mentions without further resolution, it may over-look foundational or highly relevant papers. 

To address this issue, we introduce a citation-tracing mechanism that automatically identifies and resolves indirect citations within each retrieved context set 

Crag, i. 

Specifically, the mechanism detects citation markers such as “[3]” or “(Smith et al., 2020)” in 

Crag, i 

and employs an LLM to 

3692

determine whether each refers to an original source of a key concept or result. The tracing process is confined to the source papers of the top-ranked passages in 

Crag, i. 

For each of these papers, we retrieve structured reference metadata, including stable identifiers, author lists, titles, publication years, and abstracts, using the Semantic Scholar API. Markers identified as relevant are labeled as primary-source markers and aligned with the cor-responding bibliography entries of their source pa-pers by matching author names, titles, and pub-lication years. Successfully matched references are resolved through the API, and their abstracts are appended to 

Crag, i 

to construct the citation-enriched context 

Cenrich,i. 

Unmatched markers are safely ignored to avoid error propagation. 

To maintain explicit traceability between indirect citations and their original source, each enriched paper’s abstract is linked back to the original pas-sage where its citation marker appears, allowing the writing model to reason about the origin and relevance. For example, consider the passage: 

“... recent work has introduced reward-balanced fine-tuning for alignment (Ge et al., 2023), showing improvements over DPO and RLHF ...” 

The LLM flags “(Ge et al., 2023)” as primary-source marker, identifying it as introducing a core method. The system then resolves it to: 

Title: Preserve Your Own Correlation: A New Reward-Balanced Fine-Tuning Method Abstract: ‘We introduce a reward-balanced fine-tuning (RBF) framework for language model alignment...” 

This abstract is appended to the context, enabling the system to cite this traced paper directly in the generation. Further details and a citation-enriched context example are provided in Appendix E. 

3.3.2 Memory-Aligned Skeleton-Guided Generation 

Given the enriched context 

Cenrich,i, 

subsection title and description 

(ti, di), 

and the accumulated struc-ture memory M, the system first uses an LLM (see prompt in Figure 17) to generate a writing skele-ton 

Si 

outlining the key conceptual points. The memory M, which includes prior subsections and extracted terminology, ensures content coherence and terminology consistency across the survey. 

Best-of-N Selection. 

N 

candidate drafts are first generated based on the subsection title 

si, 

descrip-tion 

di, 

writing skeleton 

Si, 

and enriched context 

Cenrich,i 

(see prompt in Figure 18). An LLM then evaluates the candidates and selects the best version based on alignment with the skeleton, contextual relevance, and overall writing quality. 

Subsection-Level Refinement. To further im-prove the selected draft, a three-stage refinement is applied. First, the structure is adjusted to better reflect the conceptual flow defined by 

Si. 

Second, the draft undergoes citation refinement, where the LLM rewrites the text based on 

Cenrich,i. 

Finally, the draft is polished to enhance fluency and clarity. 

4 Experiments and Results 

4.1 Evaluation Setup 

SurveyGen-I is evaluated across six major scientific domains, which jointly cover both theoretical and applied areas of AI. Detailed topic distribution is provided in Appendix H. 

We compare SurveyGen-I with three representa-tive baselines: AutoSurvey (Wang et al., 2024), Sur-veyForge (Yan et al., 2025), and SurveyX (Liang et al., 2025). Demo reports from SurveyForge1 and SurveyX2 are collected from their official project pages. For SurveyForge, we select reports on ex-actly matched topics, while for SurveyX, domain-level matching is applied due to differences in topic coverage. Reports for AutoSurvey are gen-erated on matched topics using the same model as SurveyGen-I (GPT4o-mini (OpenAI, 2024)) to ensure fair comparison. 

4.2 Evaluation Metrics 

We comprehensively evaluate SurveyGen-I against three competitive baselines across two core dimen-sions, content quality and reference quality. 

Content Quality Evaluation. Measures the structural and semantic strength of the generated survey. This includes five sub-dimensions: cov-erage, relevance, structure, synthesis, and consis-tency. Each aspect is scored by LLM-as-Judge (Li et al., 2024a) (specifically, rated by GPT4o-mini), with explanation-based prompts to reduce variance. This directly reflects the impact of our MGSR and 

1SurveyForge: https://github.com/ Alpha-Innovator/SurveyForge 

2SurveyX: https://github.com/IAAR-Shanghai/ SurveyX 

3693

CaM-Writing, which aim to improve global coher-ence, abstraction, and flow. Evaluation criteria can be found in Appendix N. We compute the final content quality score (CQS) as the average of five evaluation dimensions. 

Reference Quality Evaluation. To assess the ef-fectiveness and recency of reference usage in the generated survey, we adopt three reference-level metrics that reflect citation coverage, intensity, and timeliness. The Number of References (NR) counts the distinct cited works, measuring the breadth of literature coverage. The Citation Density (CD) computes the number of unique citation markers per character of text (excluding the reference sec-tion), reflecting how frequently references are inte-grated into the main narrative. For reporting clarity, we scale CD by a factor of 104. The Recency Ratio (RR@k) measures the proportion of all cited ref-erences that were published within a recent time window (e.g., within the past 

k=3 

years). A higher RR indicates better engagement with the latest de-velopments in the field, and reflects the model’s ability to retrieve and integrate timely literature. 

4.3 Main Results 

We report evaluation results across content qual-ity and reference behavior, along with an ablation-based component analysis. SurveyGen-I is com-pared against three state-of-the-art baselines: Auto-Survey (Wang et al., 2024), SurveyX (Liang et al., 2025), and SurveyForge (Yan et al., 2025). Our re-sults demonstrate that SurveyGen-I achieves signif-icant improvements across all dimensions, showing its effectiveness for automated survey generation. 

To further validate the findings and evaluation protocol, we have conducted an additional human evaluation, setups and results are in Appendix K. 

Content Quality. SurveyGen-I achieves consis-tent improvements across all five content qual-ity dimensions compared to prior systems (Ta-ble 1). The content quality score (CQS) reaches 4.59, outperforming the best baseline (SurveyForge: 4.23). Largest gains are observed in structural flow (STRUC: +0.21) and synthesis (SYN: +0.41), in-dicating that the model maintains a coherent nar-rative while integrating information from diverse sources. Coverage (4.72) and relevance (4.76) also lead all baselines, suggesting high topical breadth and alignment. Consistency (4.59) improves no-tably over SurveyX (4.29), reflecting stability in 

Text Length 

100 

200 

300 

400 

500 

Nu m 

be r O 

f R ef 

er en 

ce s 

Ours AutoSurvey SurveyX SurveyForge 

(a) Ref count vs. length 

Text Length0 

5 

10 

15 

20 

25 

30 

35 

Ci ta 

tio n 

De ns 

ity 

Ours AutoSurvey SurveyX SurveyForge 

(b) Citation density 

Figure 3: Citation quality comparisons across models using KDE-enhanced scatter plots. (a) Number of ref-erences vs. text length. SurveyGen-I demonstrates a steeper citation scaling curve, suggesting deeper inte-gration of references even in longer texts. (b) Citation density vs. text length. SurveyGen-I maintains denser citation patterns across all lengths. 

terminology and phrasing across sections. No-tably, SurveyX uses GPT4o (Hurst et al., 2024), whereas our system relies on a smaller and more cost-efficient model, making the performance gap especially significant. Observed quality gains sug-gest that systems combining structural adaptivity, iterative refinement, and citation-tracing can more reliably generate high-quality surveys. 

Model CQS 

↑ 

COV 

↑ 

REL 

↑ 

STRUC 

↑ 

SYN 

↑ 

CONSIS 

↑ 

AutoSurvey 4.08 4.10 4.17 4.03 4.10 4.00 SurveyX 4.13 4.10 4.33 4.00 3.95 4.29 SurveyForge 4.23 4.31 4.41 4.07 4.21 4.17 Ours 4.59 4.72 4.76 4.28 4.62 4.59 

Table 1: LLM-based evaluation scores across multiple survey quality dimensions. Higher is better for cover-age (COV), relevance (REL), structural flow (STRUC), synthesis (SYN), and consistency (CONSIS). 

Reference Quality. In terms of citation quality and scientific grounding, SurveyGen-I exhibits both broader and denser reference usage. It cites 281 unique works per survey on average (Table 2), rep-resenting a sharp increase over SurveyX (102), and AutoSurvey (73). Citation density also rises sub-stantially (17.28), exceeding SurveyForge (5.52) by around 3 times, indicating tighter integration of references into the body text. Importantly, 89.1% of all citations are published within the past 5 years (RR@5), compared to 66.7% in SurveyX and Sur-veyForge, demonstrating significantly improved recency alignment. 

The steep scaling trend between reference count and text length in Figure 3a shows that text length remains relatively stable in SurveyGen-I, reflecting the fixed-length constraint imposed during gener-ation. It also demonstrates that SurveyGen-I in-

3694

https://lh3.googleusercontent.com/notebooklm/AKYWMX8Biis8N9YIEr0ShSHv2dOqjpswGZCTMoHgI1oGiAqK26LBVbdjWILk1vP1ugqAwSHzZPatP5FfXulHmFyGARZ1lKL1mUtLcm0D-3q3e7VdaUjvkLpn_XeB6ONWvqGtBvQdCx7d=w148-h148-v0

ac62bd99-8c32-4afb-8132-dd1145b5131b

https://lh3.googleusercontent.com/notebooklm/AKYWMX-CGahA28-A94ccsOXeNCNZwiHKaRSfK90N61xfRcEMduh_3HZvO6lUy0dRnmMGBQGy5SfWyPimMmyQ5NnVsIg7QQHiFr815YOBmN-qIsXddSicIuMHZ0ZrIjdfdoNOx0nNL6wAJg=w148-h148-v0

9a4f6145-7af2-4e07-aaf7-e792c270b821

cludes the most references overall. In contrast, Au-toSurvey consistently generates fewer references, and its citation count remains relatively flat, even as its text length slightly increases, which is un-expected given that the length parameter was con-trolled across all generations. This suggests weaker responsiveness to contextual expansion and under-utilization of available content space. Figure 3b fur-ther shows that SurveyGen-I consistently maintains a high citation density across varying text lengths, indicating robust integration of information-dense content. 

Model RR@1 RR@3 RR@5 RR@7 RR@10 CD NR AutoSurvey 0.174 0.639 0.837 0.940 0.992 1.54 73 SurveyX 0.239 0.484 0.667 0.792 0.916 13.57 102 SurveyForge 0.137 0.437 0.667 0.824 0.907 5.52 113 Ours 0.478 0.759 0.891 0.955 0.985 17.28 281 

Table 2: Recency-focused and structural citation met-rics. RR@k measures the proportion of cited references published within the past 

k 

years. CD (scaled by ×104) measures citation density; NR is the total number of cited references. 

A fine-grained evaluation for citation recency across six domains is provided in Appendix I. 

4.4 Ablation and Further Analysis 

Ablation Studies. We conduct ablation studies on the Language Models domain to evaluate the contribution of three key mechanisms: (1) w/o Ci-tation Trace disables the citation-tracing mech-anism (see Section 3.3.1); (2) w/o Plan Update disables the MGSR (Memory-Guided Structure Re-planner) module (see Section 3.2.3), fixing the out-line and writing plan without dynamic adjustment as new subsections are generated; and (3) w/o Fi-nal Refinement removes the final-stage multi-pass refinement phase (see Section 3.2.2). 

Model CQS 

↑ 

COV 

↑ 

REL 

↑ 

STRUC 

↑ 

SYN 

↑ 

CONSIS 

↑ 

NR 

↑ 

Ours (w/o Citation Trace) 4.60 4.57 4.57 4.43 4.71 4.71 225 Ours (w/o Plan Update) 4.49 4.57 4.71 4.29 4.43 4.43 212 Ours (w/o Refine) 4.34 4.43 4.43 4.14 4.43 4.29 286 Ours (Full) 4.77 4.71 4.86 4.71 4.86 4.71 286 

Table 3: Evaluation results of ablation variants. Each component (Trace, Plan Update, Refine) contributes to overall quality. 

Table 3 reports the impact of removing specific behaviors from SurveyGen-I. The full model yields the highest CQS 

(4.77), 

with synthesis and struc-ture both at 4.86 and 4.71, respectively. Disabling final refinement results in the steepest quality drop (CQS: 

−0.43), 

particularly in synthesis 

(−0.43) 

and structure 

(−0.57), 

indicating that single-pass 

generation without revision is insufficient for main-taining narrative integration. Fixed planning further reduces structural flow (STRUC: 

−0.42) 

and con-sistency (CONSIS: 

−0.28), 

suggesting that static outlines limit the model’s ability to adjust to unfold-ing content. Removing citation resolution reduces the number of distinct references by 61, despite stable consistency. 

Effect of Citation Tracing Mechanism. To fur-ther analyze the role of the citation tracing mech-anism, we quantify the number of indirect refer-ences traced during context construction. Across 121 subsections from four surveys generated by SurveyGen-I, an average of 8.43 indirect references per subsection were successfully traced. The pro-portion of new references introduced by tracing is summarized in Table 4. 

Proportion Range (%) # Subsections Percentage of Total (%) 0 27 22.3 0–20 16 13.2 20–40 27 22.3 40–60 32 26.4 60–80 16 13.2 80–100 3 2.5 Total 121 100.0 

Table 4: Proportion of newly introduced references per subsection after citation tracing (first column). 

Effect of Memory Length and Context Length. We further examine the token length of enriched contexts and memory used during subsection gen-eration. Across 121 subsections, the citation-enriched contexts 

Cenrich,i 

contain an average of 4.6k tokens, with a maximum length of approxi-mately 21k tokens, while the memory M used for skeleton generation averages 13.4k tokens, reach-ing up to 30k tokens. Both remain well within the 128k-token input limit of GPT4o-mini. 

5 Conclusion 

We present SurveyGen-I, a fully automated frame-work for generating academic surveys with high consistency, citation coverage, and structural co-herence. By integrating coarse-to-fine retrieval, adaptive planning, and memory-guided writing, SurveyGen-I effectively captures complex litera-ture landscapes and produces high-quality surveys without manual intervention. Extensive evaluations demonstrate its effectiveness over existing meth-ods, marking a step forward in reliable and scalable scientific synthesis. 

3695

Limitations 

While SurveyGen-I shows consistently strong performance across benchmarks, our framework adopts an online retrieval strategy to ensure access to up-to-date literature. However, this design in-troduces network sensitivity, variable latency, and reliance on third-party APIs, which may restrict full-text access due to licensing constraints. Com-pared to offline-indexed corpora used in prior work, our approach trades retrieval speed and infrastruc-ture control for broader coverage and freshness. 

Additionally, for niche or emerging topics with limited source material, the achievable survey length and depth are naturally constrained. This shows a general challenge in automatic survey gen-eration: content quality is ultimately bounded by the availability and granularity of the source lit-erature. Moreover, some evaluation signals may reflect subjective preferences rather than universal writing standards. Our current evaluation primarily focuses on AI-related domains, which provides a strong but domain-specific validation. Future work will expand evaluation to broader scientific areas to test generalizability across disciplines. 

Future work may focus on minimizing exter-nal dependencies and enabling more local process-ing by developing modular, domain-specialized variants of the framework, where different agents are supported by parameter-efficient, locally fine-tuned models (Shen et al., 2025; Huang et al., 2025). Complementary reinforcement-learning-based methods (Sun et al., 2024; Jiang et al., 2025a) could further enhance adaptive control and synthe-sis stability. 

Ethics Statement 

This research focuses on developing a transparent and responsible framework for automated survey generation. SurveyGen-I is intended solely as a re-search and writing assistant to support scholars in organizing, retrieving, and synthesizing literature. It does not aim to produce publishable manuscripts without human validation. Human users must care-fully review and verify all generated content before any academic use. 

Our experiments use only open-access scientific literature and publicly available benchmarks. No personal, sensitive, or proprietary data were used. We acknowledge that automated generation may still produce incomplete or biased representations of prior work, and therefore encourage human veri-

fication in any downstream use. 

Acknowledgement 

This work was supported by the Dutch Na-tional Growth Fund through the 6G flagship project "Future Network Services" (Grant Num-ber: NGF6G2301). 

References Shubham Agarwal, Gaurav Sahu, Abhay Puri, Issam H 

Laradji, Krishnamurthy DJ Dvijotham, Jason Stan-ley, Laurent Charlin, and Christopher Pal. 2024. Litllm: A toolkit for scientific literature review. arXiv preprint arXiv:2402.01788. 

Shubham Agarwal, Gaurav Sahu, Abhay Puri, Issam H. Laradji, Krishnamurthy Dj Dvijotham, Jason Stan-ley, Laurent Charlin, and Christopher Pal. 2025. LitLLMs, LLMs for literature review: Are we there yet? Transactions on Machine Learning Research. 

Nurshat Fateh Ali, Md. Mahdi Mohtasim, Shakil Mosharrof, and T. Gopi Krishna. 2024. Automated literature review using nlp techniques and llm-based retrieval-augmented generation. In 2024 Interna-tional Conference on Innovations in Science, Engi-neering and Technology, pages 1–6. 

Waleed Ammar, Dirk Groeneveld, Chandra Bhagavat-ula, Iz Beltagy, Miles Crawford, Doug Downey, Ja-son Dunkelberger, Ahmed Elgohary, Sergey Feldman, Vu Ha, and 1 others. 2018. Construction of the liter-ature graph in semantic scholar. In Proceedings of the 2018 Conference of the North American Chap-ter of the Association for Computational Linguistics: Human Language Technologies, Volume 3 (Industry Papers), pages 84–91. 

Hongye An, Arpit Narechania, Emily Wall, and Kai Xu. 2024. Vitality 2: Reviewing academic litera-ture using large language models. arXiv preprint arXiv:2408.13450. 

Artifex. 2025. PyMuPDF 1.25.5 documentation. Ac-cessed: 2025-05-20. 

David Brett and Anniek Myatt. 2025. Patience is all you need! an agentic system for performing scientific literature review. arXiv preprint arXiv:2504.08752. 

Angela Carrera-Rivera, William Ochoa, Felix Larrinaga, and Ganix Lasa. 2022. How-to conduct a systematic literature review: A quick guide for computer science research. MethodsX, 9:101895. 

Ruediger Ehlers. 2017. Formal verification of piece-wise linear feed-forward neural networks. In Inter-national symposium on automated technology for verification and analysis, pages 269–286. 

3696

Wenqi Fan, Yujuan Ding, Liangbo Ning, Shijie Wang, Hengyun Li, Dawei Yin, Tat-Seng Chua, and Qing Li. 2024. A survey on rag meeting llms: Towards retrieval-augmented large language models. In Pro-ceedings of the 30th ACM SIGKDD Conference on Knowledge Discovery and Data Mining, pages 6491– 6501. 

Raymond Fok, Joseph Chee Chang, Marissa Raden-sky, Pao Siangliulue, Jonathan Bragg, Amy X Zhang, and Daniel S Weld. 2025. Facets, taxonomies, and syntheses: Navigating structured representa-tions in llm-assisted literature review. arXiv preprint arXiv:2504.18496. 

Yunfan Gao, Yun Xiong, Xinyu Gao, Kangxiang Jia, Jinliu Pan, Yuxi Bi, Yixin Dai, Jiawei Sun, Haofen Wang, and Haofen Wang. 2023. Retrieval-augmented generation for large language models: A survey. arXiv preprint arXiv:2312.10997. 

Cong Duy Vu Hoang and Min-Yen Kan. 2010. Towards automated related work summarization. In Coling 2010: Posters, pages 427–435. 

Yue Hu and Xiaojun Wan. 2014. Automatic genera-tion of related work sections in scientific papers: an optimization approach. In Proceedings of the 2014 Conference on Empirical Methods in Natural Lan-guage Processing, pages 1624–1633. 

Jia-Hong Huang, Yixian Shen, Hongyi Zhu, Stevan Rudinac, and Evangelos Kanoulas. 2025. Gradient weight-normalized low-rank projection for efficient llm training. In Proceedings of the AAAI Conference on Artificial Intelligence, volume 39, pages 24123– 24131. 

Aaron Hurst, Adam Lerer, Adam P Goucher, Adam Perelman, Aditya Ramesh, Aidan Clark, AJ Ostrow, Akila Welihinda, Alan Hayes, Alec Radford, and 1 others. 2024. Gpt-4o system card. arXiv preprint arXiv:2410.21276. 

Xia Jiang, Yaoxin Wu, Minshuo Li, Zhiguang Cao, and Yingqian Zhang. 2025a. Large language models as end-to-end combinatorial optimization solvers. arXiv preprint arXiv:2509.16865. 

Xia Jiang, Yaoxin Wu, Chenhao Zhang, and Yingqian Zhang. 2025b. DRoc: Elevating large language mod-els for complex vehicle routing via decomposed re-trieval of constraints. In The 13th International Con-ference on Learning Representations. 

Tetsu Kasanishi, Masaru Isonuma, Junichiro Mori, and Ichiro Sakata. 2023. SciReviewGen: A large-scale dataset for automatic literature review generation. In Findings of the Association for Computational Linguistics, pages 6695–6715. 

Guy Katz, Derek A Huang, Duligur Ibeling, Kyle Ju-lian, Christopher Lazarus, Rachel Lim, Parth Shah, Shantanu Thakoor, Haoze Wu, Aleksandar Zeljić, and 1 others. 2019. The marabou framework for ver-ification and analysis of deep neural networks. In 

International Conference on Computer Aided Verifi-cation, pages 443–452. 

Yuxuan Lai, Yupeng Wu, Yidan Wang, Wenpeng Hu, and Chen Zheng. 2024. Instruct large language mod-els to generate scientific literature survey step by step. In CCF International Conference on Natural Lan-guage Processing and Chinese Computing, pages 484–496. 

Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Hein-rich Küttler, Mike Lewis, Wen-tau Yih, Tim Rock-täschel, and 1 others. 2020. Retrieval-augmented generation for knowledge-intensive nlp tasks. Ad-vances in Neural Information Processing Systems, 33:9459–9474. 

Haitao Li, Qian Dong, Junjie Chen, Huixue Su, Yu-jia Zhou, Qingyao Ai, Ziyi Ye, and Yiqun Liu. 2024a. LLMs-as-judges: a comprehensive survey on LLM-based evaluation methods. arXiv preprint arXiv:2412.05579. 

Long Li, Weiwen Xu, Jiayan Guo, Ruochen Zhao, Xingxuan Li, Yuqian Yuan, Boqiang Zhang, Yuming Jiang, Yifei Xin, Ronghao Dang, and 1 others. 2024b. Chain of ideas: Revolutionizing research via novel idea development with llm agents. arXiv preprint arXiv:2410.13185. 

Yutong Li, Lu Chen, Aiwei Liu, Kai Yu, and Lijie Wen. 2025. Chatcite: Llm agent with human workflow guidance for comparative literature summary. In Proceedings of the 31st International Conference on Computational Linguistics, pages 3613–3630. 

Xun Liang, Jiawei Yang, Yezhaohui Wang, Chen Tang, Zifan Zheng, Shichao Song, Zehao Lin, Yebin Yang, Simin Niu, Hanyu Wang, and 1 others. 2025. Sur-veyx: Academic survey automation via large lan-guage models. arXiv preprint arXiv:2502.14776. 

Jiaxiang Liu, Yunhan Xing, Xiaomu Shi, Fu Song, Zhiwu Xu, and Zhong Ming. 2024. Abstraction and refinement: towards scalable and exact verification of neural networks. ACM Transactions on Software Engineering and Methodology, 33(5):1–35. 

Hidetsugu Nanba, Noriko Kando, and Manabu Oku-mura. 2000. Classification of research papers using citation links and citation types: Towards automatic review article generation. Advances in Classification Research Online, pages 117–134. 

Benjamin Newman, Yoonjoo Lee, Aakanksha Naik, Pao Siangliulue, Raymond Fok, Juho Kim, Daniel S Weld, Joseph Chee Chang, and Kyle Lo. 2024. ArxivDI-GESTables: Synthesizing scientific literature into tables using language models. In Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing, pages 9612–9631. 

Zach Nussbaum, John Xavier Morris, Andriy Mul-yar, and Brandon Duderstadt. 2025. Nomic embed: Training a reproducible long context text embedder. 

3697

Transactions on Machine Learning Research. Repro-ducibility Certification. 

OpenAI. 2024. Gpt-4o mini: Advancing cost-efficient intelligence. Accessed: 2025-05-20. 

Eugênio Piveta Pozzobon and Humberto Pinheiro. 2024. Implementation of a research assistant for literature review with large language models. In 16th Seminar on Power Electronics and Control, pages 1–5. IEEE. 

Pouria Rouzrokh and Moein Shariatnia. 2025. Lattere-view: A multi-agent framework for systematic re-view automation using large language models. arXiv preprint arXiv:2501.05468. 

Abdul Malik Sami, Zeeshan Rasheed, Kai-Kristian Kemell, Muhammad Waseem, Terhi Kilamo, Mika Saari, Anh Nguyen Duc, Kari Systä, and Pekka Abra-hamsson. 2024. System for systematic literature re-view using multiple ai agents: Concept and an empir-ical evaluation. arXiv preprint arXiv:2403.08399. 

Yixian Shen, Qi Bi, Jia-hong Huang, Hongyi Zhu, Andy D. Pimentel, and Anuj Pathania. 2025. MaCP: Minimal yet mighty adaptation via hierarchical co-sine projection. In Proceedings of the 63rd Annual Meeting of the Association for Computational Lin-guistics (Volume 1: Long Papers), pages 20602– 20618, Vienna, Austria. Association for Computa-tional Linguistics. 

Kartik Shinde, Trinita Roy, and Tirthankar Ghosal. 2022. An extractive-abstractive approach for multi-document summarization of scientific articles for lit-erature review. In Proceedings of the 3rd Workshop on Scholarly Document Processing, pages 204–209. 

Amanpreet Singh, Joseph Chee Chang, Chloe Anastasi-ades, Dany Haddad, Aakanksha Naik, Amber Tanaka, Angele Zamarron, Cecile Nguyen, Jena D Hwang, Jason Dunkleberger, and 1 others. 2025. Ai2 scholar qa: Organized literature synthesis with attribution. arXiv preprint arXiv:2504.10861. 

Kaitao Song, Xu Tan, Tao Qin, Jianfeng Lu, and Tie-Yan Liu. 2020. MPNet: Masked and permuted pre-training for language understanding. In Advances in Neural Information Processing Systems, volume 33, pages 16857–16867. 

Chuanneng Sun, Songjun Huang, and Dario Pompili. 2024. Llm-based multi-agent reinforcement learn-ing: Current and future directions. arXiv preprint arXiv:2405.11106. 

Xiaoping Sun and Hai Zhuge. 2019. Automatic genera-tion of survey paper based on template tree. In 15th International Conference on Semantics, Knowledge and Grids, pages 89–96. IEEE. 

Teo Susnjak, Peter Hwang, Napoleon Reyes, An-dre LC Barczak, Timothy McIntosh, and Surangika Ranathunga. 2025. Automating research synthe-sis with domain-specific large language model fine-tuning. ACM Transactions on Knowledge Discovery from Data, 19(3):1–39. 

Jie Wang, Chengzhi Zhang, Mengying Zhang, and San-hong Deng. 2018. CitationAS: A tool of automatic survey generation based on citation content. J. Data Inf. Sci., 3(2):20–37. 

Yidong Wang, Qi Guo, Wenjin Yao, Hongbo Zhang, Xin Zhang, Zhen Wu, Meishan Zhang, Xinyu Dai, Qingsong Wen, Wei Ye, and 1 others. 2024. Autosur-vey: Large language models can automatically write surveys. Advances in Neural Information Processing Systems, 37:115119–115145. 

Chang Xiao. 2023. Autosurveygpt: Gpt-enhanced auto-mated literature discovery. In Adjunct Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology, pages 1–3. 

Shitao Xiao, Zheng Liu, Peitian Zhang, Niklas Muen-nighoff, Defu Lian, and Jian-Yun Nie. 2024. C-pack: Packed resources for general chinese embeddings. In Proceedings of the 47th international ACM SIGIR conference on research and development in informa-tion retrieval, pages 641–649. 

Xiangchao Yan, Shiyang Feng, Jiakang Yuan, Renqiu Xia, Bin Wang, Lei Bai, and Bo Zhang. 2025. SUR-VEYFORGE : On the outline heuristics, memory-driven generation, and multi-dimensional evaluation for automated survey writing. In Proceedings of the 63rd Annual Meeting of the Association for Compu-tational Linguistics (Volume 1: Long Papers), pages 12444–12465. 

Yusen Zhang, Ruoxi Sun, Yanfei Chen, Tomas Pfister, Rui Zhang, and Sercan Arik. 2024. Chain of agents: Large language models collaborating on long-context tasks. Advances in Neural Information Processing Systems, 37:132208–132237. 

3698

Appendix Contents 

 Section A: SurveyGen-I Pipeline 

 Section B: SurveyGen-I Implementation Details 

 Section C: Case Study: Dynamic Outline Updating 

 Section D: Table Generation Implementation 

 Section E: Details of Citation Tracing for Context Grounding 

 Section F: AutoSurvey Implementation 

 Section G: Supplementary Experiments: Ai2 Scholar QA 

 Section H: Topic Coverage 

 Section I: Subtopic-Level Analysis of Recency Behavior 

 Section J: Discussion on Metrics and Usage 

 Section K: Human Evaluation Study 

 Section L: License and Terms of Use 

 Section M: Examples of Generated Surveys 

 Section N: Prompts Used 

A SurveyGen-I Pipeline 

B SurveyGen-I Implementation Details 

B.1 Implementation of Literature Retrieval Our literature retrieval system differentiates be-tween survey-level and subsection-level retrieval. 

At the survey level, retrieval is guided by the user-specified topic and its explanatory text, which are refined through an LLM-based intent clarifica-tion step to produce a focused query representing the overall survey scope. At the subsection level, retrieval uses the section and subsection titles and descriptions as input, enabling the LLM to dis-ambiguate fine-grained intent within the broader survey context. 

For citation expansion, citation-based expansion is performed only for the top 10 papers with higher similarity score, where their references and cita-tions are retrieved to enrich topic coverage. 

For filtering, we adopt a two-stage relevance se-lection strategy after citation expansion. First, all retrieved papers are pre-filtered by cosine similar-ity (threshold = 0.3) using all-mpnet-base-v2 embeddings (Song et al., 2020) to remove seman-tically irrelevant results. Second, the remaining papers are evaluated by an LLM that assigns a rel-evance score in the range [0, 100]; only papers with scores 

≥ 

70 are retained. These thresholds 

Algorithm 1 SurveyGen-I Pipeline Require: Research topic 

T 

, description 

E 

// LR: Coarse-to-Fine Literature Retrieval 1: Pinit 

← KEYWORDSEARCH(T,E) 

2: Psem 

← SEMANTICFILTER(Pinit, T, E) 

3: P∗ 

← EXPANDANDRANK(Psem, T, E) 

// PlanEvo: Structure Planning and Scheduling 4: O 

← GENERATEOUTLINE(P∗, T, E) 

5: Pdep 

← 

BUILDSCHEDULE(O) 6: 

M← ∅ 

// CaM-Writing 7: for 

t 

= 0 to max 

si∈O τ(si) 

do 

8: 

St ← {si ∈ 

O | 

τ(si) 

= 

t} 

9: for all 

si ∈ St 

do 

10: 

(di, ri, ti)← Pdep[si] 

11: if 

ri 

= True then 12: 

Pi ← SUBSECTIONRETRIEVAL(si, di) 

13: else 14: 

Pi ← ∅ 

15: end if 16: P∗ 

i ← 

P∗ 

∪ Pi 

17: 

Crag,i ← RAGRETRIEVE(si,P∗ i 

) 

18: 

Cenrich,i ← CITATIONTRACE(Crag,i) 

19: 

Si ← MAKESKELETON(si, di,M) 

20: 

ŝ (1:N) i ← WRITE(si, di,Si, Cenrich,i) 

21: 

ŝ∗i ← SELECTBEST(ŝ (1:N) i 

) 

22: 

ŝi ← REFINE(ŝ∗i ,Si, Cenrich,i) 

23: 

M←M∪ EXTRACTMEMORY(ŝi) 

24: end for 25: 

(O′,P 

′ 

dep)← MGSR.UPDATEPLAN(O,Pdep,M) 

26: O 

← 

O′; Pdep 

← 

P ′ 

dep 27: end for 28: 

GLOBALREFINE(O,M) 

29: return Final survey draft 

were chosen empirically to balance precision and recall across diverse topics. If no papers meet the relevance threshold, a fallback selects the top 5 most relevant candidates to ensure writing continu-ity. To control downstream computational cost, the number of retained papers per query is capped at 30. 

All filtered papers are associated with structured metadata, including bibkey, title, abstract, paper ID, and download URL. We download each pa-per’s PDF asynchronously using available metadata from Semantic Scholar. The downloaded PDFs are parsed with PyMuPDF (Artifex, 2025) to extract clean textual content, which is stored alongside the metadata for downstream use in vectorstore con-struction, RAG retrieval, and citation tracing. All paper metadata and extracted content are persisted in CSV format, and BibTeX entries for retained papers are compiled into a unified reference file for LaTeX formatting. 

3699

B.2 Outline and Writing Plan Generation 

B.2.1 Survey Outline Example The following example illustrates the JSON-based outline used to guide planning and writing. It de-fines high-level sections and their conceptual sub-sections: 

{ "section_title": "Fine -Tuning 

Methodologies for Enhanced Translation", 

"section_description": "This section categorizes and analyzes various fine -tuning methodologies employed in multilingual models , 

emphasizing their effectiveness for Chinese to Malay translation." , 

"subsections": [ { 

"subsection_title": "Adaptive Fine -Tuning Techniques", 

"subsection_description": " Discusses adaptive fine -tuning methods , including Layer -

Freezing and Low -Rank Adaptation , and their roles in optimizing model performance. 

" }, { 

"subsection_title": "Utilization of Adapter Modules", 

"subsection_description": " Explores the implementation of adapter modules for fine -

tuning , highlighting their efficiency and effectiveness in multilingual speech translation tasks." 

}, { 

"subsection_title": "Data Augmentation Strategies", 

"subsection_description": " Investigates the role of data augmentation techniques , including code -switching , in enhancing model robustness and translation quality." 

} ] 

} 

B.2.2 Writing Plan Example The following snippet is a real system-generated writing plan segment for the same section. It in-cludes execution flags, dependency controls, and writing index: 

[ { 

"section_title": "Fine -Tuning Methodologies for Enhanced Translation", 

"subsection_title": "Adaptive Fine -Tuning Techniques", 

"subsection_description": "Discusses adaptive fine -tuning methods , 

including Layer -Freezing and Low -Rank Adaptation , and their roles in optimizing model performance.", 

"index": 2, "trigger_additional_search": true , "generate_table": true , "depends_on": [ 

"Challenges in Data Availability and Quality" 

] }, { 

"section_title": "Fine -Tuning Methodologies for Enhanced Translation", 

"subsection_title": "Utilization of Adapter Modules", 

"subsection_description": "Explores the implementation of adapter modules for fine -tuning , highlighting their efficiency and effectiveness in multilingual speech translation tasks.", 

"index": 3, "trigger_additional_search": true , "generate_table": true , "depends_on": [ 

"Adaptive Fine -Tuning Techniques" ] 

}, { 

"section_title": "Fine -Tuning Methodologies for Enhanced Translation", 

"subsection_title": "Data Augmentation Strategies", 

"subsection_description": " Investigates the role of data augmentation techniques , including code -switching , in enhancing model robustness and translation quality.", 

"index": 3, "trigger_additional_search": true , "generate_table": true , "depends_on": [ 

"Challenges in Data Availability and Quality", 

"Adaptive Fine -Tuning Techniques" ] 

} ] 

B.2.3 Implementation Notes 

The index field determines batch-level parallel writing: subsections with the same index value can be written concurrently. The depends_on field specifies logical dependencies between sub-sections, indicating which earlier subsections must be completed before the current subsection. 

3700

Initial AutoML Survey Outline (Before MGSR Update) 

 Section 1: Introduction – Historical Evolution of AutoML; Motivations for Automation in Machine Learning. 

 Section 2: Conceptual Foundations of AutoML – Bi-level Optimization Framework; Search Space Design and Strategy Dynamics; Evaluation Metrics for AutoML Systems. 

 Section 3: Methodological Innovations in AutoML – Neural Architecture Search (NAS); Hyperparameter Optimization Strategies; Meta-Learning in AutoML. 

 Section 4: Applications of AutoML Across Domains – Healthcare Applications; Financial Services Applications; Marketing and Customer Analytics. 

 Section 5: Challenges and Limitations of AutoML – Transparency and Interpretability Challenges; Data Quality and Bias Issues; Scalability and Resource Limitations. 

 Section 6: Emerging Trends in AutoML – Integration with Cloud Computing; Advancements for Unstructured Data; Ethical Considerations and Governance Frameworks. 

 Section 7: Comparative Analysis of AutoML Frameworks – Benchmarking Methodologies for AutoML Tools; Usability and Accessibility of Frameworks; Performance Evaluation Across Diverse Datasets. 

 Section 8: Future Directions in AutoML Research – Advancements in Explainable AI; Cross-Domain General-ization Strategies; Integration with Other AI Paradigms. 

 Section 9: Conclusion – Recap of Key Insights; Future Research Directions. 

Figure 4: Initial AutoML outline before MGSR-based refinement. 

The trigger_additional_search flag controls whether extra paper retrieval will be performed per subsection. Finally, generate_table signals whether this subsection requires automatic genera-tion of a literature table summarizing relevant meth-ods, datasets, or evaluation metrics. 

C Case Study: Dynamic Outline Updating 

To illustrate the impact of our dynamic outline up-dating mechanism (MGSR, see Section 3.2.3), we compare the survey outline before and after itera-tive updates for the generated survey titled “Foun-dations and Future Directions of Automated Ma-chine Learning: Advancements and Applications.” The initial outline (Figure 4) represents the first au-tomatically generated structure, while the final ver-sion (Figure 5) shows the result after seven rounds of MGSR-based refinement. The comparison high-lights how MGSR improves topic coverage and conceptual organization. 

D Table Generation Implementation 

D.1 Overview For each subsection in the writing plan, the system determines whether to generate a table based on the number and diversity of relevant papers. If the number of filtered, non-review papers exceeds a 

certain threshold (typically 10), a method aggrega-tion table is created to group papers into concep-tual categories. Otherwise, the system generates an aspect-based comparison table that compares papers across a small set of important dimensions. 

D.2 Method Aggregation Table 

When a subsection contains at least ten papers, the system generates a table that organizes the liter-ature into high-level categories under a common comparative theme. The core aspect, for example, training paradigm, objective, or architecture type is first inferred using an LLM based on the subsec-tion description and paper abstracts. A set of 4–6 concise method categories is then proposed by ana-lyzing the previously written subsection content. 

Each paper is assigned to one or more categories using RAG. The system constructs a query from the paper’s metadata, retrieves relevant content from the paper’s vectorized representation, and uses an LLM to classify the paper accordingly. Categories with fewer than two papers or labeled as “Others” are excluded from the final table. 

D.3 Aspect-Based Comparison Table 

If a subsection contains fewer than ten papers, the system generates a table comparing these papers across several dimensions, typically three to five, following the method proposed in Newman et al. 

3701

https://lh3.googleusercontent.com/notebooklm/AKYWMX9lTbl07DOUJ_liouZylf4isCp3-pFHclTFTVtY_KskVowV2eN4qHRKnHw2L_ekN2b6xfJglr3nw_09JMSl_EhiYhkw17C-Kh2YhsbHR1LVBZKPZpwdEoJuFMsjnjv30Vo3E7HqbQ=w640-h370-v0

65c70966-3500-41dd-b35d-33ba4a44a2fb

Refined AutoML Survey Outline (After 7 Rounds of MGSR Updates) 

 Section 1: Introduction – Historical Evolution of AutoML; Motivations for Automation in Machine Learning. 

 Section 2: Conceptual Foundations of AutoML – Bi-level Optimization Framework; Search Space Design and Strategy Dynamics; Evaluation Metrics for AutoML Systems; Robustness and Generalization in AutoML; Theoretical Underpinnings of AutoML. 

 Section 3: Methodological Innovations in AutoML – Neural Architecture Search (NAS); Hyperparameter Opti-mization Strategies; Meta-Learning in AutoML; Transfer Learning in AutoML; Automated Feature Engineering Techniques. 

 Section 4: Applications of AutoML Across Domains – Healthcare Applications; Financial Services Applications; Marketing and Customer Analytics; Emerging Applications in Industry. 

 Section 5: Challenges and Limitations of AutoML – Transparency and Interpretability Challenges; Data Quality and Bias Issues; Ethical and Social Implications; Scalability and Resource Limitations; Deployment Bottlenecks. 

 Section 6: Emerging Trends in AutoML – Ethical Considerations and Governance Frameworks; Integration with Cloud Computing; Advancements in Explainable AI; Advancements for Unstructured Data. 

 Section 7: Comparative Analysis of AutoML Frameworks – Benchmarking Methodologies for AutoML Tools; Usability and Accessibility of Frameworks; Performance Evaluation Across Diverse Datasets; Evaluation of Frameworks for Unstructured Data. 

 Section 8: Future Directions in AutoML Research – Advancements in Explainable AI; Exploration of Domain-Specific AutoML Frameworks; Research into Bias Detection Mechanisms; Exploration of Ethical AI Practices. 

 Section 9: Conclusion – Recap of Key Insights; Future Research Directions. 

Figure 5: Final AutoML outline after seven MGSR iterations, showing enhanced conceptual coverage and structure depth. 

(2024). These aspects are automatically selected by analyzing the subsection’s topic, abstract, and the written text of this subsection. For each (paper, aspect) pair, a dedicated query is constructed, and top-ranked passages are retrieved from the paper’s content using FAISS-based similarity search and reranking. These snippets are summarized using an LLM into short, informative values. The result-ing table presents papers as rows and aspects as columns. 

E Details of Citation Tracing for Context Grounding 

Subsection-Specific RAG Retrieval and Reranking. Retrieval-Augmented Generation (RAG) (Lewis et al., 2020) combines dense retrieval with generation, enabling models to ground outputs on external knowledge (Jiang et al., 2025b; Fan et al., 2024). Given a subsection title 

si 

and description 

di, 

we form a semantic query 

qi 

and retrieve at the passage level. The retrieval corpus is the union of two sources: the survey-level collection P∗ (full-scope) and the subsection-level collection 

Pi 

(specific to 

si). 

All papers are seg-mented into textual passages and embedded with 

BAAI/bge-small-en-v1.5; each passage carries metadata (bibkey, title, abstract, pdf_path). For each source separately, we retrieve the 

top-K 

passages by cosine similarity to 

qi (top-K 

from P∗ 

and 

top-K 

from 

Pi). 

We then deduplicate across sources to obtain a merged candidate set. To refine semantic precision, we apply a cross-encoder reranker BAAI/bge-reranker-base (Xiao et al., 2024) on 

(qi, 

passage) pairs from the merged set and select the top-10 passages by the reranker score. These passages constitute the initial RAG context 

Crag,i 

for subsection 

si. 

Citation Marker Detection and Primary-source Markers Decision. Each passage in 

Crag,i 

is scanned for citation markers using regular expres-sions. The system detects both numeric patterns such as “[17]” and author-year formats such as “(Ge et al., 2023)”. These markers are then evalu-ated for whether they refer to an original contribu-tion worth tracing. 

To perform this evaluation, we prompt an LLM with the subsection title, description, and raw pas-sage text. The prompt asks the LLM to identify all citation markers and return a structured assessment for each, including a boolean flag and a natural lan-

3702

https://lh3.googleusercontent.com/notebooklm/AKYWMX_t04wl3hFpo9aw7iAZPBQXB5yTZdazTp9boxuAxv6ywTniCYosOOSJu8xNahI0hAzXoglHyZ9qPBxiJH1iJUWxbjVR6HchsnabXz_Y8u40U8XRfHdcb3sNgDCo3yl8oVYCHmd1hA=w640-h413-v0

613d9222-6e3d-4b04-a311-cf1dba6a61dd

Enriched Context Example 

Original Document: Title: Abstraction and Refinement: Towards Scalable and Exact Verification of Neural Networks Bibkey: Liu2022AbstractionAR 

RAG Snippet: 

... restoring the same amount of accuracy. Our approach is orthogonal to and can be integrated with many existing approaches. For evaluation, we implement our approach as a tool NARv using two promising and exact tools Marabou [Katz et al., 2019] and Planet [Ehlers, 2017] as back-end verification engines. 

Reasoning Trace: (Katz et al., 2019) in RAG Snippet 

→ 

Traced BIBKEY: Katz2019TheMF — Title: The Marabou Framework for Verification and Analysis of Deep Neural Networks. Abstract: Deep neural networks are revolutionizing the way complex systems are designed. (summary omitted for brevity). 

(Ehlers et al., 2017) in RAG Snippet 

→ 

Traced BIBKEY: Ehlers2017FormalVO — Title: Formal Verification of Piece-Wise Linear Feed-Forward Neural Networks. Abstract: We present an approach for the verification of feed-forward neural networks in which all nodes have a piece-wise linear activation function. (summary omitted). 

Figure 6: Illustration of citation tracing enriching retrieved RAG context. 

guage explanation. The output is parsed into a list of dictionaries; only citations flagged as primary source markers are considered for tracing. 

Example. Figure 6 illustrates how citation trac-ing expands the retrieved context by resolving ref-erenced works back to their original sources. The example passage is from Liu et al. (2024), whose inline markers trace to Katz et al. (2019) and Ehlers (2017). 

F AutoSurvey Implementation 

We follow an open-source AutoSurvey imple-mentation with the generation model set to gpt-4o-mini-2024-07-18, the embedding model set to nomic-ai/nomic-embed-text-v1 (Nuss-baum et al., 2025), and retrieval configured with 2500 papers for outline construction. To ensure a fair comparison, the list of topics used for genera-tion is aligned exactly with that of our system. 

G Supplementary Experiments: Ai2 Scholar QA 

Our task (end-to-end survey generation) optimizes document-scale qualities, including global struc-ture, cross-section consistency, and rich, traceable 

citations. This differs from long-form scientific QA, which targets query-focused aggregation of evidence. We therefore position a deployed QA system, Ai2 Scholar QA (Singh et al., 2025), as a cross-task reference to contextualize SurveyGen-I among user-facing literature tools and to contrast behaviors across settings. We run Ai2 Scholar QA on the Language Models topic in default settings to generate the report, and evaluate it with the iden-tical rubrics used in SurveyGen-I. 

Content Quality. As shown in Table 5, Ai2 Scholar QA produces generally coherent but less structured reports, achieving an overall content quality score (CQS) of 3.94. While coverage and relevance remain reasonable, synthesis (3.43) and structural flow (4.00) lag behind survey-oriented systems. 

Model CQS 

↑ 

COV 

↑ 

REL 

↑ 

STRUC 

↑ 

SYN 

↑ 

CONSIS 

↑ 

Ai2 Scholar QA 3.94 4.00 4.29 4.00 3.43 4.00 Ours 4.59 4.72 4.76 4.28 4.62 4.59 

Table 5: Supplementary content-quality evaluation re-sults for Ai2 Scholar QA. 

Reference Quality. Table 6 summarizes reference-based metrics. Although Ai2 Scholar QA 

3703

https://lh3.googleusercontent.com/notebooklm/AKYWMX_LJQT9iKTSKx3Ru68qiJWggL7ojCmL_4jxcGg2d5dH4ZqyfMpFdJqgA4mxL4RYSUCYZ_Hu7yHoTY24IVzoZYPstuKeYHp6WEhkJo-1f5gqZhx4lPrUXKLEd6BDfMl-jhcvmUwg3A=w640-h419-v0

bc91069b-45b1-4c2a-8e7a-373ceaccbf25

exhibits relatively high recency (RR@1–RR@5) and citation density (15.19), the total number of references per survey (35) is significantly smaller. 

Model RR@1 RR@3 RR@5 RR@7 RR@10 CD NR Ai2 Scholar QA 0.468 0.676 0.773 0.833 0.857 15.19 35 Ours 0.478 0.759 0.891 0.955 0.985 17.28 281 

Table 6: Supplementary reference-quality metrics for Ai2 Scholar QA. 

Overall, Ai2 Scholar QA shows good citation density and recency, but the total number of cited papers is notably limited compared with survey-generation systems. 

H Topic Coverage 

Table 7 summarizes the benchmark composition used in our experiments. The benchmark spans six major scientific domains, covering a diverse range of research areas. Each domain includes rep-resentative survey papers automatically generated by SurveyGen-I. 

I Subtopic-Level Analysis of Recency Behavior 

The impact of different subtopics on survey metrics is mainly reflected in timeliness. Table 8 presents updated recency ratio comparisons across six ma-jor subtopics. SurveyGen-I maintains consistently strong performance, ranking first in RR@1 across all subtopics, and achieving top-2 results in nearly every other metric. This indicates superior priori-tization of the most recent literature compared to all baselines. In particular, our model leads by a large margin on early recency in complex do-mains such as AI Applications, Vision, and Net-works. While AutoSurvey occasionally matches or slightly outperforms on higher-k metrics (e.g., RR@10 in Databases), its RR@1 remains substan-tially lower overall. However, this is partly due to the smaller number of available source papers in that subtopic, which reduces retrieval diversity and makes the evaluation more sensitive to a few recent citations. SurveyForge and SurveyX trail significantly, especially in foundational domains like Learning Algorithms and Big Data, reflecting weaker temporal grounding. 

J Discussion on Metrics and Usage 

Note on Metric Usage and Purpose. Our evalu-ation incorporates several citation-related quantita-tive metrics, such as recency ratio, and citation den-

sity, to benchmark the structural and referential be-havior of generated surveys. However, these indica-tors offer only partial signals of quality. Academic survey writing is inherently diverse and context-dependent: field maturity, topic breadth, and venue-specific formatting constraints (e.g., strict page lim-its) all shape citation practices and content scope. Moreover, certain high-quality surveys may inten-tionally limit citations to emphasize synthesis or conceptual framing. 

Thus, these tools collectively provide an empir-ical lens into model behavior, but should not be interpreted as exhaustive or definitive measures of writing quality. 

Disclaimer on Intended Use. This tool is devel-oped to assist researchers in efficiently exploring relevant literature and identifying topic structures. The generated content is not intended for direct use in scholarly publication. We cannot guaran-tee the factual correctness or citation fidelity of all outputs. This limitation is a known challenge in current LLM-based generation systems, espe-cially for tasks involving factual grounding or ci-tation synthesis. Users remain responsible for ver-ifying accuracy, attribution, and appropriateness. We explicitly discourage the direct submission of model-generated text for academic writing or peer-reviewed publication. All outputs require human review, editing, and contextual judgment. 

K Human Evaluation Study 

To complement the automatic evaluation and ex-amine whether the improvements observed in auto-matic scores are also reflected in expert judgment along key qualitative dimensions, we conducted a human evaluation. 

K.1 Setup and Procedure 

A group of graduate-level participants with prior experience in reading and writing survey papers were recruited as evaluators. Each participant inde-pendently assessed four anonymized survey papers generated by different systems (AutoSurvey, Sur-veyForge, SurveyX, and Ours) covering identical research topics and titles. 

Participants were asked to rate each survey along five quality dimensions, using a 1–5 Likert scale (1 = very poor, 5 = excellent). The evaluation pro-tocol was delivered via a structured questionnaire, which included both rating and optional comment fields. For each system, evaluators also provided an 

3704

Scientific Domain Generated Papers 

Language Models A Comprehensive Survey on Large Language Models for Task-Oriented Dialogue Systems; Controllable Text Generation for Large Language Models; Applications of Large Language Models in Mental Health Services; Advancements in Natural Language Processing; A Comprehensive Survey on Chinese to Malay Speech Translation; Comprehensive Survey of Large Language Model-Based Multi-Agent Sys-tems; Comprehensive Survey on Multimodal Large Language Models. 

Vision, Video, and Image Generation A Comprehensive Survey on Vision Transformers; A Comprehensive Survey on Efficient Video Generation; Improving Video Generation with Human Feedback; Layout-Guided Controllable Image Synthesis; 3D Object Detection in Autonomous Driving; Synthetic Data Generation with Diffusion Models. 

Learning Algorithms and Foundations Comprehensive Survey of Gradient Descent; Automated Machine Learning Foundations; Formal Verification of Neural Networks; Adversarial Machine Learning; Self-Supervised Learning in Computer Vision; Generative Diffusion Models. 

AI Applications and Multidisciplinary Topics Quantitative Trading with AI in Cryptocurrency; AI in Facial Recognition; AI-Powered Autonomous Scientific Discovery; Whole-Body Control for Humanoid Robots; Quantum Computing Algorithms; Human-Computer Intelligent Interaction. 

Network, Systems, and Infrastructure Edge Computing Paradigms; Federated Learning; Embodied Artificial Intelligence. 

Database and Big Data Vector Database Management Systems. 

Table 7: Generated Survey Topics for SurveyGen-I, covering six scientific domains and representative survey papers used for evaluation. 

3705

Subtopic Model Rr@1 Rr@3 Rr@5 Rr@7 Rr@10 AI Applications and Multidisciplinary Topics AutoSurvey 0.085 0.529 0.747 0.910 0.988 AI Applications and Multidisciplinary Topics Ours 0.586 0.811 0.901 0.938 0.971 AI Applications and Multidisciplinary Topics SurveyForge 0.125 0.361 0.638 0.802 0.900 AI Applications and Multidisciplinary Topics SurveyX 0.444 0.758 0.894 0.939 0.978 Database and Big Data AutoSurvey 0.375 0.833 0.870 0.910 0.966 Database and Big Data Ours 0.544 0.749 0.862 0.893 0.939 Database and Big Data SurveyForge 0.104 0.279 0.445 0.512 0.613 Database and Big Data SurveyX 0.088 0.265 0.432 0.602 0.803 Language Models AutoSurvey 0.349 0.793 0.925 0.967 0.997 Language Models Ours 0.519 0.855 0.936 0.977 0.993 Language Models SurveyForge 0.225 0.571 0.739 0.857 0.916 Language Models SurveyX 0.356 0.669 0.832 0.925 0.984 Learning Algorithms and Foundations AutoSurvey 0.080 0.541 0.788 0.940 0.991 Learning Algorithms and Foundations Ours 0.328 0.614 0.806 0.922 0.977 Learning Algorithms and Foundations SurveyForge 0.060 0.322 0.579 0.803 0.900 Learning Algorithms and Foundations SurveyX 0.185 0.372 0.538 0.624 0.812 Network, Systems, Infrastructure AutoSurvey 0.140 0.548 0.838 0.935 0.996 Network, Systems, Infrastructure Ours 0.504 0.717 0.872 0.966 0.994 Network, Systems, Infrastructure SurveyForge 0.109 0.364 0.619 0.781 0.932 Network, Systems, Infrastructure SurveyX 0.089 0.287 0.528 0.734 0.953 Vision, Video, and Image Generation AutoSurvey 0.137 0.678 0.865 0.947 0.995 Vision, Video, and Image Generation Ours 0.472 0.803 0.937 0.982 0.998 Vision, Video, and Image Generation SurveyForge 0.145 0.534 0.763 0.901 0.945 Vision, Video, and Image Generation SurveyX 0.204 0.443 0.667 0.827 0.923 

Table 8: Recency ratio comparison by model and subtopic. 

overall ranking based on perceived overall quality. Further details of the evaluation protocol and the full text of the participant instructions are provided in Figure 7. 

Model Overall 

↑ 

Cov 

↑ 

Rel 

↑ 

Struc 

↑ 

Syn 

↑ 

Consis 

↑ 

AutoSurvey 2.76 2.60 2.80 2.80 2.80 2.80 SurveyForge 2.92 3.40 3.20 2.40 2.60 3.00 SurveyX 3.80 4.00 3.60 4.00 3.80 3.60 Ours 4.16 4.20 3.80 4.60 4.00 4.20 

Table 9: Human evaluation results across five quality dimensions. Higher is better for all metrics. 

L License and Terms of Use 

All assets used in this work comply with their re-spective licenses and terms of use: 

 arXiv papers: Accessed under the arXiv API Terms of Use3, which allow downloading for non-commercial research. 

 Semantic Scholar metadata: Retrieved un-der the Semantic Scholar API License4, per-mitting non-exclusive research use with attri-bution. 

 PyMuPDF (Artifex Software): Licensed un-der the GNU Affero General Public License 

3https://info.arxiv.org/help/api/tou.html 4https://www.semanticscholar.org/product/api/ 

license 

v3.0 (AGPL-3.0)5. 

 BAAI/bge-small-en-v1.5 and BAAI/bge-reranker-base: Released under the MIT Li-cense6. 

 all-mpnet-base-v2: Released under the Apache License 2.07. 

Downloaded PDFs are obtained through official endpoints ( export.arxiv.org) with no redistri-bution. 

M Examples of Generated Surveys 

Figures 8, 9, 10, and 11 illustrate different aspects of the generated surveys, including frontmatter de-sign, citation table integration, mathematical ex-pression formatting, and glossary usage. And Fig-ure 20 presents an example output generated by our framework. 

N Prompts Used 

Figure 13-19 show representative prompt designs in SurveyGen-I; the full prompt suite is provided in the codebase. 

5https://pypi.org/project/PyMuPDF/ 6https://huggingface.co/BAAI/bge-small-en-v1. 

5 7https://huggingface.co/sentence-transformers/ 

all-mpnet-base-v2 

3706

Evaluation Instructions Sent for Human Evaluation We conducted a human evaluation to assess the quality of AI-generated survey papers. Each participant was asked to evaluate four anonymized survey drafts on a 1–5 Likert scale (1 = very poor, 5 = excellent) along the following five dimensions: 

1. Coverage – Does the survey comprehensively and selectively cover the major areas and subfields relevant to its scope? 

2. Relevance – Does the content consistently support the stated scope, objective, and framing of the survey? 

3. Structure – Is the survey logically organized, well-sectioned, and progressively layered? 

4. Synthesis – Does the survey analyze and integrate prior work into meaningful categories, comparisons, or conceptual frameworks? 

5. Consistency – Is the paper professionally written, with uniform tone, terminology, and formatting? 

After scoring each survey, participants were optionally encouraged to provide short comments highlighting strengths or weaknesses and to give an overall ranking (e.g., Survey B > Survey A > Survey C > Survey D). 

Scoring Template Provided: 

Coverage Relevance Structure Synthesis Consistency 

Survey A Survey B Survey C Survey D 

All evaluations were collected anonymously. Participants were informed that their assessments would be used solely for academic research purposes and that no personally identifiable information would be recorded. 

Figure 7: Evaluation instructions and scoring template given. 

Generative Models for 3D Scene Understanding: A Survey GENERATED BY AI This survey provides a comprehensive review of generative modeling techniques for 3D scene understanding, categorizing approaches into point-based, voxel-based, and implicit representations. It highlights the advancements in generative mod-els, such as Variational Autoencoders (VAEs), Generative Adversarial Networks (GANs), and diffusion models, which have significantly improved the efficiency and quality of scene generation. Despite these advancements, challenges remain, par-ticularly in achieving geometric consistency, semantic accuracy, and real-time performance in dynamic environments. The survey identifies critical gaps in the literature, particularly regarding the integration of object-centric representations and the effective handling of complex object interactions. Future research directions emphasize the need for hybrid models that combine the strengths of existing methodologies, the incorporation of multi-modal data sources, and the development of standardized evaluation metrics. By addressing these challenges, the field can advance towards more robust and versatile generative models, enhancing applications in robotics, virtual reality, and interactive media. 

1 INTRODUCTION TO GENERATIVE MODELING FOR 3D SCENE UNDERSTANDING 1.1 Motivations for Advancing 3D Scene Generation The increasing demand for realistic 3D scene generation is primarily driven by applications in virtual reality, gaming, and robotics. These fields necessitate high-quality, immersive environments that enhance user experi-ence and interaction [51, 207]. Traditional methods of 3D scene generation often rely on labor-intensive manual modeling, which is not only time-consuming but also limits scalability and adaptability to dynamic environments [52, 151]. Such methods typically involve explicit representations, such as meshes and point clouds, requiring extensive expertise and resources to produce high-quality outputs [51, 136]. Consequently, the industry is in-creasingly turning to automated solutions that can generate complex scenes efficiently while maintaining artistic quality and structural integrity [11, 166]. 

Recent advancements in generative modeling techniques, particularly diffusion models and Generative Ad-versarial Networks (GANs), have emerged to address the limitations of traditional methods, enabling faster and more efficient scene generation [62, 133]. For instance, diffusion models have shown promise in generating high-quality images and have been adapted for 3D applications, allowing for the synthesis of multi-view con-sistent scenes from single-view inputs [30, 94]. GANs, while historically plagued by issues of instability and mode collapse, have been refined through techniques such as periodic implicit representations [19] and compo-sitional generative neural feature fields [121], enhancing their capability to produce coherent and detailed 3D structures. Achieving multi-view consistency is crucial in 3D scene generation, as it ensures that the generated scenes appear realistic from various perspectives, thereby significantly improving the overall user experience. 

Despite these advancements, challenges remain in achieving multi-view consistency and handling complex object interactions within generated scenes. Many existing methods generate single-view images and then at-tempt to stitch them together, often resulting in spatial inconsistencies and implausible configurations [94, 207]. For instance, while techniques like SceneDreamer360 utilize 3D Gaussian Splatting to ensure consistency across multi-view images, they still face limitations in generating fully enclosed scenes that maintain visual coherence [94]. Furthermore, the integration of scene graphs and layout-guided generation approaches, such as those pro-posed in GraLa3D, aims to model complex interactions between objects but often struggles with the intricacies of real-world scenarios [65, 195]. This highlights the ongoing need for innovative frameworks that can effectively manage the relationships between multiple objects while ensuring high fidelity in scene representation. 

The emergence of object-centric generative models, such as DreamUp3D, further underscores the necessity for advancements in 3D scene generation.These models are designed to perform inference based solely on single RGB-D images, enabling real-time object segmentation and 3D reconstruction [166]. This capability is particu-larly relevant for robotics applications, where accurate 6D pose estimation and dynamic scene understanding are 

1 

Figure 8: Front page generated by SurveyGen-I, demon-strating automatic formatting of title, author, and meta-data. 

AI generated 

bibkey Data Requirements 

Evaluation Metric Learning Paradigm 

Model Generalization 

Scene Complexity 

[6] Single-view 2D RGB images and top-down semantic layouts 

Not stated Conditional generative model trained using single-view images 

Generates complex scenes with multiple objects 

complex scenes with multiple objects 

[9] RGB, depth images and 6DOF camera poses 

average FID and SwAV-FID scores 

Generative model for 3D scene generation 

Generalizes previous works by removing shared camera pose assumption 

complex and realistic 3D scenes 

[83] Not stated chamfer distance Generative Adversarial Networks (GANs) 

Unsupervised creation of 3D object models 

Not stated 

[99] Labeled categories of furniture 

auto-completion metrics 

Auto-regressive scene model with instance-level predictions 

zero-shot text-guided scene synthesis and editing 

Diverse and generalizable 

[151] Not stated mean of two evaluation metrics 

data-driven supervised learning methods and deep generative model-based approaches 

Not stated complex scene levels 

[161] Benchmarked on the SG-FRONT dataset 

Fréchet Inception Distance (FID) and Kernel Inception Distance (KID) 

Joint layout-shape generation 

Higher-fidelity 3D scene synthesis 

real-world multi-object environments 

[181] Not stated Not stated Text- and layout-guided scene generation 

3D-consistent multi-view generator 

Complex indoor scene generation 

Table 4. Comparison of papers on learning paradigms and evaluation metrics. 

Table 4 summarizes the trade-offs between supervised and unsupervised learning approaches in 3D scene generation, highlighting their implications for data requirements and model generalization. Notably, supervised methods, such as those presented by [9] and [161], often rely on extensive labeled datasets and demonstrate higher fidelity in scene synthesis, while unsupervised techniques, exemplified by [83] and [181], emphasize flexibility in data usage but may face challenges in generating complex scenes.The evaluation metrics employed, including Fréchet Inception Distance (FID) and average FID scores, further illustrate the varying effectiveness of these paradigms in capturing scene complexity. 

4.2 Loss Functions and Optimization Strategies The effectiveness of generative models in producing realistic scenes hinges significantly on the choice of loss functions, which guide the optimization process during training. Adversarial loss, commonly employed in Gen-erative Adversarial Networks (GANs), encourages the generator to produce outputs indistinguishable from real 

12 

Figure 9: Citation alignment table produced by our sys-tem, showing mapped references and their summarized claims. 

3707

https://lh3.googleusercontent.com/notebooklm/AKYWMX8n_B2-STRvmOiHYB74-_CugAmCwQBtJujZkr6vWMayLDpT8wbM5cLaIMt389gVZsxm_T9Ad7yKu7LJobbnl7EzTfqC-tAABv3J-yJVLd7_q3ZIr5G0UBNBj2B-w2bWfb_kRfQ8Tg=w640-h405-v0

eee1febf-1fc2-487d-b5ed-5ad91ed1fcff

https://lh3.googleusercontent.com/notebooklm/AKYWMX-uGDs_piSrOunz3I5rp9zeoNa35gYcUSEVSsdtNMXE1IynsoWp5i9RlK8VdsCpS_Brw7gwFV4j4VZLtxoHSMMQ2z9F_NYKYRKapgHcgA1YKK8KvGWs48-FgGVfWSV8F4DkHGa4yg=w736-h534-v0

648d4c63-22af-48db-9439-2e33fa28a364

AI generated 

Category Papers 

Depth Map Control Signals [114], [197] Geometric Prior Alignment [29], [24], [64], [92], [114], [183], [197] Multi-View Consistency [25], [24], [57], [64], [92], [114], [125], [138], [158], [183], 

[184], [197] Progressive Optimization Strategy [29], [25], [49], [57], [64], [197] Self-Supervised Learning [49], [59], [138], [158], [184] 

Table 5. Grouped papers by Geometric Consistency category. 

5 EVALUATION METRICS AND BENCHMARKING PRACTICES 

Evaluation Metrics and Benchmarking Practices 

Qualitative Assessments 

[5.2] Challenges in User Studies [7, 21, 124, 137, 150, 165] 

[5.2] User Feedback Integration [7, 21, 124, 137, 150] 

[5.2] User Studies Frameworks [7, 21, 124, 137, 150] 

Quantitative Metrics 

[5.1] No-Reference Quality Assessment [5, 50, 96, 200, 202, 203] 

[5.1] Learned Perceptual Image Patch Similarity [5, 50, 96, 200, 202, 203] 

[5.1] Frechet Inception Distance [53, 96, 185, 200] 

[5.1] Structural Similarity Index [5, 50, 96, 200, 202, 203] 

[5.1] Peak Signal To Noise Ratio [5, 50, 96, 200] 

Fig. 4. Conceptual structure of Section 5: Evaluation Metrics and Benchmarking Practices 

5.1 Quantitative Metrics for Assessing Scene Quality Peak Signal To Noise Ratio (PSNR) serves as a foundational metric in evaluating the quality of generated 3D scenes, quantifying the ratio between the maximum possible power of a signal and the power of corrupting noise. This metric is particularly relevant in the context of Neural Radiance Fields (NeRF), where it aligns well with the objective of learning spatially dependent color values [5, 50]. PSNR is computed as: 

10 · log10 

( 

!𝑀# ($ 

)2 

!%& ($ 

) 

) (1) 

where 

!𝑀# ($ 

) represents the maximum pixel value and 

!%& ($ 

) denotes the mean squared error across color channels [50].While PSNR is widely recognized for its simplicity and effectiveness, it has limitations in capturing perceptual nuances, particularly in complex sceneswhere human visual perception ismore sensitive to structural and contextual variations [96, 200]. This limitation underscores the necessity for metrics that better align with human perception. 

14 

Figure 10: Example of complex formatting support, including tables, figures, and equations generated within a single subsection. 

Generative Models for 3D Scene Understanding: A Survey 

A GLOSSARY 

Abbreviation Full Term Mentioned In 

GAN Generative Adversarial Network Section 1.1 RGB-D Red Green Blue-Depth Section 1.1 6D Six Degrees Section 1.1 VAE Variational Autoencoder Section 1.2 3D Three-Dimensional Section 1.2 3D-GAN 3D Generative Adversarial Network Section 2.1 VAE-GAN Variational Autoencoder-Generative 

Adversarial Network Section 2.1 

SRT Scene Representation Transformer Section 2.1 PVD Point-Voxel Diffusion Section 3.1 DynaVol Dynamic Volumetric Representation Section 3.1 NeRF Neural Radiance Field Section 3.1 MLP Multi-Layer Perceptron Section 3.2 NeRF++ Neural Radiance Fields Plus Plus Section 3.2 NeRF-IS Neural Radiance Fields with Implicit 

Semantics Section 3.2 

SRN Scene Representation Network Section 4.2 SDF Signed Distance Function Section 4.2 PSNR Peak Signal-to-Noise Ratio Section 5.1 SSIM Structural Similarity Index Measure Section 5.1 FID Frechet Inception Distance Section 5.1 LPIPS Learned Perceptual Image Patch 

Similarity Section 5.1 

EEP-3DQA Efficient and Effective Projection-based 3D Model Quality Assessment 

Section 5.1 

GQN Generative Query Network Section 6.1 OSRT Object Scene Representation 

Transformer Section 6.1 

SPACE Spatial Attention with Scene-Mixture Approaches 

Section 6.1 

SIMONe Scene Invariant Object Network Section 6.1 IBRNet Image-Based Rendering Network Section 6.1 CodeNeRF Code Neural Radiance Fields Section 6.2 NeRF-VAE Neural Radiance Fields Variational 

Autoencoder Section 6.2 

LiDAR Light Detection and Ranging Section 7.1 DONeRF Depth Supervision Neural Radiance 

Fields Section 7.1 

Slot Attention Slot Attention Mechanism Section 7.2 Table 7. Glossary of abbreviations and their first mentions. 

33 

Figure 11: Glossary section automatically synthesized by SurveyGen-I to define key terms and acronyms. 

You are a survey planner. Your task is to determ ine which prior subsections each subsection depends on and how essential each dependency is. Current subsection: Title: {current_title} Description: {current_description} 

Here is the full structured outline of the survey: {subsections} 

Step 1: Evaluate how m uch each **prior** subsection is required for writing this one. Assign a dependency score from  1 to 5: - 5 = absolutely essential for writing this subsection (i.e., cannot be accurately written without understanding this prior content) - 4 = strongly recom m ended - 3 = m oderately useful - 2 = slightly helpful - 1 = them atically related but not necessary 

Do **not** consider the current subsection itself. 

Step 2: Only include in the output those prior subsections with a score of **5**. These are deem ed **essential**. Most subsections should have **at m ost 2 essential dependencies**, unless truly unavoidable. 

**Im portant form atting rule**: - In your output, include only **subsection titles** (not section titles). - If a dependency involves an entire section, list the titles of **the specific subsections within that section** that are required for writing the current one. 

Output form at (return valid JSON): {{   "depends_on": ["<exact subsection title 1>", "<exact subsection title 2>", ...],   "dependency_strengths": {{     "<exact subsection title 1>": 5,     "<exact subsection title 2>": 5   }} }} 

Writing Dependency Graph Construction 

Figure 12: Writing Dependency Graph Construction prompt used in SurveyGen-I. 

You are a research assistant helping to prepare high-quality keyword search strategies for a technical literature review. ### Research Input: * **Topic**: {topic} * **Explanation**: {explanation} Your task is to generate **6 unique and diverse keyword search queries** for use in **Semantic Scholar** or similar academic databases. Please **maximize coverage** of the topic’s conceptual and technical dimensions by following these principles: 

### Keyword Generation Guidelines: * Include **general** and **specific** queries:   * 2 broad keyword capturing the overall topic   * 2 focused keywords on **core methods**, techniques, or tasks   * 1 concise query using **minimal terms** that still retrieve precise papers   * 1 alternative phrasing using **abbreviations**, synonyms, or field-specific jargon 

* Use **natural language phrases** only.   * Avoid Boolean operators (AND, OR), wildcards, or filters.   * Use 3–6 words per keyword where possible.   * Use commonly used search phrases that real researchers might type. * Ensure that the keyword set covers **different angles**, such as:   * methods, applications, systems, challenges, evaluation, or user perspectives 

### Output Format (strict JSON – no explanation, no markdown): {{   "keywords": [     "Broad keyword capturing the general research area",     "Another Broad keyword capturing the general research area",     "Focused keyword related to a central method or task",     "Another focused keyword for method/module/technique",     "Minimal yet specific keyword query",     "Alternative phrasing with synonym or abbreviation"   ] }} 

LLM-Based Keyword Generation 

Figure 13: Keyword Generation used in SurveyGen-I. 

3708

You are an expert academic writer tasked with refining the structure of a technical survey paper. Your goal is to analyze the **remaining unwritten subsections** in the outline and produce detailed **revision recommendations** based on what has already been written. * Each section should contain **no more than 5 subsections** and **at least 2 subsections**  after updates. ## Your Responsibilities You are given: - A complete outline of the survey paper (`current_outline`) - A list of already written subsections (you MUST NOT change these) - A detailed memory summary (`memory_context`) of what the written parts already cover Your task is to analyze whether the **unwritten subsections**: 1. Redundantly overlap with content already covered 2. Lack clear or distinct purpose 3. Should be renamed to clarify scope 4. Should be deleted, merged, or repositioned for better flow 5. Are missing important conceptual gaps (that should be filled by **adding** new subsections) ## Required Output Return a JSON list of **structural revision actions** (do not modify the actual outline yet). Each action must be one of: - `"merge"`: Merge an unwritten subsection into another due to redundant scope. - `"rename"`: Change the title of an unwritten subsection to clarify its distinct purpose. - `"delete"`: Remove an unwritten subsection **only** if it overlaps entirely with written content. - `"add"`: Add a new subsection if something important is missing from the outline.     - Only propose an `"add"` action when the new subsection fills a **clear conceptual gap** that is **not already covered** by any existing (written or unwritten) subsection **titles or descriptions**.     - Do **not** propose additions for small variants, rephrasings, or minor extensions of existing content.     - However, if the memory context clearly shows a **missing and important perspective**, method, or challenge not reflected anywhere else, you are encouraged to add it — with a **strong justification**. - `"reorder"`: Suggest reordering of subsections for better conceptual progression. ## Input Data ### Full Current Outline: {current_outline} ### Written Subsections (DO NOT CHANGE): {written_subsection_list} ### Memory Summary of Written Content: {memory_context} ## Output Format (STRICT JSON ONLY): {{   "recommendations": [     {{       "action": "merge",       "target": {{         "section_title": "...",         "subsection_title": "..."       }},       "with": {{         "section_title": "...",         "subsection_title": "..."       }},       "reason": "..."     }},     {{       "action": "rename",       "target": {{         "section_title": "...",         "subsection_title": "..."       }},       "new_title": "...",       "reason": "..."     }},     {{       "action": "delete",       "target": {{         "section_title": "...",         "subsection_title": "..."       }},       "reason": "..."     }},     {{     "action": "add",     "section_title": "...",                         // Must match an existing section     "subsection_title": "...",                      // Title of the new subsection     "subsection_description": "...",                // Short conceptual description     "insert_after": "Optional Subsection Title",    // Optional: insert after which existing subsection     "reason": "... (explain why this fills a GENUINE gap and does not duplicate existing coverage)"     }},     {{       "action": "reorder",       "section_title": "...",       "subsection_titles": ["...", "...", "..."],     // New order for unwritten subsections       "reason": "..."     }}   ] }} If no changes are necessary, return: {{ "recommendations": [] }} 

Structural Revision Planning for Unwritten Subsections 

Slim version 

You are a research assistant evaluating the relevance of a paper to a research topic. Research Topic: {topic} Detailed Explanation: {explanation} 

Paper Abstract: {abstract} ### Step 1: Extract the core research **task/problem** this paper addresses. Phrase it as a short sentence. 

### Step 2: Identify the core **technical method or approach** used in the paper. Be specific (e.g., "transformer-based contrastive learning", "graph-based reasoning", etc). Here are examples of relevant task types: - [task/problem]: e.g., "multi-modal video captioning", "code generation from docstrings" Expected technical methods may include: - [method 1]: transformer-based encoder-decoder - [method 2]: cross-modal attention with CLIP-style features 

### Step 3: Then assign the following scores: ### A. Problem Relevance (0–100): Evaluate how well the paper’s **core research goal** matches the target task/problem. Use the criteria: - 70–100: Same task type and objective. - 50–69: Related but not the same focus. - Below 50: Different task. ### B. Method Relevance (0–100): Evaluate how closely the **main method** aligns with what’s expected from the explanation - 70–100: Strong match with one or more expected methods. - 50–69: Similar but varied. - Below 50: Different techniques. 

### Step 4. Compute Final Score: Use the formula: `relevance_score = round(0.4 × problem_relevance + 0.6 × method_relevance)` Example: 

- problem_relevance = 45, method_relevance = 80 → relevance_score 

= 62 

### 5. Classify Relevance based on the **relevance_score** you computed before (strict): 

- 80–100 → "highly relevant" - 70–79  → "closely relevant" - 0–69   → "not relevant" 

Output format (MUST be valid JSON only — no extra text): 

{{   "problem_relevance": <integer between 0-100>,   "method_relevance": <integer between 0-100>,   "relevance_score": <computed integer between 0-100>,   "relevance": "<highly relevant | closely relevant | not relevant>" }} 

LLM-Based Relevance Scoring for Paper Filtering 

Figure 14: Relevance Scoring for Paper Filtering prompt used in SurveyGen-I. 

                                                                                              i      i i                               i i  i     i i                         i     i     i i i                     i i     i  i  i  i      i  i   i  i i  i       i   i  i        i  i i                i        i i l        i i l             i  i              

I       i   

Figure 15: Structural Revision Planning for Unwritten Subsections prompt used in SurveyGen-I. 

3709

You are writing a high-level academ ic survey outline for the following research topic: 

{topic} 

## Topic Description: 

{explanation} 

You are provided with: 

1. Several review paper outlines that already sum m arize existing work in the field. 

2. A list of candidate research papers with titles and abstracts. 

## Review Paper Outlines (trusted structure references): 

The following outlines are extracted from  existing high-quality review papers. You m ay m erge or reorganize sim ilar sections across different reviews: 

{review_outlines} 

## Candidate Research Papers: 

You should also take into account the following paper titles and abstracts when refining or extending the outline: 

{paper_list} 

## W hat You Should Do: 

You m ust design a com plete and **conceptually rich survey outline**, not a m ethod list. 

### Your goals: 

1. **Synthesize** and reorganize concepts across different outlines. 

2. G roup research based on **functionality, m echanism s, challenges, and open questions**, not im plem entation. 

3. Ensure each section has a **unique purpose**, e.g. foundational theory, learning paradigm s, generalization, robustness, system  personalization, evaluation, etc. 

4. Highlight **im portant research trade-offs**, lim itations, and underexplored areas. 

5. Include sections reflecting **m odern challenges and em erging trends**, such as interpretability, alignm ent, scalability, and data efficiency. 

## Output Requirem ents: 

Each survey should include the following structure: 

- `title`: A precise and inform ative full title for the survey. 

- `sections`: 8–10 m ajor sections. Each section should serve a **distinct conceptual function**, such as: 

  - foundational theory 

  - functional capabilities 

  - system  design or architecture 

  - learning paradigm s 

  - generalization and robustness 

  - benchm arking and evaluation 

  - hum an interaction or societal im pact 

  - adaptation and deploym ent 

  - lim itations and outlook 

Each section m ust include: 

- `section_title`: A concise heading that clearly identifies the conceptual purpose of the section. Avoid vague titles like “Background”. 

- `section_description`: 1–2 sentences explaining what this section contributes to the overall survey. W hat conceptual or m ethodological dim ension does it organize? 

- `subsections`: 3–6 subsections per section. Each m ust contain: 

  - `subsection_title`: A clear, **them e-based title** (not just a m ethod nam e). 

  - `subsection_description`: Detailed writing instructions describing: 

    - the key ideas to explain, 

    - debates or com parisons to highlight, 

    - typical lim itations or open challenges to m ention, 

    - and how m ultiple papers or system s should be synthesized into conceptual groupings. 

## **Output Form at (strict JSON)** 

Only return a valid JSON object. Do not include extra com m entary. 

- Do not include a **Survey Structure and Scope Overview** or "Objectives and Scope of the Survey" like subsection in the Introduction Section. 

{{ 

  "outline": {{ 

    "title": "Title of the Survey", 

    "sections": [ 

      {{ 

        "section_title": "Section 1 title", 

        "section_description": "Explain the high-level focus of this section.", 

        "subsections": [ 

          {{ 

            "subsection_title": "Subsection 1.1 title", 

            "subsection_description": "Describe what technical concepts, com parative analyses, and open questions this part should cover. Prioritize conceptual synthesis 

over m ethod enum eration." 

           }}, 

          // Even if a section contains only one key idea, always include a 'subsections' list with subsection_title and subsection_description. 

          // Never om it the 'subsections' field. 

          ... 

        ] 

      }}, 

      ... 

    ] 

  }} 

}} 

Draft Outline Generation from Retrieved Papers 

Figure 16: Prompt used in SurveyGen-I for draft outline generation from retrieved papers. 

3710

You are an expert academ ic survey writer. Your task is to design a **conceptually structured writing skeleton** for a specific subsection of a survey. 

This skeleton will guide high-quality academ ic writing. You m ust ensure that the structure prom otes clarity, depth, and coherence, and that it integrates well with previous 

sections of the survey. 

### Subsection Metadata 

Subsection title: {subsection_title} 

Subsection description: {subsection_description} 

You m ust focus strictly on the **subsection title and description** when selecting structure and bullet points. Your skeleton m ust reflect the **core intent** and **scope** 

of this specific subsection. 

### Retrieved Literature Context 

The following RAG -retrieved content sum m arizes relevant papers. Use it to identify key them es, m echanism s, debates, or techniques to include: 

{retrieved_context} 

This context is derived from  citation-anchored papers, but your output m ust **not** include any citations or bibkeys. 

**Do not write any inline citations, bibkey m entions, or paper identifiers.** 

You should use the content only as background knowledge to inform  concept selection and skeleton structure. 

---

### W riting Mem ory 

The following m em ory includes: 

* **Unified Term inology** from  prior subsections (e.g., how different term s m ap to the sam e canonical concepts). 

* **Structural Blueprints** already covered (avoid repeating). 

**Absolutely no conceptual or structural overlap is allowed.** 

If any m echanism , m ethod, technical insight, or debate has already appeared in prior blueprints or unified term inology, 

you m ust not m ention it again in any bullet or group, even from  a slightly different angle. 

If m em ory_context is "None", it m eans no prior structural blueprint or term inology m apping is available. 

In this case: 

* You m ay freely explore the concept space based on the current subsection title and description. 

* You do not need to avoid overlap with prior subsections. 

* However, you m ust still avoid internal repetition and ensure every bullet is conceptually distinct. 

{m em ory_context} 

## Strict Rules 

* **You are designing a writing skeleton, not the actual content.** 

* Do not expand any sentence into a paragraph. 

* **You m ust strictly avoid conceptual or structural overlap with any prior blueprint.** 

* **It is absolutely prohibited to repeat any m echanism , technique, insight, or technical point already covered in previous subsections, in any form  or rewording.** 

* If you are unsure whether a concept is already covered, exclude it to be safe. 

* Absolutely no generic or off-topic content. Every group and bullet point m ust be directly tied to the specific focus of the current subsection. Do not include boilerplate 

item s like "Evaluation", "Future Directions", or other com m on headings unless they are explicitly central to the subsection’s defined scope. No topic drift, no filler— stay 

sharply aligned with the title and description. 

### Topic-G uard (internal) 

Before producing the JSON you **m ust** run this internal checklist: 

1. Does each bullet clearly elaborate the core intent of 

   **both** `{subsection_title}` **and** `{subsection_description}`? 

2. Is this m echanism , m ethod, or insight already covered in any previous subsection (per m em ory)? 

   If “yes”, **im m ediately rem ove it**— even if it is rephrased or from  a different perspective. 

3. Could an external reviewer say the bullet is off-topic? 

   If “yes”, replace or delete that bullet. 

Only once every bullet passes this checklist m ay you output the JSON. 

# Part 1: Choose the Most Suitable Structure Type 

You m ust choose **exactly one** of the following structure types based on the **nature of the content**. 

- Absolutely no generic or off-topic content. Every group and bullet point m ust be directly tied to the specific focus of the current subsection. Do not include boilerplate item s 

like "Evaluation", "Future Directions", or other com m on headings unless they are explicitly central to the subsection’s defined scope. No topic drift, no filler— stay sharply 

aligned with the title and description.### Allowed Types (Mutually Exclusive): 

1. **"flat_bullet"** 

   - Use when the topic is conceptually narrow or them atically unified. 

   - A flat list of 3–6 dense technical insights. 

2. **"tim eline"** 

   - Use when the literature has clear chronological developm 

ent (e.g., early → recent → em 

erging). 

   - Each tim e phase should reflect conceptual progression. 

3. **"m ethod_category"** 

   - Use when works are best grouped by m ethodological differences (e.g., supervised vs RL-based). 

   - Categories m ust reflect how m ethods differ in design principles or application scope. 

# Part 2: G enerate Bullet Points 

No m atter the structure type, your bullet points m ust follow these **academ ic bullet design principles**: 

- It directly deepens, contrasts, or operationalises a concept nam ed 

  (or clearly im plied) in the subsection title / description. 

- If a bullet cannot be tied back to the subsection scope in one clause, 

  **it is off-topic and m ust not be included**.- Each bullet expresses a **technical m echanism , insight, or debate**, not just a topic nam e. 

- Focus on **conceptual richness**: highlight contrasts, consensus, or gaps. 

- Integrate **m ultiple papers or strategies** when relevant. 

- Avoid repetition of ideas from  previous subsections (see m em ory). 

- W rite each point as a **concise sentence fragm ent**, suitable for expanding into a paragraph. 

Avoid: 

- Vague or generic phrasing ("Various m ethods exist...") 

- Listing papers without synthesis 

- Overlap with prior blueprint points 

Writing Skeleton Generation Conditioned on Structure Memory 

Figure 17: Writing Skeleton Generation Conditioned on Structure Memory prompt used in SurveyGen-I. 

3711

You are writing a **technical survey subsection** for an academ ic paper. Your goal is to produce a **m echanism -focused, citation-dense, and trace-aware synthesis** of the 

given topic. 

## Subsection Context 

- **Title**: {subsection_title} 

- **Description**: {subsection_description} 

## HARD RULES  (m ust hold or output is invalid) 

1. Use only the Bibkeys provided in RAG /trace; never invent, delete, or relocate citations. 

2. Produce 3–4 paragraphs, each 3–5 sentences. 

3. The **first sentence of every paragraph** is a m echanism -level claim . 

4. **Pair-and-cite sentence rule**: within each paragraph, you can write **at least one sentence** of the form 

 “<Category> such as <Method-A> \[BibA; BibB] **and** <Method-B> \[BibC; BibD] …”. 

 Finish that sentence with a com parative or consequential clause (e.g., “drive scalable training”, “m itigate m ode collapse”). 

5. **Citation positioning**: the Bibkey block m ust appear **im m ediately after each m ethod nam e**, inside a single pair of brackets, sem icolon-separated. 

6. Do **not** use author-first phrasing (e.g., “Sm ith et al. (2024) propose…”) or concluding phrases (“In conclusion”, “Overall”). 

7. Plain text only —  no headings or bullet lists. Include a form ula only if it defines a core loss or algorithm ; write it as plain text. 

9. **Raw-bracket citation form at** – Citations m ust appear exactly as `[Bibkey]`, with no preceding backslash or escape characters (e.g., `\[Bibkey\]` is invalid). 

## STYLE G UIDELINES 

Begin each paragraph with a declarative m echanism  claim , then elaborate by contrasting or com bining m ultiple works. 

 ✓ Exam ple: *“Contrastive objectives coupled with m om entum  encoders sustain representation diversity [He2020MoCo; G rill2020BYOL].”* 

Use short connectors (“whereas”, “consequently”, “by contrast”) to m aintain flow. 

Favor concrete verbs (“aligns”, “m itigates”, “accelerates”) over descriptive sum m aries. 

Include form ulas if needed; write them  as plain text, e.g., 

 *“The loss com bines a K-L divergence term 

 **L = D_KL(qǁp) + λ·ǁθǁ₂²**.”* 

## SELF-CHECK BEFORE OUTPUT 

☑ Paragraph count = 3–4 and length ≈ 300–600 words 

☑ Each paragraph opens with a m echanism  claim 

☑ ≥ 4 Bibkeys per paragraph, ≥ 1 per sentence 

☑ All Bibkeys m atch those in the RAG /trace list 

☑ No author-first or concluding phrases 

☑ No headings/bullets 

☑ All `[Bibkey]` entries use raw brackets— no backslashes or escape characters. 

## RAG  Context Usage (for citations and origin tracing) 

Each literature block includes: 

- `Original Docum ent`: the paper where the snippet was originally retrieved from . 

- `Bibkey`: the canonical citation key that should be used when citing this paper. 

- `Abstract`: a brief sum m ary (if available). 

- `RAG  Snippet`: a raw excerpt retrieved from  the docum ent, relevant to the current subsection. 

- `Reasoning Trace`: explains if and how a citation inside the RAG  snippet was traced to another, earlier source. 

### RAG -TRACE CITATION POLICY 

▪ If you use wording or ideas from  a RAG  snippet, cite that snippet’s Bibkey. 

▪ If the snippet m entions another paper and a **Reasoning Trace** says that citation should be traced elsewhere, cite the **traced** Bibkey instead. 

▪ Each sentence m 

ust contain ≥ 1 Bibkey **if and only if the claim 

 has traceable support**; aim 

 for ≥ 6 citations per paragraph when m 

aterial allows. 

▪ Place the Bibkey block im m ediately after each individual m ethod nam e, 

 inside a single pair of brackets and separated by a sem icolon, e.g., 

 “contrastive learning [Chen2020Sim CLR; He2020MoCo]”. 

▪ You can include sentences of the form : 

 “<Category> such as <Method-A> [BibkeyA; BibkeyB] and <Method-B> [BibkeyC; BibkeyD] <consequence/contrast>.” 

▪ **Do not cite a Bibkey unless it directly supports the claim .** 

### RAG  CITATION COVERAG E POLICY 

Each sentence should include at least one citation **when the claim  is derived from  retrieved literature**. However, if a sentence conveys a connective idea, sum m arizes 

prior citations, or introduces a transition **without asserting a novel fact**, it m ay om it a citation. **Do not fabricate citations** to m eet quota. 

###CITATION ACCURACY RULE 

Every citation m ust directly support the claim  it is attached to. Do not cite a Bibkey unless its RAG  snippet or traced origin explicitly supports the sentence’s m echanism  or 

assertion. If no such support exists, rephrase or om it the claim . Citation m isuse (e.g., m ism atched or unsupported Bibkey) invalidates the output. 

## RAG  Context 

{retrieved_context} 

### **good exam ples** 

 > Several architectural variants of Transform ers have been proposed to address quadratic attention cost. Linform er [W ang2020Linform er], Perform er 

[Chorom anski2020Perform er], and Longform er [Beltagy2020Longform er] use low-rank or sparse approxim ations. Reform er [Kitaev2020Reform er] uses locality-sensitive 

hashing to reduce m em ory. These m ethods differ in trade-offs between precision and scalability [Xiong2021Nystrom form er; Tay2020EfficientTransform ers]. 

 > Message passing in G NNs [G ilm er2017MessagePassing] propagates node features through neighbors. Variants include G raph Convolutional Networks [Kipf2016G CN], 

G raph Attention Networks [Velickovic2018G AT], and G raph Isom orphism  Networks [Xu2019G IN]. Their expressiveness varies in distinguishing graph structures 

[Morris2019W eisfeiler; Zhao2020G NNExplainer]. 

 > Pretext tasks such as contrastive learning [Chen2020Sim CLR; He2020MoCo] and m asked m odeling [Devlin2018BERT; He2022MAE] have led to versatile representations 

across dom ains. Follow-ups [G rill2020BYOL; Caron2021DINO] explore collapsing avoidance and alignm ent m echanism s without negative pairs. These m ethods vary in 

optim ization stability and transfer effectiveness [Chen2021Mugs; Bardes2022VICReg]. 

## Task 

W rite the full subsection using: 

- Only Bibkeys from  the RAG  context 

- Correctly traced citations (based on Reasoning Trace) 

- Dense, survey-style paragraph structure 

- no Headings 

Do **not** copy whole snippets. Synthesize across them . Every sentence m ust be citation-backed. 

Full Subsection Writing with RAG and Citation Tracing 

Figure 18: Full Subsection Writing with RAG and Citation Tracing prompt used in SurveyGen-I. 

3712

You are an **expert academic reviewer**. For the given technical survey, assign integer scores (1–5) for the following five dimensions. Your evaluation must be **rigorous**, **evidence-driven**, and adhere to the domain-neutral rubric below. **Report Topic:** {topic} ---### **1. Coverage** **Does the survey comprehensively and selectively cover the major areas, topics, and subfields relevant to its scope, with a clear rationale for inclusion?** * **5:** Covers both foundational and emerging areas with careful selection and justification; reflects deep understanding of the domain landscape. * **4:** Covers most core topics and some recent developments; inclusion appears mostly thoughtful and relevant. * **3:** Broad but shallow coverage; includes many topics but lacks prioritization, depth, or rationale. * **2:** Touches on key areas superficially or with poor structure; lacks justification; several expected topics are missing. * **1:** Misrepresents or omits major areas; appears outdated or arbitrarily constructed. *Penalty:* Cap at **3** if long enumerations dominate without depth, rationale, or visual synthesis (e.g., figures, tables). ---### **2. Relevance** **Does the content consistently support the stated scope, objective, and framing of the survey?** * **5:** Every section advances the survey’s declared purpose; even marginal topics are tightly integrated and justified. * **4:** Content is strongly aligned; only occasional digressions. * **3:** Mostly focused, but some sections feel loosely connected to the stated objective. * **2:** Several oy-topic or generic sections reduce clarity and focus. * **1:** Large portions diverge from the intended focus or purpose. *Penalty:* Cap at **3** if significant portions provide generic background rather than domain-specific insight. ---### **3. Structure** **Is the survey logically organized, well-sectioned, and progressively layered?** * **5:** Organization is conceptually clear and layered; ideas build progressively; transitions and dependencies are handled well. * **4:** Clear and readable structure; most sections flow logically. * **3:** Reasonable outline, but weak layering or abrupt transitions between topics. * **2:** Poor transitions; topics feel listed rather than structured; unclear progression. * **1:** Disorganized or incoherent; diyicult to follow. *Penalty:* Cap at **3** if subsections follow a rigid template without conceptual grouping or progression. ---### **4. Synthesis** **Does the survey analyze and integrate prior work into meaningful categories, comparisons, or conceptual frameworks?** * **5:** Synthesizes prior work into taxonomies, comparative tables, conceptual diagrams, or analytical frameworks; demonstrates interpretive insight. * **4:** Some synthesis and comparison; related works are grouped or contrasted thoughtfully. * **3:** Begins to group or compare work but lacks deep analysis. * **2:** Minimal synthesis; mostly lists papers or methods independently. * **1:** Pure enumeration; no analysis of relationships, tradeoys, or trends. *Reward:* Tables, diagrams, design spaces, or frameworks that aid comparative understanding. *Penalty:* Cap at **3** if works are described without connections, comparisons, or grouping. ---### **5. Consistency** **Is the paper professionally written, with uniform tone, terminology, and formatting?** * **5:** The writing is polished, coherent, and consistently professional. Terminology is clearly defined and used uniformly across sections; formatting and citation style are stable throughout. Tone is academically formal with no lapses. Glossaries or term explanations are provided or implicitly maintained. * **4:** Generally consistent in tone and formatting with only isolated lapses (e.g., minor citation format drift, slightly inconsistent section intros). Terminology is mostly stable. * **3:** Some inconsistencies in phrasing templates, formality, or terminology use. For example, some sections use generic introductions while others are more technical; citation styles or paragraph flow may shift noticeably. * **2:** Frequent inconsistencies across sections in writing style, tone, or citation usage. Uses both informal and formal phrasing, or mixes diyerent citation styles (e.g., inline vs. numbered). Terminology use is unstable or vague. * **1:** Writing feels unprofessional or poorly edited. Style, terminology, formatting, or citation usage varies widely across the paper with no editorial control. **Reward:** Glossaries, clearly defined and consistently used terminology, uniform structure and tone, consistent citation formatting. **Penalty:** Cap at **3** if any of the following are present: * Section templates feel mechanically reused without stylistic adaptation. * Tone or phrasing switches between formal and informal. * Inconsistent use of terminology (e.g., “framework”, “model”, “approach” used interchangeably without definition). * Citation styles vary across sections (e.g., some use \[1], others use (Author, Year)). ---### Output Format Your evaluation should follow **two steps**: ---#### **Step 1: Evaluation Notes** For each criterion, write 1–2 sentences summarizing what the survey does well and what it lacks. Be specific. Avoid generalities. ### Review Policy * Penalize: Template-based repetition, listing without depth, general background inflation, inconsistent phrasing. * Reward: Selectivity, conceptual synthesis, structured comparisons, clear terminology. * Use full range of scores (1–5), especially when reviewing papers with mixed quality. #### **Step 2: JSON Scores** Return a valid JSON dictionary like this: ```json {{   "coverage": <1,5>,   "relevance": <1,5>,   "structure": <1,5>,   "synthesis": <1,5>,   "consistency": <1,5> }} ``` ---## Survey to Evaluate: **Report Content:** {content} 

Evaluation Scoring Prompt 

Figure 19: Evaluation Scoring prompt used in SurveyGen-I. 

3713

1 INTRODUCTION TO TEXT-TO-IMAGE GENERATION 1.1 Historical Development of Text-to-Image Generation The evolution of text-to-image generation has been significantly influenced by advancements in diffusion models, which synthesize high-quality images from textual descriptions. Early models, such as Generative Adversarial Networks (GAN) [1★], established a foundational framework for image generation but encountered challenges such as mode collapse and training instability. In contrast, diffusion models, particularly Denoising Diffusion Probabilistic Models (DDPM) [2★], utilize a forward process that incrementally adds noise to data, followed by a reverse process that reconstructs the original data. This iterative denoising approach effectively generates images that closely align with text prompts, as demonstrated by models like Stable Diffusion [3★] and Imagen [4★], which leverage large-scale datasets and advanced architectures to enhance fidelity and semantic alignment. Recent innovations have further refined diffusion models, particularly through the integration of transformer architectures. Models such 

as PixArt-α [5] and the Hybrid Autoregressive Transformer (HART) [6] illustrate that substituting traditional U-Net backbones with 

transformers significantly enhances scalability and efficiency. These transformer-based models employ advanced attention mechanisms, facilitating improved handling of complex prompts and superior image quality. The incorporation of cross-attention layers in diffusion models enables more effective integration of text and image features, resulting in better alignment between generated images and their corresponding textual descriptions [7★, 8★]. This transition towards transformer architectures underscores the critical role of attention in achieving high-quality outputs. Moreover, structured approaches to compositional generation have addressed challenges related to multi-object synthesis and attribute binding. Techniques such as Generative Semantic Nursing (GSN) [7] and Bounded Attention [9] mitigate semantic leakage and enhance the fidelity of generated images. These methods manipulate attention maps to ensure correct associations between attributes and their respective objects, thereby improving the coherence of the generated content. Additionally, frameworks like ControlNet [10★] and CountGen [11★] introduce mechanisms for spatial control and accurate object counting, further expanding the capabilities of text-to-image models in generating complex scenes. These structured approaches highlight the necessity of addressing semantic relationships in image generation, which is crucial for producing coherent and contextually relevant outputs. While diffusion models play a pivotal role in enhancing image generation, their effectiveness is significantly augmented by the integration of Pretrained Language Models (PLM), which provide robust text encoding capabilities. The trajectory of text-to-image generation continues to evolve, with ongoing research focused on optimizing inference processes and enhancing model efficiency. Approaches such as Training-Free Layout Control [12] and the use of predicate logic to guide attention [13] pave the way for more intuitive interactions with generative models. As these models become increasingly sophisticated, they promise to unlock new applications across various domains, from creative arts to technical documentation, while addressing the inherent challenges of accurately translating textual prompts into visual representations. 

[1] I. Goodfellow, Jean Pouget-Abadie, Mehdi Mirza, Bing Xu, David Warde-Farley, Sherjil Ozair, Aaron C. Courville, and Yoshua Bengio. 2021. Generative Adversarial Networks. (2021). 

[2] Jonathan Ho, Ajay Jain, and P. Abbeel. 2020. Denoising Diffusion Probabilistic Models. (2020). 

[3] Robin Rombach, A. Blattmann, Dominik Lorenz, Patrick Esser, and B. Ommer. 2021. High-Resolution Image Synthesis with Latent Diffusion Models. 2022 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) (2021), 10674–10685. 

[4] Chitwan Saharia, William Chan, Saurabh Saxena, Lala Li, Jay Whang, Emily L. Denton, Seyed Kamyar Seyed Ghasemipour, Burcu Karagol Ayan, S. S. Mahdavi, Raphael Gontijo Lopes, Tim Salimans, Jonathan Ho, David J. Fleet, and Mohammad Norouzi. 2022. Photorealistic Text-to-Image Diffusion Models with Deep Language Understanding. ArXiv abs/2205.11487 (2022). 

[5] Junsong Chen, Jincheng Yu, Chongjian Ge, Lewei Yao, Enze Xie, Yue Wu, Zhongdao Wang, James T. Kwok, Ping Luo, Huchuan Lu, and 

Zhenguo Li. 2023. PixArt-α: Fast Training of Diffusion Transformer for Photorealistic Text-to-Image Synthesis. (2023). 

[6] Haotian Tang, Yecheng Wu, Shang Yang, Enze Xie, Junsong Chen, Junyu Chen, Zhuoyang Zhang, Han Cai, Yao Lu, and Song Han. 2024. HART: Efficient Visual Generation with Hybrid Autoregressive Transformer. ArXiv abs/2410.10812 (2024). 

[7] Hila Chefer, Yuval Alaluf, Yael Vinker, Lior Wolf, and D. Cohen-Or. 2023. Attend-and-Excite: Attention-Based Semantic Guidance for Text-to-Image Diffusion Models. (2023). 

[8] Yasi Zhang, Peiyu Yu, and Yingnian Wu. 2024. Object-Conditioned Energy-Based Attention Map Alignment in Text-to-Image Diffusion Models. (2024). 

[9] Omer Dahary, Or Patashnik, Kfir Aberman, and Daniel Cohen-Or. 2024. Be Yourself: Bounded Attention for Multi-Subject Text-toImage Generation. (2024). 

[10] Lvmin Zhang, Anyi Rao, and Maneesh Agrawala. 2023. Adding Conditional Control to Text-to-Image Diffusion Models. (2023). 

[11] Lital Binyamin, Yoad Tewel, Hilit Segev, Eran Hirsch, Royi Rassin, and Gal Chechik. 2024. Make It Count: Text-to-Image Generation with an Accurate Number of Objects. (2024). 

[12] Minghao Chen, Iro Laina, and A. Vedaldi. 2023. Training-Free Layout Control with Cross-Attention Guidance. (2023). 

[13] Kota Sueyoshi and Takashi Matsubara. 2023. Predicated Diffusion: Predicate Logic-Based Attention Guidance for Text-to-Image Diffusion Models. 2024 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) (2023), 8651–8660. 

Example 

Figure 20: An example of generated example with SurveyGen-I. References marked with an asterisk (*) indicate citations that have been explicitly traced and verified. 

3714

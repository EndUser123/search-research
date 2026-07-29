---
source_id: "fb9b52af-30ae-4b00-83de-19e0baa3bb8f"
title: "Daily Papers - Hugging Face"
notebook_id: 76ace35a-a66b-47fd-b2dd-c6b50936b3e2
url: https://huggingface.co/papers?q=Intercode%20Bash
type: web_page
exported: 2026-07-28
---

# Daily Papers - Hugging Face
Daily Papers - Hugging Face

 Hugging Face

https://huggingface.co/

Models

https://huggingface.co/models

Datasets

https://huggingface.co/datasets

Spaces

https://huggingface.co/spaces

Buckets new

https://huggingface.co/storage

Docs

https://huggingface.co/docs

Enterprise

https://huggingface.co/enterprise

Pricing

https://huggingface.co/pricing

Log In

https://huggingface.co/login

Sign Up

https://huggingface.co/join

new

Get trending papers in your email inbox once a day!

Get trending papers in your email inbox!

Subscribe

https://huggingface.co/login?next=%2Fpapers

Daily Papers

by 

AK

https://huggingface.co/akhaliq

 and the research community

Intercode Bash

Daily

Weekly

Monthly 

https://huggingface.co/papers/trending

 

https://huggingface.co/papers/date/2026-03-24

Mar 25

 [-] 1

https://huggingface.co/login?next=%2Fpapers%2F2410.05434

Better than Your Teacher: LLM Agents that learn from Privileged AI Feedback

https://huggingface.co/papers/2410.05434

While large language models (LLMs) show impressive decision-making abilities, current methods lack a mechanism for automatic self-improvement from errors during task execution. We propose LEAP, an iterative fine-tuning framework that continually improves LLM agents using feedback from AI expert teachers. Our key insight is to equip the expert teachers with a privileged state -- information that is available during training but hidden at test time. This allows even weak experts to provide precise guidance, significantly improving the student agent's performance without access to privileged information at test time. We evaluate LEAP on diverse decision-making benchmarks, including text-based games (ALFWorld), web navigation (WebShop), and interactive coding ( Intercode Bash). Our experiments show that LEAP (1) outperforms behavior cloning and ReAct baselines (2) enables weak student models (e.g., Llama3-8B) to exceed the performance of strong teacher models (GPT4-o), and (3) allows weak models to self-improve using privileged versions of themselves. We also provide a theoretical analysis showing that LEAP's success hinges on balancing privileged information with the student's realizability, which we empirically validate. Our code is available at https://leap-llm.github.io

https://huggingface.co/papers/2410.05434

[

2 authors](https://huggingface.co/papers/2410.05434)

·

Oct 7, 2024

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2306.14898

InterCode: Standardizing and Benchmarking Interactive Coding with Execution Feedback

https://huggingface.co/papers/2306.14898

Humans write code in a fundamentally interactive manner and rely on constant execution feedback to correct errors, resolve ambiguities, and decompose tasks. While LLMs have recently exhibited promising coding capabilities, current coding benchmarks mostly consider a static instruction-to-code sequence transduction process, which has the potential for error propagation and a disconnect between the generated code and its final execution environment. To address this gap, we introduce InterCode, a lightweight, flexible, and easy-to-use framework of interactive coding as a standard reinforcement learning (RL) environment, with code as actions and execution feedback as observations. Our framework is language and platform agnostic, uses self-contained Docker environments to provide safe and reproducible execution, and is compatible out-of-the-box with traditional seq2seq coding methods, while enabling the development of new methods for interactive code generation. We use InterCode to create two interactive code environments with Bash and SQL as action spaces, leveraging data from the static Spider and NL2Bash datasets. We demonstrate InterCode's viability as a testbed by evaluating multiple state-of-the-art LLMs configured with different prompting strategies such as ReAct and Plan & Solve. Our results showcase the benefits of interactive code generation and demonstrate that InterCode can serve as a challenging benchmark for advancing code understanding and generation capabilities. InterCode is designed to be easily extensible and can even be used to incorporate new tasks such as Capture the Flag, a popular coding puzzle that is inherently multi-step and involves multiple programming languages. Project site with code and data: https://intercode-benchmark.github.io

https://huggingface.co/papers/2306.14898

[

4 authors](https://huggingface.co/papers/2306.14898)

·

Jun 26, 2023

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2502.06858

LLM-Supported Natural Language to Bash Translation

https://huggingface.co/papers/2502.06858

The Bourne-Again Shell (Bash) command-line interface for Linux systems has complex syntax and requires extensive specialized knowledge. Using the natural language to Bash command (NL2SH) translation capabilities of large language models (LLMs) for command composition circumvents these issues. However, the NL2SH performance of LLMs is difficult to assess due to inaccurate test data and unreliable heuristics for determining the functional equivalence of Bash commands. We present a manually verified test dataset of 600 instruction-command pairs and a training dataset of 40,939 pairs, increasing the size of previous datasets by 441% and 135%, respectively. Further, we present a novel functional equivalence heuristic that combines command execution with LLM evaluation of command outputs. Our heuristic can determine the functional equivalence of two Bash commands with 95% confidence, a 16% increase over previous heuristics. Evaluation of popular LLMs using our test dataset and heuristic demonstrates that parsing, in-context learning, in-weight learning, and constrained decoding can improve NL2SH accuracy by up to 32%. Our findings emphasize the importance of dataset quality, execution-based evaluation and translation method for advancing NL2SH translation. Our code is available at https://github.com/westenfelder/NL2SH

https://huggingface.co/papers/2502.06858

[

6 authors](https://huggingface.co/papers/2502.06858)

·

Feb 7, 2025

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F1802.08979

NL2Bash: A Corpus and Semantic Parser for Natural Language Interface to the Linux Operating System

https://huggingface.co/papers/1802.08979

We present new data and semantic parsing methods for the problem of mapping English sentences to Bash commands (NL2Bash). Our long-term goal is to enable any user to perform operations such as file manipulation, search, and application-specific scripting by simply stating their goals in English. We take a first step in this domain, by providing a new dataset of challenging but commonly used Bash commands and expert-written English descriptions, along with baseline methods to establish performance levels on this task.

https://huggingface.co/papers/1802.08979

[

4 authors](https://huggingface.co/papers/1802.08979)

·

Feb 24, 2018

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2104.13100

Shellcode_IA32: A Dataset for Automatic Shellcode Generation

https://huggingface.co/papers/2104.13100

We take the first step to address the task of automatically generating shellcodes, i.e., small pieces of code used as a payload in the exploitation of a software vulnerability, starting from natural language comments. We assemble and release a novel dataset (Shellcode_IA32), consisting of challenging but common assembly instructions with their natural language descriptions. We experiment with standard methods in neural machine translation (NMT) to establish baseline performance levels on this task.

https://huggingface.co/papers/2104.13100

[

6 authors](https://huggingface.co/papers/2104.13100)

·

Apr 26, 2021

 [-] 2

https://huggingface.co/login?next=%2Fpapers%2F1808.01400

code2seq: Generating Sequences from Structured Representations of Code

https://huggingface.co/papers/1808.01400

The ability to generate natural language sequences from source code snippets has a variety of applications such as code summarization, documentation, and retrieval. Sequence-to-sequence (seq2seq) models, adopted from neural machine translation (NMT), have achieved state-of-the-art performance on these tasks by treating source code as a sequence of tokens. We present {scriptsize CODE2SEQ}: an alternative approach that leverages the syntactic structure of programming languages to better encode source code. Our model represents a code snippet as the set of compositional paths in its abstract syntax tree (AST) and uses attention to select the relevant paths while decoding. We demonstrate the effectiveness of our approach for two tasks, two programming languages, and four datasets of up to 16M examples. Our model significantly outperforms previous models that were specifically designed for programming languages, as well as state-of-the-art NMT models. An interactive online demo of our model is available at http://code2seq.org. Our code, data and trained models are available at http://github.com/tech-srl/code2seq.

https://huggingface.co/papers/1808.01400

[

4 authors](https://huggingface.co/papers/1808.01400)

·

Aug 3, 2018

 [-] 19

https://huggingface.co/login?next=%2Fpapers%2F2409.02326

Arctic-SnowCoder: Demystifying High-Quality Data in Code Pretraining

https://huggingface.co/papers/2409.02326

Recent studies have been increasingly demonstrating that high-quality data is crucial for effective pretraining of language models. However, the precise definition of "high-quality" remains underexplored. Focusing on the code domain, we introduce Arctic-SnowCoder-1.3B, a data-efficient base code model pretrained on 555B tokens through three phases of progressively refined data: (1) general pretraining with 500B standard-quality code tokens, preprocessed through basic filtering, deduplication, and decontamination, (2) continued pretraining with 50B high-quality tokens, selected from phase one by a BERT-style quality annotator trained to distinguish good code from random data, using positive examples drawn from high-quality code files, along with instruction data from Magicoder and StarCoder2-Instruct, and (3) enhanced pretraining with 5B synthetic data created by Llama-3.1-70B using phase two data as seeds, adapting the Magicoder approach for pretraining. Despite being trained on a limited dataset, Arctic-SnowCoder achieves state-of-the-art performance on BigCodeBench, a coding benchmark focusing on practical and challenging programming tasks, compared to similarly sized models trained on no more than 1T tokens, outperforming Phi-1.5-1.3B by 36%. Across all evaluated benchmarks, Arctic-SnowCoder-1.3B beats StarCoderBase-3B pretrained on 1T tokens. Additionally, it matches the performance of leading small base code models trained on trillions of tokens. For example, Arctic-SnowCoder-1.3B surpasses StarCoder2-3B, pretrained on over 3.3T tokens, on HumanEval+, a benchmark that evaluates function-level code generation, and remains competitive on BigCodeBench. Our evaluation presents a comprehensive analysis justifying various design choices for Arctic-SnowCoder. Most importantly, we find that the key to high-quality data is its alignment with the distribution of downstream applications.

https://huggingface.co/papers/2409.02326

[

3 authors](https://huggingface.co/papers/2409.02326)

·

Sep 3, 2024 

2

https://huggingface.co/papers/2409.02326#community

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2203.03850

UniXcoder: Unified Cross-Modal Pre-training for Code Representation

https://huggingface.co/papers/2203.03850

Pre-trained models for programming languages have recently demonstrated great success on code intelligence. To support both code-related understanding and generation tasks, recent works attempt to pre-train unified encoder-decoder models. However, such encoder-decoder framework is sub-optimal for auto-regressive tasks, especially code completion that requires a decoder-only manner for efficient inference. In this paper, we present UniXcoder, a unified cross-modal pre-trained model for programming language. The model utilizes mask attention matrices with prefix adapters to control the behavior of the model and leverages cross-modal contents like AST and code comment to enhance code representation. To encode AST that is represented as a tree in parallel, we propose a one-to-one mapping method to transform AST in a sequence structure that retains all structural information from the tree. Furthermore, we propose to utilize multi-modal contents to learn representation of code fragment with contrastive learning, and then align representations among programming languages using a cross-modal generation task. We evaluate UniXcoder on five code-related tasks over nine datasets. To further evaluate the performance of code fragment representation, we also construct a dataset for a new task, called zero-shot code-to-code search. Results show that our model achieves state-of-the-art performance on most tasks and analysis reveals that comment and AST can both enhance UniXcoder.

https://huggingface.co/papers/2203.03850

[

6 authors](https://huggingface.co/papers/2203.03850)

·

Mar 7, 2022

 [-] 5

https://huggingface.co/login?next=%2Fpapers%2F2510.21057

Soft Instruction De-escalation Defense

https://huggingface.co/papers/2510.21057

Large Language Models (LLMs) are increasingly deployed in agentic systems that interact with an external environment; this makes them susceptible to prompt injections when dealing with untrusted data. To overcome this limitation, we propose SIC (Soft Instruction Control)-a simple yet effective iterative prompt sanitization loop designed for tool-augmented LLM agents. Our method repeatedly inspects incoming data for instructions that could compromise agent behavior. If such content is found, the malicious content is rewritten, masked, or removed, and the result is re-evaluated. The process continues until the input is clean or a maximum iteration limit is reached; if imperative instruction-like content remains, the agent halts to ensure security. By allowing multiple passes, our approach acknowledges that individual rewrites may fail but enables the system to catch and correct missed injections in later steps. Although immediately useful, worst-case analysis shows that SIC is not infallible; strong adversary can still get a 15% ASR by embedding non-imperative workflows. This nonetheless raises the bar.

https://huggingface.co/papers/2510.21057

 

https://huggingface.co/papers/2510.21057

 Google

https://huggingface.co/google

·

Oct 23, 2025 

1

https://huggingface.co/papers/2510.21057#community

 [-] 74

https://huggingface.co/login?next=%2Fpapers%2F2310.17680

CodeFusion: A Pre-trained Diffusion Model for Code Generation

https://huggingface.co/papers/2310.17680

Imagine a developer who can only change their last line of code, how often would they have to start writing a function from scratch before it is correct? Auto-regressive models for code generation from natural language have a similar limitation: they do not easily allow reconsidering earlier tokens generated. We introduce CodeFusion, a pre-trained diffusion code generation model that addresses this limitation by iteratively denoising a complete program conditioned on the encoded natural language. We evaluate CodeFusion on the task of natural language to code generation for Bash, Python, and Microsoft Excel conditional formatting (CF) rules. Experiments show that CodeFusion (75M parameters) performs on par with state-of-the-art auto-regressive systems (350M-175B parameters) in top-1 accuracy and outperforms them in top-3 and top-5 accuracy due to its better balance in diversity versus quality.

https://huggingface.co/papers/2310.17680

[

6 authors](https://huggingface.co/papers/2310.17680)

·

Oct 26, 2023 

10

https://huggingface.co/papers/2310.17680#community

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2210.17152

Audio Time-Scale Modification with Temporal Compressing Networks

https://huggingface.co/papers/2210.17152

We propose a novel approach for time-scale modification of audio signals. Unlike traditional methods that rely on the framing technique or the short-time Fourier transform to preserve the frequency during temporal stretching, our neural network model encodes the raw audio into a high-level latent representation, dubbed Neuralgram, where each vector represents 1024 audio sample points. Due to a sufficient compression ratio, we are able to apply arbitrary spatial interpolation of the Neuralgram to perform temporal stretching. Finally, a learned neural decoder synthesizes the time-scaled audio samples based on the stretched Neuralgram representation. Both the encoder and decoder are trained with latent regression losses and adversarial losses in order to obtain high-fidelity audio samples. Despite its simplicity, our method has comparable performance compared to the existing baselines and opens a new possibility in research into modern time-scale modification. Audio samples can be found at https://tsmnet-mmasia23.github.io

https://huggingface.co/papers/2210.17152

[

3 authors](https://huggingface.co/papers/2210.17152)

·

Oct 30, 2022

 [-] 29

https://huggingface.co/login?next=%2Fpapers%2F2310.03731

MathCoder: Seamless Code Integration in LLMs for Enhanced Mathematical Reasoning

https://huggingface.co/papers/2310.03731

The recently released GPT-4 Code Interpreter has demonstrated remarkable proficiency in solving challenging math problems, primarily attributed to its ability to seamlessly reason with natural language, generate code, execute code, and continue reasoning based on the execution output. In this paper, we present a method to fine-tune open-source language models, enabling them to use code for modeling and deriving math equations and, consequently, enhancing their mathematical reasoning abilities. We propose a method of generating novel and high-quality datasets with math problems and their code-based solutions, referred to as MathCodeInstruct. Each solution interleaves natural language, code, and execution results. We also introduce a customized supervised fine-tuning and inference approach. This approach yields the MathCoder models, a family of models capable of generating code-based solutions for solving challenging math problems. Impressively, the MathCoder models achieve state-of-the-art scores among open-source LLMs on the MATH (45.2%) and GSM8K (83.9%) datasets, substantially outperforming other open-source alternatives. Notably, the MathCoder model not only surpasses ChatGPT-3.5 and PaLM-2 on GSM8K and MATH but also outperforms GPT-4 on the competition-level MATH dataset. The dataset and models will be released at https://github.com/mathllm/MathCoder.

https://huggingface.co/papers/2310.03731

[

10 authors](https://huggingface.co/papers/2310.03731)

·

Oct 5, 2023 

4

https://huggingface.co/papers/2310.03731#community

 [-] 1

https://huggingface.co/login?next=%2Fpapers%2F2405.18400

Superposed Decoding: Multiple Generations from a Single Autoregressive Inference Pass

https://huggingface.co/papers/2405.18400

Many applications today provide users with multiple auto-complete drafts as they type, including GitHub's code completion, Gmail's smart compose, and Apple's messaging auto-suggestions. Under the hood, language models support this by running an autoregressive inference pass to provide a draft. Consequently, providing k drafts to the user requires running an expensive language model k times. To alleviate the computation cost of running k inference passes, we propose Superposed Decoding, a new decoding algorithm that generates k drafts at the computation cost of one autoregressive inference pass. We achieve this by feeding a superposition of the most recent token embeddings from the k drafts as input to the next decoding step of the language model. At every inference step we combine the k drafts with the top-k tokens to get k^2 new drafts and cache the k most likely options, using an n-gram interpolation with minimal compute overhead to filter out incoherent generations. Our experiments show that k drafts from Superposed Decoding are at least as coherent and factual as Nucleus Sampling and Greedy Decoding respectively, while being at least 2.44times faster for kge3. In a compute-normalized setting, user evaluations demonstrably favor text generated by Superposed Decoding over Nucleus Sampling. Code and more examples open-sourced at https://github.com/RAIVNLab/SuperposedDecoding.

https://huggingface.co/papers/2405.18400

[

10 authors](https://huggingface.co/papers/2405.18400)

·

May 28, 2024

 [-] 35

https://huggingface.co/login?next=%2Fpapers%2F2504.07957

MM-IFEngine: Towards Multimodal Instruction Following

https://huggingface.co/papers/2504.07957

The Instruction Following (IF) ability measures how well Multi-modal Large Language Models (MLLMs) understand exactly what users are telling them and whether they are doing it right. Existing multimodal instruction following training data is scarce, the benchmarks are simple with atomic instructions, and the evaluation strategies are imprecise for tasks demanding exact output constraints. To address this, we present MM-IFEngine, an effective pipeline to generate high-quality image-instruction pairs. Our MM-IFEngine pipeline yields large-scale, diverse, and high-quality training data MM-IFInstruct-23k, which is suitable for Supervised Fine-Tuning (SFT) and extended as MM-IFDPO-23k for Direct Preference Optimization (DPO). We further introduce MM-IFEval, a challenging and diverse multi-modal instruction-following benchmark that includes (1) both compose-level constraints for output responses and perception-level constraints tied to the input images, and (2) a comprehensive evaluation pipeline incorporating both rule-based assessment and judge model. We conduct SFT and DPO experiments and demonstrate that fine-tuning MLLMs on MM-IFInstruct-23k and MM-IFDPO-23k achieves notable gains on various IF benchmarks, such as MM-IFEval (+10.2%), MIA (+7.6%), and IFEval (+12.3%). The full data and evaluation code will be released on https://github.com/SYuan03/MM-IFEngine.

https://huggingface.co/papers/2504.07957

[

10 authors](https://huggingface.co/papers/2504.07957)

·

Apr 10, 2025 

2

https://huggingface.co/papers/2504.07957#community

 [-] 1

https://huggingface.co/login?next=%2Fpapers%2F2505.24689

BPE Stays on SCRIPT: Structured Encoding for Robust Multilingual Pretokenization

https://huggingface.co/papers/2505.24689

Byte Pair Encoding (BPE) tokenizers, widely used in Large Language Models, face challenges in multilingual settings, including penalization of non-Western scripts and the creation of tokens with partial UTF-8 sequences. Pretokenization, often reliant on complex regular expressions, can also introduce fragility and unexpected edge cases. We propose SCRIPT (Script Category Representation in PreTokenization), a novel encoding scheme that bypasses UTF-8 byte conversion by using initial tokens based on Unicode script and category properties. This approach enables a simple, rule-based pretokenization strategy that respects script boundaries, offering a robust alternative to pretokenization strategies based on regular expressions. We also introduce and validate a constrained BPE merging strategy that enforces character integrity, applicable to both SCRIPT-BPE and byte-based BPE. Our experiments demonstrate that SCRIPT-BPE achieves competitive compression while eliminating encoding-based penalties for non-Latin-script languages.

https://huggingface.co/papers/2505.24689

[

2 authors](https://huggingface.co/papers/2505.24689)

·

May 30, 2025

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2502.04536

Idioms: Neural Decompilation With Joint Code and Type Prediction

https://huggingface.co/papers/2502.04536

Decompilers are important tools for reverse engineers that help them analyze software at a higher level of abstraction than assembly. Unfortunately, because compilation is lossy, deterministic decompilers produce code that is missing many of the details that make source code readable in the first place, like variable names and types. Neural decompilers, on the other hand, offer the ability to statistically fill in these details. Existing work in neural decompilation, however, suffers from substantial drawbacks that limits its ability to handle real code: it is unable to handle user-defined composite types, which are essential to fully specifying many functions' semantics, or require test cases. In this work, we introduce a new training process to finetune any LLM into a neural decompiler capable of generating the appropriate user-defined types alongside the decompilation. We introduce a new dataset, Realtype, that includes substantially more complicated and realistic types than existing neural decompilation benchmarks. Motivated by the intuition that different parts of data structures can be operated upon by different parts of the program, we show that interprocedural context can help improve neural decompilers' ability to handle user-defined types. We show that our training process yields state-of-the-art results in neural decompilation. We also publicly release the Idioms series of finetuned neural decompilation models in support of open science. In summary, we identify the need for joint code and type prediction, show that it is a hard problem, and take the first steps towards solving it.

https://huggingface.co/papers/2502.04536

[

3 authors](https://huggingface.co/papers/2502.04536)

·

Feb 6, 2025

 [-] 1

https://huggingface.co/login?next=%2Fpapers%2F2510.27254

Languages are Modalities: Cross-Lingual Alignment via Encoder Injection

https://huggingface.co/papers/2510.27254

Instruction-tuned Large Language Models (LLMs) underperform on low resource, non-Latin scripts due to tokenizer fragmentation and weak cross-lingual coupling. We present LLINK (Latent Language Injection for Non-English Knowledge), a compute efficient language-as-modality method that conditions an instruction-tuned decoder without changing the tokenizer or retraining the decoder. First, we align sentence embeddings from a frozen multilingual encoder to the decoder's latent embedding space at a reserved position via a lightweight contrastive projector. Second, the vector is expanded into K soft slots and trained with minimal adapters so the frozen decoder consumes the signal. LLINK substantially improves bilingual retrieval and achieves 81.3% preference over the base model and 63.6% over direct fine-tuning in LLM-judged Q&A evaluations. We further find that improvements can be attributed to reduced tokenization inflation and a stronger cross lingual alignment, despite the model having residual weaknesses in numeric fidelity. Treating low resource languages as a modality offers a practical path to stronger cross-lingual alignment in lightweight LLMs.

https://huggingface.co/papers/2510.27254

[

2 authors](https://huggingface.co/papers/2510.27254)

·

Oct 30, 2025

 [-] 2

https://huggingface.co/login?next=%2Fpapers%2F2507.11538

How Many Instructions Can LLMs Follow at Once?

https://huggingface.co/papers/2507.11538

Production-grade LLM systems require robust adherence to dozens or even hundreds of instructions simultaneously. However, the instruction-following capabilities of LLMs at high instruction densities have not yet been characterized, as existing benchmarks only evaluate models on tasks with a single or few instructions. We introduce IFScale, a simple benchmark of 500 keyword-inclusion instructions for a business report writing task to measure how instruction-following performance degrades as instruction density increases. We evaluate 20 state-of-the-art models across seven major providers and find that even the best frontier models only achieve 68% accuracy at the max density of 500 instructions. Our analysis reveals model size and reasoning capability to correlate with 3 distinct performance degradation patterns, bias towards earlier instructions, and distinct categories of instruction-following errors. Our insights can help inform design of instruction-dense prompts in real-world applications and highlight important performance-latency tradeoffs. We open-source the benchmark and all results for further analysis at https://distylai.github.io/IFScale.

https://huggingface.co/papers/2507.11538

[

4 authors](https://huggingface.co/papers/2507.11538)

·

Jul 15, 2025

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2305.00909

Outline, Then Details: Syntactically Guided Coarse-To-Fine Code Generation

https://huggingface.co/papers/2305.00909

For a complicated algorithm, its implementation by a human programmer usually starts with outlining a rough control flow followed by iterative enrichments, eventually yielding carefully generated syntactic structures and variables in a hierarchy. However, state-of-the-art large language models generate codes in a single pass, without intermediate warm-ups to reflect the structured thought process of "outline-then-detail". Inspired by the recent success of chain-of-thought prompting, we propose ChainCoder, a program synthesis language model that generates Python code progressively, i.e. from coarse to fine in multiple passes. We first decompose source code into layout frame components and accessory components via abstract syntax tree parsing to construct a hierarchical representation. We then reform our prediction target into a multi-pass objective, each pass generates a subsequence, which is concatenated in the hierarchy. Finally, a tailored transformer architecture is leveraged to jointly encode the natural language descriptions and syntactically aligned I/O data samples. Extensive evaluations show that ChainCoder outperforms state-of-the-arts, demonstrating that our progressive generation eases the reasoning procedure and guides the language model to generate higher-quality solutions. Our codes are available at: https://github.com/VITA-Group/ChainCoder.

https://huggingface.co/papers/2305.00909

[

7 authors](https://huggingface.co/papers/2305.00909)

·

Apr 27, 2023

 [-] 1

https://huggingface.co/login?next=%2Fpapers%2F2410.22240

Are Decoder-Only Large Language Models the Silver Bullet for Code Search?

https://huggingface.co/papers/2410.22240

Code search is crucial for code reuse, enabling developers to efficiently locate relevant snippets. Current methods rely on encoder-based models, which suffer from limitations such as poor generalization and restricted input lengths. Decoder-only large language models (LLMs), with their extensive pre-training, larger size, and longer input capabilities, offer potential solutions to these issues, yet their effectiveness in code search remains underexplored. To fill this gap, our study presents the first systematic exploration of decoder-only LLMs for code search. We evaluate nine state-of-the-art decoder-only models using two fine-tuning methods, two datasets (CSN and CoSQA^+), and three model sizes. Our findings reveal that fine-tuned CodeGemma significantly outperforms encoder-only models like UniXcoder, achieving a 5.57% improvement in MRR on CSN and a 49.6% increase in MAP on CoSQA^+ compared to zero-shot UniXcoder. These results highlight the superior performance and adaptability of decoder-only models. Additionally, we provide valuable insights into optimizing these models for code search, covering aspects such as model selection, fine-tuning methods, training data, and model size, and discussing their strengths and limitations.

https://huggingface.co/papers/2410.22240

[

5 authors](https://huggingface.co/papers/2410.22240)

·

Oct 29, 2024

 [-] 1

https://huggingface.co/login?next=%2Fpapers%2F2402.12079

LVCHAT: Facilitating Long Video Comprehension

https://huggingface.co/papers/2402.12079

Enabling large language models (LLMs) to read videos is vital for multimodal LLMs. Existing works show promise on short videos whereas long video (longer than e.g.~1 minute) comprehension remains challenging. The major problem lies in the over-compression of videos, i.e., the encoded video representations are not enough to represent the whole video. To address this issue, we propose Long Video Chat (LVChat), where Frame-Scalable Encoding (FSE) is introduced to dynamically adjust the number of embeddings in alignment with the duration of the video to ensure long videos are not overly compressed into a few embeddings. To deal with long videos whose length is beyond videos seen during training, we propose Interleaved Frame Encoding (IFE), repeating positional embedding and interleaving multiple groups of videos to enable long video input, avoiding performance degradation due to overly long videos. Experimental results show that LVChat significantly outperforms existing methods by up to 27% in accuracy on long-video QA datasets and long-video captioning benchmarks. Our code is published at https://github.com/wangyu-ustc/LVChat.

https://huggingface.co/papers/2402.12079

[

4 authors](https://huggingface.co/papers/2402.12079)

·

Feb 18, 2024

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2407.03157

Let the Code LLM Edit Itself When You Edit the Code

https://huggingface.co/papers/2407.03157

In this work, we investigate a typical scenario in code generation where a developer edits existing code in real time and requests a code assistant, e.g., a large language model, to re-predict the next token or next line on the fly. Naively, the LLM needs to re-encode the entire KV cache to provide an accurate prediction. However, this process is computationally expensive, especially when the sequence length is long. Simply encoding the edited subsequence and integrating it to the original KV cache meets the temporal confusion problem, leading to significantly worse performance. We address this efficiency and accuracy trade-off by introducing \textbf{Positional \textbf{Integrity Encoding} (PIE). Building upon the rotary positional encoding, PIE first removes the rotary matrices in the Key cache that introduce temporal confusion and then reapplies the correct rotary matrices. This process ensures that positional relationships between tokens are correct and requires only a single round of matrix multiplication. We validate the effectiveness of PIE through extensive experiments on the RepoBench-C-8k dataset, utilizing DeepSeek-Coder models with 1.3B, 6.7B, and 33B parameters. Our evaluation includes three real-world coding tasks: code insertion, code deletion, and multi-place code editing. Results demonstrate that PIE reduces computational overhead by over 85% compared to the standard full recomputation approach across all model sizes and tasks while well approximating the model performance.

https://huggingface.co/papers/2407.03157

[

6 authors](https://huggingface.co/papers/2407.03157)

·

Jul 3, 2024

 [-] 14

https://huggingface.co/login?next=%2Fpapers%2F2407.05700

InverseCoder: Unleashing the Power of Instruction-Tuned Code LLMs with Inverse-Instruct

https://huggingface.co/papers/2407.05700

Recent advancements in open-source code large language models (LLMs) have demonstrated remarkable coding abilities by fine-tuning on the data generated from powerful closed-source LLMs such as GPT-3.5 and GPT-4 for instruction tuning. This paper explores how to further improve an instruction-tuned code LLM by generating data from itself rather than querying closed-source LLMs. Our key observation is the misalignment between the translation of formal and informal languages: translating formal language (i.e., code) to informal language (i.e., natural language) is more straightforward than the reverse. Based on this observation, we propose INVERSE-INSTRUCT, which summarizes instructions from code snippets instead of the reverse. Specifically, given an instruction tuning corpus for code and the resulting instruction-tuned code LLM, we ask the code LLM to generate additional high-quality instructions for the original corpus through code summarization and self-evaluation. Then, we fine-tune the base LLM on the combination of the original corpus and the self-generated one, which yields a stronger instruction-tuned LLM. We present a series of code LLMs named InverseCoder, which surpasses the performance of the original code LLMs on a wide range of benchmarks, including Python text-to-code generation, multilingual coding, and data-science code generation.

https://huggingface.co/papers/2407.05700

[

16 authors](https://huggingface.co/papers/2407.05700)

·

Jul 7, 2024 

2

https://huggingface.co/papers/2407.05700#community

 [-] 33

https://huggingface.co/login?next=%2Fpapers%2F2305.06161

StarCoder: may the source be with you!

https://huggingface.co/papers/2305.06161

The BigCode community, an open-scientific collaboration working on the responsible development of Large Language Models for Code (Code LLMs), introduces StarCoder and StarCoderBase: 15.5B parameter models with 8K context length, infilling capabilities and fast large-batch inference enabled by multi-query attention. StarCoderBase is trained on 1 trillion tokens sourced from The Stack, a large collection of permissively licensed GitHub repositories with inspection tools and an opt-out process. We fine-tuned StarCoderBase on 35B Python tokens, resulting in the creation of StarCoder. We perform the most comprehensive evaluation of Code LLMs to date and show that StarCoderBase outperforms every open Code LLM that supports multiple programming languages and matches or outperforms the OpenAI code-cushman-001 model. Furthermore, StarCoder outperforms every model that is fine-tuned on Python, can be prompted to achieve 40% pass@1 on HumanEval, and still retains its performance on other programming languages. We take several important steps towards a safe open-access model release, including an improved PII redaction pipeline and a novel attribution tracing tool, and make the StarCoder models publicly available under a more commercially viable version of the Open Responsible AI Model license.

https://huggingface.co/papers/2305.06161

[

67 authors](https://huggingface.co/papers/2305.06161)

·

May 8, 2023 

3

https://huggingface.co/papers/2305.06161#community

 [-] 13

https://huggingface.co/login?next=%2Fpapers%2F2503.05315

LoRACode: LoRA Adapters for Code Embeddings

https://huggingface.co/papers/2503.05315

Code embeddings are essential for semantic code search; however, current approaches often struggle to capture the precise syntactic and contextual nuances inherent in code. Open-source models such as CodeBERT and UniXcoder exhibit limitations in scalability and efficiency, while high-performing proprietary systems impose substantial computational costs. We introduce a parameter-efficient fine-tuning method based on Low-Rank Adaptation (LoRA) to construct task-specific adapters for code retrieval. Our approach reduces the number of trainable parameters to less than two percent of the base model, enabling rapid fine-tuning on extensive code corpora (2 million samples in 25 minutes on two H100 GPUs). Experiments demonstrate an increase of up to 9.1% in Mean Reciprocal Rank (MRR) for Code2Code search, and up to 86.69% for Text2Code search tasks across multiple programming languages. Distinction in task-wise and language-wise adaptation helps explore the sensitivity of code retrieval for syntactical and linguistic variations.

https://huggingface.co/papers/2503.05315

[

3 authors](https://huggingface.co/papers/2503.05315)

·

Mar 6, 2025 

2

https://huggingface.co/papers/2503.05315#community

 [-] 1

https://huggingface.co/login?next=%2Fpapers%2F2207.03578

Code Translation with Compiler Representations

https://huggingface.co/papers/2207.03578

In this paper, we leverage low-level compiler intermediate representations (IR) to improve code translation. Traditional transpilers rely on syntactic information and handcrafted rules, which limits their applicability and produces unnatural-looking code. Applying neural machine translation (NMT) approaches to code has successfully broadened the set of programs on which one can get a natural-looking translation. However, they treat the code as sequences of text tokens, and still do not differentiate well enough between similar pieces of code which have different semantics in different languages. The consequence is low quality translation, reducing the practicality of NMT, and stressing the need for an approach significantly increasing its accuracy. Here we propose to augment code translation with IRs, specifically LLVM IR, with results on the C++, Java, Rust, and Go languages. Our method improves upon the state of the art for unsupervised code translation, increasing the number of correct translations by 11% on average, and up to 79% for the Java -> Rust pair with greedy decoding. We extend previous test sets for code translation, by adding hundreds of Go and Rust functions. Additionally, we train models with high performance on the problem of IR decompilation, generating programming source code from IR, and study using IRs as intermediary pivot for translation.

https://huggingface.co/papers/2207.03578

[

6 authors](https://huggingface.co/papers/2207.03578)

·

Jun 30, 2022

 [-] 2

https://huggingface.co/login?next=%2Fpapers%2F2109.00859

CodeT5: Identifier-aware Unified Pre-trained Encoder-Decoder Models for Code Understanding and Generation

https://huggingface.co/papers/2109.00859

Pre-trained models for Natural Languages (NL) like BERT and GPT have been recently shown to transfer well to Programming Languages (PL) and largely benefit a broad set of code-related tasks. Despite their success, most current methods either rely on an encoder-only (or decoder-only) pre-training that is suboptimal for generation (resp. understanding) tasks or process the code snippet in the same way as NL, neglecting the special characteristics of PL such as token types. We present CodeT5, a unified pre-trained encoder-decoder Transformer model that better leverages the code semantics conveyed from the developer-assigned identifiers. Our model employs a unified framework to seamlessly support both code understanding and generation tasks and allows for multi-task learning. Besides, we propose a novel identifier-aware pre-training task that enables the model to distinguish which code tokens are identifiers and to recover them when they are masked. Furthermore, we propose to exploit the user-written code comments with a bimodal dual generation task for better NL-PL alignment. Comprehensive experiments show that CodeT5 significantly outperforms prior methods on understanding tasks such as code defect detection and clone detection, and generation tasks across various directions including PL-NL, NL-PL, and PL-PL. Further analysis reveals that our model can better capture semantic information from code. Our code and pre-trained models are released at https: //github.com/salesforce/CodeT5 .

https://huggingface.co/papers/2109.00859

[

4 authors](https://huggingface.co/papers/2109.00859)

·

Sep 2, 2021

 [-] 4

https://huggingface.co/login?next=%2Fpapers%2F2512.03771

In-Context Representation Hijacking

https://huggingface.co/papers/2512.03771

We introduce Doublespeak, a simple in-context representation hijacking attack against large language models (LLMs). The attack works by systematically replacing a harmful keyword (e.g., bomb) with a benign token (e.g., carrot) across multiple in-context examples, provided a prefix to a harmful request. We demonstrate that this substitution leads to the internal representation of the benign token converging toward that of the harmful one, effectively embedding the harmful semantics under a euphemism. As a result, superficially innocuous prompts (e.g., How to build a carrot?'') are internally interpreted as disallowed instructions (e.g., How to build a bomb?''), thereby bypassing the model's safety alignment. We use interpretability tools to show that this semantic overwrite emerges layer by layer, with benign meanings in early layers converging into harmful semantics in later ones. Doublespeak is optimization-free, broadly transferable across model families, and achieves strong success rates on closed-source and open-source systems, reaching 74% ASR on Llama-3.3-70B-Instruct with a single-sentence context override. Our findings highlight a new attack surface in the latent space of LLMs, revealing that current alignment strategies are insufficient and should instead operate at the representation level.

https://huggingface.co/papers/2512.03771

[

4 authors](https://huggingface.co/papers/2512.03771)

·

Dec 3, 2025 

2

https://huggingface.co/papers/2512.03771#community

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2504.09570

LLMs Can Achieve High-quality Simultaneous Machine Translation as Efficiently as Offline

https://huggingface.co/papers/2504.09570

When the complete source sentence is provided, Large Language Models (LLMs) perform excellently in offline machine translation even with a simple prompt "Translate the following sentence from [src lang] into [tgt lang]:". However, in many real scenarios, the source tokens arrive in a streaming manner and simultaneous machine translation (SiMT) is required, then the efficiency and performance of decoder-only LLMs are significantly limited by their auto-regressive nature. To enable LLMs to achieve high-quality SiMT as efficiently as offline translation, we propose a novel paradigm that includes constructing supervised fine-tuning (SFT) data for SiMT, along with new training and inference strategies. To replicate the token input/output stream in SiMT, the source and target tokens are rearranged into an interleaved sequence, separated by special tokens according to varying latency requirements. This enables powerful LLMs to learn read and write operations adaptively, based on varying latency prompts, while still maintaining efficient auto-regressive decoding. Experimental results show that, even with limited SFT data, our approach achieves state-of-the-art performance across various SiMT benchmarks, and preserves the original abilities of offline translation. Moreover, our approach generalizes well to document-level SiMT setting without requiring specific fine-tuning, even beyond the offline translation model.

https://huggingface.co/papers/2504.09570

[

7 authors](https://huggingface.co/papers/2504.09570)

·

Apr 13, 2025

 [-] 3

https://huggingface.co/login?next=%2Fpapers%2F2509.09550

Finite Scalar Quantization Enables Redundant and Transmission-Robust Neural Audio Compression at Low Bit-rates

https://huggingface.co/papers/2509.09550

Neural Audio Codecs (NACs) have become increasingly adopted in speech processing tasks due to their excellent rate-distortion performance and compatibility with Large Language Models (LLMs) as discrete feature representations for audio generation. While most existing codecs rely on Residual Vector Quantization (RVQ), Finite Scalar Quantization (FSQ) has recently emerged as a compelling alternative that simplifies training and natively supports single codebooks. We introduce NeuCodec, an FSQ-based NAC, and show that FSQ encodes baked-in redundancy which produces an encoding which is robust when transmitted through noisy channels. First, through an encoder distillation experiment, we show that two different encoders can learn to encode identical audio into vastly different code sequences whilst maintaining comparable reconstruction quality with the same quantizer and decoder. Second, we demonstrate that FSQ has vastly superior bit-level perturbation robustness by comparing the performance of RVQ and FSQ codecs when simulating the transmission of code sequences through a noisy channel.

https://huggingface.co/papers/2509.09550

[

5 authors](https://huggingface.co/papers/2509.09550)

·

Sep 11, 2025

 [-] 24

https://huggingface.co/login?next=%2Fpapers%2F2401.18058

LongAlign: A Recipe for Long Context Alignment of Large Language Models

https://huggingface.co/papers/2401.18058

Extending large language models to effectively handle long contexts requires instruction fine-tuning on input sequences of similar length. To address this, we present LongAlign -- a recipe of the instruction data, training, and evaluation for long context alignment. First, we construct a long instruction-following dataset using Self-Instruct. To ensure the data diversity, it covers a broad range of tasks from various long context sources. Second, we adopt the packing and sorted batching strategies to speed up supervised fine-tuning on data with varied length distributions. Additionally, we develop a loss weighting method to balance the contribution to the loss across different sequences during packing training. Third, we introduce the LongBench-Chat benchmark for evaluating instruction-following capabilities on queries of 10k-100k in length. Experiments show that LongAlign outperforms existing recipes for LLMs in long context tasks by up to 30%, while also maintaining their proficiency in handling short, generic tasks. The code, data, and long-aligned models are open-sourced at https://github.com/THUDM/LongAlign.

https://huggingface.co/papers/2401.18058

[

9 authors](https://huggingface.co/papers/2401.18058)

·

Jan 31, 2024 

1

https://huggingface.co/papers/2401.18058#community

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2306.14893

LongCoder: A Long-Range Pre-trained Language Model for Code Completion

https://huggingface.co/papers/2306.14893

In this paper, we introduce a new task for code completion that focuses on handling long code input and propose a sparse Transformer model, called LongCoder, to address this task. LongCoder employs a sliding window mechanism for self-attention and introduces two types of globally accessible tokens - bridge tokens and memory tokens - to improve performance and efficiency. Bridge tokens are inserted throughout the input sequence to aggregate local information and facilitate global interaction, while memory tokens are included to highlight important statements that may be invoked later and need to be memorized, such as package imports and definitions of classes, functions, or structures. We conduct experiments on a newly constructed dataset that contains longer code context and the publicly available CodeXGLUE benchmark. Experimental results demonstrate that LongCoder achieves superior performance on code completion tasks compared to previous models while maintaining comparable efficiency in terms of computational resources during inference. All the codes and data are available at https://github.com/microsoft/CodeBERT.

https://huggingface.co/papers/2306.14893

[

5 authors](https://huggingface.co/papers/2306.14893)

·

Jun 26, 2023

 [-] 32

https://huggingface.co/login?next=%2Fpapers%2F2308.07124

OctoPack: Instruction Tuning Code Large Language Models

https://huggingface.co/papers/2308.07124

Finetuning large language models (LLMs) on instructions leads to vast performance improvements on natural language tasks. We apply instruction tuning using code, leveraging the natural structure of Git commits, which pair code changes with human instructions. We compile CommitPack: 4 terabytes of Git commits across 350 programming languages. We benchmark CommitPack against other natural and synthetic code instructions (xP3x, Self-Instruct, OASST) on the 16B parameter StarCoder model, and achieve state-of-the-art performance among models not trained on OpenAI outputs, on the HumanEval Python benchmark (46.2% pass@1). We further introduce HumanEvalPack, expanding the HumanEval benchmark to a total of 3 coding tasks (Code Repair, Code Explanation, Code Synthesis) across 6 languages (Python, JavaScript, Java, Go, C++, Rust). Our models, OctoCoder and OctoGeeX, achieve the best performance across HumanEvalPack among all permissive models, demonstrating CommitPack's benefits in generalizing to a wider set of languages and natural coding tasks. Code, models and data are freely available at https://github.com/bigcode-project/octopack.

https://huggingface.co/papers/2308.07124

[

10 authors](https://huggingface.co/papers/2308.07124)

·

Aug 14, 2023 

1

https://huggingface.co/papers/2308.07124#community

 [-] 84

https://huggingface.co/login?next=%2Fpapers%2F2402.14658

OpenCodeInterpreter: Integrating Code Generation with Execution and Refinement

https://huggingface.co/papers/2402.14658

The introduction of large language models has significantly advanced code generation. However, open-source models often lack the execution capabilities and iterative refinement of advanced systems like the GPT-4 Code Interpreter. To address this, we introduce OpenCodeInterpreter, a family of open-source code systems designed for generating, executing, and iteratively refining code. Supported by Code-Feedback, a dataset featuring 68K multi-turn interactions, OpenCodeInterpreter integrates execution and human feedback for dynamic code refinement. Our comprehensive evaluation of OpenCodeInterpreter across key benchmarks such as HumanEval, MBPP, and their enhanced versions from EvalPlus reveals its exceptional performance. Notably, OpenCodeInterpreter-33B achieves an accuracy of 83.2 (76.4) on the average (and plus versions) of HumanEval and MBPP, closely rivaling GPT-4's 84.2 (76.2) and further elevates to 91.6 (84.6) with synthesized human feedback from GPT-4. OpenCodeInterpreter brings the gap between open-source code generation models and proprietary systems like GPT-4 Code Interpreter.

https://huggingface.co/papers/2402.14658

[

8 authors](https://huggingface.co/papers/2402.14658)

·

Feb 22, 2024 

6

https://huggingface.co/papers/2402.14658#community

 [-] 3

https://huggingface.co/login?next=%2Fpapers%2F2602.04289

Proxy Compression for Language Modeling

https://huggingface.co/papers/2602.04289

Modern language models are trained almost exclusively on token sequences produced by a fixed tokenizer, an external lossless compressor often over UTF-8 byte sequences, thereby coupling the model to that compressor. This work introduces proxy compression, an alternative training scheme that preserves the efficiency benefits of compressed inputs while providing an end-to-end, raw-byte interface at inference time. During training, one language model is jointly trained on raw byte sequences and compressed views generated by external compressors; through the process, the model learns to internally align compressed sequences and raw bytes. This alignment enables strong transfer between the two formats, even when training predominantly on compressed inputs which are discarded at inference. Extensive experiments on code language modeling demonstrate that proxy compression substantially improves training efficiency and significantly outperforms pure byte-level baselines given fixed compute budgets. As model scale increases, these gains become more pronounced, and proxy-trained models eventually match or rival tokenizer approaches, all while operating solely on raw bytes and retaining the inherent robustness of byte-level modeling.

https://huggingface.co/papers/2602.04289

[

5 authors](https://huggingface.co/papers/2602.04289)

·

Feb 3 

3

https://huggingface.co/papers/2602.04289#community

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2505.12668

Decompile-Bench: Million-Scale Binary-Source Function Pairs for Real-World Binary Decompilation

https://huggingface.co/papers/2505.12668

Recent advances in LLM-based decompilers have been shown effective to convert low-level binaries into human-readable source code. However, there still lacks a comprehensive benchmark that provides large-scale binary-source function pairs, which is critical for advancing the LLM decompilation technology. Creating accurate binary-source mappings incurs severe issues caused by complex compilation settings and widespread function inlining that obscure the correspondence between binaries and their original source code. Previous efforts have either relied on used contest-style benchmarks, synthetic binary-source mappings that diverge significantly from the mappings in real world, or partially matched binaries with only code lines or variable names, compromising the effectiveness of analyzing the binary functionality. To alleviate these issues, we introduce Decompile-Bench, the first open-source dataset comprising two million binary-source function pairs condensed from 100 million collected function pairs, i.e., 450GB of binaries compiled from permissively licensed GitHub projects. For the evaluation purposes, we also developed a benchmark Decompile-Bench-Eval including manually crafted binaries from the well-established HumanEval and MBPP, alongside the compiled GitHub repositories released after 2025 to mitigate data leakage issues. We further explore commonly-used evaluation metrics to provide a thorough assessment of the studied LLM decompilers and find that fine-tuning with Decompile-Bench causes a 20% improvement over previous benchmarks in terms of the re-executability rate. Our code and data has been released in HuggingFace and Github. https://github.com/albertan017/LLM4Decompile

https://huggingface.co/papers/2505.12668

[

9 authors](https://huggingface.co/papers/2505.12668)

·

May 18, 2025

 [-] 2

https://huggingface.co/login?next=%2Fpapers%2F2004.06343

Code Completion using Neural Attention and Byte Pair Encoding

https://huggingface.co/papers/2004.06343

In this paper, we aim to do code completion based on implementing a Neural Network from Li et. al.. Our contribution is that we use an encoding that is in-between character and word encoding called Byte Pair Encoding (BPE). We use this on the source code files treating them as natural text without first going through the abstract syntax tree (AST). We have implemented two models: an attention-enhanced LSTM and a pointer network, where the pointer network was originally introduced to solve out of vocabulary problems. We are interested to see if BPE can replace the need for the pointer network for code completion.

https://huggingface.co/papers/2004.06343

[

3 authors](https://huggingface.co/papers/2004.06343)

·

Apr 13, 2020

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2502.14925

CODEPROMPTZIP: Code-specific Prompt Compression for Retrieval-Augmented Generation in Coding Tasks with LMs

https://huggingface.co/papers/2502.14925

Retrieval-Augmented Generation (RAG) enhances coding tasks by incorporating retrieved code examples into prompts. However, lengthy prompts, often exceeding tens of thousands of tokens, introduce challenges related to limited context windows of language models (LMs) and high computational costs. Existing prompt compression techniques focus on natural language, lacking tailored solutions for code. To address the gap, we propose CodePromptZip, a framework that compresses code examples before integrating into RAG workflows. Our framework employs a type-aware, priority-driven strategy to construct training samples for training code compression model. By using program analysis, we identify token types (e.g., Identifier) and perform ablation analysis to rank their removal priorities based on their impact on task performance. We then train a small LM as the compressor on these samples, enabling flexible compression conditioned on specified ratios while minimizing performance degradation. Specially, the compressor is augmented with a copy mechanism, allowing tokens to be directly copied from the original code snippets. Evaluation results show that CodePromptZip surpasses SOTA entropy-based and distillation-based baselines, improving by 23.4%, 28.7%, and 8.7% over the best baseline for Assertion Generation, Bugs2Fix, and Code Suggestion, respectively.

https://huggingface.co/papers/2502.14925

[

3 authors](https://huggingface.co/papers/2502.14925)

·

Feb 19, 2025

 [-] 7

https://huggingface.co/login?next=%2Fpapers%2F2306.10763

Guiding Language Models of Code with Global Context using Monitors

https://huggingface.co/papers/2306.10763

Language models of code (LMs) work well when the surrounding code in the vicinity of generation provides sufficient context. This is not true when it becomes necessary to use types or functionality defined in another module or library, especially those not seen during training. LMs suffer from limited awareness of such global context and end up hallucinating, e.g., using types defined in other files incorrectly. Recent work tries to overcome this issue by retrieving global information to augment the local context. However, this bloats the prompt or requires architecture modifications and additional training. Integrated development environments (IDEs) assist developers by bringing the global context at their fingertips using static analysis. We extend this assistance, enjoyed by developers, to the LMs. We propose a notion of monitors that use static analysis in the background to guide the decoding. Unlike a priori retrieval, static analysis is invoked iteratively during the entire decoding process, providing the most relevant suggestions on demand. We demonstrate the usefulness of our proposal by monitoring for type-consistent use of identifiers whenever an LM generates code for object dereference. To evaluate our approach, we curate PragmaticCode, a dataset of open-source projects with their development environments. On models of varying parameter scale, we show that monitor-guided decoding consistently improves the ability of an LM to not only generate identifiers that match the ground truth but also improves compilation rates and agreement with ground truth. We find that LMs with fewer parameters, when guided with our monitor, can outperform larger LMs. With monitor-guided decoding, SantaCoder-1.1B achieves better compilation rate and next-identifier match than the much larger text-davinci-003 model. The datasets and code will be released at https://aka.ms/monitors4codegen .

https://huggingface.co/papers/2306.10763

[

5 authors](https://huggingface.co/papers/2306.10763)

·

Jun 18, 2023 

3

https://huggingface.co/papers/2306.10763#community

 [-] 108

https://huggingface.co/login?next=%2Fpapers%2F2510.00446

LongCodeZip: Compress Long Context for Code Language Models

https://huggingface.co/papers/2510.00446

Code generation under long contexts is becoming increasingly critical as Large Language Models (LLMs) are required to reason over extensive information in the codebase. While recent advances enable code LLMs to process long inputs, high API costs and generation latency remain substantial bottlenecks. Existing context pruning techniques, such as LLMLingua, achieve promising results for general text but overlook code-specific structures and dependencies, leading to suboptimal performance in programming tasks. In this paper, we propose LongCodeZip, a novel plug-and-play code compression framework designed specifically for code LLMs. LongCodeZip employs a dual-stage strategy: (1) coarse-grained compression, which identifies and ranks function-level chunks using conditional perplexity with respect to the instruction, retaining only the most relevant functions; and (2) fine-grained compression, which segments retained functions into blocks based on perplexity and selects an optimal subset under an adaptive token budget to maximize relevance. Evaluations across multiple tasks, including code completion, summarization, and question answering, show that LongCodeZip consistently outperforms baseline methods, achieving up to a 5.6x compression ratio without degrading task performance. By effectively reducing context size while preserving essential information, LongCodeZip enables LLMs to better scale to real-world, large-scale code scenarios, advancing the efficiency and capability of code intelligence applications.

https://huggingface.co/papers/2510.00446

 

https://huggingface.co/papers/2510.00446

 Stanford University

https://huggingface.co/Stanford-University

·

Sep 30, 2025 

7

https://huggingface.co/papers/2510.00446#community

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F1906.04908

SPoC: Search-based Pseudocode to Code

https://huggingface.co/papers/1906.04908

We consider the task of mapping pseudocode to long programs that are functionally correct. Given test cases as a mechanism to validate programs, we search over the space of possible translations of the pseudocode to find a program that passes the validation. However, without proper credit assignment to localize the sources of program failures, it is difficult to guide search toward more promising programs. We propose to perform credit assignment based on signals from compilation errors, which constitute 88.7% of program failures. Concretely, we treat the translation of each pseudocode line as a discrete portion of the program, and whenever a synthesized program fails to compile, an error localization method tries to identify the portion of the program responsible for the failure. We then focus search over alternative translations of the pseudocode for those portions. For evaluation, we collected the SPoC dataset (Search-based Pseudocode to Code) containing 18,356 programs with human-authored pseudocode and test cases. Under a budget of 100 program compilations, performing search improves the synthesis success rate over using the top-one translation of the pseudocode from 25.6% to 44.7%.

https://huggingface.co/papers/1906.04908

[

7 authors](https://huggingface.co/papers/1906.04908)

·

Jun 11, 2019

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2405.19265

AlchemistCoder: Harmonizing and Eliciting Code Capability by Hindsight Tuning on Multi-source Data

https://huggingface.co/papers/2405.19265

Open-source Large Language Models (LLMs) and their specialized variants, particularly Code LLMs, have recently delivered impressive performance. However, previous Code LLMs are typically fine-tuned on single-source data with limited quality and diversity, which may insufficiently elicit the potential of pre-trained Code LLMs. In this paper, we present AlchemistCoder, a series of Code LLMs with enhanced code generation and generalization capabilities fine-tuned on multi-source data. To achieve this, we pioneer to unveil inherent conflicts among the various styles and qualities in multi-source code corpora and introduce data-specific prompts with hindsight relabeling, termed AlchemistPrompts, to harmonize different data sources and instruction-response pairs. Additionally, we propose incorporating the data construction process into the fine-tuning data as code comprehension tasks, including instruction evolution, data filtering, and code review. Extensive experiments demonstrate that AlchemistCoder holds a clear lead among all models of the same size (6.7B/7B) and rivals or even surpasses larger models (15B/33B/70B), showcasing the efficacy of our method in refining instruction-following capabilities and advancing the boundaries of code intelligence.

https://huggingface.co/papers/2405.19265

[

11 authors](https://huggingface.co/papers/2405.19265)

·

May 29, 2024

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F1910.02216

JuICe: A Large Scale Distantly Supervised Dataset for Open Domain Context-based Code Generation

https://huggingface.co/papers/1910.02216

Interactive programming with interleaved code snippet cells and natural language markdown is recently gaining popularity in the form of Jupyter notebooks, which accelerate prototyping and collaboration. To study code generation conditioned on a long context history, we present JuICe, a corpus of 1.5 million examples with a curated test set of 3.7K instances based on online programming assignments. Compared with existing contextual code generation datasets, JuICe provides refined human-curated data, open-domain code, and an order of magnitude more training data. Using JuICe, we train models for two tasks: (1) generation of the API call sequence in a code cell, and (2) full code cell generation, both conditioned on the NL-Code history up to a particular code cell. Experiments using current baseline code generation models show that both context and distant supervision aid in generation, and that the dataset is challenging for current systems.

https://huggingface.co/papers/1910.02216

[

3 authors](https://huggingface.co/papers/1910.02216)

·

Oct 4, 2019

 [-] 18

https://huggingface.co/login?next=%2Fpapers%2F2404.05875

CodecLM: Aligning Language Models with Tailored Synthetic Data

https://huggingface.co/papers/2404.05875

Instruction tuning has emerged as the key in aligning large language models (LLMs) with specific task instructions, thereby mitigating the discrepancy between the next-token prediction objective and users' actual goals. To reduce the labor and time cost to collect or annotate data by humans, researchers start to explore the use of LLMs to generate instruction-aligned synthetic data. Recent works focus on generating diverse instructions and applying LLM to increase instruction complexity, often neglecting downstream use cases. It remains unclear how to tailor high-quality data to elicit better instruction-following abilities in different target instruction distributions and LLMs. To this end, we introduce CodecLM, a general framework for adaptively generating high-quality synthetic data for LLM alignment with different downstream instruction distributions and LLMs. Drawing on the Encode-Decode principles, we use LLMs as codecs to guide the data generation process. We first encode seed instructions into metadata, which are concise keywords generated on-the-fly to capture the target instruction distribution, and then decode metadata to create tailored instructions. We also introduce Self-Rubrics and Contrastive Filtering during decoding to tailor data-efficient samples. Extensive experiments on four open-domain instruction following benchmarks validate the effectiveness of CodecLM over the current state-of-the-arts.

https://huggingface.co/papers/2404.05875

[

8 authors](https://huggingface.co/papers/2404.05875)

·

Apr 8, 2024

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2507.14423

On the Effect of Token Merging on Pre-trained Models for Code

https://huggingface.co/papers/2507.14423

Tokenization is a fundamental component of language models for code. It involves breaking down the input into units that are later passed to the language model stack to learn high-dimensional representations used in various contexts, from classification to generation. However, the output of these tokenizers is often longer than that traditionally used in compilers and interpreters. This could result in undesirable effects, such as increased computational overhead. In this work, we investigate the effect of merging the hidden representations of subtokens that belong to the same semantic unit, such as subtokens that form a single identifier. We propose two strategies: one based on averaging the representations and another that leverages a learning-based approach. Both methods can be seamlessly integrated with existing language models for code. We conduct experiments using six language models for code: CodeBERT, GraphCodeBERT, UniXCoder, CdoeT5, CodeT5+ (220M), and CodeT5+ (770M), across three software engineering tasks: vulnerability detection, code classification, and code translation. Results show that these strategies can reduce the number of floating-point operations by 1% to 19%. Regarding downstream performance, the most significant degradation was observed in the vulnerability detection task, where the F1 score decreased by 1.82 points compared to the baseline. In contrast, for code translation, we observed an improvement of 2.47 points in CodeBLEU. This work contributes to the broader effort of improving language models for code across multiple dimensions, including both computational efficiency and downstream performance.

https://huggingface.co/papers/2507.14423

[

4 authors](https://huggingface.co/papers/2507.14423)

·

Jul 18, 2025

 [-] 8

https://huggingface.co/login?next=%2Fpapers%2F2510.20535

ARC-Encoder: learning compressed text representations for large language models

https://huggingface.co/papers/2510.20535

Recent techniques such as retrieval-augmented generation or chain-of-thought reasoning have led to longer contexts and increased inference costs. Context compression techniques can reduce these costs, but the most effective approaches require fine-tuning the target model or even modifying its architecture. This can degrade its general abilities when not used for this specific purpose. Here we explore an alternative approach: an encoder that compresses the context into continuous representations which replace token embeddings in decoder LLMs. First, we perform a systematic study of training strategies and architecture choices for the encoder. Our findings led to the design of an Adaptable text Representations Compressor, named ARC-Encoder, which outputs x-times fewer continuous representations (typically x!in!{4,8}) than text tokens. We evaluate ARC-Encoder across a variety of LLM usage scenarios, ranging from in-context learning to context window extension, on both instruct and base decoders. Results show that ARC-Encoder achieves state-of-the-art performance on several benchmarks while improving computational efficiency at inference. Finally, we demonstrate that our models can be adapted to multiple decoders simultaneously, allowing a single encoder to generalize across different decoder LLMs. This makes ARC-Encoder a flexible and efficient solution for portable encoders that work seamlessly with multiple LLMs. We release a training code at https://github.com/kyutai-labs/ARC-Encoder , fine-tuning dataset and pretrained models are available at https://huggingface.co/collections/kyutai/arc-encoders-68ee18787301407d60a57047 .

https://huggingface.co/papers/2510.20535

 

https://huggingface.co/papers/2510.20535

 Kyutai

https://huggingface.co/kyutai

·

Oct 23, 2025 

1

https://huggingface.co/papers/2510.20535#community

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2301.01701

Extending Source Code Pre-Trained Language Models to Summarise Decompiled Binaries

https://huggingface.co/papers/2301.01701

Reverse engineering binaries is required to understand and analyse programs for which the source code is unavailable. Decompilers can transform the largely unreadable binaries into a more readable source code-like representation. However, reverse engineering is time-consuming, much of which is taken up by labelling the functions with semantic information. While the automated summarisation of decompiled code can help Reverse Engineers understand and analyse binaries, current work mainly focuses on summarising source code, and no suitable dataset exists for this task. In this work, we extend large pre-trained language models of source code to summarise decompiled binary functions. Furthermore, we investigate the impact of input and data properties on the performance of such models. Our approach consists of two main components; the data and the model. We first build CAPYBARA, a dataset of 214K decompiled function-documentation pairs across various compiler optimisations. We extend CAPYBARA further by generating synthetic datasets and deduplicating the data. Next, we fine-tune the CodeT5 base model with CAPYBARA to create BinT5. BinT5 achieves the state-of-the-art BLEU-4 score of 60.83, 58.82, and 44.21 for summarising source, decompiled, and synthetically stripped decompiled code, respectively. This indicates that these models can be extended to decompiled binaries successfully. Finally, we found that the performance of BinT5 is not heavily dependent on the dataset size and compiler optimisation level. We recommend future research to further investigate transferring knowledge when working with less expressive input formats such as stripped binaries.

https://huggingface.co/papers/2301.01701

[

6 authors](https://huggingface.co/papers/2301.01701)

·

Jan 4, 2023

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2402.08073

Grounding Data Science Code Generation with Input-Output Specifications

https://huggingface.co/papers/2402.08073

Large language models (LLMs) have recently demonstrated a remarkable ability to generate code from natural language (NL) prompts. However, in the real world, NL is often too ambiguous to capture the true intent behind programming problems, requiring additional input-output (I/O) specifications. Unfortunately, LLMs can have difficulty aligning their outputs with both the NL prompt and the I/O specification. In this paper, we give a way to mitigate this issue in the context of data science programming, where tasks require explicit I/O specifications for clarity. Specifically, we propose GIFT4Code, a novel approach for the instruction fine-tuning of LLMs with respect to I/O specifications. Our method leverages synthetic data produced by the LLM itself and utilizes execution-derived feedback as a key learning signal. This feedback, in the form of program I/O specifications, is provided to the LLM to facilitate instruction fine-tuning. We evaluated our approach on two challenging data science benchmarks, Arcade and DS-1000. The results demonstrate a significant improvement in the LLM's ability to generate code that is not only executable but also accurately aligned with user specifications, substantially improving the quality of code generation for complex data science tasks.

https://huggingface.co/papers/2402.08073

[

6 authors](https://huggingface.co/papers/2402.08073)

·

Feb 12, 2024

 [-] 4

https://huggingface.co/login?next=%2Fpapers%2F2310.11248

CrossCodeEval: A Diverse and Multilingual Benchmark for Cross-File Code Completion

https://huggingface.co/papers/2310.11248

Code completion models have made significant progress in recent years, yet current popular evaluation datasets, such as HumanEval and MBPP, predominantly focus on code completion tasks within a single file. This over-simplified setting falls short of representing the real-world software development scenario where repositories span multiple files with numerous cross-file dependencies, and accessing and understanding cross-file context is often required to complete the code correctly. To fill in this gap, we propose CrossCodeEval, a diverse and multilingual code completion benchmark that necessitates an in-depth cross-file contextual understanding to complete the code accurately. CrossCodeEval is built on a diverse set of real-world, open-sourced, permissively-licensed repositories in four popular programming languages: Python, Java, TypeScript, and C#. To create examples that strictly require cross-file context for accurate completion, we propose a straightforward yet efficient static-analysis-based approach to pinpoint the use of cross-file context within the current file. Extensive experiments on state-of-the-art code language models like CodeGen and StarCoder demonstrate that CrossCodeEval is extremely challenging when the relevant cross-file context is absent, and we see clear improvements when adding these context into the prompt. However, despite such improvements, the pinnacle of performance remains notably unattained even with the highest-performing model, indicating that CrossCodeEval is also capable of assessing model's capability in leveraging extensive context to make better code completion. Finally, we benchmarked various methods in retrieving cross-file context, and show that CrossCodeEval can also be used to measure the capability of code retrievers.

https://huggingface.co/papers/2310.11248

[

11 authors](https://huggingface.co/papers/2310.11248)

·

Oct 17, 2023 

1

https://huggingface.co/papers/2310.11248#community

 [-] 2

https://huggingface.co/login?next=%2Fpapers%2F2402.01035

Getting the most out of your tokenizer for pre-training and domain adaptation

https://huggingface.co/papers/2402.01035

Tokenization is an understudied and often neglected component of modern LLMs. Most published works use a single tokenizer for all experiments, often borrowed from another model, without performing ablations or analysis to optimize tokenization. Moreover, the tokenizer is generally kept unchanged when fine-tuning a base model. In this paper, we show that the size, pre-tokenization regular expression, and training data of a tokenizer can significantly impact the model's generation speed, effective context size, memory usage, and downstream performance. We train specialized Byte-Pair Encoding code tokenizers, and conduct extensive ablations on the impact of tokenizer design on the performance of LLMs for code generation tasks such as HumanEval and MBPP, and provide recommendations for tokenizer hyper-parameters selection and switching the tokenizer in a pre-trained LLM. We perform our experiments on models trained from scratch and from pre-trained models, verifying their applicability to a wide range of use-cases. We find that when fine-tuning on more than 50 billion tokens, we can specialize the tokenizer of a pre-trained LLM to obtain large gains in generation speed and effective context size.

https://huggingface.co/papers/2402.01035

[

3 authors](https://huggingface.co/papers/2402.01035)

·

Feb 1, 2024

 [-] 35

https://huggingface.co/login?next=%2Fpapers%2F2409.03810

How Do Your Code LLMs Perform? Empowering Code Instruction Tuning with High-Quality Data

https://huggingface.co/papers/2409.03810

Recently, there has been a growing interest in studying how to construct better code instruction tuning data. However, we observe Code models trained with these datasets exhibit high performance on HumanEval but perform worse on other benchmarks such as LiveCodeBench. Upon further investigation, we find that many datasets suffer from severe data leakage. After cleaning up most of the leaked data, some well-known high-quality datasets perform poorly. This discovery reveals a new challenge: identifying which dataset genuinely qualify as high-quality code instruction data. To address this, we propose an efficient code data pruning strategy for selecting good samples. Our approach is based on three dimensions: instruction complexity, response quality, and instruction diversity. Based on our selected data, we present XCoder, a family of models finetuned from LLaMA3. Our experiments show XCoder achieves new state-of-the-art performance using fewer training data, which verify the effectiveness of our data strategy. Moreover, we perform a comprehensive analysis on the data composition and find existing code datasets have different characteristics according to their construction methods, which provide new insights for future code LLMs. Our models and dataset are released in https://github.com/banksy23/XCoder

https://huggingface.co/papers/2409.03810

[

14 authors](https://huggingface.co/papers/2409.03810)

·

Sep 5, 2024 

6

https://huggingface.co/papers/2409.03810#community

 [-] 48

https://huggingface.co/login?next=%2Fpapers%2F2410.09584

Toward General Instruction-Following Alignment for Retrieval-Augmented Generation

https://huggingface.co/papers/2410.09584

Following natural instructions is crucial for the effective application of Retrieval-Augmented Generation (RAG) systems. Despite recent advancements in Large Language Models (LLMs), research on assessing and improving instruction-following (IF) alignment within the RAG domain remains limited. To address this issue, we propose VIF-RAG, the first automated, scalable, and verifiable synthetic pipeline for instruction-following alignment in RAG systems. We start by manually crafting a minimal set of atomic instructions (<100) and developing combination rules to synthesize and verify complex instructions for a seed set. We then use supervised models for instruction rewriting while simultaneously generating code to automate the verification of instruction quality via a Python executor. Finally, we integrate these instructions with extensive RAG and general data samples, scaling up to a high-quality VIF-RAG-QA dataset (>100k) through automated processes. To further bridge the gap in instruction-following auto-evaluation for RAG systems, we introduce FollowRAG Benchmark, which includes approximately 3K test samples, covering 22 categories of general instruction constraints and four knowledge-intensive QA datasets. Due to its robust pipeline design, FollowRAG can seamlessly integrate with different RAG benchmarks. Using FollowRAG and eight widely-used IF and foundational abilities benchmarks for LLMs, we demonstrate that VIF-RAG markedly enhances LLM performance across a broad range of general instruction constraints while effectively leveraging its capabilities in RAG scenarios. Further analysis offers practical insights for achieving IF alignment in RAG systems. Our code and datasets are released at https://FollowRAG.github.io.

https://huggingface.co/papers/2410.09584

[

6 authors](https://huggingface.co/papers/2410.09584)

·

Oct 12, 2024 

3

https://huggingface.co/papers/2410.09584#community

 [-] 4

https://huggingface.co/login?next=%2Fpapers%2F2311.00233

Distort, Distract, Decode: Instruction-Tuned Model Can Refine its Response from Noisy Instructions

https://huggingface.co/papers/2311.00233

While instruction-tuned language models have demonstrated impressive zero-shot generalization, these models often struggle to generate accurate responses when faced with instructions that fall outside their training set. This paper presents Instructive Decoding (ID), a simple yet effective approach that augments the efficacy of instruction-tuned models. Specifically, ID adjusts the logits for next-token prediction in a contrastive manner, utilizing predictions generated from a manipulated version of the original instruction, referred to as a noisy instruction. This noisy instruction aims to elicit responses that could diverge from the intended instruction yet remain plausible. We conduct experiments across a spectrum of such noisy instructions, ranging from those that insert semantic noise via random words to others like 'opposite' that elicit the deviated responses. Our approach achieves considerable performance gains across various instruction-tuned models and tasks without necessitating any additional parameter updates. Notably, utilizing 'opposite' as the noisy instruction in ID, which exhibits the maximum divergence from the original instruction, consistently produces the most significant performance gains across multiple models and tasks.

https://huggingface.co/papers/2311.00233

[

4 authors](https://huggingface.co/papers/2311.00233)

·

Oct 31, 2023

 [-] 21

https://huggingface.co/login?next=%2Fpapers%2F2407.13739

Scaling Granite Code Models to 128K Context

https://huggingface.co/papers/2407.13739

This paper introduces long-context Granite code models that support effective context windows of up to 128K tokens. Our solution for scaling context length of Granite 3B/8B code models from 2K/4K to 128K consists of a light-weight continual pretraining by gradually increasing its RoPE base frequency with repository-level file packing and length-upsampled long-context data. Additionally, we also release instruction-tuned models with long-context support which are derived by further finetuning the long context base models on a mix of permissively licensed short and long-context instruction-response pairs. While comparing to the original short-context Granite code models, our long-context models achieve significant improvements on long-context tasks without any noticeable performance degradation on regular code completion benchmarks (e.g., HumanEval). We release all our long-context Granite code models under an Apache 2.0 license for both research and commercial use.

https://huggingface.co/papers/2407.13739

[

22 authors](https://huggingface.co/papers/2407.13739)

·

Jul 18, 2024 

3

https://huggingface.co/papers/2407.13739#community

 [-] 1

https://huggingface.co/login?next=%2Fpapers%2F2411.07781

RedCode: Risky Code Execution and Generation Benchmark for Code Agents

https://huggingface.co/papers/2411.07781

With the rapidly increasing capabilities and adoption of code agents for AI-assisted coding, safety concerns, such as generating or executing risky code, have become significant barriers to the real-world deployment of these agents. To provide comprehensive and practical evaluations on the safety of code agents, we propose RedCode, a benchmark for risky code execution and generation: (1) RedCode-Exec provides challenging prompts that could lead to risky code execution, aiming to evaluate code agents' ability to recognize and handle unsafe code. We provide a total of 4,050 risky test cases in Python and Bash tasks with diverse input formats including code snippets and natural text. They covers 25 types of critical vulnerabilities spanning 8 domains (e.g., websites, file systems). We provide Docker environments and design corresponding evaluation metrics to assess their execution results. (2) RedCode-Gen provides 160 prompts with function signatures and docstrings as input to assess whether code agents will follow instructions to generate harmful code or software. Our empirical findings, derived from evaluating three agent frameworks based on 19 LLMs, provide insights into code agents' vulnerabilities. For instance, evaluations on RedCode-Exec show that agents are more likely to reject executing risky operations on the operating system, but are less likely to reject executing technically buggy code, indicating high risks. Risky operations described in natural text lead to a lower rejection rate than those in code format. Additionally, evaluations on RedCode-Gen show that more capable base models and agents with stronger overall coding abilities, such as GPT4, tend to produce more sophisticated and effective harmful software. Our findings highlight the need for stringent safety evaluations for diverse code agents. Our dataset and code are available at https://github.com/AI-secure/RedCode.

https://huggingface.co/papers/2411.07781

[

8 authors](https://huggingface.co/papers/2411.07781)

·

Nov 12, 2024 

1

https://huggingface.co/papers/2411.07781#community

 [-] 6

https://huggingface.co/login?next=%2Fpapers%2F2412.03123

Robust Multi-bit Text Watermark with LLM-based Paraphrasers

https://huggingface.co/papers/2412.03123

We propose an imperceptible multi-bit text watermark embedded by paraphrasing with LLMs. We fine-tune a pair of LLM paraphrasers that are designed to behave differently so that their paraphrasing difference reflected in the text semantics can be identified by a trained decoder. To embed our multi-bit watermark, we use two paraphrasers alternatively to encode the pre-defined binary code at the sentence level. Then we use a text classifier as the decoder to decode each bit of the watermark. Through extensive experiments, we show that our watermarks can achieve over 99.99% detection AUC with small (1.1B) text paraphrasers while keeping the semantic information of the original sentence. More importantly, our pipeline is robust under word substitution and sentence paraphrasing perturbations and generalizes well to out-of-distributional data. We also show the stealthiness of our watermark with LLM-based evaluation. We open-source the code: https://github.com/xiaojunxu/multi-bit-text-watermark.

https://huggingface.co/papers/2412.03123

[

5 authors](https://huggingface.co/papers/2412.03123)

·

Dec 3, 2024 

2

https://huggingface.co/papers/2412.03123#community

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2507.18897

HH-Codec: High Compression High-fidelity Discrete Neural Codec for Spoken Language Modeling

https://huggingface.co/papers/2507.18897

Discrete speech tokenization is a fundamental component in speech codecs. However, in large-scale speech-to-speech systems, the complexity of parallel streams from multiple quantizers and the computational cost of high-time-dimensional codecs pose significant challenges. In this paper, we introduce HH-Codec, a neural codec that achieves extreme compression at 24 tokens per second for 24 kHz audio while relying on single-quantizer inference. Our approach involves a carefully designed Vector Quantization space for Spoken Language Modeling, optimizing compression efficiency while minimizing information loss. Building on this, we propose an asymmetric encoder-decoder architecture (Audio-VQ-Mel-Audio) that leverages dual supervision and progressive training to enhance reconstruction stability and fidelity. HH-Codec achieves state-of-the-art performance in speech reconstruction with an ultra-low bandwidth of 0.3 kbps. We further evaluate its effectiveness in codebook utilization and generative model adaptation, with extensive ablations validating the necessity of each module. HH-Codec is available at https://github.com/opendilab/HH-Codec.

https://huggingface.co/papers/2507.18897

[

6 authors](https://huggingface.co/papers/2507.18897)

·

Jul 24, 2025

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2409.05923

USCD: Improving Code Generation of LLMs by Uncertainty-Aware Selective Contrastive Decoding

https://huggingface.co/papers/2409.05923

Large language models (LLMs) have shown remarkable capabilities in code generation. However, the effects of hallucinations (e.g., output noise) make it particularly challenging for LLMs to generate high-quality code in one pass. In this work, we propose a simple and effective uncertainty-aware selective contrastive decoding (USCD) mechanism to improve the quality of one-pass code generation in LLMs and reduce the impact of output noise. To be specific, we first elaborately designed a negative prompt (namely lame prompt) to output noise by removing input-output examples from the standard few-shot prompt. Our preliminary study shows that the Jensen-Shannon divergence (JS divergence) between token distribution uncertainty and the output noise is relatively low (approximately 0.25), indicating their high relevance. Then, we selectively eliminate output noise induced by lame prompts based on the uncertainty of the prediction distribution from the standard prompt. Notably, our proposed plug-and-play mechanism is an inference-only method, enjoying appealing flexibility. Extensive experiments on widely used benchmarks, e.g., HumanEval, MBPP, and MultiPL-E, upon several LLMs (i.e., Inocder-6b, CodeLlama-7b, WizardCoder-15b, StarCoder, and Llama2-7b), demonstrate that our proposed USCD significantly improves one-pass code generation, with an average pass@1 scores increase of 16.59%. We will release code and data on GitHub.

https://huggingface.co/papers/2409.05923

[

7 authors](https://huggingface.co/papers/2409.05923)

·

Sep 8, 2024

 [-] 1

https://huggingface.co/login?next=%2Fpapers%2F2406.11925

DocCGen: Document-based Controlled Code Generation

https://huggingface.co/papers/2406.11925

Recent developments show that Large Language Models (LLMs) produce state-of-the-art performance on natural language (NL) to code generation for resource-rich general-purpose languages like C++, Java, and Python. However, their practical usage for structured domain-specific languages (DSLs) such as YAML, JSON is limited due to domain-specific schema, grammar, and customizations generally unseen by LLMs during pre-training. Efforts have been made to mitigate this challenge via in-context learning through relevant examples or by fine-tuning. However, it suffers from problems, such as limited DSL samples and prompt sensitivity but enterprises maintain good documentation of the DSLs. Therefore, we propose DocCGen, a framework that can leverage such rich knowledge by breaking the NL-to-Code generation task for structured code languages into a two-step process. First, it detects the correct libraries using the library documentation that best matches the NL query. Then, it utilizes schema rules extracted from the documentation of these libraries to constrain the decoding. We evaluate our framework for two complex structured languages, Ansible YAML and Bash command, consisting of two settings: Out-of-domain (OOD) and In-domain (ID). Our extensive experiments show that DocCGen consistently improves different-sized language models across all six evaluation metrics, reducing syntactic and semantic errors in structured code. We plan to open-source the datasets and code to motivate research in constrained code generation.

https://huggingface.co/papers/2406.11925

[

6 authors](https://huggingface.co/papers/2406.11925)

·

Jun 16, 2024

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2601.00376

In Line with Context: Repository-Level Code Generation via Context Inlining

https://huggingface.co/papers/2601.00376

Repository-level code generation has attracted growing attention in recent years. Unlike function-level code generation, it requires the model to understand the entire repository, reasoning over complex dependencies across functions, classes, and modules. However, existing approaches such as retrieval-augmented generation (RAG) or context-based function selection often fall short: they primarily rely on surface-level similarity and struggle to capture the rich dependencies that govern repository-level semantics. In this paper, we introduce InlineCoder, a novel framework for repository-level code generation. InlineCoder enhances the understanding of repository context by inlining the unfinished function into its call graph, thereby reframing the challenging repository understanding as an easier function-level coding task. Given a function signature, InlineCoder first generates a draft completion, termed an anchor, which approximates downstream dependencies and enables perplexity-based confidence estimation. This anchor drives a bidirectional inlining process: (i) Upstream Inlining, which embeds the anchor into its callers to capture diverse usage scenarios; and (ii) Downstream Retrieval, which integrates the anchor's callees into the prompt to provide precise dependency context. The enriched context, combining draft completion with upstream and downstream perspectives, equips the LLM with a comprehensive repository view.

https://huggingface.co/papers/2601.00376

[

5 authors](https://huggingface.co/papers/2601.00376)

·

Jan 1

 [-] 1

https://huggingface.co/login?next=%2Fpapers%2F2304.05216

Towards Efficient Fine-tuning of Pre-trained Code Models: An Experimental Study and Beyond

https://huggingface.co/papers/2304.05216

Recently, fine-tuning pre-trained code models such as CodeBERT on downstream tasks has achieved great success in many software testing and analysis tasks. While effective and prevalent, fine-tuning the pre-trained parameters incurs a large computational cost. In this paper, we conduct an extensive experimental study to explore what happens to layer-wise pre-trained representations and their encoded code knowledge during fine-tuning. We then propose efficient alternatives to fine-tune the large pre-trained code model based on the above findings. Our experimental study shows that (1) lexical, syntactic and structural properties of source code are encoded in the lower, intermediate, and higher layers, respectively, while the semantic property spans across the entire model. (2) The process of fine-tuning preserves most of the code properties. Specifically, the basic code properties captured by lower and intermediate layers are still preserved during fine-tuning. Furthermore, we find that only the representations of the top two layers change most during fine-tuning for various downstream tasks. (3) Based on the above findings, we propose Telly to efficiently fine-tune pre-trained code models via layer freezing. The extensive experimental results on five various downstream tasks demonstrate that training parameters and the corresponding time cost are greatly reduced, while performances are similar or better. Replication package including source code, datasets, and online Appendix is available at: https://github.com/DeepSoftwareAnalytics/Telly.

https://huggingface.co/papers/2304.05216

[

7 authors](https://huggingface.co/papers/2304.05216)

·

Apr 11, 2023

 [-] 3

https://huggingface.co/login?next=%2Fpapers%2F2005.08025

IntelliCode Compose: Code Generation Using Transformer

https://huggingface.co/papers/2005.08025

In software development through integrated development environments (IDEs), code completion is one of the most widely used features. Nevertheless, majority of integrated development environments only support completion of methods and APIs, or arguments. In this paper, we introduce IntelliCode Compose - a general-purpose multilingual code completion tool which is capable of predicting sequences of code tokens of arbitrary types, generating up to entire lines of syntactically correct code. It leverages state-of-the-art generative transformer model trained on 1.2 billion lines of source code in Python, C#, JavaScript and TypeScript programming languages. IntelliCode Compose is deployed as a cloud-based web service. It makes use of client-side tree-based caching, efficient parallel implementation of the beam search decoder, and compute graph optimizations to meet edit-time completion suggestion requirements in the Visual Studio Code IDE and Azure Notebook. Our best model yields an average edit similarity of 86.7% and a perplexity of 1.82 for Python programming language.

https://huggingface.co/papers/2005.08025

[

4 authors](https://huggingface.co/papers/2005.08025)

·

May 16, 2020

 [-] 81

https://huggingface.co/login?next=%2Fpapers%2F2309.00071

YaRN: Efficient Context Window Extension of Large Language Models

https://huggingface.co/papers/2309.00071

Rotary Position Embeddings (RoPE) have been shown to effectively encode positional information in transformer-based language models. However, these models fail to generalize past the sequence length they were trained on. We present YaRN (Yet another RoPE extensioN method), a compute-efficient method to extend the context window of such models, requiring 10x less tokens and 2.5x less training steps than previous methods. Using YaRN, we show that LLaMA models can effectively utilize and extrapolate to context lengths much longer than their original pre-training would allow, while also surpassing previous the state-of-the-art at context window extension. In addition, we demonstrate that YaRN exhibits the capability to extrapolate beyond the limited context of a fine-tuning dataset. We publish the checkpoints of Llama 2 7B/13B fine-tuned using YaRN with 64k and 128k context windows at https://github.com/jquesnelle/yarn

https://huggingface.co/papers/2309.00071

 

https://huggingface.co/papers/2309.00071

 NousResearch

https://huggingface.co/NousResearch

·

Aug 31, 2023 

4

https://huggingface.co/papers/2309.00071#community

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2601.20185

Improving X-Codec-2.0 for Multi-Lingual Speech: 25 Hz Latent Rate and 24 kHz Sampling

https://huggingface.co/papers/2601.20185

X-Codec-2.0 has shown strong performance in neural audio compression and multilingual speech modeling, operating at a 50 Hz latent rate and a 16 kHz sampling rate using frozen HuBERT features. While effective, this configuration limits temporal efficiency and audio fidelity. In this work, we explore a simple and effective modification by introducing additional pooling and increasing the decoder hop size. This reduces the latent rate from 50 Hz to 25 Hz and simultaneously raises the output sampling rate from 16 kHz to 24 kHz, improving efficiency and perceptual quality without altering the core architecture. Evaluated on the multilingual Common Voice 17 test set, the proposed configuration achieves a 0.29 MOS improvement over the original X-Codec-2.0 baseline based on UTMOSv2, and attains the best reported performance among all codecs operating at 25 Hz. The source code, checkpoints, and generation comparisons are released at https://huggingface.co/Scicom-intl/xcodec2-25TPS-24k{https://huggingface.co/Scicom-intl/xcodec2-25TPS-24k}.

https://huggingface.co/papers/2601.20185

[

1 authors](https://huggingface.co/papers/2601.20185)

·

Jan 27

 [-] 12

https://huggingface.co/login?next=%2Fpapers%2F2308.16824

Can Programming Languages Boost Each Other via Instruction Tuning?

https://huggingface.co/papers/2308.16824

When human programmers have mastered a programming language, it would be easier when they learn a new programming language. In this report, we focus on exploring whether programming languages can boost each other during the instruction fine-tuning phase of code large language models. We conduct extensive experiments of 8 popular programming languages (Python, JavaScript, TypeScript, C, C++, Java, Go, HTML) on StarCoder. Results demonstrate that programming languages can significantly improve each other. For example, CodeM-Python 15B trained on Python is able to increase Java by an absolute 17.95% pass@1 on HumanEval-X. More surprisingly, we found that CodeM-HTML 7B trained on the HTML corpus can improve Java by an absolute 15.24% pass@1. Our training data is released at https://github.com/NL2Code/CodeM.

https://huggingface.co/papers/2308.16824

[

11 authors](https://huggingface.co/papers/2308.16824)

·

Aug 31, 2023

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2508.02473

An Efficient and Adaptive Next Edit Suggestion Framework with Zero Human Instructions in IDEs

https://huggingface.co/papers/2508.02473

Code editing, including modifying, refactoring, and maintaining existing code, is the most frequent task in software development and has garnered significant attention from AI-powered tools. However, existing solutions that translate explicit natural language instructions into code edits face critical limitations, such as heavy reliance on human instruction input and high latency, which hinder their effective integration into a developer's workflow. We observe that developers' habitual behaviors and coding objectives are often reflected in their historical editing patterns, making this data key to addressing existing limitations. To leverage these insights, we propose NES (Next Edit Suggestion), an LLM-driven code editing framework that delivers an instruction-free and low-latency experience. Built on a dual-model architecture and trained with our high-quality SFT and DAPO datasets, NES enhances productivity by understanding developer intent while optimizing inference to minimize latency. NES is a scalable, industry-ready solution with a continuous Tab key interaction workflow, seamlessly adopted by a FinTech company with over 20,000 developers. Evaluations on real-world datasets show NES achieves 75.6% and 81.6% accuracy in two tasks of predicting next edit locations, alongside 91.36% ES and 27.7% EMR for intent-aligned edits, outperforming SOTA models. Our open-sourced SFT and DAPO datasets have been demonstrated to enhance the performance of open-source CodeLLMs. The demonstration of NES is available at https://youtu.be/yGoyYOe6fbY.

https://huggingface.co/papers/2508.02473

[

9 authors](https://huggingface.co/papers/2508.02473)

·

Aug 4, 2025

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2305.20019

Monotonic Location Attention for Length Generalization

https://huggingface.co/papers/2305.20019

We explore different ways to utilize position-based cross-attention in seq2seq networks to enable length generalization in algorithmic tasks. We show that a simple approach of interpolating the original and reversed encoded representations combined with relative attention allows near-perfect length generalization for both forward and reverse lookup tasks or copy tasks that had been generally hard to tackle. We also devise harder diagnostic tasks where the relative distance of the ideal attention position varies with timestep. In such settings, the simple interpolation trick with relative attention is not sufficient. We introduce novel variants of location attention building on top of Dubois et al. (2020) to address the new diagnostic tasks. We also show the benefits of our approaches for length generalization in SCAN (Lake & Baroni, 2018) and CFQ (Keysers et al., 2020). Our code is available on GitHub.

https://huggingface.co/papers/2305.20019

[

2 authors](https://huggingface.co/papers/2305.20019)

·

May 31, 2023

 [-] 21

https://huggingface.co/login?next=%2Fpapers%2F2307.12560

Interpolating between Images with Diffusion Models

https://huggingface.co/papers/2307.12560

One little-explored frontier of image generation and editing is the task of interpolating between two input images, a feature missing from all currently deployed image generation pipelines. We argue that such a feature can expand the creative applications of such models, and propose a method for zero-shot interpolation using latent diffusion models. We apply interpolation in the latent space at a sequence of decreasing noise levels, then perform denoising conditioned on interpolated text embeddings derived from textual inversion and (optionally) subject poses. For greater consistency, or to specify additional criteria, we can generate several candidates and use CLIP to select the highest quality image. We obtain convincing interpolations across diverse subject poses, image styles, and image content, and show that standard quantitative metrics such as FID are insufficient to measure the quality of an interpolation. Code and data are available at https://clintonjwang.github.io/interpolation.

https://huggingface.co/papers/2307.12560

[

2 authors](https://huggingface.co/papers/2307.12560)

·

Jul 23, 2023

 [-] 6

https://huggingface.co/login?next=%2Fpapers%2F2305.07922

CodeT5+: Open Code Large Language Models for Code Understanding and Generation

https://huggingface.co/papers/2305.07922

Large language models (LLMs) pretrained on vast source code have achieved prominent progress in code intelligence. However, existing code LLMs have two main limitations in terms of architecture and pretraining tasks. First, they often adopt a specific architecture (encoder-only or decoder-only) or rely on a unified encoder-decoder network for different downstream tasks. The former paradigm is limited by inflexibility in applications while in the latter, the model is treated as a single system for all tasks, leading to suboptimal performance on a subset of tasks. Secondly, they often employ a limited set of pretraining objectives which might not be relevant to some downstream tasks and hence result in substantial performance degrade. To address these limitations, we propose ``CodeT5+'', a family of encoder-decoder LLMs for code in which component modules can be flexibly combined to suit a wide range of downstream code tasks. Such flexibility is enabled by our proposed mixture of pretraining objectives to mitigate the pretrain-finetune discrepancy. These objectives cover span denoising, contrastive learning, text-code matching, and causal LM pretraining tasks, on both unimodal and bimodal multilingual code corpora. Furthermore, we propose to initialize CodeT5+ with frozen off-the-shelf LLMs without training from scratch to efficiently scale up our models, and explore instruction-tuning to align with natural language instructions. We extensively evaluate CodeT5+ on over 20 code-related benchmarks in different settings, including zero-shot, finetuning, and instruction-tuning. We observe state-of-the-art (SoTA) model performance on various code-related tasks, such as code generation and completion, math programming, and text-to-code retrieval tasks. Particularly, our instruction-tuned CodeT5+ 16B achieves new SoTA results on HumanEval code generation task against other open code LLMs.

https://huggingface.co/papers/2305.07922

[

6 authors](https://huggingface.co/papers/2305.07922)

·

May 13, 2023 

2

https://huggingface.co/papers/2305.07922#community

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2012.14768

Understanding and Improving Encoder Layer Fusion in Sequence-to-Sequence Learning

https://huggingface.co/papers/2012.14768

Encoder layer fusion (EncoderFusion) is a technique to fuse all the encoder layers (instead of the uppermost layer) for sequence-to-sequence (Seq2Seq) models, which has proven effective on various NLP tasks. However, it is still not entirely clear why and when EncoderFusion should work. In this paper, our main contribution is to take a step further in understanding EncoderFusion. Many of previous studies believe that the success of EncoderFusion comes from exploiting surface and syntactic information embedded in lower encoder layers. Unlike them, we find that the encoder embedding layer is more important than other intermediate encoder layers. In addition, the uppermost decoder layer consistently pays more attention to the encoder embedding layer across NLP tasks. Based on this observation, we propose a simple fusion method, SurfaceFusion, by fusing only the encoder embedding layer for the softmax layer. Experimental results show that SurfaceFusion outperforms EncoderFusion on several NLP benchmarks, including machine translation, text summarization, and grammatical error correction. It obtains the state-of-the-art performance on WMT16 Romanian-English and WMT14 English-French translation tasks. Extensive analyses reveal that SurfaceFusion learns more expressive bilingual word embeddings by building a closer relationship between relevant source and target embedding. Source code is freely available at https://github.com/SunbowLiu/SurfaceFusion.

https://huggingface.co/papers/2012.14768

[

6 authors](https://huggingface.co/papers/2012.14768)

·

Dec 29, 2020

 [-] 1

https://huggingface.co/login?next=%2Fpapers%2F2309.13320

GlotScript: A Resource and Tool for Low Resource Writing System Identification

https://huggingface.co/papers/2309.13320

We present GlotScript, an open resource and tool for low resource writing system identification. GlotScript-R is a resource that provides the attested writing systems for more than 7,000 languages. It is compiled by aggregating information from existing writing system resources. GlotScript-T is a writing system identification tool that covers all 161 Unicode 15.0 scripts. For an input text, it returns its script distribution where scripts are identified by ISO 15924 codes. We also present two use cases for GlotScript. First, we demonstrate that GlotScript supports cleaning multilingual corpora such as mC4 and OSCAR. Second, we analyze the tokenization of a number of language models such as GPT-4 using GlotScript and provide insights on the coverage of low resource scripts and languages by each language model. We hope that GlotScript will become a useful resource for work on low resource languages in the NLP community. GlotScript-R and GlotScript-T are available at https://github.com/cisnlp/GlotScript.

https://huggingface.co/papers/2309.13320

 

https://huggingface.co/papers/2309.13320

 CIS, LMU Munich

https://huggingface.co/cis-lmu

·

Sep 22, 2023

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2403.02484

Encodings for Prediction-based Neural Architecture Search

https://huggingface.co/papers/2403.02484

Predictor-based methods have substantially enhanced Neural Architecture Search (NAS) optimization. The efficacy of these predictors is largely influenced by the method of encoding neural network architectures. While traditional encodings used an adjacency matrix describing the graph structure of a neural network, novel encodings embrace a variety of approaches from unsupervised pretraining of latent representations to vectors of zero-cost proxies. In this paper, we categorize and investigate neural encodings from three main types: structural, learned, and score-based. Furthermore, we extend these encodings and introduce unified encodings, that extend NAS predictors to multiple search spaces. Our analysis draws from experiments conducted on over 1.5 million neural network architectures on NAS spaces such as NASBench-101 (NB101), NB201, NB301, Network Design Spaces (NDS), and TransNASBench-101. Building on our study, we present our predictor FLAN: Flow Attention for NAS. FLAN integrates critical insights on predictor design, transfer learning, and unified encodings to enable more than an order of magnitude cost reduction for training NAS accuracy predictors. Our implementation and encodings for all neural networks are open-sourced at https://github.com/abdelfattah-lab/flan_nas{https://github.com/abdelfattah-lab/flan_nas}.

https://huggingface.co/papers/2403.02484

[

2 authors](https://huggingface.co/papers/2403.02484)

·

Mar 4, 2024

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2502.06854

Can Large Language Models Understand Intermediate Representations in Compilers?

https://huggingface.co/papers/2502.06854

Intermediate Representations (IRs) play a critical role in compiler design and program analysis, yet their comprehension by Large Language Models (LLMs) remains underexplored. In this paper, we present an explorative empirical study evaluating the capabilities of six state-of-the-art LLMs: GPT-4, GPT-3, DeepSeek, Gemma 2, Llama 3, and Code Llama, in understanding IRs. Specifically, we assess model performance across four core tasks: control flow graph reconstruction, decompilation, code summarization, and execution reasoning. While LLMs exhibit competence in parsing IR syntax and identifying high-level structures, they consistently struggle with instruction-level reasoning, especially in control flow reasoning, loop handling, and dynamic execution. Common failure modes include misinterpreting branching instructions, omitting critical operations, and relying on heuristic reasoning rather than precise instruction-level logic. Our findings highlight the need for IR-specific enhancements in LLM design. We recommend fine-tuning on structured IR datasets and integrating control-flow-sensitive architectures to improve model effectiveness. All experimental data and source code are publicly available at

https://huggingface.co/papers/2502.06854

[

7 authors](https://huggingface.co/papers/2502.06854)

·

Feb 7, 2025

 [-] 24

https://huggingface.co/login?next=%2Fpapers%2F2307.08701

AlpaGasus: Training A Better Alpaca with Fewer Data

https://huggingface.co/papers/2307.08701

Large language models~(LLMs) obtain instruction-following capability through instruction-finetuning (IFT) on supervised instruction/response data. However, widely used IFT datasets (e.g., Alpaca's 52k data) surprisingly contain many low-quality instances with incorrect or irrelevant responses, which are misleading and detrimental to IFT. In this paper, we propose a simple and effective data selection strategy that automatically identifies and removes low-quality data using a strong LLM (e.g., ChatGPT). To this end, we introduce AlpaGasus, which is finetuned on only 9k high-quality data filtered from the 52k Alpaca data. AlpaGasus significantly outperforms the original Alpaca as evaluated by GPT-4 on multiple test sets and its 13B variant matches >90% performance of its teacher LLM (i.e., Text-Davinci-003) on test tasks. It also provides 5.7x faster training, reducing the training time for a 7B variant from 80 minutes (for Alpaca) to 14 minutes We apply IFT for the same number of epochs as Alpaca(7B) but on fewer data, using 4timesNVIDIA A100 (80GB) GPUs and following the original Alpaca setting and hyperparameters.. Overall, AlpaGasus demonstrates a novel data-centric IFT paradigm that can be generally applied to instruction-tuning data, leading to faster training and better instruction-following models. Our project page is available at: https://lichang-chen.github.io/AlpaGasus/.

https://huggingface.co/papers/2307.08701

[

11 authors](https://huggingface.co/papers/2307.08701)

·

Jul 17, 2023

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2410.02185

POSIX: A Prompt Sensitivity Index For Large Language Models

https://huggingface.co/papers/2410.02185

Despite their remarkable capabilities, Large Language Models (LLMs) are found to be surprisingly sensitive to minor variations in prompts, often generating significantly divergent outputs in response to minor variations in the prompts, such as spelling errors, alteration of wording or the prompt template. However, while assessing the quality of an LLM, the focus often tends to be solely on its performance on downstream tasks, while very little to no attention is paid to prompt sensitivity. To fill this gap, we propose POSIX - a novel PrOmpt Sensitivity IndeX as a reliable measure of prompt sensitivity, thereby offering a more comprehensive evaluation of LLM performance. The key idea behind POSIX is to capture the relative change in loglikelihood of a given response upon replacing the corresponding prompt with a different intent-preserving prompt. We provide thorough empirical evidence demonstrating the efficacy of POSIX in capturing prompt sensitivity and subsequently use it to measure and thereby compare prompt sensitivity of various open-source LLMs. We find that merely increasing the parameter count or instruction tuning does not necessarily reduce prompt sensitivity whereas adding some few-shot exemplars, even just one, almost always leads to significant decrease in prompt sensitivity. We also find that alterations to prompt template lead to the highest sensitivity in the case of MCQ type tasks, whereas paraphrasing results in the highest sensitivity in open-ended generation tasks. The code for reproducing our results is open-sourced at https://github.com/kowndinya-renduchintala/POSIX.

https://huggingface.co/papers/2410.02185

[

4 authors](https://huggingface.co/papers/2410.02185)

·

Oct 2, 2024

 [-] 35

https://huggingface.co/login?next=%2Fpapers%2F2510.14972

TokDrift: When LLM Speaks in Subwords but Code Speaks in Grammar

https://huggingface.co/papers/2510.14972

Large language models (LLMs) for code rely on subword tokenizers, such as byte-pair encoding (BPE), learned from mixed natural language text and programming language code but driven by statistics rather than grammar. As a result, semantically identical code snippets can be tokenized differently depending on superficial factors such as whitespace or identifier naming. To measure the impact of this misalignment, we introduce TokDrift, a framework that applies semantic-preserving rewrite rules to create code variants differing only in tokenization. Across nine code LLMs, including large ones with over 30B parameters, even minor formatting changes can cause substantial shifts in model behavior. Layer-wise analysis shows that the issue originates in early embeddings, where subword segmentation fails to capture grammar token boundaries. Our findings identify misaligned tokenization as a hidden obstacle to reliable code understanding and generation, highlighting the need for grammar-aware tokenization for future code LLMs.

https://huggingface.co/papers/2510.14972

 

https://huggingface.co/papers/2510.14972

 University of Waterloo

https://huggingface.co/UWaterloo

·

Oct 16, 2025 

2

https://huggingface.co/papers/2510.14972#community

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2510.16987

Back to Bytes: Revisiting Tokenization Through UTF-8

https://huggingface.co/papers/2510.16987

We present UTF8Tokenizer, a minimalist byte-level tokenizer that maps text exactly to IDs corresponding to the bytes underlying the text's UTF-8 encoding (e.g., byte x09 is token ID 9). Unlike prior byte-level approaches (Xue et al., 2021; Pagnoni et al., 2025), our implementation never introduces out-of-range IDs (i.e. there is no token ID 256) or auxiliary tokens: all special behavior (e.g., padding, boundaries, conversation structure, attention segments, tool calling, "thinking" spans, etc.) is encoded using C0 control bytes - just as ASCII was originally designed to embed control information alongside printable text. These design principles yield practical benefits: (1) faster tokenization (14x) and significantly lower host-device transfer (8x less than int64); (2) simple, shareable 256*d embedding tables that can be aligned across models; and (3) a training-time enhancement via bit-biased embeddings, which exposes per-byte bit structure and can be added to the embedding table post-training, removing inference costs. Our HuggingFace-compatible implementation improves language modeling convergence.

https://huggingface.co/papers/2510.16987

[

4 authors](https://huggingface.co/papers/2510.16987)

·

Oct 19, 2025

 [-] 2

https://huggingface.co/login?next=%2Fpapers%2F2310.20329

InstructCoder: Empowering Language Models for Code Editing

https://huggingface.co/papers/2310.20329

Code editing encompasses a variety of pragmatic tasks that developers deal with daily. Despite its relevance and practical usefulness, automatic code editing remains an underexplored area in the evolution of deep learning models, partly due to data scarcity. In this work, we explore the use of large language models (LLMs) to edit code based on user instructions, covering a broad range of implicit tasks such as comment insertion, code optimization, and code refactoring. To facilitate this, we introduce InstructCoder, the first dataset designed to adapt LLMs for general-purpose code editing, containing highdiversity code-editing tasks. It consists of over 114,000 instruction-input-output triplets and covers multiple distinct code editing scenarios. The dataset is systematically expanded through an iterative process that commences with code editing data sourced from GitHub commits as seed tasks. Seed and generated tasks are used subsequently to prompt ChatGPT for more task data. Our experiments demonstrate that open-source LLMs fine-tuned on InstructCoder can edit code correctly based on users' instructions most of the time, exhibiting unprecedented code-editing performance levels. Such results suggest that proficient instruction-finetuning can lead to significant amelioration in code editing abilities. The dataset and the source code are available at https://github.com/qishenghu/CodeInstruct.

https://huggingface.co/papers/2310.20329

[

8 authors](https://huggingface.co/papers/2310.20329)

·

Oct 30, 2023 

2

https://huggingface.co/papers/2310.20329#community

 [-] 1

https://huggingface.co/login?next=%2Fpapers%2F2305.17660

Plug-and-Play Document Modules for Pre-trained Models

https://huggingface.co/papers/2305.17660

Large-scale pre-trained models (PTMs) have been widely used in document-oriented NLP tasks, such as question answering. However, the encoding-task coupling requirement results in the repeated encoding of the same documents for different tasks and queries, which is highly computationally inefficient. To this end, we target to decouple document encoding from downstream tasks, and propose to represent each document as a plug-and-play document module, i.e., a document plugin, for PTMs (PlugD). By inserting document plugins into the backbone PTM for downstream tasks, we can encode a document one time to handle multiple tasks, which is more efficient than conventional encoding-task coupling methods that simultaneously encode documents and input queries using task-specific encoders. Extensive experiments on 8 datasets of 4 typical NLP tasks show that PlugD enables models to encode documents once and for all across different scenarios. Especially, PlugD can save 69% computational costs while achieving comparable performance to state-of-the-art encoding-task coupling methods. Additionally, we show that PlugD can serve as an effective post-processing way to inject knowledge into task-specific models, improving model performance without any additional model training.

https://huggingface.co/papers/2305.17660

[

10 authors](https://huggingface.co/papers/2305.17660)

·

May 27, 2023

 [-] 1

https://huggingface.co/login?next=%2Fpapers%2F2602.07120

Anchored Decoding: Provably Reducing Copyright Risk for Any Language Model

https://huggingface.co/papers/2602.07120

Modern language models (LMs) tend to memorize portions of their training data and emit verbatim spans. When the underlying sources are sensitive or copyright-protected, such reproduction raises issues of consent and compensation for creators and compliance risks for developers. We propose Anchored Decoding, a plug-and-play inference-time method for suppressing verbatim copying: it enables decoding from any risky LM trained on mixed-license data by keeping generation in bounded proximity to a permissively trained safe LM. Anchored Decoding adaptively allocates a user-chosen information budget over the generation trajectory and enforces per-step constraints that yield a sequence-level guarantee, enabling a tunable risk-utility trade-off. To make Anchored Decoding practically useful, we introduce a new permissively trained safe model (TinyComma 1.8B), as well as Anchored_{Byte} Decoding, a byte-level variant of our method that enables cross-vocabulary fusion via the ByteSampler framework (Hayase et al., 2025). We evaluate our methods across six model pairs on long-form evaluations of copyright risk and utility. Anchored and Anchored_{Byte} Decoding define a new Pareto frontier, preserving near-original fluency and factuality while eliminating up to 75% of the measurable copying gap (averaged over six copying metrics) between the risky baseline and a safe reference, at a modest inference overhead.

https://huggingface.co/papers/2602.07120

 

https://huggingface.co/papers/2602.07120

 University of Washington NLP

https://huggingface.co/uwnlp

·

Feb 6 

2

https://huggingface.co/papers/2602.07120#community

 [-] 1

https://huggingface.co/login?next=%2Fpapers%2F2412.05967

Language hooks: a modular framework for augmenting LLM reasoning that decouples tool usage from the model and its prompt

https://huggingface.co/papers/2412.05967

Prompting and fine-tuning have emerged as two competing paradigms for augmenting language models with new capabilities, such as the use of tools. Prompting approaches are quick to set up but rely on providing explicit demonstrations of each tool's usage in the model's prompt, thus coupling tool use to the task at hand and limiting generalisation. Fine-tuning removes the need for task-specific demonstrations of tool usage at runtime; however, this ties new capabilities to a single model, thus making already-heavier setup costs a recurring expense. In this paper, we introduce language hooks, a novel framework for augmenting language models with new capabilities that is decoupled both from the model's task-specific prompt and from the model itself. The language hook algorithm interleaves text generation by the base model with the execution of modular programs that trigger conditionally based on the existing text and the available capabilities. Upon triggering, programs may call external tools, auxiliary language models (e.g. using tool specific prompts), and modify the existing context. We benchmark our method against state-of-the-art baselines, find that it outperforms task-aware approaches, and demonstrate its ability to generalise to novel tasks.

https://huggingface.co/papers/2412.05967

[

5 authors](https://huggingface.co/papers/2412.05967)

·

Dec 8, 2024

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2410.18077

ALTA: Compiler-Based Analysis of Transformers

https://huggingface.co/papers/2410.18077

We propose a new programming language called ALTA and a compiler that can map ALTA programs to Transformer weights. ALTA is inspired by RASP, a language proposed by Weiss et al. (2021), and Tracr (Lindner et al., 2023), a compiler from RASP programs to Transformer weights. ALTA complements and extends this prior work, offering the ability to express loops and to compile programs to Universal Transformers, among other advantages. ALTA allows us to constructively show how Transformers can represent length-invariant algorithms for computing parity and addition, as well as a solution to the SCAN benchmark of compositional generalization tasks, without requiring intermediate scratchpad decoding steps. We also propose tools to analyze cases where the expressibility of an algorithm is established, but end-to-end training on a given training set fails to induce behavior consistent with the desired algorithm. To this end, we explore training from ALTA execution traces as a more fine-grained supervision signal. This enables additional experiments and theoretical analyses relating the learnability of various algorithms to data availability and modeling decisions, such as positional encodings. We make the ALTA framework -- language specification, symbolic interpreter, and weight compiler -- available to the community to enable further applications and insights.

https://huggingface.co/papers/2410.18077

[

6 authors](https://huggingface.co/papers/2410.18077)

·

Oct 23, 2024

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2310.11163

IMTLab: An Open-Source Platform for Building, Evaluating, and Diagnosing Interactive Machine Translation Systems

https://huggingface.co/papers/2310.11163

We present IMTLab, an open-source end-to-end interactive machine translation (IMT) system platform that enables researchers to quickly build IMT systems with state-of-the-art models, perform an end-to-end evaluation, and diagnose the weakness of systems. IMTLab treats the whole interactive translation process as a task-oriented dialogue with a human-in-the-loop setting, in which human interventions can be explicitly incorporated to produce high-quality, error-free translations. To this end, a general communication interface is designed to support the flexible IMT architectures and user policies. Based on the proposed design, we construct a simulated and real interactive environment to achieve end-to-end evaluation and leverage the framework to systematically evaluate previous IMT systems. Our simulated and manual experiments show that the prefix-constrained decoding approach still gains the lowest editing cost in the end-to-end evaluation, while BiTIIMT achieves comparable editing cost with a better interactive experience.

https://huggingface.co/papers/2310.11163

[

9 authors](https://huggingface.co/papers/2310.11163)

·

Oct 17, 2023

 [-] 2

https://huggingface.co/login?next=%2Fpapers%2F2406.07138

Never Miss A Beat: An Efficient Recipe for Context Window Extension of Large Language Models with Consistent "Middle" Enhancement

https://huggingface.co/papers/2406.07138

Recently, many methods have been developed to extend the context length of pre-trained large language models (LLMs), but they often require fine-tuning at the target length (gg4K) and struggle to effectively utilize information from the middle part of the context. To address these issues, we propose Continuity-Relativity indExing with gAussian Middle (CREAM), which interpolates positional encodings by manipulating position indices. Apart from being simple, CREAM is training-efficient: it only requires fine-tuning at the pre-trained context window (eg, Llama 2-4K) and can extend LLMs to a much longer target context length (eg, 256K). To ensure that the model focuses more on the information in the middle, we introduce a truncated Gaussian to encourage sampling from the middle part of the context during fine-tuning, thus alleviating the Lost-in-the-Middle'' problem faced by long-context LLMs. Experimental results show that CREAM successfully extends LLMs to the target length for both Base and Chat versions of Llama2-7B with Never Miss A Beat''. Our code will be publicly available soon.

https://huggingface.co/papers/2406.07138

[

3 authors](https://huggingface.co/papers/2406.07138)

·

Jun 10, 2024 

1

https://huggingface.co/papers/2406.07138#community

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2505.05063

CodeMixBench: Evaluating Large Language Models on Code Generation with Code-Mixed Prompts

https://huggingface.co/papers/2505.05063

Large Language Models (LLMs) have achieved remarkable success in code generation tasks, powering various applications like code completion, debugging, and programming assistance. However, existing benchmarks such as HumanEval, MBPP, and BigCodeBench primarily evaluate LLMs on English-only prompts, overlooking the real-world scenario where multilingual developers often use code-mixed language while interacting with LLMs. To address this gap, we introduce CodeMixBench, a novel benchmark designed to evaluate the robustness of LLMs on code generation from code-mixed prompts. Built upon BigCodeBench, CodeMixBench introduces controlled code-mixing (CMD) into the natural language parts of prompts across three language pairs: Hinglish (Hindi-English), Spanish-English, and Chinese Pinyin-English. We comprehensively evaluate a diverse set of open-source code generation models ranging from 1.5B to 15B parameters. Our results show that code-mixed prompts consistently degrade Pass@1 performance compared to their English-only counterparts, with performance drops increasing under higher CMD levels for smaller models. CodeMixBench provides a realistic evaluation framework for studying multilingual code generation and highlights new challenges and directions for building robust code generation models that generalize well across diverse linguistic settings.

https://huggingface.co/papers/2505.05063

[

2 authors](https://huggingface.co/papers/2505.05063)

·

May 7, 2025

 [-] 7

https://huggingface.co/login?next=%2Fpapers%2F2510.13697

On Pretraining for Project-Level Code Completion

https://huggingface.co/papers/2510.13697

Repository-level pretraining is commonly used to enable large language models for code to leverage codebase-wide context. This enhances their ability to generate accurate and context-aware code completions. In this work, we investigate how different repository-processing strategies affect in-context learning in OpenCoder, a 1.5B-parameter model. We extend its context window from 4,096 to 16,384 tokens by training on additional 1B tokens of curated repository-level data. Despite relying on a smaller dataset than competing models (which often use hundreds of billions of tokens), our model achieves comparable performance on the Long Code Arena benchmark. We find that various repository-processing techniques yield similarly strong results, with the primary gain coming from adapting to a new rotary positional embedding (RoPE) scaling parameter. Finally, we show that a simpler file-level training approach at the original sequence length remains highly effective, opening up repository-level code completion research to settings with more constrained data and compute resources.

https://huggingface.co/papers/2510.13697

 

https://huggingface.co/papers/2510.13697

 JetBrains Research

https://huggingface.co/JetBrains-Research

·

Oct 15, 2025 

2

https://huggingface.co/papers/2510.13697#community

 [-] 2

https://huggingface.co/login?next=%2Fpapers%2F2509.18420

Instruction-Following Evaluation in Function Calling for Large Language Models

https://huggingface.co/papers/2509.18420

Function calling is a core capability of large language models, essential for AI agents. Existing benchmarks such as the Berkeley Function Calling Leaderboard (BFCL), tau^2-Bench (arXiv:2506.07982), and ACEBench (arXiv:2501.12851) evaluate argument correctness but do not test adherence to format instructions embedded in parameter descriptions, such as enclosing values in double quotes or using ISO date formats. We introduce IFEval-FC, a benchmark inspired by IFEval (arXiv:2311.07911) that assesses precise instruction following in function calling. IFEval-FC encodes verifiable formats directly within JSON schema descriptions, for example specifying that a value must not contain punctuation. It includes 750 test cases, each consisting of a function with an embedded format for one of its input parameters and a corresponding user query. Evaluation is fully algorithmic, ensuring objectivity, reproducibility, and scalability. Our results show that even state-of-the-art proprietary models, including GPT-5 and Claude 4.1 Opus, frequently fail to follow basic formatting rules, highlighting a practical limitation for real-world agent systems. The complete codebase and data are publicly available at https://github.com/Skripkon/IFEval-FC.

https://huggingface.co/papers/2509.18420

[

1 authors](https://huggingface.co/papers/2509.18420)

·

Sep 22, 2025 

3

https://huggingface.co/papers/2509.18420#community

 [-] 2

https://huggingface.co/login?next=%2Fpapers%2F2306.15006

DNABERT-2: Efficient Foundation Model and Benchmark For Multi-Species Genome

https://huggingface.co/papers/2306.15006

Decoding the linguistic intricacies of the genome is a crucial problem in biology, and pre-trained foundational models such as DNABERT and Nucleotide Transformer have made significant strides in this area. Existing works have largely hinged on k-mer, fixed-length permutations of A, T, C, and G, as the token of the genome language due to its simplicity. However, we argue that the computation and sample inefficiencies introduced by k-mer tokenization are primary obstacles in developing large genome foundational models. We provide conceptual and empirical insights into genome tokenization, building on which we propose to replace k-mer tokenization with Byte Pair Encoding (BPE), a statistics-based data compression algorithm that constructs tokens by iteratively merging the most frequent co-occurring genome segment in the corpus. We demonstrate that BPE not only overcomes the limitations of k-mer tokenization but also benefits from the computational efficiency of non-overlapping tokenization. Based on these insights, we introduce DNABERT-2, a refined genome foundation model that adapts an efficient tokenizer and employs multiple strategies to overcome input length constraints, reduce time and memory expenditure, and enhance model capability. Furthermore, we identify the absence of a comprehensive and standardized benchmark for genome understanding as another significant impediment to fair comparative analysis. In response, we propose the Genome Understanding Evaluation (GUE), a comprehensive multi-species genome classification dataset that amalgamates 28 distinct datasets across 7 tasks, with input lengths ranging from 70 to 1000. Through comprehensive experiments on the GUE benchmark, we demonstrate that DNABERT-2 achieves comparable performance to the state-of-the-art model with 21 times fewer parameters and approximately 56 times less GPU time in pre-training.

https://huggingface.co/papers/2306.15006

[

6 authors](https://huggingface.co/papers/2306.15006)

·

Jun 26, 2023

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2402.09497

Instruction Tuning for Secure Code Generation

https://huggingface.co/papers/2402.09497

Modern language models (LMs) have gained widespread acceptance in everyday and professional contexts, particularly in programming. An essential procedure enabling this adoption is instruction tuning, which substantially enhances LMs' practical utility by training them to follow user instructions and human preferences. However, existing instruction tuning schemes overlook a crucial aspect: the security of generated code. As a result, even the state-of-the-art instruction-tuned LMs frequently produce unsafe code, posing significant security risks. In this work, we introduce SafeCoder to address this gap. SafeCoder performs security-centric fine-tuning using a diverse and high-quality dataset that we collected using an automated pipeline. We integrate the security fine-tuning with standard instruction tuning, to facilitate a joint optimization of both security and utility. Despite its simplicity, we show that SafeCoder is effective across a variety of popular LMs and datasets. It is able to drastically improve security (by about 30%), while preserving utility.

https://huggingface.co/papers/2402.09497

[

4 authors](https://huggingface.co/papers/2402.09497)

·

Feb 14, 2024

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2212.10773

MultiInstruct: Improving Multi-Modal Zero-Shot Learning via Instruction Tuning

https://huggingface.co/papers/2212.10773

Instruction tuning, a new learning paradigm that fine-tunes pre-trained language models on tasks specified through instructions, has shown promising zero-shot performance on various natural language processing tasks. However, it has yet to be explored for vision and multimodal tasks. In this work, we introduce MUL-TIINSTRUCT, the first multimodal instruction tuning benchmark dataset that consists of 62 diverse multimodal tasks in a unified seq-to-seq format covering 10 broad categories. The tasks are derived from 21 existing open-source datasets and each task is equipped with 5 expert-written instructions. We take OFA as the base pre-trained model for multimodal instruction tuning, and to further improve its zero-shot performance, we explore multiple transfer learning strategies to leverage the large-scale NATURAL INSTRUCTIONS dataset. Experimental results demonstrate strong zero-shot performance on various unseen multimodal tasks and the benefit of transfer learning from a text-only instruction dataset. We also design a new evaluation metric - Sensitivity, to evaluate how sensitive the model is to the variety of instructions. Our results indicate that fine-tuning the model on a diverse set of tasks and instructions leads to a reduced sensitivity to variations in instructions for each task.

https://huggingface.co/papers/2212.10773

[

3 authors](https://huggingface.co/papers/2212.10773)

·

Dec 20, 2022

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2311.17972

Self-Infilling Code Generation

https://huggingface.co/papers/2311.17972

This work introduces a general code generation framework that incorporates infilling operations into auto-regressive decoding. Our approach capitalizes on the observation that recent code language models with infilling capabilities can perform self-infilling: whereas infilling operations aim to fill in the middle based on a predefined prefix and suffix, self-infilling sequentially generates both such surrounding context and the infilled content. We utilize this feature to develop an infilling-augmented decoding process that facilitates non-monotonic generation. This approach allows for postponing the generation of uncertain code snippets until a definitive suffix is established, leading to improved control over the generation sequence. In addition, it facilitates a looping mechanism, which can iteratively update and synchronize each piece of generation in a cyclic manner. Extensive experiments are conducted to demonstrate that our proposed decoding process is effective in enhancing regularity and quality across several code generation benchmarks.

https://huggingface.co/papers/2311.17972

[

5 authors](https://huggingface.co/papers/2311.17972)

·

Nov 29, 2023

 [-] 2

https://huggingface.co/login?next=%2Fpapers%2F2312.15692

Instruction Fusion: Advancing Prompt Evolution through Hybridization

https://huggingface.co/papers/2312.15692

The fine-tuning of Large Language Models (LLMs) specialized in code generation has seen notable advancements through the use of open-domain coding queries. Despite the successes, existing methodologies like Evol-Instruct encounter performance limitations, impeding further enhancements in code generation tasks. This paper examines the constraints of existing prompt evolution techniques and introduces a novel approach, Instruction Fusion (IF). IF innovatively combines two distinct prompts through a hybridization process, thereby enhancing the evolution of training prompts for code LLMs. Our experimental results reveal that the proposed novel method effectively addresses the shortcomings of prior methods, significantly improving the performance of Code LLMs across five code generation benchmarks, namely HumanEval, HumanEval+, MBPP, MBPP+ and MultiPL-E, which underscore the effectiveness of Instruction Fusion in advancing the capabilities of LLMs in code generation.

https://huggingface.co/papers/2312.15692

[

7 authors](https://huggingface.co/papers/2312.15692)

·

Dec 24, 2023

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2403.19121

Code Comparison Tuning for Code Large Language Models

https://huggingface.co/papers/2403.19121

We present Code Comparison Tuning (CCT), a simple and effective tuning method for code large language models (Code LLMs) to better handle subtle code errors. Specifically, we integrate the concept of comparison into instruction tuning, both at the token and sequence levels, enabling the model to discern even the slightest deviations in code. To compare the original code with an erroneous version containing manually added code errors, we use token-level preference loss for detailed token-level comparisons. Additionally, we combine code segments to create a new instruction tuning sample for sequence-level comparisons, enhancing the model's bug-fixing capability. Experimental results on the HumanEvalFix benchmark show that CCT surpasses instruction tuning in pass@1 scores by up to 4 points across diverse code LLMs, and extensive analysis demonstrates the effectiveness of our method.

https://huggingface.co/papers/2403.19121

[

4 authors](https://huggingface.co/papers/2403.19121)

·

Mar 27, 2024

 [-] 9

https://huggingface.co/login?next=%2Fpapers%2F2306.17194

On the Exploitability of Instruction Tuning

https://huggingface.co/papers/2306.17194

Instruction tuning is an effective technique to align large language models (LLMs) with human intents. In this work, we investigate how an adversary can exploit instruction tuning by injecting specific instruction-following examples into the training data that intentionally changes the model's behavior. For example, an adversary can achieve content injection by injecting training examples that mention target content and eliciting such behavior from downstream models. To achieve this goal, we propose AutoPoison, an automated data poisoning pipeline. It naturally and coherently incorporates versatile attack goals into poisoned data with the help of an oracle LLM. We showcase two example attacks: content injection and over-refusal attacks, each aiming to induce a specific exploitable behavior. We quantify and benchmark the strength and the stealthiness of our data poisoning scheme. Our results show that AutoPoison allows an adversary to change a model's behavior by poisoning only a small fraction of data while maintaining a high level of stealthiness in the poisoned examples. We hope our work sheds light on how data quality affects the behavior of instruction-tuned models and raises awareness of the importance of data quality for responsible deployments of LLMs. Code is available at https://github.com/azshue/AutoPoison.

https://huggingface.co/papers/2306.17194

[

6 authors](https://huggingface.co/papers/2306.17194)

·

Jun 28, 2023

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2312.05356

Neuron Patching: Semantic-based Neuron-level Language Model Repair for Code Generation

https://huggingface.co/papers/2312.05356

Language Models (LMs) have become widely used in software engineering, especially for tasks such as code generation, where they are referred to as code LMs. These models have proven effective in generating code, making it easier for developers to automate coding activities. However, research has highlighted a significant limitation: despite their effectiveness, LMs often produce code that is incorrect, buggy, or not fully functional. Updating these models with limited data can be prohibitively challenging, yet it is essential to maximize their utility. This may require hot-fix techniques (updating models with limited data) to resolve. In this paper, we propose Model Improvement via Neuron Targeting (MINT), a novel approach for repairing code LMs. MINT leverages the semantic property of language models to perform neuron-level repairs in a novel way. Further, by analyzing the relationships between the model's latent representations, the incorrect outputs, and the desired outputs, MINT determines which neurons are worth updating. This approach ensures that only the neurons crucial to the model's failure are targeted, avoiding unnecessary changes and allowing for a more efficient and precise repair process. MINT is effective, efficient, and reliable, capable of correcting a neural model by patching a minimum number of neurons (usually one or two neurons). Our approach is evaluated on three coding tasks: line-level code generation, shellcode generation, and intent-to-bash translation. The experimental results demonstrate that the proposed approach significantly outperforms the state-of-the-art in both effectiveness and efficiency measures. In addition, we analyze and discuss the side effects of model repair techniques, including the balance between generalization and specificity, and the performance after multiple repairs in succession.

https://huggingface.co/papers/2312.05356

[

4 authors](https://huggingface.co/papers/2312.05356)

·

Dec 8, 2023

 [-] 74

https://huggingface.co/login?next=%2Fpapers%2F2502.13063

Cramming 1568 Tokens into a Single Vector and Back Again: Exploring the Limits of Embedding Space Capacity

https://huggingface.co/papers/2502.13063

A range of recent works addresses the problem of compression of sequence of tokens into a shorter sequence of real-valued vectors to be used as inputs instead of token embeddings or key-value cache. These approaches allow to reduce the amount of compute in existing language models. Despite relying on powerful models as encoders, the maximum attainable lossless compression ratio is typically not higher than x10. This fact is highly intriguing because, in theory, the maximum information capacity of large real-valued vectors is far beyond the presented rates even for 16-bit precision and a modest vector size. In this work, we explore the limits of compression by replacing the encoder with a per-sample optimization procedure. We show that vectors with compression ratios up to x1500 exist, which highlights two orders of magnitude gap between existing and practically attainable solutions. Furthermore, we empirically show that the compression limits are determined not by the length of the input but by the amount of uncertainty to be reduced, namely, the cross-entropy loss on this sequence without any conditioning. The obtained limits highlight the substantial gap between the theoretical capacity of input embeddings and their practical utilization, suggesting significant room for optimization in model design.

https://huggingface.co/papers/2502.13063

[

4 authors](https://huggingface.co/papers/2502.13063)

·

Feb 18, 2025 

4

https://huggingface.co/papers/2502.13063#community

 [-] 1

https://huggingface.co/login?next=%2Fpapers%2F2303.11525

Sparse Iso-FLOP Transformations for Maximizing Training Efficiency

https://huggingface.co/papers/2303.11525

Recent works have explored the use of weight sparsity to improve the training efficiency (test accuracy w.r.t training FLOPs) of deep neural networks (DNNs). These works aim to reduce training FLOPs but training with sparse weights often leads to accuracy loss or requires longer training schedules, making the resulting training efficiency less clear. In contrast, we focus on using sparsity to increase accuracy while using the same FLOPs as the dense model and show training efficiency gains through higher accuracy. In this work, we introduce Sparse-IFT, a family of Sparse Iso-FLOP Transformations which are used as drop-in replacements for dense layers to improve their representational capacity and FLOP efficiency. Each transformation is parameterized by a single hyperparameter (sparsity level) and provides a larger search space to find optimal sparse masks. Without changing any training hyperparameters, replacing dense layers with Sparse-IFT leads to significant improvements across computer vision (CV) and natural language processing (NLP) tasks, including ResNet-18 on ImageNet (+3.5%) and GPT-3 Small on WikiText-103 (-0.4 PPL), both matching larger dense model variants that use 2x or more FLOPs. To our knowledge, this is the first work to demonstrate the use of sparsity for improving the accuracy of dense models via a simple-to-use set of sparse transformations. Code is available at: https://github.com/CerebrasResearch/Sparse-IFT.

https://huggingface.co/papers/2303.11525

[

4 authors](https://huggingface.co/papers/2303.11525)

·

Mar 20, 2023

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2502.14005

Smaller But Better: Unifying Layout Generation with Smaller Large Language Models

https://huggingface.co/papers/2502.14005

We propose LGGPT, an LLM-based model tailored for unified layout generation. First, we propose Arbitrary Layout Instruction (ALI) and Universal Layout Response (ULR) as the uniform I/O template. ALI accommodates arbitrary layout generation task inputs across multiple layout domains, enabling LGGPT to unify both task-generic and domain-generic layout generation hitherto unexplored. Collectively, ALI and ULR boast a succinct structure that forgoes superfluous tokens typically found in existing HTML-based formats, facilitating efficient instruction tuning and boosting unified generation performance. In addition, we propose an Interval Quantization Encoding (IQE) strategy that compresses ALI into a more condensed structure. IQE precisely preserves valid layout clues while eliminating the less informative placeholders, facilitating LGGPT to capture complex and variable layout generation conditions during the unified training process. Experimental results demonstrate that LGGPT achieves superior or on par performance compared to existing methods. Notably, LGGPT strikes a prominent balance between proficiency and efficiency with a compact 1.5B parameter LLM, which beats prior 7B or 175B models even in the most extensive and challenging unified scenario. Furthermore, we underscore the necessity of employing LLMs for unified layout generation and suggest that 1.5B could be an optimal parameter size by comparing LLMs of varying scales. Code is available at https://github.com/NiceRingNode/LGGPT.

https://huggingface.co/papers/2502.14005

[

5 authors](https://huggingface.co/papers/2502.14005)

·

Feb 18, 2025

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2406.11097

InstructCMP: Length Control in Sentence Compression through Instruction-based Large Language Models

https://huggingface.co/papers/2406.11097

Extractive summarization can produce faithful summaries but often requires additional constraints such as a desired summary length. Traditional sentence compression models do not typically consider the constraints because of their restricted model abilities, which require model modifications for coping with them. To bridge this gap, we propose Instruction-based Compression (InstructCMP), an approach to the sentence compression task that can consider the length constraint through instructions by leveraging the zero-shot task-solving abilities of Large Language Models (LLMs). For this purpose, we created new evaluation datasets by transforming traditional sentence compression datasets into an instruction format. By using the datasets, we first reveal that the current LLMs still face challenges in accurately controlling the length for a compressed text. To address this issue, we propose an approach named "length priming," that incorporates additional length information into the instructions without external resources. While the length priming effectively works in a zero-shot setting, a training dataset with the instructions would further improve the ability of length control. Thus, we additionally created a training dataset in an instruction format to fine-tune the model on it. Experimental results and analysis show that applying the length priming significantly improves performances of InstructCMP in both zero-shot and fine-tuning settings without the need of any model modifications.

https://huggingface.co/papers/2406.11097

[

4 authors](https://huggingface.co/papers/2406.11097)

·

Jun 16, 2024

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2310.01732

Nugget: Neural Agglomerative Embeddings of Text

https://huggingface.co/papers/2310.01732

Embedding text sequences is a widespread requirement in modern language understanding. Existing approaches focus largely on constant-size representations. This is problematic, as the amount of information contained in text often varies with the length of the input. We propose a solution called Nugget, which encodes language into a representation based on a dynamically selected subset of input tokens. These nuggets are learned through tasks like autoencoding and machine translation, and intuitively segment language into meaningful units. We demonstrate Nugget outperforms related approaches in tasks involving semantic comparison. Finally, we illustrate these compact units allow for expanding the contextual window of a language model (LM), suggesting new future LMs that can condition on significantly larger amounts of content.

https://huggingface.co/papers/2310.01732

[

2 authors](https://huggingface.co/papers/2310.01732)

·

Oct 2, 2023

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2508.17892

ILRe: Intermediate Layer Retrieval for Context Compression in Causal Language Models

https://huggingface.co/papers/2508.17892

Large Language Models (LLMs) have demonstrated success across many benchmarks. However, they still exhibit limitations in long-context scenarios, primarily due to their short effective context length, quadratic computational complexity, and high memory overhead when processing lengthy inputs. To mitigate these issues, we introduce a novel context compression pipeline, called Intermediate Layer Retrieval (ILRe), which determines one intermediate decoder layer offline, encodes context by streaming chunked prefill only up to that layer, and recalls tokens by the attention scores between the input query and full key cache in that specified layer. In particular, we propose a multi-pooling kernels allocating strategy in the token recalling process to maintain the completeness of semantics. Our approach not only reduces the prefilling complexity from O(L^2) to O(L), but also achieves performance comparable to or better than the full context in the long context scenarios. Without additional post training or operator development, ILRe can process a single 1M tokens request in less than half a minute (speedup approx 180times) and scores RULER-1M benchmark of approx 79.8 with model Llama-3.1-UltraLong-8B-1M-Instruct on a Huawei Ascend 910B NPU.

https://huggingface.co/papers/2508.17892

[

7 authors](https://huggingface.co/papers/2508.17892)

·

Aug 24, 2025

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2507.10095

FIX-CLIP: Dual-Branch Hierarchical Contrastive Learning via Synthetic Captions for Better Understanding of Long Text

https://huggingface.co/papers/2507.10095

CLIP has shown promising performance across many short-text tasks in a zero-shot manner. However, limited by the input length of the text encoder, CLIP struggles on under-stream tasks with long-text inputs (>77 tokens). To remedy this issue, we propose FIX-CLIP, which includes three novel modules: (1) A dual-branch training pipeline that aligns short and long texts with masked and raw images, respectively, which boosts the long-text representation while preserving the short-text ability. (2) Multiple learnable regional prompts with unidirectional masks in Transformer layers for regional information extraction. (3) A hierarchical feature alignment module in the intermediate encoder layers to promote the consistency of multi-scale features. Furthermore, we collect 30M images and utilize existing MLLMs to synthesize long-text captions for training. Extensive experiments show that FIX-CLIP achieves state-of-the-art performance on both long-text and short-text retrieval benchmarks. For downstream applications, we reveal that FIX-CLIP's text encoder delivers promising performance in a plug-and-play manner for diffusion models with long-text input. The code is available at https://github.com/bcwang-sjtu/Fix-CLIP.

https://huggingface.co/papers/2507.10095

[

8 authors](https://huggingface.co/papers/2507.10095)

·

Jul 13, 2025

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2502.11460

UnitCoder: Scalable Iterative Code Synthesis with Unit Test Guidance

https://huggingface.co/papers/2502.11460

Large Language Models (LLMs) have demonstrated remarkable capabilities in various tasks, yet code generation remains a major challenge. Current approaches for obtaining high-quality code data primarily focus on (i) collecting large-scale pre-training data and (ii) synthesizing instruction data through prompt engineering with powerful models. While pre-training data faces quality consistency issues, instruction-based synthesis suffers from limited instruction diversity and inherent biases of LLMs. To address this gap, we introduce UnitCoder, a systematic pipeline leveraging model-generated unit tests to both guide and validate the code generation process. Combined with large-scale package-based retrieval from pre-training corpus, we generate a dataset of 500K+ verifiable programs containing diverse API calls. Evaluations on multiple Python benchmarks (BigCodeBench, HumanEval, MBPP) demonstrate that models fine-tuned on our synthetic data exhibit consistent performance improvements. Notably, Llama3.1-8B and InternLM2.5-7B improve from 31% and 28% to 40% and 39% success rates on BigCodeBench, respectively. Our work presents a scalable approach that leverages model-generated unit tests to guide the synthesis of high-quality code data from pre-training corpora, demonstrating the potential for producing diverse and high-quality post-training data at scale. All code and data will be released (https://github.com).

https://huggingface.co/papers/2502.11460

[

8 authors](https://huggingface.co/papers/2502.11460)

·

Feb 16, 2025

 [-] 13

https://huggingface.co/login?next=%2Fpapers%2F2410.02749

Training Language Models on Synthetic Edit Sequences Improves Code Synthesis

https://huggingface.co/papers/2410.02749

Software engineers mainly write code by editing existing programs. In contrast, large language models (LLMs) autoregressively synthesize programs in a single pass. One explanation for this is the scarcity of open-sourced edit data. While high-quality instruction data for code synthesis is already scarce, high-quality edit data is even scarcer. To fill this gap, we develop a synthetic data generation algorithm called LintSeq. This algorithm refactors existing code into a sequence of code edits by using a linter to procedurally sample across the error-free insertions that can be used to sequentially write programs. It outputs edit sequences as text strings consisting of consecutive program diffs. To test LintSeq, we use it to refactor a dataset of instruction + program pairs into instruction + program-diff-sequence tuples. Then, we instruction finetune a series of smaller LLMs ranging from 2.6B to 14B parameters on both the re-factored and original versions of this dataset, comparing zero-shot performance on code synthesis benchmarks. We show that during repeated sampling, edit sequence finetuned models produce more diverse programs than baselines. This results in better inference-time scaling for benchmark coverage as a function of samples, i.e. the fraction of problems "pass@k" solved by any attempt given "k" tries. For example, on HumanEval pass@50, small LLMs finetuned on synthetic edit sequences are competitive with GPT-4 and outperform models finetuned on the baseline dataset by +20% (+/-3%) in absolute score. Finally, we also pretrain our own tiny LMs for code understanding. We show that finetuning tiny models on synthetic code edits results in state-of-the-art code synthesis for the on-device model class. Our 150M parameter edit sequence LM matches or outperforms code models with twice as many parameters, both with and without repeated sampling, including Codex and AlphaCode.

https://huggingface.co/papers/2410.02749

[

3 authors](https://huggingface.co/papers/2410.02749)

·

Oct 3, 2024 

3

https://huggingface.co/papers/2410.02749#community

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2511.22277

TreeCoder: Systematic Exploration and Optimisation of Decoding and Constraints for LLM Code Generation

https://huggingface.co/papers/2511.22277

Large language models (LLMs) have shown remarkable ability to generate code, yet their outputs often violate syntactic or semantic constraints when guided only through natural language prompts. We introduce TreeCoder, the most general and flexible framework to date for exploring decoding strategies, constraints, and hyperparameters in LLMs, and use it in code generation to enforce correctness and structure during decoding rather than relying on prompt engineering. TreeCoder represents decoding as a tree search over candidate programs, where both decoding strategies and constraint functions - such as style, syntax, execution - are treated as first-class, optimisable components. This design enables systematic exploration and automatic tuning of decoding configurations using standard optimisation techniques. Experiments on the MBPP (Python) and SQL-Spider benchmarks show that TreeCoder consistently improves accuracy across open-source models such as CodeLlama, Mistral and DeepSeek, often outperforming their unconstrained baselines by considerable margins.

https://huggingface.co/papers/2511.22277

[

3 authors](https://huggingface.co/papers/2511.22277)

·

Nov 26, 2025

 [-] -

https://huggingface.co/login?next=%2Fpapers%2F2509.05218

HoPE: Hyperbolic Rotary Positional Encoding for Stable Long-Range Dependency Modeling in Large Language Models

https://huggingface.co/papers/2509.05218

Positional encoding mechanisms enable Transformers to model sequential structure and long-range dependencies in text. While absolute positional encodings struggle with extrapolation to longer sequences due to fixed positional representations, and relative approaches like Alibi exhibit performance degradation on extremely long contexts, the widely-used Rotary Positional Encoding (RoPE) introduces oscillatory attention patterns that hinder stable long-distance dependency modelling. We address these limitations through a geometric reformulation of positional encoding. Drawing inspiration from Lorentz transformations in hyperbolic geometry, we propose Hyperbolic Rotary Positional Encoding (HoPE), which leverages hyperbolic functions to implement Lorentz rotations on token representations. Theoretical analysis demonstrates that RoPE is a special case of our generalized formulation. HoPE fundamentally resolves RoPE's slation issues by enforcing monotonic decay of attention weights with increasing token distances. Extensive experimental results, including perplexity evaluations under several extended sequence benchmarks, show that HoPE consistently exceeds existing positional encoding methods. These findings underscore HoPE's enhanced capacity for representing and generalizing long-range dependencies. Data and code will be available.

https://huggingface.co/papers/2509.05218

[

4 authors](https://huggingface.co/papers/2509.05218)

·

Sep 5, 2025

 [-] 5

https://huggingface.co/login?next=%2Fpapers%2F2510.22907

Language Server CLI Empowers Language Agents with Process Rewards

https://huggingface.co/papers/2510.22907

Large language models routinely hallucinate APIs and mislocalize edits, while language servers compute verified, IDE-grade facts about real code. We present Lanser-CLI, a CLI-first orchestration layer that pins and mediates a Language Server Protocol (LSP) server for coding agents and CI, exposing deterministic, replayable workflows. Our position is that language servers provide not only structural information (definitions, references, types, diagnostics) but also an actionable process reward: machine-checked, step-wise signals that align an agent's planning loop with program reality. In this work, Lanser-CLI contributes: (i) a robust addressing scheme beyond brittle "file:line:col" via a Selector DSL (symbolic, AST-path, and content-anchored selectors) with a principled relocation algorithm; (ii) deterministic Analysis Bundles that normalize Language Server responses and capture environment/capability metadata with stable content hashes; (iii) a safety envelope for mutating operations (rename, code actions) with preview, workspace jails, and Git-aware, transactional apply; and (iv) a process-reward functional derived from Language Server facts (diagnostic deltas, disambiguation confidence, and safe-apply checks) that is computable online and replayable offline. We formalize determinism under frozen snapshots and establish a monotonicity property for the process reward, making it suitable for process supervision and counterfactual analysis. Project Page: https://github.com/yifanzhang-pro/lanser-cli

https://huggingface.co/papers/2510.22907

[

2 authors](https://huggingface.co/papers/2510.22907)

·

Oct 26, 2025 

1

https://huggingface.co/papers/2510.22907#community

Previous

https://huggingface.co/papers/date/2026-03-24

System theme

Company

TOS

https://huggingface.co/terms-of-service

 

Privacy

https://huggingface.co/privacy

 

About

https://huggingface.co/huggingface

 

Careers

https://apply.workable.com/huggingface/

 

https://huggingface.co/

Website

Models

https://huggingface.co/models

 

Datasets

https://huggingface.co/datasets

 

Spaces

https://huggingface.co/spaces

 

Pricing

https://huggingface.co/pricing

 

Docs

https://huggingface.co/docs

Trending Papers ranked by GitHub stars activity

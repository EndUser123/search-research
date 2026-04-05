import { Component, For } from 'solid-js';
import { VideoSourceIcon, BrainCircuit, ReviewReportsIcon } from './Icons';

export const AnalysisWorkflowStepper: Component<{
    currentStage: number;
    setStage: (stage: number) => void;
    isStageEnabled: (stage: number) => boolean;
}> = (props) => {
    const stages = [
        { id: 1, name: 'Source', icon: VideoSourceIcon },
        { id: 2, name: 'Analyze', icon: BrainCircuit },
        { id: 3, name: 'Review', icon: ReviewReportsIcon },
    ];

    return (
        <div class="max-w-5xl mx-auto py-4">
            <div class="flex justify-center items-start gap-2" role="navigation" aria-label="Analysis Workflow">
                <For each={stages}>
                    {(stage) => {
                        const isActive = () => props.currentStage === stage.id;
                        const isEnabled = () => props.isStageEnabled(stage.id);

                        return (
                            <button
                                onClick={() => isEnabled() && props.setStage(stage.id)}
                                disabled={!isEnabled()}
                                class="flex flex-col items-center justify-center w-24 gap-2 disabled:cursor-not-allowed group"
                                aria-current={isActive() ? 'step' : false}
                            >
                                <div class={`flex items-center justify-center w-[90px] h-[56px] rounded-full transition-colors duration-300
                                    ${isActive() ? 'bg-accent-primary' : ''}
                                    ${isEnabled() && !isActive() ? 'bg-background-tertiary group-hover:bg-background-interactive-hover' : ''}
                                    ${!isEnabled() ? 'bg-background-disabled' : ''}
                                `}>
                                    <stage.icon class={`w-6 h-6 transition-colors ${isActive() ? 'text-text-on-accent' : isEnabled() ? 'text-text-secondary group-hover:text-text-primary' : 'text-text-tertiary'}`} />
                                </div>
                                <span class={`text-sm font-medium transition-colors
                                    ${isActive() ? 'text-accent-primary-light' : ''}
                                    ${isEnabled() && !isActive() ? 'text-text-secondary group-hover:text-text-primary' : ''}
                                    ${!isEnabled() ? 'text-text-tertiary' : ''}
                                `}>{stage.name}</span>
                            </button>
                        );
                    }}
                </For>
            </div>
        </div>
    );
};

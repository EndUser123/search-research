/**
 * Qwen Wrapper - Node.js wrapper for @qwen-code/qwen-code-core
 *
 * This module provides a simple interface to the Qwen code core package.
 * It wraps the `runHeadless` function from @qwen-code/qwen-code-core with
 * additional error handling and validation.
 *
 * @module qwen_wrapper
 */

import { runHeadless } from '@qwen-code/qwen-code-core';

/**
 * Custom error class for Qwen wrapper related errors.
 *
 * @class QwenWrapperError
 * @extends Error
 */
export class QwenWrapperError extends Error {
    /**
     * Creates an instance of QwenWrapperError.
     *
     * @param {string} message - The error message.
     * @param {Error} [cause] - The original error that caused this error.
     */
    constructor(message, cause) {
        super(message);
        this.name = 'QwenWrapperError';
        this.cause = cause;
    }
}

/**
 * Validates that the required parameters are provided and of correct type.
 *
 * @private
 * @param {string} prompt - The prompt to validate.
 * @param {string} model - The model to validate.
 * @throws {QwenWrapperError} If validation fails.
 */
function _validateParameters(prompt, model) {
    if (typeof prompt !== 'string') {
        throw new QwenWrapperError(
            `Prompt must be a string, received: ${typeof prompt}`,
            { parameter: 'prompt', receivedType: typeof prompt }
        );
    }

    if (prompt.trim().length === 0) {
        throw new QwenWrapperError(
            'Prompt cannot be empty or whitespace only',
            { parameter: 'prompt' }
        );
    }

    if (typeof model !== 'string') {
        throw new QwenWrapperError(
            `Model must be a string, received: ${typeof model}`,
            { parameter: 'model', receivedType: typeof model }
        );
    }

    if (model.trim().length === 0) {
        throw new QwenWrapperError(
            'Model cannot be empty or whitespace only',
            { parameter: 'model' }
        );
    }
}

/**
 * Run Qwen in headless mode with enhanced error handling and validation.
 *
 * This function serves as a wrapper around the `runHeadless` function from
 * @qwen-code/qwen-code-core, providing:
 * - Input parameter validation
 * - Structured error handling with custom error types
 * - Consistent return format
 *
 * @async
 * @function runHeadlessWrapper
 *
 * @param {string} prompt - The prompt text to send to Qwen. Must be a non-empty
 *                          string after trimming whitespace.
 * @param {string} [model='qwen'] - The model name to use for generation.
 *                                  Must be a non-empty string after trimming.
 *                                  Defaults to 'qwen'.
 *
 * @returns {Promise<object>} A promise that resolves to the JSON output from Qwen.
 *                            The structure of the returned object depends on the
 *                            qwen-code-core package implementation.
 *
 * @throws {QwenWrapperError} When:
 *                            - Prompt or model is not a string
 *                            - Prompt or model is empty/whitespace only
 *                            - The underlying qwen-code-core call fails
 *
 * @example
 * // Basic usage
 * try {
 *     const result = await runHeadlessWrapper('Explain JavaScript closures');
 *     console.log(result);
 * } catch (error) {
 *     if (error instanceof QwenWrapperError) {
 *         console.error('Qwen wrapper error:', error.message);
 *     }
 * }
 *
 * @example
 * // Using a specific model
 * const result = await runHeadlessWrapper(
 *     'Write a Python function to calculate fibonacci numbers',
 *     'qwen-coder'
 * );
 */
export async function runHeadlessWrapper(prompt, model = 'qwen') {
    try {
        // Validate inputs before making the API call
        _validateParameters(prompt, model);

        // Call the underlying qwen-code-core function
        const result = await runHeadless(prompt, model);

        // Ensure we always return an object
        if (result === null || result === undefined) {
            throw new QwenWrapperError(
                'Qwen returned null or undefined result',
                { prompt, model, result }
            );
        }

        return result;
    } catch (error) {
        // Re-throw QwenWrapperError as-is
        if (error instanceof QwenWrapperError) {
            throw error;
        }

        // Wrap other errors in QwenWrapperError for consistent error handling
        const wrappedError = new QwenWrapperError(
            `Failed to execute Qwen: ${error.message}`,
            error
        );

        // Preserve stack trace from original error
        wrappedError.stack = error.stack;
        throw wrappedError;
    }
}

/**
 * Default export object containing the main wrapper function.
 *
 * This allows for both named and default imports:
 *
 * @example
 * // Named import
 * import { runHeadlessWrapper } from './qwen_wrapper.js';
 *
 * @example
 * // Default import
 * import qwenWrapper from './qwen_wrapper.js';
 * qwenWrapper.runHeadless('Hello');
 */
export default {
    /**
     * Alias for runHeadlessWrapper for compatibility.
     *
     * @type {typeof runHeadlessWrapper}
     */
    runHeadless: runHeadlessWrapper
};

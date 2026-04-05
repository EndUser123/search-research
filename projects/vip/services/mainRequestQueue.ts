type RequestFn<T> = () => Promise<T>;

interface QueueItem {
  request: RequestFn<any>;
  resolve: (value: any) => void;
  reject: (reason?: any) => void;
  retries: number;
}

const MAX_RETRIES = 5;
const queue: Array<QueueItem> = [];
let isProcessing = false;

// --- Dynamic Delay Configuration ---
const SAFE_START_DELAY = 4500; // Start at a safe ~13 RPM
const MIN_DELAY = 1500;        // Don't go faster than 40 RPM
const MAX_BACKOFF_DELAY = 61000; // Max wait of ~1 minute
const SUCCESS_ADJUSTMENT_FACTOR = 0.95; // Speed up by 5% on success (more conservative)
let currentDelay = SAFE_START_DELAY;

const processQueue = async () => {
  if (isProcessing || queue.length === 0) {
    isProcessing = false;
    return;
  }

  isProcessing = true;

  // Wait for the current delay *before* picking an item from the queue
  await new Promise(res => setTimeout(res, currentDelay));

  // Check if queue is still populated after the delay
  if (queue.length === 0) {
    isProcessing = false;
    return;
  }

  const item = queue.shift()!;
  const { request, resolve, reject, retries } = item;

  try {
    const result = await request();
    resolve(result);

    // On success, conservatively decrease the delay for the *next* request.
    currentDelay = Math.max(MIN_DELAY, currentDelay * SUCCESS_ADJUSTMENT_FACTOR);
    console.log(`[Queue] Request succeeded. Next delay: ${currentDelay.toFixed(0)}ms.`);

    // Immediately try to process the next item
    processQueue();

  } catch (error) {
    const errorString = JSON.stringify(error).toLowerCase();
    const isQuotaError = errorString.includes('429') ||
                         errorString.includes('resource_exhausted') ||
                         errorString.includes('user has exceeded quota');

    if (isQuotaError && retries < MAX_RETRIES) {
      console.warn(`[Queue] Quota error on attempt ${retries + 1}/${MAX_RETRIES}. Re-queueing and initiating hard backoff.`);

      // Re-add the failed request to the front of the queue
      queue.unshift({ ...item, retries: retries + 1 });

      // ** CRITICAL CHANGE **
      // On quota error, perform a hard reset to the maximum backoff time to allow the API quota to reset.
      // This directly answers "how much later?" with "in about a minute".
      currentDelay = MAX_BACKOFF_DELAY + (Math.random() * 2000 - 1000); // 61s +/- 1s jitter
      console.log(`[Queue] Hard backoff initiated. Next attempt in ~${(currentDelay / 1000).toFixed(1)} seconds.`);

      // Continue processing, which will now wait for the long backoff period.
      isProcessing = false;
      processQueue();

    } else {
      // Handle non-retryable errors or max retries exceeded
      if (retries >= MAX_RETRIES) {
          console.error(`[Queue] Request failed after ${MAX_RETRIES} retries with a quota error. Rejecting.`, error);
      } else {
          console.error(`[Queue] Non-retryable error encountered. Rejecting.`, error);
      }
      reject(error);

      // Reset delay to the safe default before continuing with the next item
      // to avoid punishing subsequent, unrelated requests.
      currentDelay = SAFE_START_DELAY;
      isProcessing = false;
      processQueue();
    }
  }
};

export const addToMainQueue = <T>(request: RequestFn<T>): Promise<T> => {
  return new Promise((resolve, reject) => {
    queue.push({ request, resolve, reject, retries: 0 });
    if (!isProcessing) {
      // Kick off the queue processor. The first request will wait for the initial `currentDelay`.
      // Reset the delay to the safe default in case it was modified by a previous batch.
      currentDelay = SAFE_START_DELAY;
      processQueue();
    }
  });
};

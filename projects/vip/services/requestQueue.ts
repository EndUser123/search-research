type RequestFn<T> = () => Promise<T>;

const queue: Array<{ request: RequestFn<any>, resolve: (value: any) => void, reject: (reason?: any) => void }> = [];
let isProcessing = false;
// Increased delay to stay well within typical API rate limits (e.g., 60 QPM).
// 1100ms allows for ~54 requests per minute, providing a safe buffer.
const DELAY_BETWEEN_REQUESTS = 1100; // ms

const processQueue = async () => {
  if (isProcessing || queue.length === 0) {
    return;
  }

  isProcessing = true;
  const { request, resolve, reject } = queue.shift()!;

  try {
    const result = await request();
    resolve(result);
  } catch (error) {
    reject(error);
  } finally {
    setTimeout(() => {
        isProcessing = false;
        processQueue();
    }, DELAY_BETWEEN_REQUESTS);
  }
};

export const addToThumbnailQueue = <T>(request: RequestFn<T>): Promise<T> => {
  return new Promise((resolve, reject) => {
    queue.push({ request, resolve, reject });
    if (!isProcessing) {
      processQueue();
    }
  });
};

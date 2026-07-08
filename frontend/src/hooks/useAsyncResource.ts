import { useEffect, useState } from "react";

type AsyncResourceState<T> = {
  data: T | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
};

export function useAsyncResource<T>(
  loader: () => Promise<T>,
  deps: readonly unknown[] = [],
): AsyncResourceState<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      const nextData = await loader();
      setData(nextData);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error ? caughtError.message : "Unable to load this section.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, deps);

  return { data, isLoading, error, refresh };
}

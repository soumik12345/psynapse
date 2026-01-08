import { useState, useEffect } from "react";
import type { FunctionSchema } from "../types/schema";
import { api } from "../utils/api";

export const useSchema = () => {
  const [schemas, setSchemas] = useState<FunctionSchema[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSchemas = async () => {
      try {
        setLoading(true);
        const data = await api.getSchemas();
        setSchemas(data);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch schemas",
        );
        console.error("Error fetching schemas:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchSchemas();
  }, []);

  return { schemas, loading, error };
};

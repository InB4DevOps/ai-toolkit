'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/utils/api';
import type { MediaCounts } from '@/server/mediaFiles';

export default function useDatasetCounts() {
  const [counts, setCounts] = useState<Record<string, MediaCounts>>({});
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  const refreshCounts = () => {
    setStatus('loading');
    apiClient
      .get('/api/datasets/counts')
      .then(res => res.data)
      .then((data: Record<string, MediaCounts>) => {
        console.log('Dataset counts:', data);
        setCounts(data ?? {});
        setStatus('success');
      })
      .catch(error => {
        console.error('Error fetching dataset counts:', error);
        setStatus('error');
      });
  };
  useEffect(() => {
    refreshCounts();
  }, []);

  return { counts, setCounts, status, refreshCounts };
}

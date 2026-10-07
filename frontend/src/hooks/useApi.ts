import { useState, useEffect, useCallback, useRef } from 'react'
import { getCached, setCached } from '../lib/cache'
import {
  fetchOverview, fetchFraudTrend, fetchRiskDistribution, fetchFraudByCategory,
  fetchAnomalyDistribution, fetchBehaviorAnalytics, fetchTransactions,
  fetchTransaction, fetchCustomers, fetchCustomer, fetchAlerts,
  fetchModelInfo, fetchModelMetrics, fetchTrainingHistory,
  fetchGeospatialData, fetchImpossibleTravel
} from '../services/api'
import type {
  OverviewStats, FraudTrendPoint, RiskDistribution, CategoryFraud,
  AnomalyBin, BehaviorData, Transaction, TransactionDetail,
  TransactionListResponse, CustomerSummary, CustomerProfile,
  CustomerListResponse, Alert, ModelInfo, ModelMetrics, TrainingEpoch,
  GeoPoint, ImpossibleTravel
} from '../types'

interface ApiState<T> {
  data: T | null
  loading: boolean
  error: string | null
  refetch: () => void
}

function useApi<T>(
  cacheKey: string,
  fetchFn: () => Promise<T>,
  deps: unknown[] = []
): ApiState<T> {
  const cached = getCached<T>(cacheKey)
  const [data, setData] = useState<T | null>(cached)
  const [loading, setLoading] = useState(!cached)
  const [error, setError] = useState<string | null>(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  const load = useCallback(async (force = false) => {
    // Return cached data immediately without showing spinner
    if (!force) {
      const hit = getCached<T>(cacheKey)
      if (hit) {
        setData(hit)
        setLoading(false)
        return
      }
    }
    setLoading(true)
    setError(null)
    try {
      const result = await fetchFn()
      if (mountedRef.current) {
        setData(result)
        setCached(cacheKey, result)
      }
    } catch (e: unknown) {
      if (mountedRef.current) {
        setError(e instanceof Error ? e.message : 'An error occurred')
      }
    } finally {
      if (mountedRef.current) setLoading(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cacheKey, ...deps])

  useEffect(() => { load() }, [load])

  return { data, loading, error, refetch: () => load(true) }
}

export function useOverview(): ApiState<OverviewStats> {
  return useApi('overview', fetchOverview)
}

export function useFraudTrend(period: string): ApiState<FraudTrendPoint[]> {
  return useApi(`fraud-trend-${period}`, () => fetchFraudTrend(period), [period])
}

export function useRiskDistribution(): ApiState<RiskDistribution> {
  return useApi('risk-distribution', fetchRiskDistribution)
}

export function useFraudByCategory(): ApiState<CategoryFraud[]> {
  return useApi('fraud-by-category', fetchFraudByCategory)
}

export function useAnomalyDistribution(): ApiState<AnomalyBin[]> {
  return useApi('anomaly-distribution', fetchAnomalyDistribution)
}

export function useBehaviorAnalytics(): ApiState<BehaviorData> {
  return useApi('behavior-analytics', fetchBehaviorAnalytics)
}

export function useTransactions(params: Parameters<typeof fetchTransactions>[0] = {}): ApiState<TransactionListResponse> {
  const key = `transactions-${JSON.stringify(params)}`
  return useApi(key, () => fetchTransactions(params), [key])
}

export function useTransaction(id: string): ApiState<TransactionDetail> {
  return useApi(`transaction-${id}`, () => fetchTransaction(id), [id])
}

export function useCustomers(params: Parameters<typeof fetchCustomers>[0] = {}): ApiState<CustomerListResponse> {
  const key = `customers-${JSON.stringify(params)}`
  return useApi(key, () => fetchCustomers(params), [key])
}

export function useCustomer(id: string): ApiState<CustomerProfile> {
  return useApi(`customer-${id}`, () => fetchCustomer(id), [id])
}

export function useAlerts(): ApiState<Alert[]> {
  return useApi('alerts', () => fetchAlerts({ limit: 50 }))
}

export function useModelInfo(): ApiState<ModelInfo> {
  return useApi('model-info', fetchModelInfo)
}

export function useModelMetrics(): ApiState<ModelMetrics> {
  return useApi('model-metrics', fetchModelMetrics)
}

export function useTrainingHistory(): ApiState<TrainingEpoch[]> {
  return useApi('training-history', fetchTrainingHistory)
}

export function useGeospatialData(): ApiState<GeoPoint[]> {
  return useApi('geospatial', fetchGeospatialData)
}

export function useImpossibleTravel(): ApiState<ImpossibleTravel[]> {
  return useApi('impossible-travel', fetchImpossibleTravel)
}

export default useApi

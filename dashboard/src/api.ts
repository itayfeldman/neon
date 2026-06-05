import axios from 'axios'

const http = axios.create({ baseURL: '/stock' })
const api = axios.create()

export interface HistoryResponse {
  dates: string[]
  opens: number[]
  highs: number[]
  lows: number[]
  closes: number[]
  volumes: number[]
}

export interface OptionRow {
  strike: number
  iv: number
  bid: number
  ask: number
  volume: number
  option_type: 'call' | 'put'
}

export interface OptionsResponse {
  calls: OptionRow[]
  puts: OptionRow[]
}

export interface GreeksRow {
  strike: number
  option_type: 'call' | 'put'
  delta: number
  gamma: number
  vega: number
  theta: number
}

export interface GreeksResponse {
  rows: GreeksRow[]
}

export const fetchHistory = (ticker: string, period = '1y') =>
  http.get<HistoryResponse>(`/${ticker}/history`, { params: { period } }).then(r => r.data)

export const fetchOptions = (ticker: string, expiry: string) =>
  http.get<OptionsResponse>(`/${ticker}/options/${expiry}`).then(r => r.data)

export const fetchGreeks = (ticker: string, expiry: string) =>
  http.get<GreeksResponse>(`/${ticker}/greeks/${expiry}`).then(r => r.data)

export interface SurfaceResponse {
  strikes: number[]
  expiries: string[]
  vols: number[][]
}

export const fetchSviSurface = (ticker: string) =>
  http.get<SurfaceResponse>(`/${ticker}/svi-surface`).then(r => r.data)

export interface PositionRequest {
  ticker: string
  expiry: string
  strike: number
  option_type: 'call' | 'put'
  quantity: number
}

export interface PortfolioGreeksResponse {
  delta: number
  gamma: number
  vega: number
  theta: number
}

export const fetchPortfolioGreeks = (positions: PositionRequest[]) =>
  api.post<PortfolioGreeksResponse>('/portfolio/greeks', { positions }).then(r => r.data)

export interface BondRequest {
  face_value: number
  coupon_rate: number
  coupon_freq: number
  issue_date: string
  maturity_date: string
  ytm: number
}

export interface BondResponse {
  dirty_price: number
  clean_price: number
  accrued_interest: number
  modified_duration: number
  macaulay_duration: number
  dv01: number
  convexity: number
}

export const fetchBondPrice = (req: BondRequest) =>
  api.post<BondResponse>('/bonds/price', req).then(r => r.data)

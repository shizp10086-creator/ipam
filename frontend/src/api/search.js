import request from './request'

/**
 * 全局搜索
 */
export function globalSearch(query, limit = 10) {
  return request({
    url: '/search',
    method: 'get',
    params: {
      q: query,
      limit
    }
  })
}
